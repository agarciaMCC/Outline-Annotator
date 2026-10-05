# -*- coding: utf-8 -*-
# Test view only: draw each review item's intended dim line in red plus two
# green calibration crosses inside the model crop, export the view to PNG,
# then delete everything drawn. Globals in: VIEW_NAME, JSON, PNG_BASE.
import sys, io, json, os
from System.Collections.Generic import List
lib = r"C:\Users\agarcia\Desktop\Claude Projects\Outline Annotator\MCC.extension\lib"
if lib not in sys.path:
    sys.path.insert(0, lib)
import mcc_place as PL
import mcc_coverage as CV
import mcc_plan as P

data = json.loads(io.open(JSON, encoding="utf-8").read())
tv = next(v for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan) if v.Name == VIEW_NAME)
assert tv.Name.startswith("ZZ CLAUDE TEST")
z = tv.GenLevel.ProjectElevation
red = DB.OverrideGraphicSettings().SetProjectionLineColor(DB.Color(255, 0, 0)).SetProjectionLineWeight(10)
green = DB.OverrideGraphicSettings().SetProjectionLineColor(DB.Color(0, 200, 0)).SetProjectionLineWeight(10)

# calibration points inside the MODEL crop (detail lines are clipped by it),
# one toward the lower left, one toward the upper right
mc = CV.crop_poly(tv)
mxs = [p[0] for p in mc]; mys = [p[1] for p in mc]
def ok(c):
    return all(P.point_in_poly(c[0] + dx, c[1] + dy, mc) for dx in (-2, 2) for dy in (-2, 2))
grid = [(min(mxs) + i * 2.0, min(mys) + j * 2.0)
        for i in range(int((max(mxs) - min(mxs)) / 2)) for j in range(int((max(mys) - min(mys)) / 2))]
inside = [c for c in grid if ok(c)]
cal_a = min(inside, key=lambda c: c[0] + c[1])
cal_b = max(inside, key=lambda c: c[0] + c[1])

def seg(a, b):
    return DB.Line.CreateBound(DB.XYZ(a[0], a[1], z), DB.XYZ(b[0], b[1], z))

made, cal = [], []
t, log = PL.transaction_with_log(doc, "Claude: review markers (temporary)")
try:
    for cx, cy in (cal_a, cal_b):
        for a, b in (((cx - 1.5, cy), (cx + 1.5, cy)), ((cx, cy - 1.5), (cx, cy + 1.5))):
            cal.append(doc.Create.NewDetailCurve(tv, seg(a, b)))
    # item lines are drawn onto each close-up afterwards (one per card), not here
    for d in made:
        tv.SetElementOverrides(d.Id, red)
    for d in cal:
        tv.SetElementOverrides(d.Id, green)
    made += cal
    t.Commit()
except Exception:
    if t.HasStarted() and not t.HasEnded():
        t.RollBack()
    raise
try:
    o = DB.ImageExportOptions()
    o.ExportRange = DB.ExportRange.SetOfViews
    o.SetViewsAndSheets(List[DB.ElementId]([tv.Id]))
    o.FilePath = PNG_BASE
    o.ZoomType = DB.ZoomFitType.FitToPage
    o.PixelSize = 6000
    o.HLRandWFViewsFileType = DB.ImageFileType.PNG
    o.ImageResolution = DB.ImageResolution.DPI_300
    doc.ExportImage(o)
finally:
    t2, log2 = PL.transaction_with_log(doc, "Claude: remove review markers")
    doc.Delete(List[DB.ElementId]([d.Id for d in made]))
    t2.Commit()
data["cal"] = [list(cal_a), list(cal_b)]
io.open(JSON, "w", encoding="utf-8").write(unicode(json.dumps(data, indent=1)))
print("drew and removed", len(made), "lines; calibration at", cal_a, cal_b)
