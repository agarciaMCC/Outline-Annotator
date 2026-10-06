# -*- coding: utf-8 -*-
# Headless: clear the test view's dims, run Dim Soffit v2 on it, export images.
# Writes dimsoffit_v2_L3N_runN.md + L3N_v2_runN.png. Globals in: RUN (int).
import sys, os, time
from System.Collections.Generic import List
t0 = time.time()
for m in [m for m in list(sys.modules) if m.startswith("mcc_")]: del sys.modules[m]
import mcc_place as PL
D = r"C:\Users\agarcia\Desktop\Claude Projects\Outline Annotator\Claude outputs\audit_R26"
EXT = r"C:\Users\agarcia\Desktop\Claude Projects\Outline Annotator\MCC.extension"
VIEW_NAME = globals().get("VIEW_NAME", "ZZ CLAUDE TEST - L3 NORTH (auto-dim)")
TAG = globals().get("TAG", "L3N")
tv = next(v for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan) if v.Name == VIEW_NAME)
# guard (2026-10-06): a stale request re-ran "run 63" while Adolfo was starting an edit round and wiped the
# view. A run number that already has a report is never re-run - pick a new RUN.
if os.path.exists(D + r"\dimsoffit_v2_%s_run%d.md" % (TAG, RUN)):
    raise Exception("run %d of %s already exists - not clearing the view; use a new RUN number" % (RUN, TAG))
ids = [d.Id for d in DB.FilteredElementCollector(doc).OfClass(DB.Dimension) if d.OwnerViewId == tv.Id]
ids += [e.Id for e in DB.FilteredElementCollector(doc, tv.Id).OfClass(DB.TextNote) if e.OwnerViewId == tv.Id and e.Text.strip().startswith("DIM?")]
ids += [e.Id for e in DB.FilteredElementCollector(doc, tv.Id).OfClass(DB.CurveElement) if e.OwnerViewId == tv.Id and isinstance(e, DB.DetailLine)]
if ids:
    t, log = PL.transaction_with_log(doc, "Claude: clear test view dims"); doc.Delete(List[DB.ElementId](ids)); t.Commit()
g = dict(globals())
g.update(SCRIPT=EXT + r"\MCC.tab\WIP.panel\Dim Soffit v2.pushbutton\script.py", VIEW=tv, PICKS=[], YES=False)
import traceback
try:
    execfile(D + r"\run_button.py", g)
    rep = g["BUTTON_REPORT"]
except Exception:
    rep = (g.get("BUTTON_REPORT") or "") + "\n\nTRACEBACK:\n" + traceback.format_exc()
rep += "\n\nvisible dims: %d | seconds: %.1f\n" % (DB.FilteredElementCollector(doc, tv.Id).OfClass(DB.Dimension).GetElementCount(), time.time() - t0)
f = open(D + r"\dimsoffit_v2_%s_run%d.md" % (TAG, RUN), "w"); f.write(rep.encode("utf-8") if isinstance(rep, unicode) else rep); f.close()
o = DB.ImageExportOptions()
o.ExportRange = DB.ExportRange.SetOfViews
o.SetViewsAndSheets(List[DB.ElementId]([tv.Id]))
o.FilePath = os.path.join(D, "%s_v2_run%d" % (TAG, RUN))
o.ZoomType = DB.ZoomFitType.FitToPage
o.PixelSize = 6000
o.HLRandWFViewsFileType = DB.ImageFileType.PNG
o.ImageResolution = DB.ImageResolution.DPI_300
doc.ExportImage(o)
print("done run", RUN)
