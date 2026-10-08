"""MCC - column schedule reader (CPython 3 + PyMuPDF).

Reads the common ways a structural engineer lays out a column schedule:

  grid       marks across the top, levels down the side (Kalae S3.11, Horizon House S-4.03).
             A size written in a level's row runs up until the next size; an empty
             cell continues from below; a gray (or "-", "N/A") cell = no column.
             Several tables on one sheet (tower + podium) are read separately.
  transposed levels across the top, marks down the side - same rules, turned 90 deg.
  list       one row per mark (MARK | SIZE | ... ), optionally with FROM / TO
             (or BASE / TOP, LEVELS) columns; no level columns = every level.

Levels are text keys: "1", "33", "B7", "P2", "ROOF", "MACHINE ROOM"
("LEVEL 01", "L1", "LVL 1" all read as "1"). Sizes: 24x24, 24"x24", 18 X 24,
2'-0"x2'-6", 24"Ø, Ø24", 24" DIA. Detail type: T9, [9], TYPE 9.
"""
import collections, re, statistics

import pymupdf

MARK_RE = r'[A-Z]{0,2}C-?\d+(?:X\d+)?(?:-\d+)?[A-Z]?'
BULLNOSE_TYPES = {'T9'}
ROUND_TYPES = {'T10', 'T11'}
LEVEL_WORDS = {'LEVEL', 'LVL', 'LEV', 'FLOOR', 'FLR'}
ID_RE = r'(?:[A-Z]{1,2}-?)?\d{1,3}[A-Z]?'
NAMED = ['MACHINE ROOM', 'UPPER ROOF', 'LOW ROOF', 'HIGH ROOF', 'MAIN ROOF', 'ROOF',
         'PENTHOUSE', 'MEZZANINE', 'MEZZ', 'GROUND', 'PLAZA', 'PODIUM', 'FOUNDATION', 'MAT']
TOP_NAMED = {'MACHINE ROOM', 'UPPER ROOF', 'HIGH ROOF', 'MAIN ROOF', 'ROOF', 'PENTHOUSE', 'LOW ROOF'}
NO_COLUMN = {'-', '--', '---', '—', '–', 'N/A', 'NA', 'NONE'}


# ---------------------------------------------------------------------------
# small parsers
# ---------------------------------------------------------------------------
def norm_level(s):
    """'LEVEL 01' / 'L1' / 'Level B7' / 'roof' -> '1' / '1' / 'B7' / 'ROOF'."""
    s = re.sub(r'\s+', ' ', str(s or '').upper().replace('.', ' ')).strip()
    for n in NAMED:
        if re.search(r'\b%s\b' % n, s):
            return n
    m = re.fullmatch(r'(?:(?:LEVEL|LVL|LEV|FLOOR|FLR)\s*|L(?=\d))?(%s)' % ID_RE, s)
    if not m:
        m = re.search(r'\b(%s)\b' % ID_RE, s)
    if not m:
        return s
    t = m.group(1).replace('-', '')
    t = re.sub(r'^([A-Z]*)0+(\d)', r'\1\2', t)
    return t


def level_rank(key):
    """Rough height order for keys from different tables / list ranges."""
    key = key.split('..')[0]
    if key in TOP_NAMED:
        return 1000 + (1 if key == 'MACHINE ROOM' else 0)
    if key in ('GROUND', 'PLAZA'):
        return 0.5
    if key in ('FOUNDATION', 'MAT'):
        return -100
    m = re.fullmatch(r'(B|LL|SB|SL|P)(\d+)', key)
    if m:
        return -int(m.group(2))
    m = re.fullmatch(r'(\d+)([A-Z]?)', key)
    if m:
        return int(m.group(1)) + (0.5 if m.group(2) else 0)
    m = re.search(r'\d+', key)
    return int(m.group(0)) if m else 0


def _inches(tok):
    tok = tok.replace(' ', '')
    m = re.fullmatch(r"(\d+)'-?(\d+(?:\.\d+)?)?\"?", tok)
    if m and "'" in tok:
        return int(m.group(1)) * 12 + float(m.group(2) or 0)
    return float(tok.rstrip('"'))


DIM = r"\d+\s*'\s*-?\s*\d+(?:\.\d+)?\s*\"?|\d+\s*'|\d+(?:\.\d+)?\s*\"?"


def parse_size(txt):
    """-> ('rect', [w, d]) | ('round', [dia]) | None  (inches, ints)."""
    t = (txt or '').upper()
    t = t.replace('×', 'X').replace('″', '"').replace('′', "'").replace("''", '"')
    t = re.sub(r'(\d)"\s*S\b', r'\1" Ø', t)          # SHX fonts draw Ø as S (24"S)
    t = re.sub(r'[⌀øØ∅Φφ]|\bDIA\b\.?|\bDIAM(?:ETER)?\b|\bRND\b|\bROUND\b', ' Ø ', t)
    hits = []
    for m in re.finditer(r'(?<![A-Z\d#@/])(%s)\s*X\s*(%s)' % (DIM, DIM), t):
        a, b = _inches(m.group(1)), _inches(m.group(2))
        if 4 <= a <= 240 and 4 <= b <= 240:
            hits.append((m.start(), 'rect', [int(round(a)), int(round(b))]))
            break
    for pat in (r'(?<![\d#@])(%s)\s*Ø' % DIM, r'Ø\s*(%s)' % DIM):
        for m in re.finditer(pat, t):
            d = _inches(m.group(1))
            if 4 <= d <= 240:
                hits.append((m.start(), 'round', [int(round(d))]))
                break
    if not hits:
        return None
    hits.sort(key=lambda h: h[0])            # first size in reading order wins
    return hits[0][1], hits[0][2]


def parse_type(txt):
    t = (txt or '').upper()
    m = re.search(r'\bT\d+[A-Z]?\b', t)
    if m:
        return m.group(0)
    m = re.search(r'\[\s*(\d+[A-Z]?)\s*\]', t)
    if m:
        return '[%s]' % m.group(1)
    m = re.search(r'\bTYPE\s*(\d+[A-Z]?)\b', t)
    if m:
        return 'TYPE %s' % m.group(1)
    return None


STEEL_RE = r'\b(W\d{1,2}\s*X\s*\d{2,3}(?:\.\d)?|HSS\s*[\d./]+(?:\s*X\s*[\d./]+){1,2}|PIPE\s*\d+|TS\s*[\d./]+X[\d./]+)'


def make_cell(txt, gray):
    u = (txt or '').upper()
    st = re.search(STEEL_RE, u)
    sz = None if st else parse_size(txt)
    if txt.strip().upper() in NO_COLUMN:
        gray = True
    return dict(text=txt, gray=gray,
                size=sz[1] if sz and sz[0] == 'rect' else None,
                dia=sz[1][0] if sz and sz[0] == 'round' else None,
                type=parse_type(txt),
                steel=re.sub(r'\s+', '', st.group(1)) if st else None)


# ---------------------------------------------------------------------------
# page items
# ---------------------------------------------------------------------------
class Word(object):
    __slots__ = ('x', 'y', 'x0', 'y0', 'x1', 'y1', 't', 'ox', 'oy')

    def __init__(self, x0, y0, x1, y1, t):
        self.x0, self.y0, self.x1, self.y1, self.t = x0, y0, x1, y1, t
        self.x, self.y = (x0 + x1) / 2, (y0 + y1) / 2
        self.ox, self.oy = self.x, self.y            # reading-order coords (never swapped)

    def swapped(self):
        w = Word(self.y0, self.x0, self.y1, self.x1, self.t)
        w.ox, w.oy = self.ox, self.oy
        return w


def page_items(p):
    """Words, gray fills and horizontal / vertical ruling segments in display
    coordinates (the page as you'd view it, rotation applied)."""
    M = p.rotation_matrix
    W = []
    for w in p.get_text('words'):
        r = pymupdf.Rect(w[:4]) * M
        r.normalize()
        W.append(Word(r.x0, r.y0, r.x1, r.y1, w[4]))
    G, H, V = [], [], []
    for d in p.get_drawings():
        f = d.get('fill')
        if f and d['type'] in ('f', 'fs') and 0.55 < f[0] < 0.92 and abs(f[0] - f[1]) < 0.03 \
                and abs(f[1] - f[2]) < 0.03:
            r = d['rect'] * M
            r.normalize()
            G.append(r)
        if d['type'] in ('s', 'fs') or (f and d['type'] == 'f'):
            for it in d['items']:
                if it[0] == 'l':
                    a, b = it[1] * M, it[2] * M
                    if abs(a.y - b.y) < 0.3:
                        H.append((a.y, min(a.x, b.x), max(a.x, b.x)))
                    elif abs(a.x - b.x) < 0.3:
                        V.append((a.x, min(a.y, b.y), max(a.y, b.y)))
                elif it[0] == 're':
                    r = it[1] * M
                    r.normalize()
                    if r.height < 1.2 and r.width > 3:
                        H.append((r.y0 + r.height / 2, r.x0, r.x1))
                    elif r.width < 1.2 and r.height > 3:
                        V.append((r.x0 + r.width / 2, r.y0, r.y1))
                    elif d['type'] in ('s', 'fs'):
                        H += [(r.y0, r.x0, r.x1), (r.y1, r.x0, r.x1)]
                        V += [(r.x0, r.y0, r.y1), (r.x1, r.y0, r.y1)]
    return W, G, H, V


def level_labels(W):
    """(x, y, key, strong) for every level-looking label, in display coords."""
    out, used = [], set()
    rows = collections.defaultdict(list)
    for i, w in enumerate(W):
        rows[round(w.y / 3)].append(i)

    def right_of(i):
        w = W[i]
        c = [j for k in (-1, 0, 1) for j in rows.get(round(w.y / 3) + k, ())
             if j != i and abs(W[j].y - w.y) < 3 and 0 < W[j].x0 - w.x1 < 25]
        return sorted(c, key=lambda j: W[j].x0)
    for i, w in enumerate(W):
        u = w.t.upper().rstrip(':')
        if u in LEVEL_WORDS:
            nx = right_of(i)
            if nx:
                j = nx[0]
                v = W[j].t.upper().rstrip(':')
                if re.fullmatch(ID_RE, v) or v in ('ROOF', 'MEZZ', 'MEZZANINE'):
                    out.append(((w.x0 + W[j].x1) / 2, w.y, norm_level(v), True))
                    used |= {i, j}
            continue
        if re.fullmatch(r'(?:LEVEL|LVL|L)-?(\d{1,3}[A-Z]?)', u) or re.fullmatch(r'(?:B|LL|P)\d{1,2}', u):
            out.append((w.x, w.y, norm_level(u), u.startswith('LEVEL') or u.startswith('LVL')))
            used.add(i)
    for i, w in enumerate(W):
        if i in used:
            continue
        u = w.t.upper()
        if u == 'MACHINE':
            nx = right_of(i)
            if nx and W[nx[0]].t.upper() == 'ROOM':
                out.append(((w.x0 + W[nx[0]].x1) / 2, w.y, 'MACHINE ROOM', False))
                used.add(nx[0])
        elif u in ('ROOF', 'PENTHOUSE', 'MEZZANINE', 'MEZZ') and not any(
                W[j].t.upper() in ('MACHINE', 'LOW', 'UPPER', 'HIGH', 'MAIN')
                for k in (-1, 0, 1) for j in rows.get(round(w.y / 3) + k, ())
                if abs(W[j].y - w.y) < 3 and 0 < w.x0 - W[j].x1 < 25):
            out.append((w.x, w.y, norm_level(u), False))
    # level ranges: "L34 TO L38", "LEVEL 3 THRU 6", "L24-L25", "L39 TO ROOF" -> one row key 'lo..hi'
    for i, w in enumerate(W):
        m = re.fullmatch(r'(?:L|LEVEL|LVL)?(\d{1,3})-(?:L|LEVEL|LVL)?(\d{1,3})', w.t.upper())
        if m and int(m.group(2)) > int(m.group(1)):
            out.append((w.x, w.y, '%s..%s' % (int(m.group(1)), int(m.group(2))), True))
    merged, drop = [], set()
    for i, a in enumerate(out):
        for j, b in enumerate(out):
            if i == j or i in drop or j in drop or abs(a[1] - b[1]) > 3 or not 0 < b[0] - a[0] < 110:
                continue
            mid = [w for w in W if abs(w.y - a[1]) < 3 and a[0] < w.x < b[0]
                   and w.t.upper() in ('TO', 'THRU', 'THROUGH', '-', '\u2013')]
            if mid and '..' not in a[2] and '..' not in b[2]:
                merged.append(((a[0] + b[0]) / 2, a[1], '%s..%s' % (a[2], b[2]), a[3] or b[3]))
                drop |= {i, j}
    for i, a in enumerate(out):              # "L39" over "TO ROOF" on the next line
        for j, b in enumerate(out):
            if i == j or i in drop or j in drop or not 0 < b[1] - a[1] < 20 or abs(b[0] - a[0]) > 40:
                continue
            to = [w for w in W if abs(w.y - b[1]) < 3 and w.t.upper() in ('TO', 'THRU', 'THROUGH') and w.x < b[0]
                  and b[0] - w.x < 45]
            if to and '..' not in a[2] and '..' not in b[2]:
                merged.append((a[0], b[1], '%s..%s' % (a[2], b[2]), a[3] or b[3]))
                drop |= {i, j}
    out = [l for k, l in enumerate(out) if k not in drop] + merged
    # a range word also produces the plain labels of its ends - keep the range only
    rng = [l for l in out if '..' in l[2]]
    out = [l for l in out if '..' in l[2] or not any(abs(l[1] - r[1]) < 3 and abs(l[0] - r[0]) < 60 for r in rng)]
    return out


def expand_range(key):
    if '..' not in key:
        return [key]
    lo, hi = key.split('..')
    if re.fullmatch(r'\d+', lo) and re.fullmatch(r'\d+', hi) and int(hi) >= int(lo):
        return [str(k) for k in range(int(lo), int(hi) + 1)]
    return sorted([lo, hi], key=lambda k: level_rank(k))


def _lines_across(H, lo, hi, ymin, ymax):
    """y of horizontal rules covering at least half of [lo, hi]."""
    cov = collections.defaultdict(list)
    for y, a, b in H:
        if ymin <= y <= ymax and b > lo and a < hi:
            cov[round(y * 2) / 2].append((max(a, lo), min(b, hi)))
    out = []
    for y, segs in cov.items():
        segs.sort()
        tot, cur = 0, None
        for a, b in segs:
            if cur is None or a > cur[1]:
                if cur:
                    tot += cur[1] - cur[0]
                cur = [a, b]
            else:
                cur[1] = max(cur[1], b)
        if cur:
            tot += cur[1] - cur[0]
        if tot >= 0.5 * (hi - lo):
            out.append(y)
    out.sort()
    merged = []
    for y in out:
        if merged and y - merged[-1] < 1.5:
            continue
        merged.append(y)
    return merged


def _swap(W, G, H, V, L):
    W2 = [w.swapped() for w in W]
    G2 = [pymupdf.Rect(r.y0, r.x0, r.y1, r.x1) for r in G]
    L2 = [(y, x, k, s) for x, y, k, s in L]
    return W2, G2, V, H, L2


# ---------------------------------------------------------------------------
# grid tables (marks across one edge, levels down the other)
# ---------------------------------------------------------------------------
def _mark_rows(W, min_n=4):
    ms = [w for w in W if re.fullmatch(MARK_RE, w.t.rstrip(','))]
    by = collections.defaultdict(list)
    for w in ms:
        by[round(w.y / 4)].append(w)
    rows = []
    for k in sorted(by):
        grp = by[k] + by.get(k + 1, [])
        if rows and abs(rows[-1][0] - k) <= 1:
            continue
        uniq = {}
        for w in grp:
            uniq.setdefault(w.t.rstrip(','), w)
        ok = len(uniq) >= min_n
        if not ok and len(uniq) >= 2:
            # short tables (2-3 marks) count when the row is labelled MARK / COLUMN MARK
            x0 = min(w.x0 for w in uniq.values())
            y = statistics.median(w.y for w in uniq.values())
            ok = any(v.t.upper().rstrip(':') in ('MARK', 'MK') and abs(v.y - y) < 5 and 0 < x0 - v.x1 < 300
                     for v in W)
        if ok:
            rows.append((k, list(uniq.values())))
    return [r[1] for r in rows]


def _grid_tables(W, G, H, V, L, transposed=False):
    rows = _mark_rows(W)
    tables, used = [], set()
    for i, r in enumerate(rows):
        if i in used:
            continue
        xs = sorted(w.x for w in r)
        y0 = statistics.median(w.y for w in r)
        mates = [j for j in range(i + 1, len(rows)) if j not in used
                 and len({w.t for w in rows[j]} & {w.t for w in r}) >= 0.5 * len(r)
                 and abs(min(w.x for w in rows[j]) - xs[0]) < 40]
        y1 = None
        if mates:
            j = mates[0]
            used.add(j)
            y1 = statistics.median(w.y for w in rows[j])
            have = {w.t for w in r}
            r = r + [w for w in rows[j] if w.t not in have]     # marks printed only at the bottom
        up = False
        if y1 is None:
            # a lone mark row can be the table's header (table below) or its footer
            # (table above, Kinect S4.01): the level labels next to it decide
            p_ = statistics.median(b - a for a, b in zip(xs, xs[1:])) if len(xs) > 1 else 40
            zone = [l for l in L if xs[0] - 450 < l[0] < xs[0] - 0.35 * p_]
            da = min([y0 - l[1] for l in zone if 0 < y0 - l[1] < 800], default=1e9)
            db = min([l[1] - y0 for l in zone if 0 < l[1] - y0 < 800], default=1e9)
            up = da < db
        tables.append(dict(row=r, y0=y0, y1=y1, up=up))
    out = []
    for n, t in enumerate(tables):
        r = sorted(t['row'], key=lambda w: w.x)
        cols = dict((w.t.rstrip(','), w.x) for w in r)
        xs = sorted(cols.values())
        pitch = statistics.median(b - a for a, b in zip(xs, xs[1:])) if len(xs) > 1 else 40
        # marks sharing one schedule column ("C-5, C-5A"): same cells, column centre
        grp = []
        for mk, x in sorted(cols.items(), key=lambda kv: kv[1]):
            if grp and x - grp[-1][-1][1] < 0.6 * pitch:
                grp[-1].append((mk, x))
            else:
                grp.append([(mk, x)])
        if any(len(g) > 1 for g in grp):
            for g in grp:
                cx = sum(x for _, x in g) / len(g)
                for mk, _ in g:
                    cols[mk] = cx
            xs = sorted(set(cols.values()))
            pitch = statistics.median(b - a for a, b in zip(xs, xs[1:])) if len(xs) > 1 else 40
        lo, hi = xs[0] - pitch / 2, xs[-1] + pitch / 2
        y0 = t['y0']
        # table bottom: its own bottom mark row, else the next table header below it
        nxt = [u['y0'] for u in tables if u['y0'] > y0 + 10 and abs(min(w.x for w in u['row']) - xs[0]) < 600]
        y1 = t['y1'] if t['y1'] else (min(nxt) if nxt else 1e9)
        if t.get('up'):
            # footer row: the table runs up from it to the end of its run of rules
            y1 = y0
            prv = [u['y0'] for u in tables if u['y0'] < y1 - 10 and abs(min(w.x for w in u['row']) - xs[0]) < 600]
            ytop = max(prv) if prv else y1 - 4000
            rr = sorted([y for y in _lines_across(H, lo, hi, ytop, y1 - 2)], reverse=True)
            for k in range(1, len(rr)):
                if rr[k - 1] - rr[k] > 250:
                    rr = rr[:k]
                    break
            y0 = (rr[-1] - 2) if len(rr) >= 2 else ytop
        elif not t['y1']:
            # no bottom mark row: the table ends at the last of its run of ruling lines
            rr = _lines_across(H, lo, hi, y0 - 2, min(y1, y0 + 4000))
            rr = [y for y in rr if y > y0]
            for k in range(1, len(rr)):
                if rr[k] - rr[k - 1] > 250:
                    rr = rr[:k]
                    break
            if len(rr) >= 2:
                y1 = min(y1, rr[-1] + 2)
        labs = [l for l in L if y0 + 3 < l[1] < y1 + 3 and
                (xs[0] - 450 < l[0] < xs[0] - 0.35 * pitch or xs[-1] + 0.35 * pitch < l[0] < xs[-1] + 450)]
        # bare level numbers under a LEVEL / FLOOR column header (Baldridge, many others)
        if len([l for l in labs if l[3]]) < 3:
            for hw in W:
                if hw.t.upper().rstrip(':') not in ('LEVEL', 'FLOOR', 'LVL', 'FLR', 'STORY', 'LEVELS'):
                    continue
                if not (y0 - 60 < hw.y < y0 + 80):
                    continue
                if not (xs[0] - 450 < hw.x < xs[0] - 0.35 * pitch or xs[-1] + 0.35 * pitch < hw.x < xs[-1] + 450):
                    continue
                col = []
                for w in W:
                    if abs(w.x - hw.x) < 30 and hw.y + 5 < w.y < y1 + 3:
                        u = w.t.upper().rstrip(':')
                        if re.fullmatch(ID_RE, u) or u in ('ROOF', 'MEZZ', 'MEZZANINE', 'PENTHOUSE'):
                            col.append((w.x, w.y, norm_level(u), True))
                col.sort(key=lambda c: c[1])
                for k in range(1, len(col)):          # stop at the end of the table
                    if col[k][1] - col[k - 1][1] > 150:
                        col = col[:k]
                        break
                if len(col) >= 2:
                    have = set((l[2], round(l[1])) for l in labs)
                    labs += [c for c in col if (c[2], round(c[1])) not in have]
        strong = [l for l in labs if l[3]]
        if strong:
            colx = [l[0] for l in strong]
            labs = [l for l in labs if l[3] or any(abs(l[0] - x) < 60 for x in colx)]
        left = [l for l in labs if l[0] < xs[0]]
        if left:                      # right-side labels only when they repeat the left column
            lk = set(l[2] for l in left)
            labs = [l for l in labs if l[0] < xs[0] or l[2] in lk]
        # one label per key (schedules often repeat the level column on the right)
        best = {}
        for l in labs:
            side = 0 if l[0] < xs[0] else 1
            if l[2] not in best or side < best[l[2]][0]:
                best[l[2]] = (side, l)
        labs = sorted((v[1] for v in best.values()), key=lambda l: l[1])
        rng = [l for l in labs if '..' in l[2]]
        labs = [l for l in labs if '..' in l[2] or not any(
            abs(l[1] - r[1]) < 4 or (abs(l[1] - r[1]) < 25 and l[2] in expand_range(r[2])) for r in rng)]
        if len(labs) < 1 or (len(labs) < 2 and not strong):
            continue
        if not t['y1']:
            y1 = labs[-1][1] + 40
        rules = _lines_across(H, lo, hi, y0 - 2, y1 + 2)
        use_rules = len(rules) >= 0.6 * len(labs)
        # row bands: each label owns the band that ends at the first rule below it
        bands = []
        prev = None
        hdr_rules = [y for y in rules if y > y0 + 2]
        top = hdr_rules[0] if hdr_rules and hdr_rules[0] < labs[0][1] else y0 + 6
        for l in labs:
            if use_rules:
                below = [y for y in rules if y > l[1] + 0.5]
                bot = below[0] if below else l[1] + 4.5
            else:
                bot = l[1] + 4.5
            ytop = prev if prev is not None else (top if use_rules else y0 + 4.5)
            bands.append((l[2], ytop, bot))
            prev = bot
        # two labels in one rule band ("L6" at the top, "L5" at the bottom of one block):
        # the block is the story above the lower label; the upper one is just the top
        for k in range(len(bands) - 1):
            if use_rules and abs(bands[k][2] - bands[k + 1][2]) < 0.5:
                bands[k + 1] = (bands[k + 1][0], bands[k][1], bands[k][2])
                bands[k] = (bands[k][0], bands[k][1], bands[k][1])
        # labels hung just under their level line (label at the TOP of its band): the story
        # below a label belongs to the next label down (its base level)
        if use_rules and len(bands) >= 3:
            fr = [(l[1] - b[1]) / (b[2] - b[1]) for l, b in zip(labs, bands) if b[2] - b[1] > 3]
            if fr and statistics.median(fr) < 0.35:
                bands = [(bands[0][0], bands[0][1], bands[0][1])] + [
                    (bands[k][0], bands[k - 1][1], bands[k - 1][2]) for k in range(1, len(bands))]
        # labels centred in a merged cell (sub-rows SIZE / REINF / TIES beside them): the
        # label's own cell in the level column is the band. Rules drawn through the level
        # column bound it; sub-row rules stop at the level column.
        cells = []
        for l in labs:
            above = [y for y, a, b in H if a - 1 <= l[0] <= b + 1 and y0 - 2 < y < l[1] - 1.5]
            below = [y for y, a, b in H if a - 1 <= l[0] <= b + 1 and l[1] + 1.5 < y < y1 + 20]
            cells.append((max(above), min(below)) if above and below else None)
        ok = [c for c in cells if c]
        so = sorted(ok)
        distinct = len(set(ok)) == len(ok) and all(a[1] <= b[0] + 0.5 for a, b in zip(so, so[1:]))
        if distinct and len(ok) >= 0.8 * len(labs) and len(labs) >= 2:
            sub = sum(1 for c, b in zip(cells, bands) if c and (c[1] - c[0]) > (b[2] - b[1]) * 1.3)
            # use the cells when they are clearly taller than the rule-to-rule bands
            # (merged level cells) - otherwise the two agree and nothing changes
            if sub >= 0.5 * len(ok):
                bands = [(b[0], c[0], c[1]) if c else b for b, c in zip(bands, cells)]
        # which way is up? numbers growing down the page = bottom level at the top
        num = [(level_rank(l[2]), l[1]) for l in labs if re.fullmatch(r'\d+[A-Z]?|B\d+', l[2])]
        flip = False
        if len(num) >= 3:
            up = sum(1 for (a, ya), (b, yb) in zip(num, num[1:]) if (b - a) * (yb - ya) > 0)
            flip = up > (len(num) - 1) / 2
        table = {}
        # sub-row labels in the label column: DETAIL-TYPE / TYPE rows give the type
        type_rows = [w.y for w in W if re.fullmatch(r'(?:DETAIL-?)?TYPE:?|DETAIL', w.t.upper())
                     and xs[0] - 450 < w.x < xs[0] - 0.3 * pitch and y0 < w.y < y1 + 5]
        for key, ya, yb in bands:
            mid = (ya + yb) / 2
            trow = [y for y in type_rows if ya < y < yb]
            for mk, x in cols.items():
                cell = [w for w in W if abs(w.x - x) < pitch * 0.5 and ya + 0.5 < w.y < yb - 0.5
                        and not re.fullmatch(MARK_RE, w.t)]
                txt = ' '.join(w.t for w in sorted(cell, key=lambda w: (round(w.oy / 2), w.ox)))
                gray = any(g.x0 <= x <= g.x1 and g.y0 <= mid <= g.y1 for g in G)
                c = make_cell(txt, gray)
                if trow and not c['type']:
                    tw = [w.t for w in cell if abs(w.y - trow[0]) < 4]
                    if tw and re.fullmatch(r'[A-Z]{1,3}\d{0,2}', tw[0].upper()):
                        c['type'] = tw[0].upper()
                for k2 in expand_range(key):
                    table[(mk, k2)] = c
        order = [b[0] for b in bands]           # top of page first
        order = order if flip else order[::-1]  # -> bottom level first
        order = list(dict.fromkeys(k2 for k in order for k2 in expand_range(k)))
        # property rows outside the level rows: "COLUMN SIZE (INCHES)" under the table
        # gives each mark one size for all its levels
        defaults = {}
        btop, bbot = min(b[1] for b in bands), max(b[2] for b in bands)
        for sw in W:
            if sw.t.upper() != 'SIZE' or not (xs[0] - 450 < sw.x < xs[0] - 0.3 * pitch):
                continue
            if not (bbot - 2 < sw.y < bbot + 200 or btop - 200 < sw.y < btop + 2):
                continue
            if not (y0 < sw.y < y1 + 30):
                continue
            for mk, x in cols.items():
                cell = [w for w in W if abs(w.x - x) < pitch * 0.5 and abs(w.y - sw.y) < 9]
                c = make_cell(' '.join(w.t for w in sorted(cell, key=lambda w: w.ox)), False)
                if (c['size'] or c['dia']) and mk not in defaults:
                    defaults[mk] = c
            if defaults:
                break
        # a range row continues from below only at its lowest level: the others repeat its cell
        out.append(dict(kind='transposed' if transposed else 'grid', marks=cols, levels=order,
                        table=table, rules=use_rules, defaults=defaults, bands=bands, pitch=pitch))
    return out


# ---------------------------------------------------------------------------
# list tables (one row per mark)
# ---------------------------------------------------------------------------
def _expand_marks(txt):
    marks = []
    t = txt.upper()
    for a, b in re.findall(r'(%s)\s*(?:-|–|THRU|TO)\s*(%s)' % (MARK_RE, MARK_RE), t):
        pa, na = re.match(r'(\D*)(\d+)', a).groups()
        pb, nb = re.match(r'(\D*)(\d+)', b).groups()
        if pa == pb and int(nb) >= int(na) and int(nb) - int(na) < 60:
            marks += ['%s%d' % (pa, k) for k in range(int(na), int(nb) + 1)]
    t = re.sub(r'(%s)\s*(?:-|–|THRU|TO)\s*(%s)' % (MARK_RE, MARK_RE), ' ', t)
    marks += re.findall(r'\b%s\b' % MARK_RE, t)
    return list(dict.fromkeys(marks))


def _level_range(txt):
    t = txt.upper().strip()
    if not t or re.fullmatch(r'ALL(?: LEVELS)?|TYP(?:ICAL)?\.?', t):
        return None, None
    parts = re.split(r'\s*(?:\bTO\b|\bTHRU\b|\bTHROUGH\b|–|—|(?<=\w)-(?=\s*(?:L|LEVEL|B|P)?\s*\d))\s*', t)
    parts = [p for p in parts if p]
    if len(parts) >= 2:
        return norm_level(parts[0]), norm_level(parts[-1])
    return norm_level(parts[0]), norm_level(parts[0])


LIST_MARK = r'[A-Z]{1,3}-?\d[A-Z0-9\-./]*,?'
SIZE_HDR = r'\b(SIZE|DIMENSIONS?|DIM|DIA|DIAMETER)\b'
W_HDR = r'^(WIDTH|W|B|WIDE)$'
D_HDR = r'^(DEPTH|LENGTH|D|H|L|DEEP|LONG)$'


def _list_tables(W, G, H, V, L):
    """One row per mark. Header: a MARK / COLUMN (MARK) word over a column of
    marks, and a size column (SIZE, DIMENSIONS, or a WIDTH + DEPTH/LENGTH pair)
    - picked by which columns actually read as sizes."""
    out, done = [], set()
    heads = [w for w in W if w.t.upper().rstrip(':') in ('MARK', 'MK', 'COLUMN', 'COL', 'COL.', 'TYPE')]
    for h in heads:
        below = [w for w in W if re.fullmatch(LIST_MARK, w.t) and h.y + 4 < w.y < h.y + 900
                 and (abs(w.x0 - h.x0) < 30 or abs(w.x - h.x) < 40)]
        if len(below) < 2:
            continue
        below.sort(key=lambda w: w.y)
        # rows = runs of marks down the column, stop at a big gap (end of table)
        ys = []
        for w in below:
            if ys and w.y - ys[-1] <= 4:
                continue
            if len(ys) >= 2 and w.y - ys[-1] > 3 * statistics.median(b - a for a, b in zip(ys, ys[1:])) + 2:
                break
            if len(ys) == 1 and w.y - ys[0] > 60:
                break
            ys.append(w.y)
        if len(ys) < 2 or (round(h.x), round(ys[0])) in done:
            continue
        done.add((round(h.x), round(ys[0])))
        gap = statistics.median(b - a for a, b in zip(ys, ys[1:]))
        y_first = ys[0]
        hdr = [w for w in W if y_first - 60 < w.y < y_first - gap * 0.4 and h.x0 - 20 < w.x < h.x + 1200]
        leaf_y = max((w.y for w in hdr), default=h.y)
        leaf = sorted([w for w in hdr if w.y > leaf_y - 8] + [h], key=lambda w: w.x0)
        edges = []
        for w in leaf:
            if not edges or w.x0 - edges[-1] > 8:
                edges.append(w.x0)
        # data words right of the last edge but inside the table width
        right = max((w.x1 for w in hdr), default=h.x1) + 20

        def col_bounds(i):
            return edges[i] - 6, (edges[i + 1] - 6 if i + 1 < len(edges) else right)

        def name_of(i):
            x0, x1 = col_bounds(i)
            ws = [w for w in hdr if x0 - 20 <= w.x <= x1 + 20 and (w.y > leaf_y - 8 or x0 - 4 <= w.x0 < x1)]
            return ' '.join(w.t.upper() for w in sorted(ws, key=lambda w: (w.y, w.x)))
        names = [name_of(i) for i in range(len(edges))]
        mcol = min(range(len(edges)), key=lambda i: abs(edges[i] - h.x0))

        def row_band(k):
            y = ys[k]
            ya = y - gap * 0.45
            yb = (ys[k + 1] - 0.5) if k + 1 < len(ys) else y + gap * 0.55
            return ya, yb

        def text_in(i, k):
            if i is None:
                return ''
            x0, x1 = col_bounds(i)
            ya, yb = row_band(k)
            ws = [w for w in W if ya < w.y < yb and x0 <= w.x0 < x1]
            return ' '.join(w.t for w in sorted(ws, key=lambda w: (round(w.oy / 2), w.ox)))
        # candidate size readers: one column, or a width + depth pair
        cands = []
        for i in range(len(edges)):
            if i == mcol:
                continue
            cands.append(('one', i, None, 2 if re.search(SIZE_HDR, names[i]) else 0))
            if i + 1 < len(edges):
                n1, n2 = names[i].split()[-1:] or [''], names[i + 1].split()[-1:] or ['']
                if re.match(W_HDR, n1[0]) and re.match(D_HDR, n2[0]) or re.match(D_HDR, n1[0]) and re.match(W_HDR, n2[0]):
                    cands.append(('pair', i, i + 1, 3))

        def read(c, k):
            if c[0] == 'one':
                return text_in(c[1], k)
            a_, b_ = text_in(c[1], k), text_in(c[2], k)
            if 'Ø' in a_ or 'DIA' in a_.upper() or b_.strip() in ('-', '--', '', 'N/A'):
                return a_
            return '%s x %s' % (a_, b_)
        best = None
        for c in cands:
            n = sum(1 for k in range(len(ys)) if parse_size(read(c, k)))
            score = (n >= 0.5 * len(ys), c[3], n)
            if n and (best is None or score > best[0]):
                best = (score, c)
        if not best or not best[0][0]:
            continue
        csize = best[1]
        find = lambda pat, excl=(): next((i for i, n in enumerate(names) if re.search(pat, n) and i not in excl
                                          and i != mcol), None)
        c_from = find(r'\b(FROM|BASE|BOTTOM|START)\b')
        c_to = find(r'\b(TO|TOP|END|THRU)\b', (c_from,))
        c_lev = find(r'\bLEVELS?\b|\bFLOORS?\b', (c_from, c_to))
        c_type = find(r'\bTYPE|DETAIL|PATTERN|CONFIG', (c_from, c_to, c_lev, csize[1]))
        ranges = collections.defaultdict(list)
        marks = {}
        for k in range(len(ys)):
            mks = _expand_marks(text_in(mcol, k)) or re.findall(LIST_MARK, text_in(mcol, k).split(' ')[0])
            mks = [m.rstrip(',') for m in mks]
            if not mks:
                continue
            ttxt = text_in(c_type, k)
            cell = make_cell(read(csize, k), False)
            if ttxt and not cell['type']:
                cell['type'] = parse_type(ttxt) or ttxt.strip().split(' ')[0].upper()
            if not (cell['size'] or cell['dia']):
                continue
            if c_from is not None or c_to is not None:
                lo = norm_level(text_in(c_from, k)) if text_in(c_from, k) else None
                hi = norm_level(text_in(c_to, k)) if text_in(c_to, k) else None
            elif c_lev is not None:
                lo, hi = _level_range(text_in(c_lev, k))
            else:
                lo = hi = None
            for mk in mks:
                ranges[mk].append((lo, hi, cell))
                marks[mk] = cell
        # only column schedules: most marks must look like column marks (not F1 footings etc.)
        if ranges and sum(1 for mk in ranges if re.fullmatch(MARK_RE, mk)) >= 0.5 * len(ranges):
            out.append(dict(kind='list', marks=marks, ranges=dict(ranges), levels=[]))
    return out


# ---------------------------------------------------------------------------
def parse_schedule_page(p):
    W, G, H, V = page_items(p)
    L = level_labels(W)
    tables = _grid_tables(W, G, H, V, L)
    taken = set(mk for t in tables for mk in t['marks'])
    # transposed: marks in a column down the side, levels across the top
    W2, G2, H2, V2, L2 = _swap(W, G, H, V, L)
    for t in _grid_tables(W2, G2, H2, V2, L2, transposed=True):
        if not (set(t['marks']) & taken):
            tables.append(t)
            taken |= set(t['marks'])
    for t in _list_tables(W, G, H, V, L):
        new = dict((mk, v) for mk, v in t['ranges'].items() if mk not in taken)
        if new:
            t['ranges'] = new
            t['marks'] = dict((mk, t['marks'][mk]) for mk in new)
            tables.append(t)
            taken |= set(new)
    return tables


def parse_schedule(path):
    doc = pymupdf.open(path)
    S = dict(marks={}, levels=[], table={}, order={}, ranges={}, pages=[])
    seen_lv = []
    per_mark = collections.defaultdict(list)
    for i, p in enumerate(doc):
        for t in parse_schedule_page(p):
            S['pages'].append(dict(page=i + 1, kind=t['kind'], marks=len(t['marks']),
                                   levels=len(t['levels'])))
            for mk in t['marks']:
                S['marks'].setdefault(mk, i + 1)
            if t['kind'] == 'list':
                for mk, rs in t['ranges'].items():
                    S['ranges'].setdefault(mk, []).extend(rs)
                continue
            S['table'].update(t['table'])
            for mk, c in t.get('defaults', {}).items():
                S['ranges'].setdefault(mk, []).append((None, None, c))
            for l in t['levels']:
                if l not in seen_lv:
                    seen_lv.append(l)
            for mk in t['marks']:
                per_mark[mk].append(t['levels'])
    for mk, lists in per_mark.items():
        lists.sort(key=lambda ls: statistics.median(level_rank(l) for l in ls))
        order = []
        for ls in lists:
            order += [l for l in ls if l not in order]
        S['order'][mk] = order
    S['levels'] = sorted(seen_lv, key=level_rank)
    for rs in S['ranges'].values():
        for lo, hi, c in rs:
            for l in (lo, hi):
                if l and l not in S['levels']:
                    S['levels'].append(l)
    return S


def family_for(entry):
    if entry.get('dia') or entry.get('type') in ROUND_TYPES:
        return 'circular'
    if entry.get('type') in BULLNOSE_TYPES:
        return 'bullnose'
    return 'rectangular'


def _rank_in(S, L):
    return level_rank(L)


def lookup(S, mk, L):
    """Schedule entry for mark at level L: a cell dict, 'none' (schedule shows
    no column there) or None (not in the schedule). Grid tables walk down to
    the size the column continues from."""
    L = norm_level(L)
    order = S['order'].get(mk)
    if order and L in order:
        for l in reversed(order[:order.index(L) + 1]):
            c = S['table'].get((mk, l))
            if c is None:
                break
            if c['size'] or c['dia'] or c.get('steel'):
                return c
            if c['gray']:
                return 'none'
    rs = S['ranges'].get(mk)
    if rs:
        r = level_rank(L)
        hits = [c for lo, hi, c in rs if (lo is None or level_rank(lo) <= r) and (hi is None or r <= level_rank(hi))]
        if hits:
            return hits[0]
        return 'none' if all(lo or hi for lo, hi, c in rs) else None
    return None


def all_types(S):
    """Every distinct (family, size) in the whole schedule."""
    seen = {}

    def add(mk, e):
        if not isinstance(e, dict) or e.get('steel') or not (e['size'] or e['dia']):
            return
        fam = family_for(e)
        key = (fam, tuple(e['size']) if e['size'] else (e['dia'],))
        seen.setdefault(key, set()).add(mk)
    for mk, order in S['order'].items():
        for l in order:
            add(mk, lookup(S, mk, l))
    for mk, rs in S['ranges'].items():
        for lo, hi, c in rs:
            add(mk, c)
    return [dict(family=k[0], size=list(k[1]), marks=sorted(v)) for k, v in sorted(seen.items())]


def summary(S):
    """One line per table for the button's status text."""
    return ['p%d %s table: %d marks x %d levels' % (t['page'], t['kind'], t['marks'], t['levels'])
            if t['kind'] != 'list' else 'p%d list table: %d marks' % (t['page'], t['marks'])
            for t in S['pages']]


if __name__ == '__main__':
    import sys
    S = parse_schedule(sys.argv[1])
    print('\n'.join(summary(S)))
    print('levels:', ' '.join(S['levels']))
    for L in sys.argv[2:]:
        for mk in sorted(S['marks'], key=lambda m: (re.sub(r'\d', '', m), int(re.search(r'\d+', m).group(0)))):
            e = lookup(S, mk, L)
            if isinstance(e, dict):
                print(L, mk, e['size'] or ('%dØ' % e['dia']), e['type'], family_for(e))
            else:
                print(L, mk, e)
