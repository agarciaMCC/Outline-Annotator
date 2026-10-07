# -*- coding: utf-8 -*-
"""Dimension a soffit plan the way the Kalae sheets are hand-dimensioned:
one short two-reference dimension per fact, placed right beside the object.

Passes (tick the ones to run):
  Slab edges  - each perimeter edge -> its nearest grid; jogs edge -> edge
  Openings    - size across the opening (+ every step) and near edge ->
                nearest grid, or -> wall face when a wall is right there
  Beams       - width across the beam + near side -> grid (or side|grid|side
                when centred); free ends -> grid / column face
  Walls       - face -> grid (or face|grid|face when centred)
  CJ lines    - "Large Scale" detail lines -> nearest grid

Recognize (mcc_model) -> Decide (mcc_rules) -> Place (mcc_place).
Reruns offer to replace the dimensions this button made in the view."""
__title__ = "Dim\nSoffit"
__author__ = "MCC ENG"

from pyrevit import revit, DB, forms, script
import mcc_model as M
import mcc_rules as R
import mcc_place as PL

doc, uidoc = revit.doc, revit.uidoc
view = doc.ActiveView
out = script.get_output()

# =====================================================================
# CONFIG
# =====================================================================
DIM_TYPE_NAME = '5/64" Arial Narrow (Transparent)'   # audit: the workhorse
PLACE = {
    "STEP": 1.0,            # ft; station search step
    "GRID_CLEAR": 1.5,      # ft; keep dim text off a grid running along it
    "STATION_GAP": 1.75,    # ft; parallel strings closer than this must not
                            # overlap in extent (same line = fine)
    "BEAMS_SOFT": True,     # a dim line over a beam is allowed, at a cost
    "SOFT_PENALTY": 3.0,    # ft-equivalent cost of crossing a beam
    "OUTSIDE_W": 2.0,       # cost per ft the station sits past its home span
    "OUTWARD_W": 4.0,       # cost for going the non-preferred way
    "MIN_VALUE": 1.0 / 96,
    "PULL_TEXT": True,
    "TEXT_PULL": 1.5,       # text heights to pull short text outward
    "TEXT_FIT_MARGIN": 0.5,
}
RULES = {}                  # overrides for mcc_rules.DEFAULTS, e.g. {"JOG_MAX": 4}
PASSES = [("Slab edges", "slab_edges"), ("Openings", "openings"),
          ("Beams", "beams"), ("Walls", "walls"), ("CJ lines", "cjs")]
REMEMBER = "Remember this selection as my default"
# =====================================================================

if not isinstance(view, DB.ViewPlan) or view.GenLevel is None:
    forms.alert("Open the soffit plan view first.", exitscript=True)

cfg = script.get_config()
# walls are located on their own sheets (4.x / 5.x): off by default
saved = getattr(cfg, "passes", None) or [p[0] for p in PASSES if p[0] != "Walls"]
items = [forms.TemplateListItem(name, checked=(name in saved))
         for name, attr in PASSES] + [forms.TemplateListItem(REMEMBER, checked=False)]
picked = forms.SelectFromList.show(items, multiselect=True, checked_only=True,
                                   title="Dim Soffit - what to dimension",
                                   button_name="Dimension")
if not picked:
    script.exit()
picked = [p if isinstance(p, str) else str(p) for p in picked]
if REMEMBER in picked:
    cfg.passes = [p for p in picked if p != REMEMBER]
    script.save_config()
    picked.remove(REMEMBER)
run = [attr for name, attr in PASSES if name in picked]

# dimension type
dim_type = None
for t in DB.FilteredElementCollector(doc).OfClass(DB.DimensionType):
    p = t.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    if p and p.AsString() == DIM_TYPE_NAME:
        dim_type = t
        break

# rerun cleanup
old = PL.previous_ids(doc, view)
if old and not forms.alert(
        "Replace the {} dimensions Dim Soffit made in this view last time?"
        .format(len(old)), yes=True, no=True):
    old = []

# selection = only these floors (optional)
sel = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()]
floors = [e for e in sel if isinstance(e, DB.Floor)] or None

with forms.ProgressBar(title="Reading the model ...") as pb:
    model = M.PlanModel(doc, view, floors=floors)
rules = R.Rules(model, RULES)
intents = []
for attr in run:
    intents.extend(getattr(rules, attr)())
intents = PL.dedupe(intents, notes=rules.notes, merge_tol=1.0 / 24)   # v1 keeps its 1/2" witness merge (v2 uses 0.4")
if not intents:
    forms.alert("Nothing to dimension in this view.", exitscript=True)

Z = view.GenLevel.ProjectElevation
placer = PL.Placer(model, PLACE)
made = []
t, wlog = PL.transaction_with_log(doc, "MCC: Dim Soffit")
try:
    for i in old:
        try:
            doc.Delete(i)
        except Exception:
            pass
    with forms.ProgressBar(title="Placing dimensions ... {value} of {max_value}",
                           cancellable=True) as pb:
        for k, it in enumerate(intents):
            if pb.cancelled:
                break
            pb.update_progress(k + 1, len(intents))
            d = placer.place(it, dim_type, Z)
            if d is not None:
                made.append((d.Id, it))
    t.Commit()
except Exception:
    if t.HasStarted() and not t.HasEnded():
        t.RollBack()
    raise
# Revit may delete dims at commit (lost references) - keep the survivors
kept = [(i, it) for i, it in made if doc.GetElement(i) is not None]
dropped = {}
for i, it in made:
    if doc.GetElement(i) is None:
        k = getattr(it, "label", None) or type(it).__name__
        dropped[k] = dropped.get(k, 0) + 1
made = [doc.GetElement(i) for i, it in kept]
PL.remember(view, made)

# ---------------- report ----------------
out.print_md("## Dim Soffit: {}".format(view.Name))
out.print_md("Model: {} slabs, {} beams, {} walls, {} columns, {} CJ lines, "
             "{} grid directions. Dim type: **{}**".format(
                 len(model.slabs), len(model.beams), len(model.walls),
                 len(model.columns), len(model.cjs), len(model.families),
                 DIM_TYPE_NAME if dim_type else "(view default)"))
out.print_table([[k, v] for k, v in sorted(placer.count.items())] +
                [["failed to create", placer.failed],
                 ["text pulled out", placer.pulled]],
                columns=["Dimensions placed", "count"])
rows = [[k, v] for k, v in sorted(rules.notes.items())] + \
       [[k, v] for k, v in sorted(placer.skipped.items())]
if rows:
    out.print_table(rows, columns=["Skipped / notes", "count"])
if dropped or wlog.messages:
    out.print_md("**Revit removed {} dims at commit** (by kind: {}). Warnings: {}".format(
        sum(dropped.values()), ", ".join("{} {}".format(k, v) for k, v in sorted(dropped.items())) or "-",
        " | ".join("{} x{}".format(m, wlog.messages.count(m)) for m in sorted(set(wlog.messages)))[:600]))
if placer.errors:
    out.print_md("**Errors (first 6):** " + " | ".join(
        sorted(set(placer.errors))[:6]))
