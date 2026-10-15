# -*- coding: utf-8 -*-
"""Hides the section marks in the open plan whose section is not on a sheet,
and shows again any hidden ones whose section now is. Once a section is
placed on a sheet its marks come back on their own (see startup.py)."""
__title__ = "Hide Unplaced\nSections"
__author__ = "MCC ENG"

from pyrevit import revit, DB, forms
import mcc_sections as S
from mcc_place import transaction_with_log

doc = revit.doc
view = doc.ActiveView

if not isinstance(view, DB.ViewPlan):
    forms.alert("Open a plan view first.", exitscript=True)

t, log = transaction_with_log(doc, "MCC: Hide unplaced sections")
try:
    S.sync_plan(doc, view)
    t.Commit()
except Exception as ex:
    t.RollBack()
    forms.alert("Nothing changed - hiding the section marks failed:\n{}".format(ex))
