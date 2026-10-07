"""Measure how the past soffit plans in Soffit Plans/ are dimensioned (dims read by dimgeom.py).

Per sheet -> dim_stats.csv; `--summary` prints the totals by era (job 1038-1099, 1100-1199, 1200+).

What is measured, all on paper unless stated:
- dims: count, lengths (model ft), share over 20 / 30 ft, words after the value (R.O., TO CJ, TYP ...)
- strings: dims on one line joined end to end (a chain) - size of each
- stacks: dims on parallel lines sharing one end (baseline from one grid / edge) - rows per stack, spacing
  between rows, whether lengths grow row by row, and whether the shortest row is nearest the element (from the
  witness line at the far end: it runs from the dim line toward what is dimensioned)
- first row off the element: witness line length at a stack's shortest row

CPython 3 + PyMuPDF.  Run:  python analyze_dims.py    |    python analyze_dims.py --summary
"""
import collections
import csv
import glob
import json
import multiprocessing
import os
import statistics
import sys

import pymupdf

import dimgeom

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "dim_stats.csv")
EPS = 0.6 / 72                       # same point / same line, paper inches
ROW_MAX = 0.6                        # rows of one stack: neighbours at most this far apart, paper inches
FIELDS = ["file", "job", "scale", "texts", "dims", "lengths", "over20", "over30", "suffixes", "strings",
          "string_sizes", "stacks", "stack_rows", "row_gaps", "stack_monotonic", "shortest_nearest",
          "first_row", "joined_dims", "grids", "grid_classes", "over30_by_class", "points", "located_direct",
          "located_chain"]
GTOL = 1.0 / 72                      # a dim end on a grid line


def segments(pg):
    """Axis-aligned straight lines, paper inches: (kind h/v, fixed coord, lo, hi)."""
    out = []
    for d in pg.get_drawings():
        for it in d["items"]:
            if it[0] == "re":                      # some exports draw thin lines as hairline rectangles
                r = it[1]
                if r.width < 0.8 and r.height > 1.0:
                    out.append(("v", (r.x0 + r.x1) / 144, r.y0 / 72, r.y1 / 72))
                elif r.height < 0.8 and r.width > 1.0:
                    out.append(("h", (r.y0 + r.y1) / 144, r.x0 / 72, r.x1 / 72))
                continue
            if it[0] != "l":
                continue
            a, b = it[1], it[2]
            if abs(a.x - b.x) < 0.2 and abs(a.y - b.y) > 1.0:
                out.append(("v", a.x / 72, min(a.y, b.y) / 72, max(a.y, b.y) / 72))
            elif abs(a.y - b.y) < 0.2 and abs(a.x - b.x) > 1.0:
                out.append(("h", a.y / 72, min(a.x, b.x) / 72, max(a.x, b.x) / 72))
    return out


def witness_side(dim, end, segs_by):
    """At the dim's end `end` (a coordinate along it) the witness line runs across the dim line, long toward what
    is dimensioned.  Returns (+1 / -1 side of the dim line, its length past the dim line) or None."""
    kind = "v" if dim["axis"] == "x" else "h"
    best = None
    for k in (round(end * 72) - 1, round(end * 72), round(end * 72) + 1):
        for _, c, lo, hi in segs_by.get((kind, k), ()):
            if abs(c - end) > EPS or not (lo - EPS <= dim["p"] <= hi + EPS):
                continue
            up, down = hi - dim["p"], dim["p"] - lo
            side, ln = (1, up) if up > down else (-1, down)
            if ln > 0.03 and (best is None or ln > best[1]):
                best = (side, ln)
    return best


def split_rows(ms, dims):
    """Cut a sorted list of rows wherever two neighbours are more than ROW_MAX apart."""
    out, cur = [], [ms[0]] if ms else []
    for m in ms[1:]:
        if dims[m[0]]["p"] - dims[cur[-1][0]]["p"] > ROW_MAX:
            out.append(cur)
            cur = []
        cur.append(m)
    out.append(cur)
    return [c for c in out if len(c) >= 2]


def stack_stats(ms, dims, segs_by, rows, gaps, mono, near, first):
    rows.append(len(ms))
    ps = [dims[m[0]]["p"] for m in ms]
    gaps += [round(b - a, 4) for a, b in zip(ps, ps[1:])]
    lens = [abs(m[2] - m[1]) for m in ms]
    inc = all(x <= y + 1e-6 for x, y in zip(lens, lens[1:]))
    dec = all(x >= y - 1e-6 for x, y in zip(lens, lens[1:]))
    mono.append(inc or dec)
    shortest = min(ms, key=lambda m: abs(m[2] - m[1]))
    w = witness_side(dims[shortest[0]], shortest[2], segs_by)
    if w:
        others = [dims[m[0]]["p"] - dims[shortest[0]]["p"] for m in ms if m is not shortest]
        near.append(all((o > 0) != (w[0] > 0) for o in others))
        first.append(round(w[1], 3))


def sheet_stats(path):
    pymupdf.TOOLS.mupdf_display_errors(False)
    doc = pymupdf.open(path)
    pg = doc[0]
    dims, scale = dimgeom.extract(pg)
    gr = dimgeom.grids(pg)
    ntexts = len(dimgeom._texts(pg))
    segs_by = collections.defaultdict(list)
    for s in segments(pg):
        segs_by[(s[0], round(s[1] * 72))].append(s)
    doc.close()

    # strings: same axis, same line, sharing an end
    n = len(dims)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    byline = collections.defaultdict(list)
    for i, d in enumerate(dims):
        byline[(d["axis"], round(d["p"] * 72))].append(i)
    for idx in byline.values():
        for i in idx:
            for j in idx:
                if i < j and abs(dims[i]["p"] - dims[j]["p"]) < EPS and (
                        abs(dims[i]["a1"] - dims[j]["a0"]) < EPS or abs(dims[i]["a0"] - dims[j]["a1"]) < EPS):
                    parent[find(i)] = find(j)
    sizes = sorted(collections.Counter(find(i) for i in range(n)).values())

    # stacks: dims on parallel lines sharing one end, the other ends all the same way
    ends = collections.defaultdict(list)
    for i, d in enumerate(dims):
        for e, other in ((d["a0"], d["a1"]), (d["a1"], d["a0"])):
            ends[(d["axis"], round(e * 72 / 0.6))].append((i, e, other))
    rows, gaps, mono, near, first = [], [], [], [], []
    for members in ends.values():
        grp = {}
        for m in members:
            grp.setdefault(m[2] > m[1], []).append(m)
        for ms in grp.values():
            byp = {}
            for m in sorted(ms, key=lambda m: abs(m[2] - m[1])):
                byp.setdefault(round(dims[m[0]]["p"] * 72), m)       # one row per line
            ms = sorted(byp.values(), key=lambda m: dims[m[0]]["p"])
            # rows of one stack sit next to each other; the same end on the far side of the plan is another group
            for ms in split_rows(ms, dims):
                stack_stats(ms, dims, segs_by, rows, gaps, mono, near, first)
    lengths = [round(d["ft"], 2) for d in dims]

    # grid anchoring (only when the sheet's grids were found: >= 3 each way)
    has_grids = len(gr["x"]) >= 3 and len(gr["y"]) >= 3
    on_grid = lambda d, e: any(abs(e - g) < GTOL for g in gr[d["axis"]])  # noqa: E731
    classes = collections.Counter()
    over30 = collections.Counter()
    points, direct, chained = set(), set(), set()
    if has_grids:
        for i, d in enumerate(dims):
            k = on_grid(d, d["a0"]) + on_grid(d, d["a1"])
            c = ["no grid", "one end on grid", "grid to grid"][k]
            classes[c] += 1
            if d["ft"] > 30:
                over30[c] += 1
            for e, o in ((d["a0"], d["a1"]), (d["a1"], d["a0"])):
                if not on_grid(d, e):
                    pt = (d["axis"], round(e * 72), round(d["p"] * 72 / 72))   # point ~ coord + rough region
                    points.add(pt)
                    if on_grid(d, o):
                        direct.add(pt)
        # through a chain: a string with a grid at one end locates every point on it (piece by piece)
        strings = collections.defaultdict(list)
        for i in range(n):
            strings[find(i)].append(dims[i])
        for ds in strings.values():
            if any(on_grid(d, e) for d in ds for e in (d["a0"], d["a1"])):
                for d in ds:
                    for e in (d["a0"], d["a1"]):
                        if not on_grid(d, e):
                            chained.add((d["axis"], round(e * 72), round(d["p"] * 72 / 72)))
    suf = collections.Counter(d["suffix"].upper().rstrip(".") for d in dims if d["suffix"])
    return dict(file=os.path.relpath(path, HERE), job=os.path.basename(os.path.dirname(path))[:4], scale=scale,
                texts=ntexts, dims=n, lengths=json.dumps(lengths), over20=sum(x > 20 for x in lengths),
                over30=sum(x > 30 for x in lengths), suffixes=json.dumps(dict(suf)), strings=len(sizes),
                string_sizes=json.dumps(sizes), stacks=len(rows), stack_rows=json.dumps(rows), row_gaps=json.dumps(gaps),
                stack_monotonic=json.dumps(mono), shortest_nearest=json.dumps(near), first_row=json.dumps(first),
                joined_dims=sum(s for s in sizes if s > 1), grids=int(has_grids),
                grid_classes=json.dumps(dict(classes)), over30_by_class=json.dumps(dict(over30)), points=len(points),
                located_direct=len(direct & points), located_chain=len((direct | chained) & points))


def summary():
    rows = [r for r in csv.DictReader(open(OUT, encoding="utf-8")) if int(r["dims"]) >= 10]
    era = lambda j: "1038-1099" if j < "1100" else ("1100-1199" if j < "1200" else "1200+")  # noqa: E731
    groups = collections.defaultdict(list)
    for r in rows:
        groups[era(r["job"])].append(r)
        groups["ALL"].append(r)
    L = lambda r, k: json.loads(r[k])  # noqa: E731
    for k in ["1038-1099", "1100-1199", "1200+", "ALL"]:
        rs = groups[k]
        lens = [x for r in rs for x in L(r, "lengths")]
        big = sorted(x for x in lens if x >= 1)
        sizes = [x for r in rs for x in L(r, "string_sizes")]
        stk = [x for r in rs for x in L(r, "stack_rows")]
        gaps = [x for r in rs for x in L(r, "row_gaps")]
        mono = [x for r in rs for x in L(r, "stack_monotonic")]
        near = [x for r in rs for x in L(r, "shortest_nearest")]
        first = sorted(x for r in rs for x in L(r, "first_row"))
        suf = collections.Counter()
        for r in rs:
            suf.update(L(r, "suffixes"))
        print("== %s: %d sheets from %d jobs; %d dims (median %d per sheet; %d%% of length texts matched a dim line)"
              % (k, len(rs), len({r["job"] for r in rs}), len(lens), statistics.median(int(r["dims"]) for r in rs),
                 100 * len(lens) // max(1, sum(int(r["texts"]) for r in rs))))
        print("   length: > 20 ft %.1f%%; > 30 ft %.1f%%; sheets with a dim > 30 ft %d%%; quantiles 50/75/90/95/99: %s ft"
              % (100.0 * sum(x > 20 for x in big) / len(big), 100.0 * sum(x > 30 for x in big) / len(big),
                 100 * sum(int(r["over30"]) > 0 for r in rs) // len(rs),
                 ", ".join("%.0f" % big[int(f * (len(big) - 1))] for f in (0.5, 0.75, 0.9, 0.95, 0.99))))
        print("   strings: %d; single dims %d%%; chains of 2+ %d%% of strings holding %d%% of dims; chain size median %s"
              % (len(sizes), 100 * sum(s == 1 for s in sizes) // len(sizes), 100 * sum(s > 1 for s in sizes) // len(sizes),
                 100 * sum(s for s in sizes if s > 1) // sum(sizes), statistics.median([s for s in sizes if s > 1] or [0])))
        print("   stacks (parallel rows sharing an end): %d; rows per stack %s" % (
            len(stk), dict(sorted(collections.Counter(min(x, 6) for x in stk).items()))))
        gh = collections.Counter(round(g * 64) for g in gaps if g < 1)
        print("   row spacing in 64ths of an inch (count): %s; median %.3f\"" % (
            ", ".join("%d:%d" % kv for kv in sorted(gh.most_common(8))), statistics.median(gaps)))
        print("   stack lengths grow row by row: %d%%; shortest row nearest the element: %d%% (n=%d)" % (
            100 * sum(mono) // max(1, len(mono)), 100 * sum(near) // max(1, len(near)), len(near)))
        print("   first row off the element (witness): median %.3f\", quartiles %.3f-%.3f\"" % (
            statistics.median(first), first[len(first) // 4], first[3 * len(first) // 4]))
        g = [r for r in rs if r["grids"] == "1"]
        cls, o30 = collections.Counter(), collections.Counter()
        for r in g:
            cls.update(L(r, "grid_classes"))
            o30.update(L(r, "over30_by_class"))
        tot = sum(cls.values()) or 1
        print("   grids found on %d sheets: dims %s; over 30 ft by kind %s" % (
            len(g), {c: "%d%%" % (100 * v // tot) for c, v in cls.items()},
            {c: "%d of %d (%d%%)" % (o30[c], cls[c], 100 * o30[c] // max(1, cls[c])) for c in cls}))
        pts = sum(int(r["points"]) for r in g) or 1
        print("   points (dim ends off grid): located straight off a grid %d%%, incl. through a grid-anchored chain %d%%"
              % (100 * sum(int(r["located_direct"]) for r in g) // pts, 100 * sum(int(r["located_chain"]) for r in g) // pts))
        print("   scales (model in per paper in): %s" % collections.Counter(r["scale"] for r in rs).most_common(6))
        print("   words on dims: %s" % suf.most_common(14))


def main():
    if "--summary" in sys.argv:
        return summary()
    files = sorted(glob.glob(os.path.join(HERE, "Soffit Plans", "*", "*.pdf")))
    with multiprocessing.Pool(8) as pool, open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        for row in pool.imap_unordered(sheet_stats, files, chunksize=4):
            w.writerow(row)
    summary()


if __name__ == "__main__":
    main()
