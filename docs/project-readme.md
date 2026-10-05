# MCC pyRevit Extension - Soffit Plans (v0.3)

Local folder: `C:\Users\agarcia\Desktop\Claude Projects\Outline Annotator\MCC.extension` (pyRevit points at the Outline Annotator folder). See also `sheet-standards.md`, `kalae-model-config.md`, `dimensioning-rules.md` and `annotation-style-observations.md` in this project.

## Buttons (MCC tab > Soffit Plans)
- **Inspect Model** — read-only dump of template / title block / legend / scope box / dim type / sheet & view params / tag families / element parameter names. Run first on any new project.
- **Build Soffit Sheets** — pick levels → structural plan of view type `Outlines - Soffit Plan` (picker if missing), hosted one level below the picked level (soffit views look up), template `Plan - Outlines - Soffit View`, sheet `1.{level}.0` named `Level {n} - {Area} (Soffit Plan)`, `Issued For` filled, plan + `S1. SOFFIT PLAN` legend placed.
- **Tag Soffit** — MCC 3-Box tags on floors / beams / columns / walls; fills `Bottom Reference Elevation` from the support found below (skips elements in model groups and lists them).
- **Refresh Support Elev** — re-measures supports, updates the parameter, lists shore heights.
- **Dim Slab Edges** — perimeter edges located from grid (outside strings near the plan edge, otherwise one dim at a turn), chain check string, openings grid → near → far, obstacle/grid/crossing avoidance, short text pulled out with leaders. Rules in `dimensioning-rules.md`.
- **Dim Columns** — nearest grid in each direction, centerline or face (asked per run); columns centred on a grid skipped.
- **Dim Grids** — grid-to-grid + overall strings outside the slab.
- **Fit Grids** — trims grid extents to the slab in the active view only (view-specific extents).

Settings: CONFIG block at the top of each button's `script.py`; value edits take effect on the next click, no reload.

## Status (2026-09-28)
- Extension installed and running on 1268 - Kalae (Level 7 soffit view on LEVEL-8 slab).
- Currently iterating Dim Slab Edges placement rules against Adolfo's review screenshots.
- Open decisions: sheet numbering for odd levels (4.5, ROOF, ELEV MECH RM); per-level scope boxes; whether opening far edges also need their own grid dim.

## Next up (not yet built)
- **Settings window with live preview** (agreed, after rules settle): sliders/checkboxes for the main CONFIG values; Preview draws real dims into the view and replaces them on each change; Apply keeps, Cancel removes; values saved per user; shift+click runs with saved values. Needs Dim Slab Edges refactored into a callable function first; then Dim Columns / Dim Grids.
- Port partner-side / crossing / alignment rules from Dim Slab Edges to Dim Columns.
- Key plan annotation (per-level highlight) placed by the sheet builder
- Building section per level (1.X.0 spec: one bay, slab thk + shoring HT)
- Pre-issue QA check against the 1.X.0 "includes" list
