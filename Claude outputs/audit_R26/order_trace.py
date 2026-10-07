# -*- coding: utf-8 -*-
"""Read-only: log the order and spot each string is placed in (dry layout).
Globals in: VIEW_NAME, OUT."""
import sys, io
lib = r"C:\Users\agarcia\Desktop\Claude Projects\Outline Annotator\MCC.extension\lib"
if lib not in sys.path:
    sys.path.insert(0, lib)
for m in [m for m in list(sys.modules) if m.startswith("mcc_")]:
    del sys.modules[m]
import mcc_model as M, mcc_coverage as CV, mcc_strings as S, mcc_layout as LY
tv = next(v for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan) if v.Name == VIEW_NAME)
dt = next(t for t in DB.FilteredElementCollector(doc).OfClass(DB.DimensionType)
          if t.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == '5/64" Arial Narrow (Transparent)')
model = M.PlanModel(doc, tv)
fs, pl = S.plan_view(model, CV.crop_poly(tv))
lines = ["PLAN %d %s | %s" % (i, s.label, [round(v, 3) for v in s.values()]) for i, s in enumerate(pl.strings)]
lay = LY.Layout(model, pl.strings, tv, dt, CV.annotation_crop_poly(tv))
orig = lay.place_one
def spy(s, allow_last_resort=False):
    r = orig(s, allow_last_resort)
    p = r[0]
    if s.label.startswith("core opening anchor|edges|anchor") and [round(v, 2) for v in s.values()] == [8.25, 11.75]:
        for base, st, cand in lay.candidates(s)[:12]:
            pen, why = lay.evaluate(s, st)
            lines.append("  CAND st %.3f base %.3f pen %s %s %s" % (st, base, pen, cand, why if pen is None else ""))
    lines.append("PLACE %s | %s -> %s" % (s.label, [round(v, 3) for v in s.values()], None if p is None else round(p.st_f, 3)))
    return r
lay.place_one = spy
lay.run()
for p in lay.placed:
    lines.append("FINAL %s | %s @ %.3f" % (p.s.label, [round(v, 3) for v in p.s.values()], p.st_f))
io.open(OUT, "w", encoding="utf-8").write(u"\n".join(unicode(l) for l in lines))
print(len(lines))
