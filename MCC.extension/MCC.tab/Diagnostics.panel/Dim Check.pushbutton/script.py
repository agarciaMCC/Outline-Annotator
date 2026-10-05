# -*- coding: utf-8 -*-
"""Dim Check - QA for a dimensioned soffit plan: which slab edges, opening
edges, beam sides/ends and CJ lines inside the view's crop can NOT be
located off a gridline (or an in-line wall face) from the dimensions in
the view.

Marks each unlocated edge in the view with a detail line along the edge
and a "DIM?" note (view-specific, nothing in the model), so the links in
the report zoom straight to the spot. Rerunning offers to remove the
previous marks; "Clear marks" = run with nothing to mark."""
__title__ = "Dim\nCheck"
__author__ = "MCC ENG"

import json
from collections import Counter
from mcc_compat import eid_int, make_eid
from pyrevit import revit, DB, forms, script
import mcc_model as M
import mcc_coverage as CV
import mcc_place as PL
from mcc_dim import is_dim

doc = revit.doc
view = doc.ActiveView
out = script.get_output()
if not isinstance(view, DB.ViewPlan) or view.GenLevel is None:
    forms.alert("Open the soffit plan view first.", exitscript=True)

# ---------------- previous marks ----------------
def journal_path():
    return script.get_document_data_file("mcc_dimcheck", "json")

def load_marks():
    try:
        with open(journal_path(), "r") as fh:
            return json.load(fh)
    except Exception:
        return {}

def save_marks(data):
    try:
        with open(journal_path(), "w") as fh:
            json.dump(data, fh)
    except Exception:
        pass

marks = load_marks()
key = str(eid_int(view.Id))
old = [make_eid(i) for i in marks.get(key, []) if doc.GetElement(make_eid(i)) is not None]

# ---------------- check ----------------
model = M.PlanModel(doc, view)
T, angled, ongrid, res = CV.coverage(doc, model, [view], is_dim, crop_view=view)
g = res[view.Name]
c = Counter(g)
loc = c["DIRECT"] + c["WALL"]
missing = [(t, x) for t, x in zip(T, g) if x not in ("DIRECT", "WALL")]

# ---------------- marks ----------------
mark_ids = []
do_mark = bool(missing) and forms.alert(
    "Mark the {} unlocated edges in this view with a line and a DIM? note?"
    "\n(View-specific only; rerun Dim Check to refresh or clear them.)".format(len(missing)),
    yes=True, no=True)
z = view.GenLevel.ProjectElevation
# smallest text note type in the model, so the marks stay quiet
tn_type = doc.GetDefaultElementTypeId(DB.ElementTypeGroup.TextNoteType)
try:
    types = list(DB.FilteredElementCollector(doc).OfClass(DB.TextNoteType))
    def _sz(t):
        p = t.get_Parameter(DB.BuiltInParameter.TEXT_SIZE)
        return p.AsDouble() if p else 1.0
    small = [t for t in types if _sz(t) >= 1.0 / 16 / 12]      # >= 1/16"
    if small:
        tn_type = min(small, key=_sz).Id
except Exception:
    pass
ogs = DB.OverrideGraphicSettings()
try:
    ogs.SetProjectionLineColor(DB.Color(255, 0, 0))
    ogs.SetProjectionLineWeight(5)
except Exception:
    pass
t, wlog = PL.transaction_with_log(doc, "MCC: Dim Check marks")
try:
    if old:
        from System.Collections.Generic import List
        doc.Delete(List[DB.ElementId](old))
    if do_mark:
        for tt, x in missing:
            p0 = DB.XYZ(tt.p0[0], tt.p0[1], z)
            p1 = DB.XYZ(tt.p1[0], tt.p1[1], z)
            line_id = None
            try:
                dl = doc.Create.NewDetailCurve(view, DB.Line.CreateBound(p0, p1))
                line_id = dl.Id
                mark_ids.append(eid_int(dl.Id))
                try:
                    view.SetElementOverrides(dl.Id, ogs)
                except Exception:
                    pass
            except Exception:
                pass
            try:
                m = tt.mid()
                off = 0.75
                pos = DB.XYZ(m[0] + tt.n[0] * off, m[1] + tt.n[1] * off, z)
                note = DB.TextNote.Create(doc, view.Id, pos, "DIM?", tn_type)
                mark_ids.append(eid_int(note.Id))
                try:
                    view.SetElementOverrides(note.Id, ogs)
                except Exception:
                    pass
                if line_id is None:
                    line_id = note.Id
            except Exception:
                pass
            tt.mark = line_id
    t.Commit()
except Exception:
    if t.HasStarted() and not t.HasEnded():
        t.RollBack()
    raise
marks[key] = mark_ids
save_marks(marks)

# ---------------- report ----------------
out.print_md("## Dim Check: {}".format(view.Name))
out.print_md("{} edges in the crop: **{} located** off a grid or wall ({}%), {} only by edge-to-edge check dims, "
             "{} chained, **{} not dimensioned**. ({} on a grid, {} angled to every grid family.)".format(
                 len(T), loc, 100 * loc // max(1, len(T)), c["CHECK"], c["CHAINED"], c["NONE"], len(ongrid), len(angled)))
byk = {}
for tt, x in zip(T, g):
    byk.setdefault(sorted(tt.kinds)[0], Counter())[x] += 1
out.print_table([[k, sum(cc.values()), cc["DIRECT"] + cc["WALL"], cc["CHECK"], cc["NONE"]] for k, cc in sorted(byk.items())],
                columns=["edge type", "edges", "located", "check only", "none"])
if missing:
    rows = []
    for tt, x in sorted(missing, key=lambda m: (m[1], sorted(m[0].kinds)[0])):
        m = tt.mid()
        link = out.linkify(getattr(tt, "mark", None) or make_eid(tt.owner)) if (getattr(tt, "mark", None) or tt.owner) else ""
        rows.append([link, x, "/".join(sorted(tt.kinds)), "{:.1f} ft".format(tt.length), "({:.1f}, {:.1f})".format(m[0], m[1])])
    out.print_md("### Not located ({}) - click the link to zoom to the mark".format(len(rows)))
    out.print_table(rows, columns=["zoom", "status", "edge", "length", "at (x, y)"])
if old and not do_mark:
    out.print_md("Removed {} previous marks.".format(len(old)))
