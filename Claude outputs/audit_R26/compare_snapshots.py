# -*- coding: utf-8 -*-
"""Read-only: compare the before/after dim snapshots of a test view and
classify each change in the planner's own terms (the element's span along
the grid frame). Globals in: VIEW_NAME, BEFORE, AFTER, OUT."""
import sys, io, json, math
lib = r"C:\Users\agarcia\Desktop\Claude Projects\Outline Annotator\MCC.extension\lib"
if lib not in sys.path:
    sys.path.insert(0, lib)
for m in [m for m in list(sys.modules) if m.startswith("mcc_")]:
    del sys.modules[m]
import mcc_model as M, mcc_coverage as CV, mcc_strings as S, mcc_layout as LY
from mcc_compat import eid_int

B = json.loads(io.open(BEFORE, encoding="utf-8").read())
A = json.loads(io.open(AFTER, encoding="utf-8").read())
tv = next(v for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan) if v.Name == VIEW_NAME)
k_in = 12.0 / tv.Scale                      # ft -> paper inches
model = M.PlanModel(doc, tv)
fs, pl = S.plan_view(model, CV.crop_poly(tv))
dt = next(t for t in DB.FilteredElementCollector(doc).OfClass(DB.DimensionType)
          if t.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == '5/64" Arial Narrow (Transparent)')
lay = LY.Layout(model, pl.strings, tv, dt, CV.annotation_crop_poly(tv))
lay.run()


def key_of(elems, values):
    return (tuple(sorted(elems)), tuple(sorted(round(v * 96) for v in values if v)))


strings = {}
for p in lay.placed:
    strings.setdefault(key_of([eid_int(r[1].ElementId) for r in p.s.refs], p.s.values()), []).append(p)

after = dict((d["id"], d) for d in A["dims"])
rows = []
for d in B["dims"]:
    k = key_of(d["ref_elems"], [sg["value"] for sg in d["segments"]])
    pl_ = strings.get(k, [None])[0]
    s = pl_.s if pl_ else None
    t = d.get("tool", {})
    row = {"id": d["id"], "what": t.get("describe", ""), "feature": t.get("feature"), "role": t.get("role"),
           "label": t.get("label")}
    if d["id"] not in after:
        row["change"] = "deleted"
        rows.append(row); continue
    a = after[d["id"]]
    if sorted(a["ref_elems"]) != sorted(d["ref_elems"]) or \
            [round(x["value"] or 0, 3) for x in a["segments"]] != [round(x["value"] or 0, 3) for x in d["segments"]]:
        row["refs_changed"] = {"before": [round(x["value"] or 0, 3) for x in d["segments"]],
                               "after": [round(x["value"] or 0, 3) for x in a["segments"]],
                               "elems_before": d["ref_elems"], "elems_after": a["ref_elems"]}
    # the line moved? (perpendicular to the dim direction = along the element)
    u = d["dir"]; n = (-u[1], u[0])
    shift = (a["origin"][0] - d["origin"][0]) * n[0] + (a["origin"][1] - d["origin"][1]) * n[1]
    row["moved_in"] = round(shift * k_in, 3)
    if s is not None:
        g, g0, gu, gn = model.grids[s.gi]
        st0 = (d["origin"][0] - g0[0]) * gu[0] + (d["origin"][1] - g0[1]) * gu[1]
        st1 = (a["origin"][0] - g0[0]) * gu[0] + (a["origin"][1] - g0[1]) * gu[1]
        ext = lay._extent(s.feature, s.gi) if s.feature is not None else None
        lo, hi = ext if ext else s.span
        def where(st):
            if st < lo - 0.05: return ("below", lo - st)
            if st > hi + 0.05: return ("above", st - hi)
            return ("inside", 0.0)
        w0, w1 = where(st0), where(st1)
        row["before"] = "%s %.2fin" % (w0[0], w0[1] * k_in)
        row["after"] = "%s %.2fin" % (w1[0], w1[1] * k_in)
        if abs(shift) > 0.05:
            if w0[0] != w1[0] and "inside" not in (w0[0], w1[0]):
                row["move"] = "to the other side"
            elif w0[0] == "inside" and w1[0] != "inside":
                row["move"] = "out of the element to beside it"
            elif w0[0] != "inside" and w1[0] == "inside":
                row["move"] = "onto the element"
            elif w1[1] > w0[1]:
                row["move"] = "further from the element"
            elif w1[1] < w0[1]:
                row["move"] = "closer to the element"
            else:
                row["move"] = "along"
    # text moved relative to its segment
    tm = []
    for sb, sa in zip(d["segments"], a["segments"]):
        if "text" not in sb or "text" not in sa:
            continue
        rb = (sb["text"][0] - sb["origin"][0], sb["text"][1] - sb["origin"][1])
        ra = (sa["text"][0] - sa["origin"][0], sa["text"][1] - sa["origin"][1])
        dd = math.hypot(ra[0] - rb[0], ra[1] - rb[1]) * k_in
        if dd > 0.03:
            tm.append(round(dd, 2))
    if tm:
        row["text_moved_in"] = tm
    if a.get("type") != d.get("type"):
        row["type"] = [d.get("type"), a.get("type")]
    if any(x in row for x in ("move", "text_moved_in", "refs_changed", "type")):
        row["change"] = "edited"
    else:
        row["change"] = "unchanged"
    rows.append(row)
before_ids = set(d["id"] for d in B["dims"])
for a in A["dims"]:
    if a["id"] in before_ids:
        continue
    names = []
    for e in a["ref_elems"]:
        el = doc.GetElement(DB.ElementId(DB.Int64(e))) if hasattr(DB, "Int64") else None
        if el is None:
            try:
                el = doc.GetElement(M.make_eid(e)) if hasattr(M, "make_eid") else None
            except Exception:
                el = None
        names.append("%s %s" % (el.Category.Name if el is not None and el.Category else "?", el.Name if el is not None else e))
    rows.append({"id": a["id"], "change": "added", "values": [round(x["value"] or 0, 3) for x in a["segments"]],
                 "refs": names})
io.open(OUT, "w", encoding="utf-8").write(unicode(json.dumps(rows, indent=1)))
from collections import Counter
c = Counter(r["change"] for r in rows)
print(dict(c), dict(Counter(r.get("move") for r in rows if r.get("move"))))
