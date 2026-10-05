# -*- coding: utf-8 -*-
"""Re-measures the concrete support below every floor and beam in the
active plan and updates Bottom Reference Elevation where it changed, so
the 3-Box tags show the current shoring height."""
__title__ = "Refresh\nSupport Elev"
__author__ = "MCC ENG"

from pyrevit import revit, DB, forms, script
import mcc_elev as E

doc = revit.doc
view = doc.ActiveView
output = script.get_output()

if not isinstance(view, DB.ViewPlan) or view.GenLevel is None:
    forms.alert("Open the soffit plan view first.", exitscript=True)

level = view.GenLevel
rows, counts = [], {"updated": 0, "unchanged": 0, "no support": 0,
                    "param missing": 0}
heights = set()

with revit.Transaction("MCC: Refresh support elevations"):
    ray_view = E.get_ray_view(doc)
    for key in E.SUPPORT_CATS:
        for e in E.elements_in_view(doc, view, key):
            xy = E.support_point(doc, view, e)
            if xy is None:
                continue
            r = E.measure(doc, ray_view, xy[0], xy[1], level, xy[2])
            st, old, new = E.write_support(e, r)
            if st == "ok":
                counts["updated"] += 1
                rows.append([key, output.linkify(e.Id), E.fmt_ft_in(old),
                             E.fmt_ft_in(new)])
            elif st == "unchanged":
                counts["unchanged"] += 1
            elif st == "missing":
                counts["param missing"] += 1
            elif st == "grouped":
                counts["in group (not written)"] += 1
                rows.append([key, output.linkify(e.Id), E.fmt_ft_in(old),
                             "IN GROUP - needs {}".format(E.fmt_ft_in(new))
                             if new is not None else r.note])
            else:
                counts["no support"] += 1
                rows.append([key, output.linkify(e.Id), "-", r.note])
            if r.bottom is not None and r.support is not None:
                heights.add(E.fmt_ft_in(r.bottom - r.support))

output.print_md("## Refresh support elevations: {}".format(view.Name))
output.print_table([[k, v] for k, v in counts.items() if v],
                   columns=["Result", "Count"])
if rows:
    output.print_table(rows, columns=["Cat", "Element", "Was", "Now"])
if len(heights) > 1:
    output.print_md("**Distinct shore heights on this level:** " +
                    ", ".join(sorted(heights)) +
                    " - check SHORE HT CHANGES callouts.")
