# -*- coding: utf-8 -*-
"""Read-only: snapshot every dimension in a test view (position, references,
segments, text positions), tagged with what Dim Soffit v2 meant by it, so a
later snapshot after Adolfo's hand edits can be compared dimension by
dimension. Globals in: VIEW_NAME, OUT (json path), TAG_LAYOUT (bool)."""
import sys, io, json
lib = r"C:\Users\agarcia\Desktop\Claude Projects\Outline Annotator\MCC.extension\lib"
if lib not in sys.path:
    sys.path.insert(0, lib)
for m in [m for m in list(sys.modules) if m.startswith("mcc_")]:
    del sys.modules[m]
from mcc_compat import eid_int

tv = next(v for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan) if v.Name == VIEW_NAME)


def rep(r):
    try:
        return r.ConvertToStableRepresentation(doc)
    except Exception:
        return "eid:%s" % eid_int(r.ElementId)


def xyz(p):
    return [round(p.X, 4), round(p.Y, 4)]


dims = []
for d in DB.FilteredElementCollector(doc, tv.Id).OfClass(DB.Dimension):
    if d.OwnerViewId != tv.Id:
        continue
    try:
        ln = d.Curve
        o, u = ln.Origin, ln.Direction
    except Exception:
        continue
    segs = list(d.Segments) if d.NumberOfSegments > 1 else [d]
    sd = []
    for sg in segs:
        try:
            sd.append({"value": round(sg.Value or 0, 5), "origin": xyz(sg.Origin), "text": xyz(sg.TextPosition),
                       "string": sg.ValueString, "suffix": (sg.Suffix or "")})     # suffix: "R.O." retention is reviewable
        except Exception:
            sd.append({"value": None})
    refs = [rep(r) for r in d.References]
    dims.append({
        "id": eid_int(d.Id), "type": doc.GetElement(d.GetTypeId()).get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString(),
        "origin": xyz(o), "dir": [round(u.X, 5), round(u.Y, 5)], "refs": refs,
        "ref_elems": [eid_int(r.ElementId) for r in d.References],
        "segments": sd, "leader": bool(getattr(d, "HasLeader", False)),
    })

meta = {}
if TAG_LAYOUT:
    # what the tool meant by each dim: rerun the plan + layout (nothing created)
    import mcc_model as M, mcc_coverage as CV, mcc_strings as S, mcc_layout as LY
    model = M.PlanModel(doc, tv)
    fs, pl = S.plan_view(model, CV.crop_poly(tv))
    dt = next(t for t in DB.FilteredElementCollector(doc).OfClass(DB.DimensionType)
              if t.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == '5/64" Arial Narrow (Transparent)')
    lay = LY.Layout(model, pl.strings, tv, dt, CV.annotation_crop_poly(tv))
    lay.run()
    # match on the referenced elements + the measured values (Revit hands back
    # the same references with different stable representations)
    def key_of(elems, values):
        return (tuple(sorted(elems)), tuple(sorted(round(v * 96) for v in values if v)))
    by_refs = {}
    for p in lay.placed:
        s = p.s
        key = key_of([eid_int(r[1].ElementId) for r in s.refs], s.values())
        by_refs.setdefault(key, []).append({
            "label": s.label, "role": s.role, "kind": s.feature.kind if s.feature else None,
            "feature": s.feature.label() if s.feature else None, "describe": pl.describe(s),
            "side": p.side, "cand": str(p.cand[1]),
        })
    hit = 0
    for d in dims:
        k = key_of(d["ref_elems"], [sg["value"] for sg in d["segments"]])
        if k in by_refs and by_refs[k]:
            d["tool"] = by_refs[k].pop(0); hit += 1
    meta["matched_to_layout"] = hit
meta.update({"view": VIEW_NAME, "scale": tv.Scale, "count": len(dims)})
io.open(OUT, "w", encoding="utf-8").write(unicode(json.dumps({"meta": meta, "dims": dims}, indent=1)))
print(meta)
