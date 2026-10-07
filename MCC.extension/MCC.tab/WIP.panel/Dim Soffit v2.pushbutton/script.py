# -*- coding: utf-8 -*-
"""Dim Soffit v2 - features -> string plan -> layout -> create.
Design: claude/dim-soffit-v2-design.md. Dimensions only what is inside the
view's crop. Reruns offer to replace what this button made last time."""
__title__ = "Dim\nSoffit v2"
__author__ = "MCC ENG"

from mcc_compat import eid_int, make_eid
from pyrevit import revit, DB, forms, script
import mcc_model as M
import mcc_coverage as CV
import mcc_strings as S
import mcc_layout as LY
import mcc_place as PL

# ---------------- CONFIG ----------------
DIM_TYPE_NAME = '5/64" Arial Narrow (Transparent)'
SHOW_REPORT = True      # the run report window after every run. False for coworkers (MCC Testing tab): no
                        # end-of-run report, only an alert when something went wrong, offering the details

doc, uidoc = revit.doc, revit.uidoc
view = doc.ActiveView
out = script.get_output()

if not isinstance(view, DB.ViewPlan) or view.GenLevel is None:
    forms.alert("Open the soffit plan view first.", exitscript=True)

dim_type = None
for t in DB.FilteredElementCollector(doc).OfClass(DB.DimensionType):
    p = t.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    if p and p.AsString() == DIM_TYPE_NAME:
        dim_type = t
        break

old = PL.previous_ids(doc, view)
if old and not forms.alert("Replace the {} dimensions Dim Soffit made in this view last time?"
                           .format(len(old)), yes=True, no=True):
    old = []

with forms.ProgressBar(title="Reading the model ...") as pb:
    model = M.PlanModel(doc, view)
crop = CV.crop_poly(view)
fs, plan = S.plan_view(model, crop)
with forms.ProgressBar(title="Laying out {} strings ...".format(len(plan.strings))) as pb:
    lay = LY.Layout(model, plan.strings, view, dim_type, CV.annotation_crop_poly(view))
    placed, review = lay.run()

Z = view.GenLevel.ProjectElevation
t, wlog = PL.transaction_with_log(doc, "MCC: Dim Soffit v2")
made, failed = [], []
try:
    for i in old:
        try:
            doc.Delete(i)
        except Exception:
            pass
    made, failed = lay.create(doc, dim_type, Z)
    made_ids = [d.Id for d in made]
    # dims allowed up to CROP_OUT past the annotation crop (Adolfo 2026-10-06:
    # the beams running off the bottom of L3N): widen the annotation crop so
    # Revit shows them. Plan views only, un-rotated (right = +X, up = +Y)
    over = lay.crop_overshoot()
    widened = dict((k, v) for k, v in over.items() if v > 0)
    if widened:
        try:
            sm = view.GetCropRegionShapeManager()
            rd, ud = view.RightDirection, view.UpDirection
            if abs(rd.X - 1) < 1e-6 and abs(ud.Y - 1) < 1e-6:
                if over["left"]: sm.LeftAnnotationCropOffset = sm.LeftAnnotationCropOffset + over["left"]
                if over["right"]: sm.RightAnnotationCropOffset = sm.RightAnnotationCropOffset + over["right"]
                if over["bottom"]: sm.BottomAnnotationCropOffset = sm.BottomAnnotationCropOffset + over["bottom"]
                if over["top"]: sm.TopAnnotationCropOffset = sm.TopAnnotationCropOffset + over["top"]
            else:
                widened = {}
        except Exception:
            widened = {}
    t.Commit()
except Exception:
    if t.HasStarted() and not t.HasEnded():
        t.RollBack()
    raise
kept = [doc.GetElement(i) for i in made_ids if doc.GetElement(i) is not None]
PL.remember(view, kept)

n_over, n_text = LY.actual_overlaps(doc, view, kept, lay.tsize)


# ---------------- report ----------------
def report():
    out.print_md("## Dim Soffit v2: {}".format(view.Name))
    out.print_md("Features in crop: {}".format(", ".join("{} {}".format(k, v) for k, v in sorted(fs.summary().items()))))
    out.print_md("Strings planned: **{}** ({} locate, {} check) - placed **{}**, needs review **{}**, created **{}** "
                 "(Revit removed {} at commit, {} failed)".format(
                     len(plan.strings), sum(1 for s in plan.strings if s.role == "locate"),
                     sum(1 for s in plan.strings if s.role == "check"), len(placed), len(review), len(kept),
                     len(made) - len(kept), len(failed)))
    out.print_md("Text boxes overlapping after creation: **{}** of {}".format(n_over, n_text))
    out.print_md("Stacks reordered shortest-nearest: {} | dims joined end to end: {} | intermediate beam dims with no room (left out): {} | placed on a wider search: {}".format(
        getattr(lay, "notes_order", 0), getattr(lay, "notes_join", 0), getattr(lay, "notes_optional", 0), getattr(lay, "notes_harder", 0)))
    if widened:
        out.print_md("Annotation crop widened to show dims past it: " + ", ".join("{} {:.1f} ft".format(k, v) for k, v in sorted(widened.items())))
    out.print_md("Model: {} lines from the view's cut plane skipped, {} holes filled by other floors ignored, {} curb/CMU walls ignored, {} walls standing on the slab ignored".format(
        getattr(model, "cut_edges", 0), getattr(model, "filled_holes", 0), len(getattr(model, "soft_walls", [])),
        len(getattr(model, "upper_walls", []))))
    if getattr(plan, "enlarged", None):
        out.print_md("### For an enlarged plan ({}) - small openings/notches too crowded at this scale".format(len(plan.enlarged)))
        out.print_md(", ".join(plan.enlarged))
    if plan.notes:
        out.print_table(sorted(plan.notes.items()), columns=["plan notes", "count"])
    if review:
        out.print_md("### Needs review ({}) - not placed".format(len(review)))
        rows = []
        for s, why in review:
            f = s.feature
            m = f.mid() if f else (0, 0)
            link = out.linkify(make_eid(list(f.owners)[0])) if f and f.owners else ""
            rows.append([f.label() if f else "?", plan.describe(s), why, "({:.1f}, {:.1f})".format(m[0], m[1]), link])
        out.print_table(rows, columns=["feature", "string", "blocked by", "at", "element"])
    if wlog.messages:
        out.print_md("Revit warnings: " + " | ".join("{} x{}".format(m, wlog.messages.count(m)) for m in sorted(set(wlog.messages)))[:800])


problems = []
if review:
    problems.append("{} dimension strings could not be placed".format(len(review)))
if failed or len(made) - len(kept):
    problems.append("{} dimensions failed or were removed by Revit".format(len(failed) + len(made) - len(kept)))
if n_over:
    problems.append("{} dimension texts overlap".format(n_over))
if SHOW_REPORT:
    report()
elif problems and forms.alert("Dim Soffit v2 finished, with problems:\n- " + "\n- ".join(problems)
                              + "\n\nShow the details?", yes=True, no=True):
    report()
