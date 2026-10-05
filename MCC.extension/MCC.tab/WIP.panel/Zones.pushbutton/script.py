# -*- coding: utf-8 -*-
"""Zones: draw a scope box for a sheet area, name it for its level and
zone (L3 NORTH), see what it cuts through on every level you want it on,
then copy it to those levels.

Revit's API can't create or resize a scope box, so drawing is Revit's own
Scope Box tool - this button launches it, then does everything else.

Run 1 (nothing selected): opens the Scope Box tool. Draw the zone.
Run 2 (scope box selected): name -> levels -> cut-through report -> copy."""
__title__ = "Zones"
__author__ = "MCC ENG"

from mcc_compat import eid_int
from System.Collections.Generic import List
from pyrevit import revit, DB, UI, forms, script
import mcc_sheet as ms

doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()

# =====================================================================
LEVEL_PREFIX = "LEVEL"
NAME_FMT = "L{tok} {zone}"            # scope box name, e.g. L3 NORTH
HOST_LEVEL_OFFSET = 0                 # MCC soffit plans are hosted on the
                                      # level whose slab they show
CUT_CATEGORIES = [DB.BuiltInCategory.OST_Floors,
                  DB.BuiltInCategory.OST_StructuralFraming,
                  DB.BuiltInCategory.OST_StructuralColumns,
                  DB.BuiltInCategory.OST_Columns,
                  DB.BuiltInCategory.OST_Walls]
EDGE_TOL = 0.25                        # ft: touching the edge isn't "cut"
# =====================================================================

SCOPE_BOX_CMD = "ID_VOLUME_OF_INTEREST"   # Revit's Scope Box ribbon button


def pick(items, title, **kw):
    res = forms.SelectFromList.show(items, title=title, **kw)
    if res is None:
        script.exit()
    return res


levels = sorted(DB.FilteredElementCollector(doc).OfClass(DB.Level),
                key=lambda l: l.Elevation)
tok_of = dict((eid_int(l.Id), ms.level_token(l.Name, LEVEL_PREFIX))
              for l in levels)
by_tok = dict((tok_of[eid_int(l.Id)], l) for l in levels)
all_boxes = ms.scope_boxes(doc)
existing = set(b.Name for b in all_boxes)


def level_of(box):
    for r in ms.level_refs(box.Name):
        if r in by_tok:
            return by_tok[r]
    _, _, z0, _ = ms.box_center(box)
    below = [l for l in levels if l.Elevation <= z0 + 0.5]
    return below[-1] if below else levels[0]


# ------------------------------------------------ run 1: draw a box
sel = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()]
src = [e for e in sel if e.Category and eid_int(e.Category.Id) ==
       int(DB.BuiltInCategory.OST_VolumeOfInterest)]
if not src:
    view = doc.ActiveView
    if view.ViewType not in ms.PLAN_VIEW_TYPES:
        forms.alert("Open the soffit plan of the level you want to zone, "
                    "then run Zones.", exitscript=True)
    cmd = None
    try:
        cmd = UI.RevitCommandId.LookupCommandId(SCOPE_BOX_CMD)
    except Exception:
        pass
    if cmd is None or not revit.uidoc.Application.CanPostCommand(cmd):
        forms.alert("Draw a scope box with View > Scope Box, select it, "
                    "and run Zones again.", exitscript=True)
    forms.alert("Draw the zone as a scope box (two corners).\n\n"
                "Then select it and run Zones again to name it, check "
                "what it cuts through, and copy it to other levels.",
                title="Zones")
    revit.uidoc.Application.PostCommand(cmd)
    script.exit()

# ------------------------------------------------ run 2: name it
box = src[0]
if len(src) > 1:
    forms.alert("Select one scope box at a time.", exitscript=True)
# which slab level is this zone for? Default = the level the current view
# shows (view's level minus the host offset), else the box's own guess.
view = doc.ActiveView
guess_lvl = None
if view.ViewType in ms.PLAN_VIEW_TYPES and view.GenLevel is not None:
    vi = next((i for i, l in enumerate(levels)
               if l.Id == view.GenLevel.Id), None)
    if vi is not None:
        gi = vi - HOST_LEVEL_OFFSET
        guess_lvl = levels[gi] if 0 <= gi < len(levels) else levels[vi]
if guess_lvl is None:
    guess_lvl = level_of(box)
lvl_items = ["{}   (this view)".format(guess_lvl.Name)] + \
    [l.Name for l in levels if l.Id != guess_lvl.Id]
lvl_pick = pick(lvl_items, "Which level's slab is this zone for?")
src_level = guess_lvl if lvl_pick.endswith("(this view)") \
    else next(l for l in levels if l.Name == lvl_pick)
src_tok = tok_of[eid_int(src_level.Id)]
guess = ms.zone_name(box.Name) if ms.level_refs(box.Name) else ""
zone = forms.ask_for_string(
    default=guess, prompt="Zone name (NORTH, SOUTH, EAST WING...). "
    "Box is on {}.".format(src_level.Name), title="Zones")
if zone is None:
    script.exit()
zone = zone.strip().upper()
src_name = NAME_FMT.format(tok=src_tok, zone=zone).strip() if zone \
    else "L{}".format(src_tok)

# ------------------------------------------------ levels
targets = pick([l for l in levels if l.Id != src_level.Id],
               "Copy '{}' to levels (none = just name it)".format(src_name),
               name_attr="Name", multiselect=True)

# ------------------------------------------------ cut-through report
bb = box.get_BoundingBox(None)
x0, y0, x1, y1 = bb.Min.X, bb.Min.Y, bb.Max.X, bb.Max.Y
zlo, zhi = bb.Min.Z, bb.Max.Z
cats = List[DB.BuiltInCategory](CUT_CATEGORIES)
elems = list(DB.FilteredElementCollector(doc)
             .WherePasses(DB.ElementMulticategoryFilter(cats))
             .WhereElementIsNotElementType())


def classify(e, dz):
    """'in', 'cut', or None (outside / not in the box's height)."""
    eb = e.get_BoundingBox(None)
    if eb is None:
        return None
    if eb.Max.Z < zlo + dz or eb.Min.Z > zhi + dz:
        return None
    if eb.Max.X < x0 or eb.Min.X > x1 or eb.Max.Y < y0 or eb.Min.Y > y1:
        return None
    inside = (eb.Min.X >= x0 - EDGE_TOL and eb.Max.X <= x1 + EDGE_TOL and
              eb.Min.Y >= y0 - EDGE_TOL and eb.Max.Y <= y1 + EDGE_TOL)
    return "in" if inside else "cut"


def cat_name(e):
    return e.Category.Name if e.Category else "?"


jobs = []      # (level, new_name, dz, status)
for t in [src_level] + list(targets):
    dz = t.Elevation - src_level.Elevation
    new = src_name if t.Id == src_level.Id else \
        NAME_FMT.format(tok=tok_of[eid_int(t.Id)], zone=zone).strip()
    status = ""
    if t.Id != src_level.Id and new in existing:
        status = "exists"
    jobs.append((t, new, dz, status))

output.print_md("## Zone '{}' - what the box cuts through".format(zone or
                                                                    src_name))
output.print_md("Box height {:.1f} ft ({:.1f} to {:.1f}); slab of each "
                "level must fall inside it.".format(zhi - zlo, zlo, zhi))
summary = []
for t, new, dz, status in jobs:
    counts, cut = {}, []
    for e in elems:
        c = classify(e, dz)
        if c is None:
            continue
        counts[c] = counts.get(c, 0) + 1
        if c == "cut":
            cut.append(e)
    # does the level's slab sit inside the shifted box height?
    slab_ok = zlo + dz - 0.5 <= t.Elevation <= zhi + dz + 0.5
    summary.append([t.Name, new, counts.get("in", 0), len(cut),
                    "yes" if slab_ok else "NO - stretch the box",
                    status or ("source" if t.Id == src_level.Id else "copy")])
    if cut:
        output.print_md("**{} - {}**: {} elements cut by the zone edge"
                        .format(t.Name, new, len(cut)))
        by_cat = {}
        for e in cut:
            by_cat.setdefault(cat_name(e), []).append(e)
        for cn in sorted(by_cat):
            links = " ".join(output.linkify(e.Id) for e in by_cat[cn][:40])
            more = " (+{})".format(len(by_cat[cn]) - 40) \
                if len(by_cat[cn]) > 40 else ""
            output.print_md("- {} ({}): {}{}".format(cn, len(by_cat[cn]),
                                                     links, more))
output.print_md("### Summary")
output.print_table(summary, columns=["Level", "Box name", "Inside",
                                     "Cut by edge", "Level in box height",
                                     "Action"])
output.print_md("Click an id to select and zoom to it. Cut elements are "
                "the ones that will show on two sheets - move the box or "
                "plan the split dims there.")

# ------------------------------------------------ confirm + copy
todo = [j for j in jobs if not j[3] and j[0].Id != src_level.Id]
msg = "Rename the box to '{}'".format(src_name) if box.Name != src_name \
    else "Keep the name '{}'".format(src_name)
if todo:
    msg += " and copy it to {} level(s):\n  {}".format(
        len(todo), "\n  ".join(j[1] for j in todo))
skipped = [j for j in jobs if j[3]]
if skipped:
    msg += "\n\nAlready exist (skipped):\n  " + "\n  ".join(
        j[1] for j in skipped)
if not forms.alert(msg + "\n\nGo ahead?", title="Zones", yes=True, no=True):
    script.exit()

rows = []
with revit.Transaction("MCC: Zones"):
    if box.Name != src_name:
        try:
            box.Name = src_name
            rows.append([src_level.Name, src_name, "renamed"])
        except Exception as ex:
            rows.append([src_level.Name, src_name,
                         "rename failed: {}".format(ex)])
    for t, new, dz, _ in todo:
        ids = List[DB.ElementId]([box.Id])
        new_ids = DB.ElementTransformUtils.CopyElements(
            doc, ids, DB.XYZ(0, 0, dz))
        nb = doc.GetElement(list(new_ids)[0])
        try:
            nb.Name = new
            rows.append([t.Name, new, "created"])
        except Exception as ex:
            rows.append([t.Name, new, "copied, rename failed: {}".format(ex)])
        existing.add(new)

output.print_md("### Done")
output.print_table(rows, columns=["Level", "Scope box", "Result"])
output.print_md("Next: draw the next zone (run Zones with nothing "
                "selected), or Build Soffit Sheets and tick these boxes.")
