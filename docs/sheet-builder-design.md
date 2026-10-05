# Sheet Builder — design (2026-09-29)

Replaces Build Soffit Sheets (retired to `_to_delete`). Adolfo wants one tool to duplicate sheets of any type — soffit plans, embed plans, vertical plans, etc. — with their view properties across multiple levels. Those sheet types are ordinary plan views, each with its own view template (Adolfo, 2026-09-29).

## Principle
**The prototype sheets are the whole spec.** Nothing is configured per sheet type; the builder reads everything from the finished sheets you pick.

## Modes
1. **Clone sheets to other levels** — prototype sheets (Project Browser selection or list) → target levels → preview → build.
2. **Split a view into zone sheets** — sets up the first level of a new sheet type: pick a plan view, scope boxes and/or typed zone names, title block, number/name pattern → dependents (annotation crop on) + blank sheets. Then sketch crops and lay out by hand.

## Clone rules
- Sheet number: level token swapped in the dotted parts (`6.3.0` → `6.5.0`, `14.3.0A` → `14.5.0A`); name, view names and Title on Sheet swapped via `rename_for_level`. Same title block as the prototype sheet; project sheet params copied.
- Prototype level = GenLevel of the biggest plan viewport; every plan view on the sheet is cloned at the same level offset (a "level below" view stays level below).
- New view: `ViewPlan.Create` with the prototype's view type + template, then every writable parameter the template doesn't control is copied (level-valued ElementIds shifted by the level offset — underlay etc.; phase comes along this way). View range copied plane by plane, explicit levels shifted, skipped if the template controls it.
- Dependents: parent found on the target level by swapped name, else the single view with the same type + template (asks if several), else created like the prototype's parent. Unplaced views with the target name are reused.
- Crop: scope box reused if its Z range spans the level, else its level-named twin, else crop box copied; sketched shape / crop box copied exactly (dz shift); CropBoxVisible and annotation crop copied from the prototype (no longer forced on).
- Grids: `copy_grid_display` (extents, 3D/2D ends, bubbles, elbows, hidden grids).
- Placement: `place_like` — the prototype view's crop centre is mapped through model→projection→sheet transforms and matched exactly; viewport type, rotation and title (LabelOffset / LabelLineLength) copied. Scale mismatch warned.
- Legends reused at the same spot; schedules, text, symbols, lines copied; sections / elevations / drafting views can't repeat → reported.

## Superseded Build Soffit Sheets decisions
Config-driven template name, `VIEW_RANGE` standard, `VIEW_PHASE`, forced annotation crop, all-caps name formatting, prototype-level zone specs — all now come from the prototype. Standing facts still true: soffit plans hosted on the slab's own level; New Construction phase; MCC names are all caps (prototype names already are).

## Panel layout
- **Sheets** panel: Sheet Builder, Fit View Titles.
- **Soffit Plans** panel: Zones, View Range 3D, Tag Soffit, dim buttons, etc.

## Open
- Not yet run in Revit (TESTING.md §2).
- Key plans (tabled); sections/elevations per level; saved presets ("Soffit set", "Embed set").
- Odd level tokens (4.5, ROOF, ELEVMECHRM) numbering.
- Note: device_commit_files sometimes silently doesn't land — verify md5 on disk after committing; fall back to base64 over device_bash.
