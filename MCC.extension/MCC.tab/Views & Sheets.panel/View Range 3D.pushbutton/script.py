# -*- coding: utf-8 -*-
"""See and edit a plan's view range in 3D.

Run from a plan (soffit plan). Opens a floating window with:
  - a live 3D preview of MCC VIEW RANGE 3D, section-boxed to the plan's
    crop and view range,
  - each plane (Top / Cut / Bottom / View Depth) drawn in color in the 3D
    (and as lines in sections / elevations),
  - fields to change each plane's level and offset and push them back to
    the plan (or its view template).
The window refreshes by itself when the plan's range, crop, template or
the levels change, and follows you to another plan view. Rerun the
button to rebuild the window."""
__title__ = "View Range\n3D"
__author__ = "MCC ENG"
__persistentengine__ = True     # keeps the window, events and graphics alive

from pyrevit import revit

import mcc_vr3d
try:
    reload(mcc_vr3d)        # pick up edits without reloading pyRevit
except Exception:
    pass

mcc_vr3d.run(revit.doc, revit.uidoc)
