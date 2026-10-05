# -*- coding: utf-8 -*-
# Read-only: re-run Dim Soffit v2's plan + layout for a test view (no dims
# created) and dump the review list with each string's intended line, for the
# review page. Globals in: VIEW_NAME, OUT (json path).
import sys, json, io
lib = r"C:\Users\agarcia\Desktop\Claude Projects\Outline Annotator\MCC.extension\lib"
if lib not in sys.path:
    sys.path.insert(0, lib)
for m in [m for m in list(sys.modules) if m.startswith("mcc_")]:
    del sys.modules[m]
import mcc_model as M, mcc_coverage as CV, mcc_strings as S, mcc_layout as LY
from mcc_compat import eid_int

tv = next(v for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan) if v.Name == VIEW_NAME)
model = M.PlanModel(doc, tv)
fs, pl = S.plan_view(model, CV.crop_poly(tv))
dt = next(t for t in DB.FilteredElementCollector(doc).OfClass(DB.DimensionType)
          if t.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == '5/64" Arial Narrow (Transparent)')
ac = CV.annotation_crop_poly(tv)
lay = LY.Layout(model, pl.strings, tv, dt, ac)
lay.run()

KIND = {"run": "Slab edge", "corner": "Slab corner", "bump": "Slab bump", "notch": "Slab notch", "step": "Slab step",
        "opening": "Opening", "beam": "Beam", "cj": "Construction joint"}
SUB = {"core": "core opening", "shaft": "shaft", "void": "small void", "penetration": "penetration", "plain": "opening"}
REF = {"grid": "grid", "slab edge": "slab edge", "opening edge": "opening edge", "beam side": "beam side",
       "beam end": "beam end", "cj": "CJ", "wall face": "wall face"}

items = []
for k, (s, why) in enumerate(lay.review):
    f = s.feature
    kind = KIND.get(f.kind, f.kind) if f else "?"
    if f is not None and f.kind == "opening":
        kind = SUB.get(getattr(f, "sub", ""), "opening").capitalize()
    offs = [r[0] for r in s.refs]
    lo, hi = min(offs), max(offs)
    st = s.prefer if s.prefer is not None else sum(s.span) / 2.0
    p = lay.world(s.gi, st, lo)
    q = lay.world(s.gi, st, hi)
    # ref chain in words: grid CC -> 15'-0" -> opening edge
    parts = []
    vals = s.values()
    for i, r in enumerate(s.refs):
        nm = s.names[i] if i < len(s.names) else r[2]
        if r[2] == "grid":
            parts.append("grid " + nm)
        else:
            parts.append(REF.get(r[2], r[2]))
        if i < len(vals):
            parts.append(S.ftin(vals[i]))
    eid = ""
    if f is not None and f.owners:
        eid = str(list(f.owners)[0])
    items.append({
        "id": "%s-%02d" % (VIEW_NAME.split(" - ")[1].split(" (")[0].replace(" ", ""), k + 1),
        "kind": kind, "role": s.role, "reason": why, "chain": parts,
        "label": s.label, "p": [p[0], p[1]], "q": [q[0], q[1]],
        "intermediate": bool(getattr(s, "intermediate", False)), "element": eid,
    })
xs = [pt[0] for pt in ac]; ys = [pt[1] for pt in ac]
out = {"view": VIEW_NAME, "scale": tv.Scale, "crop": [min(xs), min(ys), max(xs), max(ys)], "items": items}
with io.open(OUT, "w", encoding="utf-8") as fh:
    fh.write(unicode(json.dumps(out, indent=1)))
print(len(items), "items; crop", out["crop"])
