"""MCC - columns from a PDF plan sheet + column schedule sheet(s).
Runs under regular CPython 3 + PyMuPDF (same Python the Grids from PDF button uses).

    python columns.py --out result.json --plan PLAN.pdf:PAGE --schedule SCHED.pdf
                      --level 1 [--scale auto|0.09375] [--check-dir DIR]
    python columns.py --out types.json --schedule SCHED.pdf --types-only

Plan: gray-filled column shapes (true outline = the clip path drawn with the
fill), each mark label followed along its leader to its column, size callout
next to the mark. Grids are read with the Grids from PDF engine, so column
positions come out in the same sheet coordinates (feet, y up) as the grids.
Schedule: see schedule.py (grid, transposed and list layouts; any level names).
"""
import argparse, collections, json, math, os, re, statistics, sys

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
GRIDS = os.path.join(HERE, '..', '..', 'Grids from PDF.pushbutton', 'pdfgrids')
sys.path.insert(0, os.path.normpath(GRIDS))
sys.path.insert(0, HERE)
import detect as GD                                    # noqa: E402

from schedule import (MARK_RE, parse_schedule, family_for, lookup, all_types,  # noqa: E402
                      norm_level, summary)


# ---------------------------------------------------------------------------
# plan
# ---------------------------------------------------------------------------
def _hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def _minrect(h):
    best = None
    for i in range(len(h)):
        a, b = h[i], h[(i + 1) % len(h)]
        L = math.dist(a, b)
        if L < 1e-6:
            continue
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        n = (-u[1], u[0])
        s = [x * u[0] + y * u[1] for x, y in h]
        t = [x * n[0] + y * n[1] for x, y in h]
        A = (max(s) - min(s)) * (max(t) - min(t))
        if not best or A < best[0]:
            cs, ct = (min(s) + max(s)) / 2, (min(t) + max(t)) / 2
            best = (A, max(s) - min(s), max(t) - min(t), u,
                    (cs * u[0] + ct * n[0], cs * u[1] + ct * n[1]))
    return best


def mark_prefix(m):
    return re.match(r'[A-Z]*-?', m).group(0)


def plan_columns(path, page_no, ppf, prefixes=None):
    """Columns in sheet feet, y up (same frame as the grid engine)."""
    doc = pymupdf.open(path)
    p = doc[page_no - 1]
    M = p.rotation_matrix

    def T(x, y):                     # page -> display -> feet, y up
        q = pymupdf.Point(x, y) * M
        return (q.x / ppf, -q.y / ppf)
    DX = p.get_drawings(extended=True)
    fill_rgb = collections.Counter()
    for d in DX:
        f = d.get('fill')
        if d['type'] in ('f', 'fs') and f and abs(f[0] - f[1]) < 0.02 and abs(f[1] - f[2]) < 0.02 \
                and 0.3 < f[0] < 0.92:
            fill_rgb[round(f[0], 2)] += 1
    gray = fill_rgb.most_common(1)[0][0] if fill_rgb else 0.76
    cols, clips = [], []
    for d in DX:
        if d['type'] == 'clip':
            clips = (clips + [d])[-6:]
            continue
        f = d.get('fill')
        if not (d['type'] in ('f', 'fs') and f and abs(f[0] - gray) < 0.01):
            continue
        r = d['rect']
        clip = next((c for c in reversed(clips) if c.get('scissor') and abs(c['scissor'].x0 - r.x0) < 0.5
                     and abs(c['scissor'].y1 - r.y1) < 0.5), None)
        pts, ncurve = [], 0
        for it in (clip['items'] if clip else []):
            if it[0] == 'l':
                pts += [(it[1].x, it[1].y), (it[2].x, it[2].y)]
            elif it[0] == 'c':
                pts += [(q.x, q.y) for q in it[1:]]
                ncurve += 1
            elif it[0] == 're':
                R = it[1]
                pts += [(R.x0, R.y0), (R.x1, R.y0), (R.x1, R.y1), (R.x0, R.y1)]
            elif it[0] == 'qu':
                pts += [(q.x, q.y) for q in it[1]]
        if len(pts) < 3:
            pts = [(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1)]
        fpts = [T(x, y) for x, y in pts]
        A, a, b, u, c = _minrect(_hull([(round(x, 4), round(y, 4)) for x, y in fpts]))
        cols.append(dict(center=c, a=a, b=b, u=u, bbox=r, curves=ncurve, gray=gray))
    # labels
    words = p.get_text('words')
    marks = []
    for w in words:                     # the same text drawn twice on top of itself = one label
        if re.fullmatch(MARK_RE, w[4]) and (not prefixes or mark_prefix(w[4]) in prefixes) and not any(
                m[4] == w[4] and abs(m[0] - w[0]) < 2 and abs(m[1] - w[1]) < 2 for m in marks):
            marks.append(w)
    sizes = [w for w in words if re.fullmatch(r'\d+X\d+|\d+"?Ø', w[4])]
    lines = []
    for d in DX:
        if d['type'] in ('s', 'fs'):
            for it in d['items']:
                if it[0] == 'l':
                    lines.append(((it[1].x, it[1].y), (it[2].x, it[2].y)))
    ends = collections.defaultdict(list)
    for a, b in lines:
        ends[(int(a[0] // 6), int(a[1] // 6))].append((a, b))
        ends[(int(b[0] // 6), int(b[1] // 6))].append((b, a))

    def near(pt, rad):
        kx, ky = int(pt[0] // 6), int(pt[1] // 6)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for a, b in ends.get((kx + dx, ky + dy), ()):
                    if math.dist(a, pt) < rad:
                        yield a, b

    def col_at(pt, tol=3):
        best = None
        for i, c in enumerate(cols):
            r = c['bbox']
            if r.x0 - tol <= pt[0] <= r.x1 + tol and r.y0 - tol <= pt[1] <= r.y1 + tol:
                d = math.dist(pt, ((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2))
                if not best or d < best[0]:
                    best = (d, i)
        return best[1] if best else None

    def candidates(w):
        """Every column reachable along a line leaving the text box, with the
        path length (text centre -> line start -> ... -> column)."""
        R = pymupdf.Rect(w[0] - 8, w[1] - 8, w[2] + 8, w[3] + 8)
        mc = ((w[0] + w[2]) / 2, (w[1] + w[3]) / 2)
        found = {}
        for a, b in lines:
            for s, e in ((a, b), (b, a)):
                if not (R.contains(pymupdf.Point(*s)) and not R.contains(pymupdf.Point(*e))
                        and math.dist(s, e) > 15):
                    continue
                cur, prev, length = e, s, math.dist(mc, s) + math.dist(s, e)
                for _ in range(3):
                    hit = col_at(cur)
                    if hit is not None:
                        if hit not in found or length < found[hit]:
                            found[hit] = length
                        break
                    nxt = [q for q in near(cur, 1.5) if math.dist(q[1], prev) > 1]
                    if not nxt:
                        break
                    length += math.dist(cur, nxt[0][1])
                    prev, cur = cur, nxt[0][1]
        return sorted((L, i) for i, L in found.items())

    def build_labels():
        labels = []
        for w in marks:
            mc = ((w[0] + w[2]) / 2, (w[1] + w[3]) / 2)
            sz = None
            if sizes:
                s_ = min(sizes, key=lambda s: math.dist(((s[0] + s[2]) / 2, (s[1] + s[3]) / 2), mc))
                if math.dist(((s_[0] + s_[2]) / 2, (s_[1] + s_[3]) / 2), mc) < 20:
                    sz = s_[4]
            labels.append(dict(mark=w[4], size=sz, col=None, how=None, cands=candidates(w), mc=mc))
        # one label per column: shortest leaders claim first; a label whose best
        # column is taken moves to its next candidate
        taken = {}
        order = sorted(range(len(labels)), key=lambda k: labels[k]['cands'][0][0] if labels[k]['cands'] else 1e9)
        for k in order:
            L = labels[k]
            for length, i in L['cands']:
                if i not in taken:
                    taken[i] = k
                    L['col'], L['how'] = i, 'leader'
                    break
            if L['col'] is None and L['cands']:
                L['col'], L['how'] = L['cands'][0][1], 'leader (shared)'
        for L in labels:
            if L['col'] is None:
                best = None
                for i, c in enumerate(cols):
                    if i in taken:
                        continue
                    r = c['bbox']
                    d = math.dist(((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2), L['mc'])
                    if d < 80 and (not best or d < best[0]):
                        best = (d, i)
                if best:
                    L['col'], L['how'] = best[1], 'nearest'
                    taken[best[1]] = True
            L.pop('cands', None)
            L.pop('mc', None)
        return labels
    labels = build_labels()
    matched = sum(1 for L in labels if L['col'] is not None and L['how'] != 'nearest')
    if marks and len(marks) >= 3 and matched < 0.5 * len(marks):
        # columns drawn as outlines (no gray fill): closed rectangles / circles of
        # column size with no text inside, reached by the mark leaders
        oc = outline_shapes(p, DX, words, T, ppf)
        if oc:
            keep = cols[:]
            cols[:] = oc
            lab2 = build_labels()
            m2 = sum(1 for L in lab2 if L['col'] is not None and L['how'] != 'nearest')
            if m2 > matched:
                labels = lab2
            else:
                cols[:] = keep
    return cols, labels, doc, p


def outline_shapes(p, DX, words, T, ppf):
    inch = ppf / 12.0
    boxes = [pymupdf.Rect(w[:4]) for w in words]
    cand = []
    for d in DX:
        f = d.get('fill')
        if d['type'] not in ('s', 'fs', 'f'):
            continue
        if d['type'] in ('fs', 'f') and not (f and all(v > 0.95 for v in f)):
            continue                     # white masks / outlines only (gray fills handled above)
        it = d['items']
        pts, ncurve = [], 0
        if len(it) == 1 and it[0][0] == 're':
            R = it[0][1]
            pts = [(R.x0, R.y0), (R.x1, R.y0), (R.x1, R.y1), (R.x0, R.y1)]
        elif 3 <= len(it) <= 8 and all(i[0] == 'l' for i in it):
            pts = [(i[1].x, i[1].y) for i in it] + [(it[-1][2].x, it[-1][2].y)]
            if math.dist(pts[0], pts[-1]) > 1.0 and not d.get('closePath'):
                continue
        elif len(it) >= 4 and all(i[0] == 'c' for i in it):
            for i in it:
                pts += [(q.x, q.y) for q in i[1:]]
            ncurve = len(it)
        else:
            continue
        r = d['rect']
        wmin, wmax = min(r.width, r.height) / inch, max(r.width, r.height) / inch
        if not (5.5 <= wmin and wmax <= 150 and wmax / max(wmin, 0.1) <= 15):
            continue
        if any(r.contains(pymupdf.Point((b.x0 + b.x1) / 2, (b.y0 + b.y1) / 2)) for b in boxes
               if b.width < r.width * 1.5):
            continue
        fpts = [T(x, y) for x, y in pts]
        A, a, b, u, c = _minrect(_hull([(round(x, 4), round(y, 4)) for x, y in fpts]))
        cand.append(dict(center=c, a=a, b=b, u=u, bbox=r, curves=ncurve, gray=None, outline=True))
    # keep the outer shape of nested ones (ties drawn inside the column outline)
    cand.sort(key=lambda c: -c['bbox'].get_area())
    out = []
    for c in cand:
        r = c['bbox']
        if any(o['bbox'].contains(pymupdf.Rect(r.x0 + 0.3, r.y0 + 0.3, r.x1 - 0.3, r.y1 - 0.3)) for o in out):
            continue
        out.append(c)
    return out


INFO_FLAGS = ('bullnose', 'in a wall')


class WallProbe(object):
    """Is a sheet point (feet, y up) on a gray fill? Renders small pieces of
    the sheet on demand (the same gray the columns and walls are filled with)."""
    Z = 4.0

    def __init__(self, page, ppf):
        self.p, self.ppf, self.cache = page, ppf, {}

    def _tile(self, k):
        if k not in self.cache:
            T = 120.0                                     # tile size, display points
            clip = pymupdf.Rect(k[0] * T, k[1] * T, (k[0] + 1) * T, (k[1] + 1) * T)
            pm = self.p.get_pixmap(matrix=pymupdf.Matrix(self.Z, self.Z), clip=clip,  # clip = page.rect space
                                   colorspace=pymupdf.csRGB, alpha=False)
            self.cache[k] = (pm, k[0] * T, k[1] * T)
        return self.cache[k]

    def gray_at(self, pt, gray):
        dx, dy = pt[0] * self.ppf, -pt[1] * self.ppf       # feet -> display points
        pm, ox, oy = self._tile((int(dx // 120), int(dy // 120)))
        px, py = int((dx - ox) * self.Z), int((dy - oy) * self.Z)
        g = int(round(gray * 255))
        hits = 0
        for ex in (-1, 0, 1):
            for ey in (-1, 0, 1):
                x, y = min(max(px + ex, 0), pm.width - 1), min(max(py + ey, 0), pm.height - 1)
                r, gg, b = pm.pixel(x, y)[:3]
                if abs(r - g) < 18 and abs(gg - g) < 18 and abs(b - g) < 18:
                    hits += 1
        return hits >= 4

    def edge_gray(self, pts, gray):
        return sum(1 for q in pts if self.gray_at(q, gray)) / float(len(pts))


def into_wall(probe, c, size, tol=1.5):
    """A column partly inside a wall shows only its visible part. Keep the
    faces that aren't against a wall and extend the column into the wall on
    the side(s) that are, until it is the schedule size.
    c: plan column (center, a/b in ft along u/n, u, gray); size: [W, D] inches.
    Returns dict(ok, center, drawn [along u, along n] in, outline, how, warn) or
    dict(ok=False, why) or None when the column can't be judged."""
    if c.get('gray') is None:            # outline-drawn columns: no fill to test walls against
        return None
    cx, cy = c['center']
    u = c['u']
    n = (-u[1], u[0])
    a, b = c['a'] * 12, c['b'] * 12                   # drawn inches along u, n
    off = 2.5 / probe.ppf                             # 2.5 pt past the face, in ft
    gray = c.get('gray', 0.76)

    def P(su, sn):                                    # inches from centre -> sheet ft
        return (cx + (u[0] * su + n[0] * sn) / 12.0, cy + (u[1] * su + n[1] * sn) / 12.0)

    def face_on_wall(axis, sign):
        """fraction of points just outside that face that are gray."""
        half_self, half_other = (a / 2, b / 2) if axis == 0 else (b / 2, a / 2)
        pts = []
        for t in (-0.3, -0.15, 0, 0.15, 0.3):
            along = t * 2 * half_other
            d = sign * (half_self + off * 12)
            pts.append(P(d, along) if axis == 0 else P(along, d))
        return probe.edge_gray(pts, gray)
    walls = {}
    for axis in (0, 1):
        for sign in (-1, 1):
            walls[(axis, sign)] = face_on_wall(axis, sign) >= 0.6
    best = None
    for su, sn in ((size[0], size[1]), (size[1], size[0])):
        if su < a - tol or sn < b - tol:
            continue
        plan, cost, bad = [], 0, None
        for axis, S, d in ((0, su, a), (1, sn, b)):
            ext = S - d
            if ext <= tol:
                plan.append((axis, 0, 0.0))
                continue
            sides = [sg for sg in (-1, 1) if walls[(axis, sg)]]
            if len(sides) == 1:
                plan.append((axis, sides[0], ext))
            elif len(sides) == 2:
                plan.append((axis, 0, ext))            # wall both sides: grow both ways
            else:
                bad = 'no wall against the short side'
            cost += ext
        if bad:
            if best is None:
                best = (1e9, None, bad)
            continue
        if best is None or cost < best[0]:
            best = (cost, (su, sn, plan), None)
    if best is None:
        return dict(ok=False, why='schedule size is smaller than the drawn shape')
    if best[1] is None:
        return dict(ok=False, why=best[2])
    su, sn, plan = best[1]
    du = dn = 0.0
    how, warn = [], []
    for axis, sign, ext in plan:
        if ext == 0:
            continue
        shift = sign * ext / 2.0
        if axis == 0:
            du = shift
        else:
            dn = shift
        how.append('%.0f"' % ext)
        if sign == 0:
            warn.append('wall on both sides of the visible part - extended both ways, check')
    cen = P(du, dn)
    corners = [P(du + x * su / 2.0, dn + y * sn / 2.0) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    # the hidden part should lie inside the wall: test just inside each moved face
    for axis, sign, ext in plan:
        if ext == 0 or sign == 0:
            continue
        pts = []
        for t in (-0.3, 0, 0.3):
            if axis == 0:
                pts.append(P(du + sign * (su / 2.0 - off * 12), dn + t * sn))
            else:
                pts.append(P(du + t * su, dn + sign * (sn / 2.0 - off * 12)))
        if probe.edge_gray(pts, gray) < 0.6:
            warn.append('extended face comes out past the wall - check the size or the wall')
    return dict(ok=True, center=cen, drawn=[su, sn], outline=[list(q) for q in corners],
                how=' + '.join(how), warn=warn)


def build(args):
    S = parse_schedule(args.schedule)
    if args.types_only:
        return dict(version=1, kind='types', schedule=S['pages'], schedule_summary=summary(S),
                    types=all_types(S))
    level = norm_level(args.level)
    path, page = re.fullmatch(r'(.+?)(?::(\d+))?', args.plan).groups()
    page = int(page or 1)
    # grids + scale via the grid engine (same frame as Grids from PDF)
    sheet = GD.detect_sheet(path, page, args.scale, None)
    ipf = GD.parse_scale(sheet['scale'])
    ppf = 72.0 * ipf
    # only marks of the kinds the schedule uses (C-1 yes, PC-1 pile caps no)
    prefixes = set(mark_prefix(m) for m in S['marks']) or None
    cols, labels, doc, p = plan_columns(path, page, ppf, prefixes)
    by_col = collections.defaultdict(list)
    for L in labels:
        if L['col'] is not None:
            by_col[L['col']].append(L)
    # legend samples ("INDICATES COLUMN MARK ...") are not real columns
    legend = [pymupdf.Rect(w[:4]) for w in p.get_text('words') if w[4].upper() == 'INDICATES']
    out, legend_ids = [], set()
    probe = WallProbe(p, ppf)
    for i, c in enumerate(cols):
        ls = by_col.get(i, [])
        if not ls:
            continue
        r = c['bbox']
        if any(abs((L.x0 + L.x1) / 2 - (r.x0 + r.x1) / 2) < 140 and abs((L.y0 + L.y1) / 2 - (r.y0 + r.y1) / 2) < 140
               for L in legend):
            legend_ids.add(i)
            continue
        mks = sorted(set(l['mark'] for l in ls))
        flags = []
        if len(mks) > 1:
            flags.append('one drawn shape carries marks %s - check' % ', '.join(mks))
        mk = ls[0]['mark']
        lab = ls[0]['size']
        e = lookup(S, mk, level)
        a_in, b_in = c['a'] * 12, c['b'] * 12
        rec = dict(_i=i, _ppf=ppf, mark=mk, label=lab, center=[round(v, 5) for v in c['center']],
                   u=[round(v, 6) for v in c['u']], drawn=[round(a_in, 1), round(b_in, 1)],
                   curves=c['curves'], flags=flags)
        if e is None:
            rec['flags'].append('mark not found in the schedule at level %s' % level)
            rec['family'] = 'rectangular'
            if lab and 'X' in lab:
                rec['size'] = [int(v) for v in lab.split('X')]
                rec['flags'].append('size taken from the plan label')
        elif isinstance(e, dict) and e.get('steel'):
            rec['flags'].append('steel column %s in the schedule - not placed (no steel family yet)' % e['steel'])
            rec['family'] = 'rectangular'
            rec['size'] = None
            rec['detail'] = e['steel']
        elif e == 'none':
            rec['flags'].append('schedule shows no column for this mark at level %s' % level)
            rec['family'] = 'rectangular'
            rec['size'] = None
        else:
            rec['family'] = family_for(e)
            rec['size'] = e['size'] or [e['dia']]
            rec['detail'] = e['type']
            rec['schedule_text'] = e['text']
            if lab and 'X' in lab and e['size'] and sorted(map(int, lab.split('X'))) != sorted(e['size']):
                rec['flags'].append('plan label %s but schedule %dx%d - schedule used' % (lab, e['size'][0], e['size'][1]))
        sz = rec.get('size')
        if sz and len(sz) == 2:
            if abs(sorted(sz)[0] - min(a_in, b_in)) > 1.5 or abs(sorted(sz)[1] - max(a_in, b_in)) > 1.5:
                fix = into_wall(probe, c, sz)
                if fix and fix['ok']:
                    rec['center'] = [round(v, 5) for v in fix['center']]
                    rec['drawn'] = [round(v, 1) for v in fix['drawn']]
                    rec['extended'] = fix['outline']
                    rec['flags'].append('in a wall - drawn %.0fx%.0f, hidden part extended %s into the wall to %dx%d'
                                        % (min(a_in, b_in), max(a_in, b_in), fix['how'], sz[0], sz[1]))
                    rec['flags'] += fix['warn']
                else:
                    why = (' (%s)' % fix['why']) if fix else ''
                    rec['flags'].append('drawn shape %.0fx%.0f doesn\'t match %dx%d%s - placed at the shape\'s centre, check'
                                        % (min(a_in, b_in), max(a_in, b_in), sz[0], sz[1], why))
        if rec['family'] == 'bullnose':
            rec['flags'].append('bullnose - flip if the rounded end is on the wrong side')
        out.append(rec)
    n = 0
    for rec in sorted(out, key=lambda r: (-round(r['center'][1] / 20), r['center'][0])):
        if rec['flags']:
            n += 1
            rec['ref'] = n
    unmarked = sum(1 for i in range(len(cols)) if i not in by_col and i not in legend_ids)
    for i in legend_ids:
        by_col.pop(i, None)
    cols = [dict(c, legend=(i in legend_ids)) for i, c in enumerate(cols)]
    grids = [dict(label=g['label'], angle=f['angle'], t=f['t'], n=f['n'], pos=g['pos'], along=g['along'])
             for f in sheet['families'] for g in f['grids']]
    check = None
    if args.check_dir:
        try:
            check = draw_check(doc, p, cols, by_col, out, args.check_dir,
                               os.path.splitext(os.path.basename(path))[0])
        except Exception as ex:
            sheet['warnings'].append('check PDF not saved (%s)' % ex)
    if not S['marks']:
        sheet['warnings'].append('no column schedule table found in %s' % os.path.basename(args.schedule))
    elif S['levels'] and level not in S['levels'] and not any(
            lo is None for rs in S['ranges'].values() for lo, hi, c in rs):
        sheet['warnings'].append('level "%s" is not in the schedule - its levels are: %s'
                                 % (level, ', '.join(S['levels'])))
    return dict(version=1, kind='columns', plan=path, page=page, level=level,
                schedule_summary=summary(S),
                scale=sheet['scale'], scale_source=sheet['scale_source'],
                schedule=S['pages'], schedule_levels=S['levels'], grids=grids,
                columns=out, unmarked_shapes=unmarked, legend_skipped=len(legend_ids), warnings=sheet['warnings'],
                check_pdf=check)


def draw_check(doc, p, cols, by_col, recs, folder, name):
    """Green box = column read; orange dashed = gray shape with no mark (not
    placed); red / blue circle + number = flagged column, number matches the
    #n in the button's list (red = check it, blue = bullnose, flip if needed)."""
    import glob, time
    sh = p.new_shape()
    miss = p.new_shape()
    for i, c in enumerate(cols):
        r = c['bbox']
        if c.get('legend'):
            continue
        (sh if i in by_col else miss).draw_rect(pymupdf.Rect(r.x0 - 2, r.y0 - 2, r.x1 + 2, r.y1 + 2))
    sh.finish(color=(0, 0.6, 0), width=1.5)
    sh.commit()
    miss.finish(color=(1, 0.5, 0), width=1.5, dashes='[4 2] 0')
    miss.commit()
    M = p.rotation_matrix
    IM = p.derotation_matrix
    ext = p.new_shape()
    n_ext = 0
    for rec in recs:
        o = rec.get('extended')
        if o:
            pts = [pymupdf.Point(x * rec['_ppf'], -y * rec['_ppf']) * IM for x, y in o]
            ext.draw_polyline(pts + [pts[0]])
            n_ext += 1
    if n_ext:
        ext.finish(color=(0.1, 0.35, 0.9), width=1.2, dashes='[3 2] 0')
        ext.commit()
    for rec in recs:
        if not rec.get('ref'):
            continue
        r = cols[rec['_i']]['bbox']
        only_bull = all(f.startswith(INFO_FLAGS) for f in rec['flags'])
        col = (0.1, 0.35, 0.9) if only_bull else (0.85, 0, 0)
        ctr = pymupdf.Point((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)
        rad = max(r.width, r.height) / 2 + 7
        cd = ctr * M
        tag_d = pymupdf.Point(cd.x + rad + 10, cd.y - rad - 10)
        ring = p.new_shape()
        ring.draw_circle(ctr, rad)
        ring.draw_line(pymupdf.Point(cd.x + rad * 0.71, cd.y - rad * 0.71) * IM,
                       pymupdf.Point(tag_d.x - 6.4, tag_d.y + 6.4) * IM)
        ring.finish(color=col, width=2.5)
        ring.draw_circle(tag_d * IM, 9)
        ring.finish(color=col, fill=(1, 1, 1), width=1.5)
        ring.commit()
        txt = str(rec['ref'])
        fs = 10 if len(txt) < 3 else 8
        w = pymupdf.get_text_length(txt, fontname='hebo', fontsize=fs)
        base = pymupdf.Point(tag_d.x - w / 2, tag_d.y + fs * 0.35) * IM
        p.insert_text(base, txt, fontname='hebo', fontsize=fs, color=col, rotate=p.rotation)
    for old in glob.glob(os.path.join(folder, name + ' - detected columns*.pdf')):
        try:
            os.remove(old)
        except OSError:
            pass
    out = os.path.join(folder, '%s - detected columns %s.pdf' % (name, time.strftime('%H%M%S')))
    doc.select([p.number])
    doc.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--plan')
    ap.add_argument('--schedule', required=True)
    ap.add_argument('--level', default='1')
    ap.add_argument('--scale', default='auto')
    ap.add_argument('--check-dir')
    ap.add_argument('--types-only', action='store_true')
    a = ap.parse_args()
    if not a.types_only and not a.plan:
        raise SystemExit('--plan is required')
    res = build(a)
    with open(a.out, 'w') as fh:
        json.dump(res, fh, indent=1)
    if res['kind'] == 'types':
        print('OK %d column types' % len(res['types']))
    else:
        print('OK %d columns, %d flagged' % (len(res['columns']),
                                            sum(1 for c in res['columns'] if c['flags'])))


if __name__ == '__main__':
    try:
        main()
    except SystemExit as e:
        if e.code not in (None, 0):
            sys.stderr.write(str(e.code) + '\n')
            sys.exit(2)
