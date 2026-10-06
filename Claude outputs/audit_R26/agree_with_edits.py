# -*- coding: utf-8 -*-
"""CPython, no Revit. Score a run's dim snapshot against Adolfo's hand-edited
version of the same view: dims matched by referenced elements + values, then
the perpendicular offset of the dim line in paper inches.
usage: python agree_with_edits.py snapshot_L3N_run54.json [snapshot_L3N_after_edits.json]"""
import sys, json, io

TOL_IN = 0.1875          # "agrees" = within 3/16" of his line
run = sys.argv[1]
hand = sys.argv[2] if len(sys.argv) > 2 else "snapshot_L3N_after_edits.json"
R = json.load(io.open(run, encoding="utf-8"))
H = json.load(io.open(hand, encoding="utf-8"))
scale = R["meta"].get("scale") or H["meta"].get("scale") or 128
k_in = 12.0 / scale


def key(d):
    return (tuple(sorted(d["ref_elems"])), tuple(sorted(int(round(s["value"] * 96)) for s in d["segments"] if s["value"])))


def offset_in(a, b):
    # perpendicular distance from b's origin to a's dim line, paper inches
    dx, dy = b["origin"][0] - a["origin"][0], b["origin"][1] - a["origin"][1]
    ux, uy = a["dir"]
    return abs(dx * uy - dy * ux) * k_in


hand_by = {}
for d in H["dims"]:
    hand_by.setdefault(key(d), []).append(d)
agree = moved = only_tool = 0
moves = []
for d in R["dims"]:
    cands = hand_by.get(key(d))
    if not cands:
        only_tool += 1
        continue
    off = min(offset_in(d, h) for h in cands)
    if off <= TOL_IN:
        agree += 1
    else:
        moved += 1
        moves.append((off, d["id"], [s["value"] for s in d["segments"]]))
used = set(key(d) for d in R["dims"])
only_hand = sum(1 for d in H["dims"] if key(d) not in used)
print("%s vs %s (scale 1:%d)" % (run, hand, scale))
print("  tool dims %d: same dim as his, within 3/16\": %d | same dim, further off: %d | he does not have it: %d"
      % (len(R["dims"]), agree, moved, only_tool))
print("  his dims %d: not produced by the tool: %d" % (len(H["dims"]), only_hand))
for off, i, v in sorted(moves, reverse=True)[:12]:
    print("    off %.2f in  dim %d  %s" % (off, i, ["%.2f" % x for x in v]))
