# -*- coding: utf-8 -*-
"""CPython, no Revit. Score a run's dim snapshot against Adolfo's hand-edited
version of the same view, SEGMENT by segment (a chain he drew as two dims on
one line and the tool as one joined string must count as the same thing):
a segment = (its two referenced elements, its value); it agrees when his
has the same segment with its line within 3/16" (paper) of ours.
usage: python agree_with_edits.py snapshot_L3N_run63.json [snapshot_L3N_after_edits.json]"""
import sys, json, io

TOL_IN = 0.1875          # "agrees" = within 3/16" of his line
run = sys.argv[1]
hand = sys.argv[2] if len(sys.argv) > 2 else "snapshot_L3N_after_edits.json"
R = json.load(io.open(run, encoding="utf-8"))
H = json.load(io.open(hand, encoding="utf-8"))
scale = R["meta"].get("scale") or H["meta"].get("scale") or 128
k_in = 12.0 / scale


def segments(d):
    """[(key, dim)] - one per segment: the two elements it runs between
    (refs are in witness order) and its value in 1/8"."""
    out = []
    els = d["ref_elems"]
    for i, s in enumerate(d["segments"]):
        if not s["value"]:
            continue
        pair = tuple(sorted(els[i:i + 2])) if i + 1 < len(els) else tuple(els[i:i + 1])
        out.append(((pair, int(round(s["value"] * 96))), d))
    return out


def offset_in(a, b):
    # perpendicular distance from b's origin to a's dim line, paper inches
    dx, dy = b["origin"][0] - a["origin"][0], b["origin"][1] - a["origin"][1]
    ux, uy = a["dir"]
    return abs(dx * uy - dy * ux) * k_in


hand_by = {}
for d in H["dims"]:
    for key, dd in segments(d):
        hand_by.setdefault(key, []).append(dd)
agree = moved = only_tool = 0
n_tool = 0
moves = []
used = set()
for d in R["dims"]:
    for key, dd in segments(d):
        n_tool += 1
        cands = hand_by.get(key)
        if not cands:
            only_tool += 1
            continue
        used.add(key)
        off = min(offset_in(d, h) for h in cands)
        if off <= TOL_IN:
            agree += 1
        else:
            moved += 1
            moves.append((off, d["id"], key[1] / 96.0))
n_hand = sum(len(segments(d)) for d in H["dims"])
only_hand = sum(1 for d in H["dims"] for key, _ in segments(d) if key not in used)
print("%s vs %s (scale 1:%d) - by segment" % (run, hand, scale))
print("  tool segments %d: same as his, within 3/16\": %d | same, further off: %d | he does not have it: %d"
      % (n_tool, agree, moved, only_tool))
print("  his segments %d: not produced by the tool: %d" % (n_hand, only_hand))
for off, i, v in sorted(moves, reverse=True)[:12]:
    print("    off %.2f in  dim %d  %.2f ft" % (off, i, v))
