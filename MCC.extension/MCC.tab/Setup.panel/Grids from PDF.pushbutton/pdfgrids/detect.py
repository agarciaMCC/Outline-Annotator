"""MCC - grids from PDF plan sheets (runs under regular CPython 3 + PyMuPDF).

Called by the Grids from PDF pyRevit button:
    python detect.py --out result.json [--scale auto|3/32] [--check-dir DIR]
                     SHEET.pdf:PAGE [SHEET2.pdf:PAGE ...]

Per sheet:
 1. bubbles  = circles of the common bubble size with a short label inside
 2. grid line = the line leaving the bubble through its centre (elbow
    leaders followed), dashes joined along it
 3. angle families (parallel grids); angles snapped to a clean value
 4. scale    = read from grid dimensions (auto) or given
 5. spacing  = called-out dimension between neighbours governs; gaps with
    no dimension keep the measured value (flagged)
Across sheets: sheets are registered on their common grids, then every gap
is compared. Called-out values that disagree -> conflict (user picks).
"""
import argparse, collections, json, math, os, re, statistics, sys

import pymupdf

GAP_BUBBLES = 7          # dashes may be up to 7 bubble diameters apart
DIM_TOL_FT = 3 / 12.0    # a dimension must be within 3" of the measured gap
SAME_TOL_FT = 1 / 32.0 / 12  # called-out values "equal" within 1/32"
PLACE_TOL_FT = 0.25 / 12     # geometric placement agreement 1/4"
STD_SCALES = [  # (label, inches of paper per foot)
    ('1/32" = 1\'-0"', 1 / 32), ('1/16" = 1\'-0"', 1 / 16), ('3/32" = 1\'-0"', 3 / 32),
    ('1/8" = 1\'-0"', 1 / 8), ('3/16" = 1\'-0"', 3 / 16), ('1/4" = 1\'-0"', 1 / 4),
    ('3/8" = 1\'-0"', 3 / 8), ('1/2" = 1\'-0"', 1 / 2), ('3/4" = 1\'-0"', 3 / 4),
    ('1" = 1\'-0"', 1.0), ('1" = 10\'', 1 / 10), ('1" = 20\'', 1 / 20), ('1" = 30\'', 1 / 30),
    ('1" = 40\'', 1 / 40), ('1" = 50\'', 1 / 50), ('1" = 60\'', 1 / 60), ('1" = 100\'', 1 / 100)]


def parse_scale(txt):
    """'3/32' or '3/32" = 1'-0"' or '1"=20'' -> inches per foot."""
    t = txt.replace(' ', '')
    try:
        return float(t)                       # inches of paper per foot
    except ValueError:
        pass
    for lab, v in STD_SCALES:
        if t == lab.replace(' ', ''):
            return v
    m = re.fullmatch(r'(\d+)/(\d+)"?(=1\'-0")?', t)
    if m:
        return int(m.group(1)) / int(m.group(2))
    m = re.fullmatch(r'1"=(\d+)\'', t)
    if m:
        return 1 / int(m.group(1))
    m = re.fullmatch(r'([\d.]+)"(=1\'-0")?', t)          # our own label for odd scales
    if m:
        return float(m.group(1))
    raise ValueError('scale not understood: ' + txt)


def printed_scale(texts):
    """Most common scale note printed on the sheet (view titles), or None."""
    found = collections.Counter()
    for x in texts:
        t = x['text'].upper().replace(' ', '').replace('\u2019', "'").replace('\u201d', '"')
        for m in re.finditer(r'(\d+)/(\d+)"=1\'-0"', t):
            found[int(m.group(1)) / int(m.group(2))] += 1
        for m in re.finditer(r'(?<![/\d])(\d)"=1\'-0"', t):
            found[float(m.group(1))] += 1
        for m in re.finditer(r'(?<![/\d])1"=(\d+)\'(?!-)', t):
            found[1.0 / int(m.group(1))] += 1
    return found.most_common(1)[0][0] if found else None


def scale_label(ipf):
    for lab, v in STD_SCALES:
        if abs(v - ipf) < 1e-9:
            return lab
    return '%.4f" = 1\'-0"' % ipf


def ftin(ft):
    s = '-' if ft < 0 else ''
    ft = abs(ft)
    tot = round(ft * 12 * 8) / 8.0            # nearest 1/8"
    f, i = int(tot // 12), tot - 12 * int(tot // 12)
    whole = int(i)
    frac = i - whole
    fr = '' if frac == 0 else ' %d/%d' % (
        [(1, 8), (1, 4), (3, 8), (1, 2), (5, 8), (3, 4), (7, 8)][int(round(frac * 8)) - 1])
    return '%s%d\'-%d%s"' % (s, f, whole, fr)


def dim_value(t):
    m = re.fullmatch(r"(\d+)' ?- ?(\d+)(?:\s?(\d+)/(\d+))?\"", t.strip())
    if not m:
        return None
    ft, i, n, d = m.groups()
    return int(ft) + (int(i) + (int(n) / int(d) if n else 0)) / 12.0


# ---------------------------------------------------------------------------
# geometry helpers (page points, display orientation, y down)
# ---------------------------------------------------------------------------
class Seg(object):
    __slots__ = ('a', 'b', 'L', 'u')

    def __init__(self, a, b):
        self.a, self.b = a, b
        self.L = math.dist(a, b)
        self.u = ((b[0] - a[0]) / self.L, (b[1] - a[1]) / self.L)


def perp(p, o, u):
    return abs((p[0] - o[0]) * u[1] - (p[1] - o[1]) * u[0])


def cross(u, v):
    return u[0] * v[1] - u[1] * v[0]


def load_page(path, page_no):
    doc = pymupdf.open(path)
    if not 1 <= page_no <= len(doc):
        raise SystemExit('%s has %d page(s); page %d asked' % (path, len(doc), page_no))
    page = doc[page_no - 1]
    M = page.rotation_matrix

    def T(pt):
        q = pymupdf.Point(pt) * M
        return (q.x, q.y)

    def Tdir(v):
        q = pymupdf.Point(v) * M - pymupdf.Point(0, 0) * M
        return (q.x, q.y)

    segs, circles = [], []
    for x in page.get_drawings():
        it = x['items']
        r = x['rect']
        if it and len(it) >= 4 and all(i[0] == 'c' for i in it):
            if abs(r.width - r.height) < 0.5 and r.width > 8:
                circles.append((T(((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)), r.width / 2))
        elif it and len(it) >= 8 and all(i[0] == 'l' for i in it) and r.width > 8 \
                and abs(r.width - r.height) < 0.05 * r.width + 0.5:
            # bubble drawn as a polyline circle (some CAD exports, e.g. DCI)
            cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
            ds = [math.dist((cx, cy), (i[1].x, i[1].y)) for i in it]
            if max(ds) - min(ds) < 0.12 * r.width / 2:
                circles.append((T((cx, cy)), r.width / 2))
        elif it and len(it) == 1 and it[0][0] == 're' and 12 < r.width < 70 \
                and abs(r.width - r.height) < 0.05 * r.width + 0.5:
            # square grid tags (1215 parking); kept only if they are the common tag size
            circles.append((T(((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)), r.width / 2))
        for i in it:
            if i[0] == 'l':
                a, b = T(i[1]), T(i[2])
                if math.dist(a, b) > 0.5:
                    segs.append(Seg(a, b))
    words = [(T(((w[0] + w[2]) / 2, (w[1] + w[3]) / 2)), w[4]) for w in page.get_text('words')]
    texts = []
    for blk in page.get_text('dict')['blocks']:
        for ln in blk.get('lines', []):
            t = ''.join(s['text'] for s in ln['spans']).strip()
            r = ln['bbox']
            texts.append(dict(text=t, c=T(((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)),
                              dir=Tdir(ln['dir'])))
    return page, doc, segs, circles, words, texts


# ---------------------------------------------------------------------------
# 1-2. bubbles and their grid lines
# ---------------------------------------------------------------------------
def find_bubbles(circles, words):
    cands = []
    for c, R in circles:
        lab = ' '.join(t for p, t in words if math.dist(p, c) < R * 0.8)
        if lab and len(lab) <= 5 and ' ' not in lab:
            cands.append((c, R, lab))
    if not cands:
        return []
    common = collections.Counter(round(R * 2) for c, R, l in cands).most_common(1)[0][0]
    return [dict(c=c, R=R, label=l) for c, R, l in cands if abs(R * 2 - common) <= 1]


class Index(object):
    """Bucket segments by rounded angle so collinear searches stay fast."""

    def __init__(self, segs):
        self.by_ang = collections.defaultdict(list)
        for s in segs:
            a = math.degrees(math.atan2(s.u[1], s.u[0])) % 180
            self.by_ang[int(a)].append(s)
        self.segs = segs
        self.ends = collections.defaultdict(list)
        for s in segs:
            for p in (s.a, s.b):
                self.ends[(int(p[0] // 4), int(p[1] // 4))].append(s)

    def parallel(self, u):
        a = int(math.degrees(math.atan2(u[1], u[0])) % 180)
        for k in (a - 1, a, a + 1):
            for s in self.by_ang.get(k % 180, ()):
                yield s

    def touching(self, p, exclude):
        kx, ky = int(p[0] // 4), int(p[1] // 4)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for s in self.ends.get((kx + dx, ky + dy), ()):
                    if s is exclude:
                        continue
                    if math.dist(s.a, p) < 1.0:
                        yield s, s.a, s.b
                    elif math.dist(s.b, p) < 1.0:
                        yield s, s.b, s.a


def collinear_pts(idx, o, u, tol_ang, tol_d):
    pts = []
    for s in idx.parallel(u):
        if abs(cross(s.u, u)) < tol_ang and perp(s.a, o, u) < tol_d and perp(s.b, o, u) < tol_d:
            pts += [s.a, s.b]
    return pts


def trace_grid(idx, B, gap):
    c, R = B['c'], B['R']
    best = None
    for s in idx.segs:
        for e, o in ((s.a, s.b), (s.b, s.a)):
            de = math.dist(e, c)
            if abs(de - R) > 3 or math.dist(o, c) <= de or perp(c, s.a, s.u) > 1.5:
                continue
            u = s.u if (o[0] - e[0]) * s.u[0] + (o[1] - e[1]) * s.u[1] > 0 else (-s.u[0], -s.u[1])
            anchor, elbow = c, False
            if s.L < 4 * R:                      # maybe an elbow leader
                for q, qa, qb in idx.touching(o, s):
                    if abs(cross(q.u, u)) > 0.2:
                        for q2, q2a, q2b in idx.touching(qb, q):
                            if abs(cross(q2.u, u)) < 0.01:
                                anchor, elbow = q2a, True
            n = len(collinear_pts(idx, anchor, u, 0.01, 2.5))
            if not best or n > best[0]:
                best = (n, u, anchor, elbow)
    if not best:
        return None
    n, u, o, elbow = best
    pts = []
    for tol in ((0.01, 2.5), (0.003, 1.0)):
        pts = [p for p in collinear_pts(idx, o, u, *tol)
               if (p[0] - o[0]) * u[0] + (p[1] - o[1]) * u[1] > -1]
        if len(pts) >= 4:
            ts = sorted(((p[0] - o[0]) * u[0] + (p[1] - o[1]) * u[1], p) for p in pts)
            end = ts[0]
            for t in ts:
                if t[0] - end[0] > gap:
                    break
                end = t
            L = math.dist(end[1], o)
            if L > 50:
                u = ((end[1][0] - o[0]) / L, (end[1][1] - o[1]) / L)
    ts = sorted((p[0] - o[0]) * u[0] + (p[1] - o[1]) * u[1] for p in pts) or [R]
    end = ts[0]
    for t in ts:
        if t - end > gap:
            break
        end = max(end, t)
    start = 0 if elbow else R
    return dict(a=(o[0] + u[0] * start, o[1] + u[1] * start),
                b=(o[0] + u[0] * end, o[1] + u[1] * end), elbow=elbow)


def detect_sheet(path, page_no, scale_arg, check_dir):
    page, doc, segs, circles, words, texts = load_page(path, page_no)
    bubbles = find_bubbles(circles, words)
    warnings = []
    if not segs:
        raise SystemExit('%s p%d has no vector lines - scanned sheet?' % (path, page_no))
    if not bubbles:
        raise SystemExit('%s p%d: no grid bubbles found' % (path, page_no))
    idx = Index(segs)
    gap = GAP_BUBBLES * 2 * bubbles[0]['R']
    lines = collections.defaultdict(list)
    for B in bubbles:
        r = trace_grid(idx, B, gap)
        if r:
            lines[B['label']].append(r)
        else:
            warnings.append('bubble %s: no grid line found' % B['label'])
    # page coords -> math frame (y up), still points
    def up(p):
        return (p[0], -p[1])
    grids = []
    for lab, rs in lines.items():
        segs2 = [(up(r['a']), up(r['b']), r['elbow']) for r in rs]
        a0, b0 = segs2[0][0], segs2[0][1]
        L0 = math.dist(a0, b0) or 1
        u0 = ((b0[0] - a0[0]) / L0, (b0[1] - a0[1]) / L0)
        same = all(perp(s[0], a0, u0) < 1.0 and perp(s[1], a0, u0) < 1.0 for s in segs2[1:])
        if len(segs2) > 1 and same:
            pts = [p for s in segs2 for p in s[:2]]
            pa, pb = max(((p, q) for p in pts for q in pts), key=lambda z: math.dist(*z))
            segs2 = [(pa, pb, any(s[2] for s in segs2))]
        for k, (pa, pb, elbow) in enumerate(segs2):
            g = dict(label=lab if k == 0 else '%s #%d' % (lab, k + 1), a=pa, b=pb, flags=[])
            if elbow:
                g['flags'].append('bubble on elbow leader - grid placed on the line, not the bubble')
            if k:
                g['flags'].append('second "%s" bubble not in line with the first - excluded' % lab)
                g['exclude'] = True
            grids.append(g)
    # 3. families by angle
    for g in grids:
        dx, dy = g['b'][0] - g['a'][0], g['b'][1] - g['a'][1]
        ang = math.degrees(math.atan2(dy, dx)) % 180
        g['ang'] = ang - 180 if ang > 179.4 else ang
    order = sorted((g for g in grids if not g.get('exclude')), key=lambda g: g['ang'])
    fams, cur = [], []
    for g in order:
        if cur and g['ang'] - cur[-1]['ang'] > 0.6:
            fams.append(cur)
            cur = []
        cur.append(g)
    if cur:
        fams.append(cur)
    families = []
    for fg in fams:
        med = statistics.median(g['ang'] for g in fg)
        ang = round(med) if abs(med - round(med)) < 0.05 else round(med, 2)
        th = math.radians(ang)
        t, n = (math.cos(th), math.sin(th)), (-math.sin(th), math.cos(th))
        for g in fg:
            if abs(g['ang'] - ang) > 0.05:
                g['flags'].append('angle %.2f deg straightened to %g deg' % (g['ang'], ang))
            mid = ((g['a'][0] + g['b'][0]) / 2, (g['a'][1] + g['b'][1]) / 2)
            g['off'] = mid[0] * n[0] + mid[1] * n[1]
            al = sorted(p[0] * t[0] + p[1] * t[1] for p in (g['a'], g['b']))
            g['along'] = al
        fg.sort(key=lambda g: g['off'])
        if len(fg) == 1:
            fg[0]['flags'].append('only grid at this angle')
        families.append(dict(angle=ang, t=t, n=n, grids=fg))
    # dimension strings
    dims = []
    for x in texts:
        v = dim_value(x['text'])
        if v is not None:
            c = up(x['c'])
            dims.append(dict(text=x['text'], v=v, c=c, dir=(x['dir'][0], -x['dir'][1])))

    def dims_between(f, a, b):
        n = f['n']
        for d in dims:
            if abs(d['dir'][0] * n[0] + d['dir'][1] * n[1]) > 0.95:
                o = d['c'][0] * n[0] + d['c'][1] * n[1]
                if a['off'] < o < b['off']:
                    yield d
    # 4. scale
    ratios = []
    for f in families:
        for a, b in zip(f['grids'], f['grids'][1:]):
            m = b['off'] - a['off']
            ds = list(dims_between(f, a, b))
            if ds:
                # the dimension nearest the midpoint between the grids
                mid = (a['off'] + b['off']) / 2
                d = min(ds, key=lambda d: abs(d['c'][0] * f['n'][0] + d['c'][1] * f['n'][1] - mid))
                ratios.append(m / d['v'] / 72.0)       # inches paper per foot
    auto = None
    if ratios:
        mode = collections.Counter(round(r, 3) for r in ratios).most_common(1)[0][0]
        close = [r for r in ratios if abs(r - mode) / mode < 0.02]
        est = statistics.median(close)
        near = min(STD_SCALES, key=lambda s: abs(s[1] - est) / s[1])
        auto = near[1] if abs(near[1] - est) / near[1] < 0.015 else est
    printed = printed_scale(texts)
    if auto is not None and not any(abs(v - auto) / v < 0.015 for lab, v in STD_SCALES) and printed:
        warnings.append('grid dimensions read as an odd scale (%s) - using the printed scale %s'
                        % (scale_label(auto), scale_label(printed)))
        auto, close = printed, []
    if auto is None and printed:
        auto, close = printed, []
        warnings.append('no grid dimensions to check the scale - using the printed scale %s' % scale_label(printed))
    if scale_arg == 'auto':
        if auto is None:
            raise SystemExit('%s p%d: could not read the scale from grid dimensions - '
                             'pick the scale in the dialog' % (path, page_no))
        ipf, src = auto, ('read from %d grid dimensions' % len(close)) if close else 'printed on the sheet'
    else:
        ipf, src = parse_scale(scale_arg), 'entered'
        if auto and abs(auto - ipf) / ipf > 0.015:
            warnings.append('scale entered %s but grid dimensions read as %s'
                            % (scale_label(ipf), scale_label(auto)))
    ppf = 72.0 * ipf                                    # points per foot
    # 5. govern spacing, positions in feet
    out_fams = []
    for f in families:
        gs = f['grids']
        gaps = []
        for a, b in zip(gs, gs[1:]):
            m = (b['off'] - a['off']) / ppf
            best = None
            for d in dims_between(f, a, b):
                if abs(d['v'] - m) < DIM_TOL_FT and (not best or abs(d['v'] - m) < abs(best['v'] - m)):
                    best = d
            gaps.append(dict(a=a['label'], b=b['label'], measured=m,
                             value=best['v'] if best else round(m * 96) / 96.0,
                             text=best['text'] if best else None))
        cum = [0.0]
        for g in gaps:
            cum.append(cum[-1] + g['value'])
        p0 = sum(g['off'] / ppf - c for g, c in zip(gs, cum)) / len(gs)
        out_fams.append(dict(
            angle=f['angle'], t=f['t'], n=f['n'], gaps=gaps,
            grids=[dict(label=g['label'], pos=round(p0 + c, 6),
                        measured=round(g['off'] / ppf, 6),
                        along=[round(v / ppf, 4) for v in g['along']], flags=g['flags'])
                   for g, c in zip(gs, cum)]))
    excluded = [dict(label=g['label'], flags=g['flags']) for g in grids if g.get('exclude')]
    name = os.path.splitext(os.path.basename(path))[0]
    if len(doc) > 1:
        name += ' p%d' % page_no
    check = None
    if check_dir:
        try:
            check = draw_check(path, page_no, grids, check_dir, name)
        except Exception as ex:                  # never fail the run over it
            warnings.append('check PDF not saved (%s)' % str(ex).splitlines()[-1][:120])
    return dict(name=name, file=path, page=page_no, scale=scale_label(ipf), scale_source=src,
                bubbles=len(bubbles), families=out_fams, excluded=excluded,
                warnings=warnings, check_pdf=check)


def draw_check(path, page_no, grids, folder, name):
    doc = pymupdf.open(path)
    page = doc[page_no - 1]
    IM = page.derotation_matrix
    sh = page.new_shape()
    bad = page.new_shape()
    for g in grids:
        a = pymupdf.Point(g['a'][0], -g['a'][1]) * IM
        b = pymupdf.Point(g['b'][0], -g['b'][1]) * IM
        (bad if g.get('exclude') else sh).draw_line(a, b)
    sh.finish(color=(1, 0, 0), width=3, stroke_opacity=0.5)
    sh.commit()
    bad.finish(color=(1, 0.6, 0), width=3, stroke_opacity=0.6, dashes='[12 6] 0')
    bad.commit()
    # clear old check PDFs that aren't open anywhere; a new name each run
    # so one left open in a PDF viewer never blocks the save
    import glob, time
    for old in glob.glob(os.path.join(folder, name + ' - detected grids*.pdf')):
        try:
            os.remove(old)
        except OSError:
            pass
    out = os.path.join(folder, '%s - detected grids %s.pdf' % (name, time.strftime('%H%M%S')))
    doc.select([page_no - 1])
    doc.save(out)
    return out


# ---------------------------------------------------------------------------
# combine sheets
# ---------------------------------------------------------------------------
def register(ref, other):
    """Rotation + translation taking `other` sheet coordinates onto `ref`,
    fitted on grids both sheets share (by label)."""
    rl = {g['label']: (f, g) for f in ref['families'] for g in f['grids']}
    ol = {g['label']: (f, g) for f in other['families'] for g in f['grids']}
    common = [k for k in rl if k in ol]
    if len(common) < 3:
        return None
    dang = statistics.median(((rl[k][0]['angle'] - ol[k][0]['angle'] + 90) % 180) - 90 for k in common)
    # rotate other's families by dang (angles, normals, positions unchanged by rotation about origin)
    th = math.radians(dang)
    cs, sn = math.cos(th), math.sin(th)
    for f in other['families']:
        f['angle'] = round(f['angle'] + dang, 4)
        t, n = f['t'], f['n']
        f['t'] = (t[0] * cs - t[1] * sn, t[0] * sn + t[1] * cs)
        f['n'] = (n[0] * cs - n[1] * sn, n[0] * sn + n[1] * cs)
    # translation: n_f . T = pos_ref - pos_other, least squares
    A = [[0, 0], [0, 0]]
    y = [0, 0]
    for k in common:
        n = rl[k][0]['n']
        d = rl[k][1]['pos'] - ol[k][1]['pos']
        for i in range(2):
            y[i] += n[i] * d
            for j in range(2):
                A[i][j] += n[i] * n[j]
    det = A[0][0] * A[1][1] - A[0][1] * A[1][0]
    if abs(det) < 1e-6:
        return None
    Tx = (y[0] * A[1][1] - y[1] * A[0][1]) / det
    Ty = (A[0][0] * y[1] - A[1][0] * y[0]) / det
    for f in other['families']:
        sh = Tx * f['n'][0] + Ty * f['n'][1]
        sa = Tx * f['t'][0] + Ty * f['t'][1]
        for g in f['grids']:
            g['pos'] += sh
            g['measured'] += sh
            g['along'] = [v + sa for v in g['along']]
    return dict(rotation=dang, translation=(Tx, Ty), common=len(common))


def combine(sheets):
    ref = sheets[0]
    notes = []
    for s in sheets[1:]:
        r = register(ref, s)
        if r is None:
            notes.append('%s shares fewer than 3 grids with %s - kept separate' % (s['name'], ref['name']))
            s['skip'] = True
        else:
            s['registration'] = r
    use = [s for s in sheets if not s.get('skip')]
    # match families across sheets by angle
    fams = []
    for s in use:
        for f in s['families']:
            tgt = next((F for F in fams if abs(((F['angle'] - f['angle'] + 90) % 180) - 90) < 0.3), None)
            if tgt is None:
                tgt = dict(angle=f['angle'], t=f['t'], n=f['n'], per_sheet={})
                fams.append(tgt)
            tgt['per_sheet'][s['name']] = f
    out = []
    for F in fams:
        # union of labels ordered by position
        pos = {}
        for sname, f in F['per_sheet'].items():
            for g in f['grids']:
                pos.setdefault(g['label'], []).append((sname, g))
        labels = sorted(pos, key=lambda k: statistics.mean(g['pos'] for s, g in pos[k]))
        grids = []
        for k in labels:
            sheets_with = [s for s, g in pos[k]]
            flags = []
            for s, g in pos[k]:
                for fl in g['flags']:
                    fl2 = fl if len(use) == 1 else '%s: %s' % (s, fl)
                    if fl2 not in flags:
                        flags.append(fl2)
            if len(use) > 1 and len(sheets_with) < len(use):
                flags.append('only on ' + ', '.join(sheets_with))
            first = pos[k][0][1]
            grids.append(dict(label=k, sheets=sheets_with, along=first['along'], flags=flags))
        # gaps between neighbours
        gaps = []
        for a, b in zip(labels, labels[1:]):
            opts = []
            for sname, f in F['per_sheet'].items():
                L = [g['label'] for g in f['grids']]
                if a in L and b in L:
                    i, j = L.index(a), L.index(b)
                    run = f['gaps'][i:j]
                    val = sum(g['value'] for g in run)
                    dimmed = all(g['text'] for g in run)
                    txt = ' + '.join(g['text'] or ftin(g['value']) for g in run)
                    opts.append(dict(sheet=sname, value=round(val, 6), dimmed=dimmed,
                                     text=txt if dimmed else txt + ' (measured)'))
            gap = dict(a=a, b=b, options=opts, conflict=False, choice=0, note='')
            dimmed = [o for o in opts if o['dimmed']]
            if not opts:
                # neighbours never on the same sheet: take position difference
                pa = statistics.mean(g['pos'] for s, g in pos[a])
                pb = statistics.mean(g['pos'] for s, g in pos[b])
                gap['options'] = [dict(sheet='combined', value=round(pb - pa, 6), dimmed=False,
                                       text=ftin(pb - pa) + ' (from placement)')]
                gap['note'] = 'not dimensioned on any sheet'
            elif dimmed:
                vals = sorted(set(round(o['value'] / SAME_TOL_FT) for o in dimmed))
                if len(vals) > 1:
                    gap['conflict'] = True
                    gap['choice'] = None
                    gap['options'] = dimmed
                    gap['note'] = 'sheets call out different dimensions - pick one'
                else:
                    gap['choice'] = opts.index(dimmed[0])
                    if len(dimmed) < len(opts):
                        gap['note'] = 'dimensioned on %s only - that value used' % dimmed[0]['sheet']
            else:
                spread = max(o['value'] for o in opts) - min(o['value'] for o in opts)
                if spread > PLACE_TOL_FT:
                    gap['conflict'] = True
                    gap['choice'] = None
                    gap['note'] = 'no dimension on any sheet and measurements differ - pick one'
                else:
                    gap['note'] = 'no dimension - measured value used'
            gaps.append(gap)
        # placement of the family: fit the combined spacing chain to each
        # sheet's measured grid positions; p0 = position of the first grid
        cum = {labels[0]: 0.0}
        for gp, b in zip(gaps, labels[1:]):
            o = gp['options'][gp['choice'] if gp['choice'] is not None else 0]
            cum[b] = cum[gp['a']] + o['value']
        popts = []
        for sname in F['per_sheet']:
            r = [g['measured'] - cum[k] for k in labels for s, g in pos[k] if s == sname]
            popts.append(dict(sheet=sname, p0=round(statistics.mean(r), 6)))
        spread = max(o['p0'] for o in popts) - min(o['p0'] for o in popts)
        place = dict(first=labels[0], options=popts, conflict=spread > PLACE_TOL_FT,
                     choice=0, p0=round(statistics.mean(o['p0'] for o in popts), 6), note='')
        if place['conflict']:
            place['choice'] = None
            place['note'] = ('the sheets place this grid family %s apart (no dimension ties it '
                             'to the other grids) - pick one' % ftin(spread))
        out.append(dict(angle=F['angle'], t=F['t'], n=F['n'], grids=grids, gaps=gaps,
                        placement=place))
    return dict(version=1, sheets=[{k: v for k, v in s.items() if k != 'families'} for s in sheets],
                families=out, notes=notes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--scale', default='auto')
    ap.add_argument('--check-dir')
    ap.add_argument('sheets', nargs='+', help='file.pdf[:page]')
    a = ap.parse_args()
    sheets = []
    for s in a.sheets:
        m = re.fullmatch(r'(.+?)(?::(\d+))?', s)
        path, page = m.group(1), int(m.group(2) or 1)
        sheets.append(detect_sheet(path, page, a.scale, a.check_dir))
    res = combine(sheets)
    with open(a.out, 'w') as fh:
        json.dump(res, fh, indent=1)
    n = sum(len(f['grids']) for f in res['families'])
    c = sum(g['conflict'] for f in res['families'] for g in f['gaps']) + \
        sum(f['placement']['conflict'] for f in res['families'])
    print('OK %d grids, %d conflict(s)' % (n, c))


if __name__ == '__main__':
    try:
        main()
    except SystemExit as e:
        if e.code not in (None, 0):
            sys.stderr.write(str(e.code) + '\n')
            sys.exit(2)
