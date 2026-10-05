# -*- coding: utf-8 -*-
"""Places MCC 3-Box tags on every untagged floor, beam, column and wall
in the active soffit plan, and fills Bottom Reference Elevation on floors
and beams from the concrete support found below each one."""
__title__ = "Tag\nSoffit"
__author__ = "MCC ENG"

from mcc_compat import eid_int
from pyrevit import revit, DB, forms, script
import mcc_elev as E

doc, uidoc = revit.doc, revit.uidoc
view = doc.ActiveView
output = script.get_output()

if not isinstance(view, DB.ViewPlan) or view.GenLevel is None:
    forms.alert("Open the soffit plan view first.", exitscript=True)

# ---------- preflight ----------
symbols, problems = {}, []
for key in E.TAGS:
    if E.TAGS[key] is None:
        continue
    s = E.get_tag_symbol(doc, key)
    if s is None:
        problems.append("{} tag '{}' / '{}' not found".format(
            key, E.TAGS[key][0], E.TAGS[key][1]))
    symbols[key] = s
if problems:
    forms.alert("Fix TAGS in lib/mcc_elev.py:\n\n" + "\n".join(problems),
                exitscript=True)

picked = forms.SelectFromList.show(
    sorted(symbols), multiselect=True, title="Tag which categories?",
    default=sorted(symbols))
if not picked:
    script.exit()

# use current selection if any, else everything visible in the view
sel_ids = set(eid_int(i) for i in uidoc.Selection.GetElementIds())
level = view.GenLevel
already = E.tagged_ids(doc, view)
rows, counts = [], {"tagged": 0, "skipped (tagged)": 0, "support set": 0,
                    "support unchanged": 0, "no support": 0,
                    "param missing": 0, "in group (not written)": 0, "no location": 0}

with revit.Transaction("MCC: Tag soffit plan"):
    ray_view = E.get_ray_view(doc)
    for key in picked:
        sym = symbols[key]
        if not sym.IsActive:
            sym.Activate()
        for e in E.elements_in_view(doc, view, key):
            if sel_ids and eid_int(e.Id) not in sel_ids:
                continue
            note = ""
            if key in E.SUPPORT_CATS:
                xy = E.support_point(doc, view, e)
                if xy:
                    r = E.measure(doc, ray_view, xy[0], xy[1], level, xy[2])
                    st, old, new = E.write_support(e, r)
                    if st == "ok":
                        counts["support set"] += 1
                        note = "support {}".format(E.fmt_ft_in(new))
                    elif st == "unchanged":
                        counts["support unchanged"] += 1
                    elif st == "missing":
                        counts["param missing"] += 1
                    elif st == "grouped":
                        counts["in group (not written)"] += 1
                        if new is not None:
                            note = "IN GROUP - set support {} by hand".format(
                                E.fmt_ft_in(new))
                    else:
                        counts["no support"] += 1
                        note = r.note
            if eid_int(e.Id) in already:
                counts["skipped (tagged)"] += 1
                continue
            pt = E.tag_point(doc, view, e)
            if pt is None:
                counts["no location"] += 1
                continue
            try:
                E.place_tag(doc, view, sym, e, pt)
                counts["tagged"] += 1
                if note:
                    rows.append([key, output.linkify(e.Id), note])
            except Exception as ex:
                rows.append([key, output.linkify(e.Id),
                             "tag failed: {}".format(ex)])

output.print_md("## Tag Soffit: {}".format(view.Name))
output.print_table([[k, v] for k, v in counts.items() if v],
                   columns=["Result", "Count"])
if rows:
    output.print_table(rows, columns=["Cat", "Element", "Note"])
if counts["in group (not written)"]:
    output.print_md("**Some floors/beams are in model groups** - their "
                    "support elevation wasn't written (Revit blocks edits "
                    "outside group edit mode). Values listed above.")
if counts["param missing"]:
    output.print_md("**'{}' not found on some elements** - check the "
                    "shared parameter is loaded.".format(E.BOTTOM_REF_PARAM))
output.print_md("Tags land at each element's center - drag to tidy. "
                "Level head check: **{}** = **{}**".format(
                    level.Name, E.fmt_ft_in(level.Elevation)))
