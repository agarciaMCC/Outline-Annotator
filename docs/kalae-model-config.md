# Kalae (1268, R23) model names + decisions for the MCC extension

## Confirmed config (set in scripts 2026-09-28, host level corrected 2026-09-29)
- View template: `Plan - Outlines - Soffit View`. Its View Range should be Associated Level on all four planes: Top +4'-0", Cut −5'-0", Bottom −5'-0", View Depth +4'-0" (Adolfo's hand-built L3 view, 2026-09-29). Earlier it pulled Level Above — fix in Manage View Templates.
- **Phase: New Construction** (Adolfo, 2026-09-29). Phases in the model: Existing / New Construction / Future (not MCC). API-created views default to the last phase (Future), which drew everything halftone with no cut/shade fills — the builder now sets `VIEW_PHASE = "New Construction"` on every new parent and dependent.
- **Soffit plan views are hosted on the level whose slab they show** (Adolfo, 2026-09-29): the L2 soffit plan is hosted on Level 2 and its view range brackets the L2 slab. So `HOST_LEVEL_OFFSET = 0` in Build Soffit Sheets and Zones — level, view, sheet and zone names all use the same level.
- Title block: `Title Block - MCC Standard (R22)` type `30x42 Sheet`
- Legend on soffit sheet: `S1. SOFFIT PLAN` (position TBD on first run)
- Sheet param for issue status: `Issued For`
- Sheet number: `1.{level}.{idx}`; sheet name **all caps** — MCC doesn't use lower case (Adolfo, 2026-09-29): `LEVEL {n} - {ZONE} (SOFFIT PLAN)`, e.g. `LEVEL 3 - NORTH (SOFFIT PLAN)`. The builder upper-cases the whole name.
- 14.x series = falsework plans (soffit plan as ghosted background) — no collision
- Levels: LEVEL-1 … LEVEL-38, LEVEL-4.5, ROOF, ELEV MECH RM, MECH ROOF. Odd tokens (4.5, ROOF, ELEVMECHRM) need a numbering decision.
- Scope boxes exist per level (`Level 1`…`Level 5`, `L6 to L40 Tower Footprint`) — the builder matches them to levels by name.

## Elevation boxes — design change (v0.2)
MCC uses live Revit annotation, not a custom text family:
- `Tag - Floor - Box, Top Elev, Bot Elev (R22)` types 2-Box/3-Box (L/R, opaque) — 3-Box shows top / bottom / **shoring height read from a floor parameter** (name TBD — Inspect Model now lists floor params)
- `Tag - Beam - Box, Top Elev, Bott Elev, Clear Height (R22)` 3-Box
- `Tag - Column - Box, Soffit and Floor (R22)`
- `Tag - Wall - Box, Top Elev, Bot Elev, Height (R22)` 3-Box (All Info Calculated)
- `Tag - Edge - Box, Top Elev, Bot Elev (R23)` slab edge tags
- Spot elevations: symbol `Spot Elevations - Elevation Box`, dim types `1-Box - Soffit Elevation (Above/Below)`, `2-Box - THK 6"/12 3/4"/24"`, `2-Box - Above/Below`
- Adolfo: soffit plans use the beam/column/wall box tags; shoring HT lives in the 3-Box floor tag.

Plan: rewrite Place Elev Box → "Tag Soffit": place the real box tags on floors/beams/columns/walls in the view; use the raycast engine only to compute shoring HT and write it to the floor parameter the 3-Box tag reads. Refresh Elev Boxes → becomes "Refresh Shore HT" (recompute the floor parameter), tags update on their own. The old 3-BOX MANUAL family config in lib/mcc_elev.py is obsolete.

## Dim Slab Edges
- Dimension types available: `Gridline Dimensions`, `Horizontal`, `5/64" Arial Narrow…`. Create a dedicated `MCC - AUTO DIM` type (duplicate of the standard one) before testing so reruns can clean up.
