# MCC Testing - pyRevit extension

Adds an "MCC Testing" tab to Revit with buttons that are still being tested.
Expect rough edges. Every button's changes can be undone with Ctrl+Z.

## Buttons
- **Dim Soffit v2** - open a soffit plan view, click the button. It dimensions the
  slab edges, beams, openings and construction joints inside the view's crop.
  Clicking it again in the same view offers to replace the dimensions it made last time.
  It shows nothing when the run goes well. If some dimensions could not be placed, a short message
  says so and offers the details.
- **Grids from PDF** - pick the structural and/or architectural plan PDF. It reads the grid
  bubbles and called-out grid dimensions, lets you pick where the sheets disagree, then you
  click where one grid intersection goes and it makes the grids.
- **Columns from PDF** - make the grids first. Pick a level plan PDF and the column schedule;
  it places the columns on the grids with sizes from the schedule. Load your concrete column
  families (rectangular, round, bullnose) into the model before running it.

Grids and Columns need the vector PDF exported from Revit/CAD (scanned PDFs can't be read),
and Python 3 on your PC: install it from python.org and tick "Add python.exe to PATH".
The first run offers to install the PDF reader (needs internet, takes a minute).

## Install
1. Install pyRevit (free): https://github.com/pyrevitlabs/pyRevit/releases
2. Unzip this file somewhere permanent, e.g. C:\Users\<you>\Documents\pyRevit\
   You should end up with ...\pyRevit\MCC-Testing.extension\
3. In Revit: pyRevit tab > Settings > Custom Extension Directories > Add
   and pick the folder that CONTAINS MCC-Testing.extension (e.g. ...\Documents\pyRevit).
4. Save Settings, then click Reload on the pyRevit tab.
5. The MCC Testing tab appears with the Dim Soffit v2, Grids from PDF and Columns from PDF buttons.

## Feedback
Tell Adolfo which view you ran it in and what looked wrong (a screenshot helps).

Questions: Adolfo Garcia, McClone Construction
