"""Read the dimensions off a PDF soffit plan exported from Revit.

A dimension is recognised when a length text (8'-11 1/2", 10", 1'-3" TO CJ) sits beside two tick marks on a line
running the same way, one each side of the text, whose spacing is that length at the sheet's scale. The scale is
not trusted from the title block: every text / tick-pair candidate votes, the most common ratio wins
(model inches per paper inch, e.g. 96 = 1/8" = 1'-0"). Texts pulled off their line with a leader are not matched.

All positions are in paper inches in the PDF's own (unrotated) page frame; `axis` says which way the dim runs.

CPython 3 + PyMuPDF.
"""
import collections
import re

import pymupdf

FT = re.compile(r"^(\d{1,3})'\s*-?\s*(\d{1,4})?(?:\s+(\d{1,2})/(\d{1,2}))?\"?\s*(.*)$")
IN = re.compile(r"^(\d{1,2})(?:\s+(\d{1,2})/(\d{1,2}))?\"\s*(.*)$")
DENOM = re.compile(r"^(2|4|8|16|32|64)\"$")
TICK_MIN, TICK_MAX = 1.5, 9.0          # tick mark box size, points
PERP_MAX = 16.0                        # text centre to dim line, points
SCALE_TOL = 0.025                      # match: within 2.5 % of the sheet scale (+ 1" model)


def parse(t):
    """(feet, suffix) or None.  A glued fraction numerator ('8'-111' = 8'-11 1/2") is dropped, not misread."""
    t = t.replace("|", "").strip()
    m = FT.match(t)
    if m:
        inch = m.group(2) or ""
        if len(inch) >= 2 and int(inch[:2]) <= 11:
            inch = inch[:2]
        elif inch:
            inch = inch[0]
        v = int(m.group(1)) + (int(inch) if inch else 0) / 12.0
        if m.group(3):
            v += float(m.group(3)) / float(m.group(4)) / 12.0
        return v, m.group(5).strip()
    m = IN.match(t)
    if m and int(m.group(1)) < 12:
        v = int(m.group(1)) / 12.0
        if m.group(2):
            v += float(m.group(2)) / float(m.group(3)) / 12.0
        return v, m.group(4).strip()
    return None


def _texts(pg):
    out = []
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            t = "".join(s["text"] for s in l["spans"]).strip()
            if not t or DENOM.match(t):
                continue
            p = parse(t)
            if p is None or len(p[1]) > 16 or re.search(r"[a-z]", p[1]):
                continue
            if re.search(r"SLAB|WALL|BEAM|COL\b|COLUMN|\bDP\b|X\d|THK|PT\b|MILD|CIP|CMU", p[1]):
                continue
            dx, dy = l["dir"]
            if abs(dx) > 0.98:
                axis = "x"
            elif abs(dy) > 0.98:
                axis = "y"
            else:
                continue                       # dims on angled grids: skipped
            r = pymupdf.Rect(l["bbox"])
            out.append(dict(text=t, ft=p[0], suffix=p[1], axis=axis, cx=(r.x0 + r.x1) / 2, cy=(r.y0 + r.y1) / 2,
                            size=l["spans"][0]["size"]))
    return out


def _ticks(pg):
    """Tick centres: small drawings, plus short 45-degree strokes inside larger paths (Revit often draws the
    dim line and its ticks as one path).  Doubles (fill + stroke, both edges of a thick tick) merged within 1.5 pt."""
    pts = []
    for d in pg.get_drawings():
        r = d["rect"]
        if TICK_MIN < r.width < TICK_MAX and TICK_MIN < r.height < TICK_MAX:
            pts.append(((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2))
            continue
        for it in d["items"]:
            if it[0] != "l":
                continue
            a, b = it[1], it[2]
            dx, dy = abs(b.x - a.x), abs(b.y - a.y)
            if 1.5 < dx < 7 and 1.5 < dy < 7 and 0.6 < dx / dy < 1.6:
                pts.append(((a.x + b.x) / 2, (a.y + b.y) / 2))
    grid, uniq = {}, []
    for x, y in pts:
        k = (int(x // 1.5), int(y // 1.5))
        if any(abs(x - u[0]) < 1.5 and abs(y - u[1]) < 1.5
               for i in (-1, 0, 1) for j in (-1, 0, 1) for u in grid.get((k[0] + i, k[1] + j), ())):
            continue
        grid.setdefault(k, []).append((x, y))
        uniq.append((x, y))
    return uniq


def _candidates(texts, ticks):
    """For each text: per nearby parallel line, the nearest tick each side → (text, a0, a1, p)."""
    byp = collections.defaultdict(list)                       # bucket ticks by perpendicular coordinate
    for x, y in ticks:
        byp[("x", round(y))].append((x, y))                   # x-running dims: same y
        byp[("y", round(x))].append((y, x))
    out = []
    for t in texts:
        a, p = (t["cx"], t["cy"]) if t["axis"] == "x" else (t["cy"], t["cx"])
        lines = collections.defaultdict(list)
        for k in range(int(p - PERP_MAX) - 1, int(p + PERP_MAX) + 2):
            for aa, pp in byp.get((t["axis"], k), ()):
                if abs(pp - p) <= PERP_MAX:
                    lines[round(pp * 2)].append((aa, pp))
        for pts in lines.values():
            left = [q for q in pts if q[0] < a]
            right = [q for q in pts if q[0] > a]
            if left and right:
                l, r = max(left), min(right)
                if r[0] - l[0] > 2:
                    out.append((t, l[0], r[0], (l[1] + r[1]) / 2))
    return out


def extract(pg):
    """(dims, scale).  dims: dict(ft, suffix, text, axis, a0, a1, p) in paper inches; scale = model in per paper in."""
    texts, ticks = _texts(pg), _ticks(pg)
    cands = _candidates(texts, ticks)
    votes = collections.Counter()
    for t, a0, a1, p in cands:
        if t["ft"] >= 2.0:
            votes[round(t["ft"] * 12 / ((a1 - a0) / 72.0))] += 1
    if not votes:
        return [], None
    # cluster the votes (±2 %) and take the best cluster
    best = max(votes, key=lambda s: sum(n for v, n in votes.items() if abs(v - s) <= 0.02 * s))
    scale = best
    dims, used = [], set()
    for t, a0, a1, p in sorted(cands, key=lambda c: abs(c[3] - (c[0]["cy"] if c[0]["axis"] == "x" else c[0]["cx"]))):
        if id(t) in used:
            continue
        model_in = (a1 - a0) / 72.0 * scale
        if abs(model_in - t["ft"] * 12) <= 1.0 + SCALE_TOL * t["ft"] * 12:
            used.add(id(t))
            dims.append(dict(ft=t["ft"], suffix=t["suffix"], text=t["text"], axis=t["axis"],
                             a0=a0 / 72.0, a1=a1 / 72.0, p=p / 72.0))
    return dims, scale


def unmatched_texts(pg, dims):
    """Length texts that did not match a dim line (pulled-out text, elevation tags, notes)."""
    got = {d["text"] for d in dims}
    return [t for t in _texts(pg) if t["text"] not in got]


GRID_LABEL = re.compile(r"[A-Z]{1,2}(\.\d{1,2})?|\d{1,3}(\.\d{1,2})?|[A-Z]{0,2}-?\d{1,2}[A-Z]?(\.\d)?")


def grids(pg):
    """Grid lines from their bubbles: a short label (A, 12, CA.2, ...) inside a circle; the two bubbles of one
    label on the same x make a vertical grid, on the same y a horizontal one.  Returns {"x": [x...], "y": [y...]}
    in paper inches - "x" holds the x of vertical grids (what x-running dims end on), "y" the y of horizontal ones.
    Angled grids and grids with a single bubble are left out."""
    circles = [d["rect"] for d in pg.get_drawings()
               if any(it[0] == "c" for it in d["items"]) and 10 < d["rect"].width < 70
               and abs(d["rect"].width - d["rect"].height) < 2]
    found = collections.defaultdict(list)
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            t = "".join(s["text"] for s in l["spans"]).strip()
            if not t or not GRID_LABEL.fullmatch(t):
                continue
            r = pymupdf.Rect(l["bbox"])
            c = pymupdf.Point((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)
            for cr in circles:
                if cr.contains(c):
                    found[t].append(((cr.x0 + cr.x1) / 2, (cr.y0 + cr.y1) / 2))
                    break
    out = {"x": [], "y": []}
    for pts in found.values():
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                (x1, y1), (x2, y2) = pts[i], pts[j]
                if abs(x1 - x2) < 1.0 and abs(y1 - y2) > 50:
                    out["x"].append((x1 + x2) / 144)
                elif abs(y1 - y2) < 1.0 and abs(x1 - x2) > 50:
                    out["y"].append((y1 + y2) / 144)
    for k in out:
        out[k] = sorted(set(round(v, 3) for v in out[k]))
    return out
