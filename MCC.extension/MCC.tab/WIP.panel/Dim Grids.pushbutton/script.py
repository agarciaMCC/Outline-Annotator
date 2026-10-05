# -*- coding: utf-8 -*-
"""Grid-to-grid dimension strings plus an overall, on two sides of the
plan (one per grid direction), placed outside the slab shown in the view.
Reruns replace strings of AUTO_DIM_TYPE if set."""
__title__ = "Dim\nGrids"
__author__ = "MCC ENG"

from pyrevit import revit, DB, forms, script
import mcc_view as V

doc = revit.doc
view = doc.ActiveView
output = script.get_output()

# =====================================================================
# CONFIG
# =====================================================================
AUTO_DIM_TYPE = None        # e.g. "MCC - AUTO GRID DIM"; reruns replace
GRID_TIER_OFFSET = 10.0     # ft outside the slab for the grid string
                            # (leave room for the edge dims inside it)
OVERALL_GAP = 3.0           # ft further out for the overall string
SIDES = "max"               # "max" = top/right, "min" = bottom/left,
                            # "both" = all four sides
MIN_SPAN = 0.5              # ft; skip grids closer than this (duplicates)
# =====================================================================

if not isinstance(view, DB.ViewPlan) or view.GenLevel is None:
    forms.alert("Open the soffit plan view first.", exitscript=True)

floors, slab_level = V.soffit_floors(doc, view)
ext = V.plan_extent(floors, view) if floors else None
if ext is None:
    cb = view.CropBox
    ext = (cb.Min.X, cb.Min.Y, cb.Max.X, cb.Max.Y)
grids = V.straight_grids(doc, view)
if not grids:
    forms.alert("No straight grids in this view.", exitscript=True)
fams = V.grid_families(grids)
Z = view.GenLevel.ProjectElevation

dim_type = None
if AUTO_DIM_TYPE:
    dim_type = next((t for t in DB.FilteredElementCollector(doc)
                     .OfClass(DB.DimensionType)
                     if V.type_name(t) == AUTO_DIM_TYPE), None)
    if dim_type is None:
        forms.alert("Dimension type '{}' not found.".format(AUTO_DIM_TYPE),
                    exitscript=True)

corners = [(ext[0], ext[1]), (ext[2], ext[1]), (ext[2], ext[3]),
           (ext[0], ext[3])]
jobs = []
for fam in fams:
    g, g0, u, n = grids[fam[0]]
    # offsets of every grid in the family along n, from the first grid
    offs = sorted(((grids[gi][1][0] - g0[0]) * n[0] +
                   (grids[gi][1][1] - g0[1]) * n[1], gi) for gi in fam)
    refs = []
    for o, gi in offs:
        if refs and o - refs[-1][0] < MIN_SPAN:
            continue
        refs.append((o, DB.Reference(grids[gi][0])))
    if len(refs) < 2:
        continue
    sts = [(c[0] - g0[0]) * u[0] + (c[1] - g0[1]) * u[1] for c in corners]
    for side, sign, base in (("max", 1, max(sts)), ("min", -1, min(sts))):
        if SIDES != "both" and SIDES != side:
            continue
        st = base + sign * GRID_TIER_OFFSET
        jobs.append((fam[0], st, refs, "grid to grid"))
        if len(refs) > 2:
            jobs.append((fam[0], st + sign * OVERALL_GAP,
                         [refs[0], refs[-1]], "overall"))

old = []
if dim_type:
    old = [d for d in DB.FilteredElementCollector(doc, view.Id)
           .OfClass(DB.Dimension) if d.GetTypeId() == dim_type.Id]

made, failed = {}, 0
with revit.Transaction("MCC: Dimension grids"):
    for d in old:
        doc.Delete(d.Id)
    for gi, st, refs, label in jobs:
        g, g0, u, n = grids[gi]
        ra = DB.ReferenceArray()
        for o, r in refs:
            ra.Append(r)
        lo, hi = refs[0][0], refs[-1][0]
        px, py = g0[0] + u[0] * st, g0[1] + u[1] * st
        line = DB.Line.CreateBound(DB.XYZ(px + n[0] * lo, py + n[1] * lo, Z),
                                   DB.XYZ(px + n[0] * hi, py + n[1] * hi, Z))
        try:
            if dim_type:
                doc.Create.NewDimension(view, line, ra, dim_type)
            else:
                doc.Create.NewDimension(view, line, ra)
            made[label] = made.get(label, 0) + 1
        except Exception:
            failed += 1

output.print_md("## Grid dimensions: {}".format(view.Name))
output.print_table([[k, v] for k, v in sorted(made.items())] +
                   [["failed", failed]], columns=["Strings", "Count"])
output.print_md("Placed {} ft outside the slab{}. Run **Fit Grids** to trim "
                "grid extents to suit.".format(
                    GRID_TIER_OFFSET,
                    " on level " + slab_level.Name if slab_level else ""))
