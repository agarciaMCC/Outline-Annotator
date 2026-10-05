# Auto-dim scoring runs (Dim Soffit vs hand-dimensioned sheets)

Run via the Revit MCP connection on the R26 TEST model. Runner: `Claude outputs/audit_R26/run_button.py` (drives any MCC button headless: stubs pick lists, yes/no alerts, progress bars, output; swaps `doc.ActiveView` for a given view). Reports saved next to it (`dimsoffit_L3N_runN.md`, `score_L3N_runN.md`). Test view: `ZZ CLAUDE TEST - L3 NORTH (auto-dim)` (independent copy of LEVEL 3 - SOFFIT PLAN cropped like L3 North, CJ lines copied in).

## Current status — run 10 (2026-10-01), L3 North
**Grid-location coverage: TOOL 163/217 edges (75%) vs HAND sheet 79/217 (36%).** 224 visible tool dims (passes: slab edges, openings, beams, CJ lines; walls off).

| target | n | HAND located | TOOL located | TOOL check-only | TOOL none |
|---|---|---|---|---|---|
| beam end (free ends only) | 16 | 25% | 100% | 0% | 0% |
| beam side | 42 | 28% | 52% | 14% | 33% |
| cj | 29 | 62% | 79% | 3% | 17% |
| opening edge | 80 | 37% | 80% | 6% | 13% |
| slab edge | 50 | 30% | 76% | 12% | 12% |
- Hand-located edges the tool misses: 9. Tool-located edges the hand sheet doesn't locate: 93. Neither: 45.
- Remaining gap: beam sides — most are slab edges running along a beam face (merged targets) where no beam dim lands within reach; next to investigate.

## Primary metric: grid-location coverage
Per Adolfo: the key requirement is that **every edge/point can be located off a gridline**; edge-to-edge dims are acceptable double checks, so precision vs the hand sheet is secondary. `lib/mcc_coverage.py`:
- Targets from `PlanModel`: slab perimeter edges (incl. soffit steps), opening edges, beam sides, **free** beam ends (ends framing into a column/wall are skipped — located by that member), CJ lines — limited to the view's crop, ≥ 6" long; coincident targets (same plane, overlapping) merged with their extents combined. Wall faces are not targets (walls are located on their own sheets). On a grid → ON GRID; no parallel grid family → ANGLED.
- Grade per target: **DIRECT** (grid witness line adjacent), **WALL** (dimensioned to an adjacent wall face, or the edge lies on a wall face — elevator openings / slab edges at walls), **CHAINED**, **CHECK** (edge-to-edge only), **NONE**. "Located" = DIRECT or WALL. Dim must sit within 8 ft of the target's extent. Plane tol ½".

## Changes to Dim Soffit 2026-10-01 (in order)
- **Geometric scorer** (`lib/mcc_score.py`, used by Score Dims; old version `script_v1_refstrings.py.bak`): hand dims reference slab side **faces** (SURFACE), Dim Soffit references **edges** (LINEAR); copied CJ lines have new ids.
- **CJ detection**: family "Annotation - Line - CJ Form Line", **type** "Large Scale" (older models: family "Large Scale") — either accepted. **CJ reference** = family's CenterFrontBack plane (instance-geometry line refs are symbol-level → Revit deleted 41 of 51 CJ dims at commit).
- **No blocking dialogs**: `PL.transaction_with_log` (IFailuresPreprocessor) — warnings dismissed, errors take Revit's default resolution (delete the bad dim), report lists what Revit removed. Unhandled commit dialogs freeze Revit and the MCP link.
- **De-duplication** (`mcc_place.dedupe`, before placing): coincident witness lines merged; dims repeating an earlier one (same family, same offsets ½", spans within 2 ft) dropped.
- **Walls pass off by default** on soffit plans (walls located on 4.x/5.x sheets).
- **Beam ends** located off a grid, never a nearby column face (`BEAM_END_TO_COLUMN` restores the old way); ends framing into a column/wall skipped.
- **Join cuts are not openings** (`PlanModel._drop_join_cuts`): a joined column/wall/beam cuts its outline out of the slab's soffit face (an 18x18 column on the rotated wing reads as a 2'x2' hole). Inner loops entirely inside one member's outline are dropped — 13 on L3. Real small holes left are Shaft Openings (Opening Cut); per Adolfo dimension them (user deletes if not wanted).
- **Annotation crop**: dims placed outside the view's annotation crop exist but are hidden (39 were). Placer now keeps both dim-line ends ≥ 1 ft inside the crop (`CROP_MARGIN`); objects with no room inside are skipped ("no room inside the view crop").
- **Every edge off a grid**: openings get a separate grid → edge dim for **every** edge (near edge may come off an in-line wall face instead), stacked in lanes 1.75 ft apart (`LANE_STEP`); beams get grid → near side **and** grid → far side, width dim kept as the check. Backup of the rules before this: `lib/mcc_rules_before_faredges.py.bak`.

## Test-view setup (important)
- Zone views (e.g. LEVEL 3 - NORTH AREA) are **dependents** — `Duplicate` of a dependent makes another dependent that **shares the parent's annotations**, so auto-dims would land on the real sheets. Instead: duplicate the **parent** (`ViewDuplicateOption.Duplicate`, no detailing) → independent view, then copy the zone view's CropBox + crop shape + annotation-crop setting.
- CJ lines are **view-specific detail items owned by the parent soffit view** → copy them into the test view (`ElementTransformUtils.CopyElements` view-to-view) before running.
- Count dims with `OwnerViewId == view.Id` as well as the view collector — the collector skips dims hidden by the annotation crop.

## History — match score vs hand sheet (secondary metric)
Run 5 (340 dims): recall 80% (exact 41%), precision 45% (exact 21%). Run 6 (255 dims, after de-dup): recall 80%, precision 44%. Precision is low by design: edge-to-edge check dims and grid dims the detailer didn't draw count against it.
