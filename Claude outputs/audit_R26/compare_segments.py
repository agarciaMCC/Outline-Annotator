# -*- coding: utf-8 -*-
"""CPython, no Revit. Segment-by-segment comparison of a tool snapshot (real or
synthetic) with Adolfo's hand-edited snapshot of the same view, when element
ids can't be matched (the view was re-placed in between). A segment = the two
elements it runs between + its value. Classifies each tool segment as
left (his line within TOL of ours) / moved (offset, direction) / deleted, and
each of his segments the tool lacks as added. Writes a JSON for the analyst.
usage: python compare_segments.py <tool.json> <hand.json> <out.json>"""
import sys, json, io, math

TOL_IN = 0.1875
tool, hand, outp = sys.argv[1], sys.argv[2], sys.argv[3]
T = json.load(io.open(tool, encoding="utf-8"))
H = json.load(io.open(hand, encoding="utf-8"))
scale = T["meta"].get("scale") or H["meta"].get("scale") or 128
k_in = 12.0 / scale


def segs(d):
    out = []
    els = d["ref_elems"]
    for i, s in enumerate(d["segments"]):
        if not s["value"]:
            continue
        pair = tuple(sorted(els[i:i + 2])) if i + 1 < len(els) else tuple(els[i:i + 1])
        out.append(((pair, int(round(s["value"] * 96))), d, s))
    return out


def offset_in(a, b):
    """Signed perpendicular offset of b's origin from a's dim line, paper inches."""
    dx, dy = b["origin"][0] - a["origin"][0], b["origin"][1] - a["origin"][1]
    ux, uy = a["dir"]
    return (dx * uy - dy * ux) * k_in


hand_by = {}
hand_all = []
for d in H["dims"]:
    for key, dd, s in segs(d):
        hand_by.setdefault(key, []).append((dd, s))
        hand_all.append((key, dd, s))


def same_dim_elsewhere(d, s, key):
    """The same dimension drawn to a different reference (beam centreline
    halves, the 12" slab instead of the 10", a CJ whose id changed when the
    test view was duplicated): equal value, parallel, segment midpoints within
    8 ft. -> [(hand dim, hand seg, hand key)] or []."""
    out = []
    for hkey, hd, hs in hand_all:
        if hkey[1] != key[1] or abs(hd["dir"][0] * d["dir"][0] + hd["dir"][1] * d["dir"][1]) < 0.98:
            continue
        if math.hypot(hs["origin"][0] - s["origin"][0], hs["origin"][1] - s["origin"][1]) > 8.0:
            continue
        out.append((hd, hs, hkey))
    return out


rows = []
used = set()
for d in T["dims"]:
    chain = [round(s["value"], 2) for s in d["segments"]]
    for key, dd, s in segs(d):
        cands = hand_by.get(key)
        base = {"tool_dim": d["id"], "label": (d.get("tool") or {}).get("label"), "elements": list(key[0]),
                "value_ft": key[1] / 96.0, "chain": chain, "at": [round(x, 1) for x in s["origin"]],
                "dir": d["dir"]}
        if not cands:
            alt = same_dim_elsewhere(d, s, key)
            if alt:
                cands = [(hd, hs) for hd, hs, hk in alt]
                for hd, hs, hk in alt:
                    used.add(hk)
                base["other_reference"] = True
        if not cands:
            base["change"] = "deleted"
            rows.append(base); continue
        used.add(key)
        off, hd = min(((offset_in(d, h), h) for h, hs in cands), key=lambda t: abs(t[0]))
        base["his_dim"] = hd["id"]
        base["his_chain"] = [round(x["value"], 2) for x in hd["segments"]]
        base["offset_in"] = round(off, 2)
        base["change"] = "left" if abs(off) <= TOL_IN else "moved"
        rows.append(base)
for d in H["dims"]:
    chain = [round(s["value"], 2) for s in d["segments"]]
    for key, dd, s in segs(d):
        if key in used:
            continue
        rows.append({"his_dim": d["id"], "elements": list(key[0]), "value_ft": key[1] / 96.0, "chain": chain,
                     "at": [round(x, 1) for x in s["origin"]], "dir": d["dir"], "change": "added"})
counts = {}
for r in rows:
    counts[r["change"]] = counts.get(r["change"], 0) + 1
json.dump({"tool": tool, "hand": hand, "scale": scale, "tol_in": TOL_IN, "counts": counts, "rows": rows},
          io.open(outp, "w", encoding="utf-8"), indent=1)
print(counts)
