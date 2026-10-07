# MCC Testing - pyRevit extension

Adds an "MCC Testing" tab to Revit with buttons that are still being tested.
Expect rough edges. Every button's changes can be undone with Ctrl+Z.

## Buttons
- **Dim Soffit v2** - open a soffit plan view, click the button. It dimensions the
  slab edges, beams, openings and construction joints inside the view's crop.
  Clicking it again in the same view offers to replace the dimensions it made last time.

## Install
1. Install pyRevit (free): https://github.com/pyrevitlabs/pyRevit/releases
2. Unzip this file somewhere permanent, e.g. C:\Users\<you>\Documents\pyRevit\
   You should end up with ...\pyRevit\MCC-Testing.extension\
3. In Revit: pyRevit tab > Settings > Custom Extension Directories > Add
   and pick the folder that CONTAINS MCC-Testing.extension (e.g. ...\Documents\pyRevit).
4. Save Settings, then click Reload on the pyRevit tab.
5. The MCC Testing tab appears with the Dim Soffit v2 button.

## Feedback
Tell Adolfo which view you ran it in and what looked wrong (a screenshot helps).

Questions: Adolfo Garcia, McClone Construction
