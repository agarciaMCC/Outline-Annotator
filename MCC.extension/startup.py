# -*- coding: utf-8 -*-
"""Runs once when Revit loads the MCC extension."""
try:
    import mcc_sections
    mcc_sections.register_updater(__revit__.Application.ActiveAddInId)
except Exception as ex:
    print("MCC: section-mark updater not started: {}".format(ex))
