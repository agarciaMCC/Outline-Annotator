# v0.1 first-run test plan

Work in a **detached copy** of a real project model (or a scratch central) -
everything the buttons do is undoable, but test on a copy anyway.

## 0. Install
- [ ] pyRevit installed, Revit restarted.
- [ ] pyRevit > Settings > Custom Extension Directories: add the
      `Outline Annotator` folder (the one that *contains*
      `MCC.extension`). Reload pyRevit. Expect an **MCC** tab, 5 buttons.
- [ ] If the tab doesn't appear: check the folder path in Settings ends at
      the folder containing `MCC.extension`, not the extension itself.

## 1. Inspect Model  (read-only)
- [ ] Run it. Paste the whole output into the Claude project chat.
- [ ] From the output, set:
      - `Build Soffit Sheets/script.py` CONFIG: VIEW_TEMPLATE_NAME,
        TITLEBLOCK_FAMILY / TITLEBLOCK_TYPE, LEGENDS names, SHEET_PARAMS
        keys, SHEET_NUMBER_FMT vs the existing sheet numbering
      - `lib/mcc_elev.py`: TAGS types per category (already set for R22 template)
      - `Dim Slab Edges/script.py`: AUTO_DIM_TYPE (create an
        "MCC - AUTO DIM" dimension type in the model first)

## 2. Sheet Builder (Sheets panel)
On the Kalae copy:
- [ ] Soffit: select 1.2.0 + 1.2.1 (finished by hand) in the browser,
      Sheet Builder > Clone, Levels 3-4. Preview shows 1.3.0 / 1.3.1 /
      1.4.0 / 1.4.1 with "new ... (of <L3 soffit plan>)" - the existing
      L3 soffit plan is found as parent, not duplicated.
- [ ] New views: same template, phase New Construction, view range
      Associated Level like L2 (check with View Range 3D), crop shape,
      crop hidden/shown, annotation crop, grids like L2.
- [ ] 1.3.0 over 1.2.0: plan, title, legends, notes in the same place.
- [ ] Embed / vertical plan: finish one level's sheet by hand, clone it
      to two levels. Its own template + view range carried over?
- [ ] Rerun -> SKIP sheet exists. Ctrl+Z undoes a whole run.
- [ ] Split mode: pick a level's plan, type NORTH, SOUTH -> dependents
      + blank sheets; sketch crops, lay out, then clone from them.

## 3. Tag Soffit  (on the new soffit plan)
- [ ] Select ONE floor, run, pick "floor" only. Expect a 3-Box floor tag
      at its center showing type / top / bottom / shoring height.
- [ ] Check the Bottom Reference Elevation it wrote against a section
      through that slab: is it the top of the slab/SOG/footing below, on
      the same basis as the level heads? Note any offset: __________
- [ ] Run with nothing selected on a small level. Count tags; look for
      tags in openings, wrong tag type, beams with no support found.
- [ ] Rerun -> everything "skipped (tagged)", nothing duplicated.

## 4. Refresh Support Elev
- [ ] Move or thicken a slab below, run. Expect only affected floors in
      the Was/Now table and the distinct-shore-heights line.

## 5. Dim Slab Edges
- [ ] Run with nothing selected. Count created vs failed.
- [ ] Look for: dims to the wrong grid, dims that should be one string,
      duplicated dims, edges that got skipped but should be dimmed.
- [ ] Rerun with AUTO_DIM_TYPE set -> old auto dims replaced, not stacked.

## View Range 3D (v2)
- [ ] Run on the L2 soffit plan. Window opens; preview shows the box.
- [ ] Colored planes visible in the preview? If not, *Split view*
      - visible there? Planes as lines in a building section?
- [ ] Nudge Cut plane +/-, type an offset + Enter, pick Level Above for
      Top. Plan updates, 3D follows. Try Cut above Top -> red message.
- [ ] If the soffit template controls View Range: tick box appears;
      editing it changes the other soffit plans too.
- [ ] Change the range in Revit's own dialog / drag the crop -> 3D
      follows without rerunning. Ctrl+Z -> follows back.
- [ ] Switch to the L3 soffit plan -> window retargets.
- [ ] Close the window -> planes disappear from sections.

## Findings log
| Button | What happened | Expected | Fix / decision |
|---|---|---|---|
|  |  |  |  |
