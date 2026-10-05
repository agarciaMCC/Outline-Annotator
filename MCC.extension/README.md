# MCC pyRevit Extension - Soffit Plans (v0.4)

## Install
1. Install pyRevit (https://github.com/pyrevitlabs/pyRevit/releases) if not already.
2. Copy the `MCC.extension` folder somewhere stable (e.g. a shared Egnyte/network folder).
3. pyRevit tab > Settings > Custom Extension Directories > add the folder CONTAINING `MCC.extension`.
4. Reload pyRevit. An **MCC** tab appears with a **Soffit Plans** panel (**Inspect Model**,
   **Zones**, **Tag Soffit**, **Refresh Support Elev**, **Dim Slab Edges**,
   **Dim Grids**, **Dim Columns**, **Fit Grids**) and a **Dimensions** panel
   (**Dim Text**) and a **Setup** panel (**Grids from PDF**, **Columns from PDF**).

## Grids from PDF (Setup panel)
Creates named Revit grids from the PDF plan sheets we get from the design
team (vector PDFs exported from Revit/CAD - scanned sheets can't be read).
1. Sheet 1 = the reference sheet (e.g. structural level plan), Sheet 2 =
   optional second sheet (e.g. architectural). Page number for full sets.
   Scale: Auto reads it from the grid dimensions (or pick one).
2. **Read grids.** Bubbles and grid lines are read off the sheet; elbow
   bubbles are followed back to the grid; the **called-out grid
   dimensions set the spacing**. Sheet 2 is lined up on the grids both
   sheets share. **Open check PDF** shows what was found (red; orange
   dashed = excluded).
3. **Sheets disagree** (only shown when needed): where the two sheets call
   out different dimensions for the same gap, pick which one to use -
   nothing is chosen for you. A gap dimensioned on one sheet only uses
   that sheet's dimension. Undimensioned gaps keep the measured value and
   are noted in the list.
4. Untick any grids you don't want (names already in the model are
   skipped), pick the grid intersection (default e.g. 1 / AA) and where it
   goes - a point you click, or the internal origin - plus rotation and
   grid type. **Dimension grids** (on by default) adds one string per grid
   family at BOTH ends, set in 3/8" (paper) from the grid ends so it sits
   just inside the bubbles, in the active plan view. **Create grids** - one undoable transaction; new grids are
   left selected.

Needs **Python 3** on the PC for the PDF step (python.org, tick "Add
python.exe to PATH"). The first run finds it and offers to install the
PDF reader (`pip install --user pymupdf`). Files: `pdfgrids/detect.py`
(PDF engine), `lib/mcc_gridpdf.py` (picks and placement).

## Columns from PDF (Setup panel)
Places structural columns on one level from that level's PDF plan plus the
column schedule PDF (all pages). Make the grids first with Grids from PDF -
the columns are lined up on the grids already in the model (no pick).
- Level = the Revit level to place on (defaults to the active plan's level);
  "schedule level" = the level number in the schedule (read from the name).
- **Read columns**: column outlines from the plan (true shape, incl. rotated
  wings), each mark followed along its leader, size/type from the schedule at
  that level. Listed by mark with the family: T9 = Bullnose, T10/T11 or a
  diameter = Circular, else Rectangular - change any mark's family there.
- **Place columns**: base at the level (0'-0"), top at the level above,
  attached to the slab above; Mark = schedule mark; Width = schedule W along
  the matching drawn side. Bullnose columns follow their outline - flip the
  rounded end by hand if needed. Missing types are created ("18x18 COL",
  "24 DIA COL").
- **Create all types from schedule**: makes every size in the schedule as a
  column type up front.
Families: Structural - Columns - Concrete Rectangular / Circular / Bullnose.

## Zones
Sets up the sheet areas (zones) as scope boxes, one level at a time, and
copies them to the other levels. Revit's API can't create or resize a
scope box, so the drawing is Revit's own Scope Box tool; the button does
the rest.
- Run with nothing selected in a plan view: it opens the Scope Box tool.
  Draw the zone (two corners).
- Select the box and run again: type the zone name (NORTH...), pick the
  levels to copy to. The output window then shows, per level, how many
  floors / beams / columns / walls are inside the box, which ones are
  **cut by the zone edge** (clickable ids - these end up on two sheets),
  and whether the level's slab falls inside the box height. Say yes and
  the box is renamed `L3 NORTH` and copied to each level as `L4 NORTH`,
  `L5 NORTH`... (moved by the level difference). Existing names are
  skipped; heights are copied as-is - stretch in a section if needed.
- Repeat for the next zone, then Build Soffit Sheets and tick the boxes.

## Sheet Builder (Sheets panel)
Clones finished sheets of **any type** - soffit, embed, vertical plans,
partial plans - to other levels. The prototype sheets are the whole spec;
nothing is configured per sheet type.

**Clone sheets to other levels**
1. Select the prototype sheets in the Project Browser (or pick them from
   the list), e.g. 1.3.0 + 1.3.1, or 6.3.0.
2. Pick the target levels. 3. Untick anything in the preview. Build.

For each target level, each prototype sheet gets a copy:
- number and name with the level swapped (6.3.0 -> 6.5.0,
  `LEVEL 3 - NORTH (EMBED PLAN)` -> `LEVEL 5 - ...`), same title block,
  sheet parameters, legends, schedules, text, symbols, lines
- every level-based plan view on it gets a counterpart on the target
  level (a view of the level below stays "the level below"): same view
  type and template, every setting the template doesn't control (scale,
  phase, detail level, underlay...), view range copied relative to the
  level, Title on Sheet with the level swapped
- dependents are recreated under the matching parent on the target
  level. The parent is found by name (level swapped) or as the one view
  there with the same template and type - asks if several - else made
- crop: same scope box if it spans the level, else its level twin
  (`L3 NORTH` -> `L5 NORTH`); sketched crop / crop box copied exactly;
  crop visibility and annotation crop as on the prototype
- grid ends / bubbles / elbows / hidden grids like the prototype view
- placed exactly where the prototype's view sits (matches a model point,
  not the viewport box), same viewport type, rotation, title position
Existing sheet numbers are skipped; views already made (same name, not
on a sheet) are reused. Sections, elevations, drafting views can only be
on one sheet - listed in the report, not copied. One undoable run.

**Split a view into zone sheets** (first level of a new sheet type)
Pick a plan view, pick scope boxes and/or type zone names, title block,
number / name pattern. Makes a dependent per zone (annotation crop on)
and a sheet for each. Then sketch crops, lay the sheets out by hand, and
clone them with the first mode.

Shared code in `lib/mcc_sheet.py`. The old Build Soffit Sheets button is
in `_to_delete`.

## Fit View Titles
Sets each viewport's title line to the title's width plus two characters
(`PAD_CHARS`). Revit can't measure how wide a title draws, so the width
is estimated from the character count (Title on Sheet, else view name),
calibrated once per viewport type.
- Run it and pick: selected viewports, this sheet, or sheets from a list.
- If a viewport type isn't calibrated yet, it asks you right then to
  click 2+ titles of that type on the open sheet that you've already
  fitted by hand (different lengths), calibrates, and carries on - one
  run. Pre-selected hand-fitted titles count too.
- Calibrations live in `title_fit.json` next to the script, so everyone
  using this extension folder shares them. *Recalibrate* (with viewports
  selected) redoes a type. One undoable run.

## View Range 3D
Run from a plan (soffit plan). Opens a small floating control window and
the 3D view `MCC VIEW RANGE 3D` as a tab tiled beside the plan,
section-boxed to the plan's crop (rotated crops follow) and view range.
Code lives in `lib/mcc_vr3d.py` (pyRevit clears a button script's globals
after it runs, which broke the live window). The embedded preview pane is
off (`USE_PREVIEW = False` in that file); it can be turned back on.
- **Planes in color**: Top blue, Cut red, Bottom green, View Depth orange,
  drawn as translucent sheets with the crop outline (polygon crops too).
  Also drawn as lines in sections / elevations while the window is open
  (option). Temporary graphics only - nothing is added to the model or
  printed. If the planes don't show in the preview pane, use
  *Split view* - they always show in the real 3D view.
- **Edit the range**: level + offset per plane (`2'-6"`, `-6"`, `1 1/2"`,
  `2.5` = feet), -/+ nudge by the chosen step, Enter applies. With
  *Apply each change right away* every nudge / level pick applies. Checks
  Top >= Cut >= Bottom >= View Depth before sending. *Revert* goes back to
  the range the plan had when the window picked it up.
- **Drag a plane with the section box arrow**: pick the plane in *Drag
  with section box arrow*. The 3D's section box snaps one face to it (top
  face for floor plans, bottom face for ceiling/soffit plans - flipped
  when it's the outermost plane), and dragging that face's arrow moves the
  plane (offset kept on its level, rounded to 1/8"). Dragging any other
  face just snaps back. Set it to Off for the full range. Nothing is added
  to the model. (Replaced the v2 grip pads; any left in a model are
  deleted when the button runs.)
- **View template controls View Range**: a tick box appears to edit the
  template instead - that changes every view using it.
- **Live refresh**: range, crop, scope box, template or level changes
  (incl. undo) refresh the 3D by themselves. *Follow the active plan*
  retargets when you switch plan views.
- *Show 3' of model beyond the range* pads the box above and below.
- Options are remembered. Close the window to stop the live link; rerun
  the button to rebuild it in the same spot.
- Note: when the box has to move, the refresh is its own small undo step
  ("MCC: View Range 3D"), so undoing a range change can take two Ctrl+Z.
- Needs pyRevit's `dc3dserver` for the planes (pyRevit 4.8+); without it
  everything else still works.

## Tag Soffit / Refresh Support Elev
Settings live in `lib/mcc_elev.py` (tag family/type per category, the
support parameter name). MCC's 3-Box tags read top/bottom from the model
and shoring height = bottom - **Bottom Reference Elevation**.
- **Tag Soffit**: open a soffit plan, pick categories. Every untagged
  floor / beam / column / wall in the view gets its MCC 3-Box tag at its
  center (drag to tidy). Floors and beams also get Bottom Reference
  Elevation filled from the concrete support found below them. Select
  elements first to limit it to those.
- **Refresh Support Elev**: re-measures supports after model changes,
  updates Bottom Reference Elevation where it moved, lists the distinct
  shore heights on the level.
- A 3D view named MCC_RAYCAST_3D is created once for the calculations;
  don't add a view template or hide structure in it.

## Dim Slab Edges
Settings at the top of its script.py.
- Select floors first, or run with nothing selected to use every floor on
  the view's level.
- Each straight soffit edge (slab edge, opening, drop, soffit step) gets
  a dimension to the nearest parallel grid. Top-of-slab edges are off by
  default (INCLUDE_TOP_FACE), since they're hidden info on soffit plans. Edges on a grid, duplicates, and short notches
  are skipped. Angled and curved edges are reported for manual dims.
- Set AUTO_DIM_TYPE to a dedicated dimension type so reruns replace the
  previous auto dimensions instead of stacking new ones.

## Dim Text (Dimensions panel)
Batch version of Revit's Dimension Text dialog, applied to everything
selected at once.
- Selecting: pre-select dimensions (whole strings), or run with nothing
  selected and pick them on screen (Revit's normal pick, then Finish).
  Revit can't select one segment of a string, so the window lists every
  segment of each picked string with a tick box, showing its value and
  marking the one you clicked (pre-ticked). All / None buttons for speed.
  Pre-selected strings start fully ticked.
- **Dimension Value**: *Leave as is* / *Use actual value* (clears any
  override) / *Replace with text* (starts at `?'-?"` for unknown dims;
  the real value stays underneath).
- **Text Fields**: Above / Prefix / Suffix / Below (e.g. suffix `R.O.` on
  rough-opening dims). The space between prefix/suffix and the value is
  added for you (tick box to turn off). Blank fields are left alone; tick
  **Clear fields left blank** to wipe them.
- **Dimension style** dropdown, or "(keep current style)". Only applied
  where Revit allows it for that dimension's kind (linear vs angular).
- **Set as default** remembers the whole form (per user, pyRevit config).
- Shared code is in `lib/mcc_dim.py`.

## Inspect Model
Read-only. Lists the template, title block, legend, scope box, dimension
type, sheet parameter and elevation-box family names in the open model so
the CONFIG blocks can be matched to it. Run this first on a new project.

## Status (2026-09-28)
- pyRevit installed; extension loads; Inspect Model runs on 1268 - Kalae.
- CONFIG set from Kalae: template `Plan - Outlines - Soffit View`, title
  block `Title Block - MCC Standard (R22) : 30x42 Sheet`, legend
  `S1. SOFFIT PLAN`, sheet `1.{level}.0` / `Level {n} - {Area} (Soffit Plan)`.
- v0.2: elevation boxes rewritten to place MCC's real 3-Box tags and fill
  `Bottom Reference Elevation`. **Not yet tested** - next is TESTING.md
  steps 2-5 on a Kalae copy. Legend/plan coordinates still need tuning.

## Next up (not yet built)
- Key plan annotation (per-level highlight) placed by the sheet builder
- Building section per level (1.X.0 spec: one bay, slab thk + shoring HT)
- Chain edge dims into strings; grid-to-grid strings
- Pre-issue QA check against the 1.X.0 "includes" list
