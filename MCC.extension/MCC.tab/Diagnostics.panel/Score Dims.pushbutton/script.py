# -*- coding: utf-8 -*-
"""Scores an auto-dimensioned view against a hand-dimensioned one.

Pick the REFERENCE view (the finished sheet view) and the TEST view (a
duplicate of it that Dim Soffit ran on - same model elements, so element
ids line up). Every dimension becomes a signature: the set of
(reference kind, element id) it touches. Matching is GEOMETRIC (lib/mcc_score.py): a dim is its direction
plus the positions of its witness lines, each tagged with what it touches.
EXACT = parallel and every witness line coincides (1/2"). OBJECT = the
object's own witness lines coincide but it is anchored differently (other
grid, other face). Face vs edge references and copied elements don't matter.

Reports recall (hand dims the tool reproduced) and precision (tool dims a
detailer also drew) per object category, then lists what was missed and
what was extra with values, so each can be looked at. Read-only."""
__title__ = "Score\nDims"
__author__ = "MCC ENG"

from mcc_compat import eid_int, make_eid
from collections import OrderedDict
from pyrevit import revit, DB, forms, script
from mcc_dim import is_dim
import mcc_score as SC

doc = revit.doc
out = script.get_output()

plans = sorted((v for v in DB.FilteredElementCollector(doc).OfClass(DB.View)
                if isinstance(v, DB.ViewPlan) and not v.IsTemplate),
               key=lambda v: v.Name)
names = OrderedDict((v.Name, v) for v in plans)
ref_name = forms.SelectFromList.show(list(names.keys()), title="REFERENCE view "
                                     "(hand-dimensioned)", button_name="Next")
if not ref_name:
    script.exit()
test_name = forms.SelectFromList.show(
    [k for k in names.keys() if k != ref_name],
    title="TEST view (auto-dimensioned copy)", button_name="Score")
if not test_name:
    script.exit()
ref_view, test_view = names[ref_name], names[test_name]



ref_sigs = [s for s in SC.view_signatures(doc, ref_view, is_dim) if s["cat"] != "grid"]
test_sigs = [s for s in SC.view_signatures(doc, test_view, is_dim) if s["cat"] != "grid"]
rows, missed, extra = SC.score(ref_sigs, test_sigs)

out.print_md("## Score: {} vs hand-dimensioned {}".format(test_name, ref_name))
out.print_table(rows, columns=["category", "hand dims", "tool dims",
                               "recall exact", "recall exact+object",
                               "precision exact", "precision exact+object"])
out.print_md("**Recall** = share of the detailer's dims the tool reproduced. "
             "**Precision** = share of the tool's dims a detailer also drew. "
             "Exact = same witness lines; object = same object faces, "
             "different anchor. Grid-only strings excluded.")
if missed:
    out.print_md("### Missed by the tool ({}) - hand dims with no counterpart"
                 .format(len(missed)))
    out.print_table([[out.linkify(make_eid(s["id"])), s["cat"], s["kinds"],
                      s["vals"]] for s in missed[:150]],
                    columns=["hand dim", "cat", "references", "values"])
if extra:
    out.print_md("### Extra from the tool ({}) - no hand counterpart"
                 .format(len(extra)))
    out.print_table([[out.linkify(make_eid(s["id"])), s["cat"], s["kinds"],
                      s["vals"]] for s in extra[:150]],
                    columns=["tool dim", "cat", "references", "values"])
