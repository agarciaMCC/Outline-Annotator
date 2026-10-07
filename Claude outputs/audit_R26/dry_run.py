# -*- coding: utf-8 -*-
"""Read-only dry run of Dim Soffit v2: plan + layout for a test view with
layout setting overrides, NOTHING created in the model. Writes a synthetic
snapshot per variant in the snapshot_dims.py format, so compare_segments.py /
agree_with_edits.py score it like a real run. Lets a setting sweep run without
clearing the test views.
Globals in: VIEW_NAME, TAG, VARIANTS = [(name, {layout cfg overrides}), ...].
Writes dry_<TAG>_<name>.json; prints one line per variant."""
import sys, io, json, math, time
lib = r"C:\Users\agarcia\Desktop\Claude Projects\Outline Annotator\MCC.extension\lib"
if lib not in sys.path:
    sys.path.insert(0, lib)
for m in [m for m in list(sys.modules) if m.startswith("mcc_")]:
    del sys.modules[m]
import mcc_model as M, mcc_coverage as CV, mcc_strings as S, mcc_layout as LY
from mcc_compat import eid_int

D = r"C:\Users\agarcia\Desktop\Claude Projects\Outline Annotator\Claude outputs\audit_R26"
tv = next(v for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan) if v.Name == VIEW_NAME)
dt = next(t for t in DB.FilteredElementCollector(doc).OfClass(DB.DimensionType)
          if t.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == '5/64" Arial Narrow (Transparent)')
model = M.PlanModel(doc, tv)
crop, acrop = CV.crop_poly(tv), CV.annotation_crop_poly(tv)


def r4(v):
    return round(v, 4)


for name, cfg in VARIANTS:
    t0 = time.time()
    fs, pl = S.plan_view(model, crop)          # fresh strings: the layout edits them (joins)
    lay = LY.Layout(model, pl.strings, tv, dt, acrop, cfg=cfg)
    if globals().get("NO_CACHE"):
        _ev = lay.evaluate
        def _ev2(s_, st_, _ev=_ev, lay=lay):
            lay._ext_cache = {}
            return _ev(s_, st_)
        lay.evaluate = _ev2
    placed, review = lay.run()
    dims = []
    for i, p in enumerate(lay.placed):
        s = p.s
        st = p.cand[0]
        refs = sorted(s.refs, key=lambda r: r[0])
        a = lay.world(s.gi, st, refs[0][0])
        b = lay.world(s.gi, st, refs[-1][0])
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        segs = []
        for r0, r1 in zip(refs, refs[1:]):
            mid = lay.world(s.gi, st, (r0[0] + r1[0]) / 2.0)
            segs.append({"value": round(r1[0] - r0[0], 5), "origin": [r4(mid[0]), r4(mid[1])]})
        dims.append({"id": i, "origin": [r4(a[0]), r4(a[1])], "dir": [round((b[0] - a[0]) / L, 5), round((b[1] - a[1]) / L, 5)],
                     "ref_elems": [eid_int(r[1].ElementId) for r in refs], "segments": segs,
                     "tool": {"label": s.label, "role": s.role}})
    out = D + r"\dry_%s_%s.json" % (TAG, name)
    meta = {"view": VIEW_NAME, "scale": tv.Scale, "count": len(dims), "review": len(review or []),
            "variant": name, "cfg": cfg, "seconds": round(time.time() - t0, 1)}
    io.open(out, "w", encoding="utf-8").write(unicode(json.dumps({"meta": meta, "dims": dims}, indent=1)))
    print("%s %s: %d placed, %d review, %.1f s" % (TAG, name, len(dims), len(review or []), time.time() - t0))
