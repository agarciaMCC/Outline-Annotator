# Other projects study — how McClone soffit plans are dimensioned (2026-10-05)

Source: issued PDF sets in `Reference Projects/` (not on GitHub). Images: `Claude outputs/reference_study/`
(PNGs, local only; `crop.py` renders a page region: `python crop.py <pdf> <page> x0 y0 x1 y1 <dpi> <out>`
with page fractions). Revit models not opened yet — next step is Audit Dims on detached copies.

| Project | Set | Sheets looked at |
|---|---|---|
| 1256 Alia (tower on garage podium, Honolulu) | Garage Podium (56 p), Tower (27 p), 2026-07 | 1.3.1 L3 tower soffit, 1.3C.1 L3 tower control plan, 1.9.0 L9–23 odd tower soffit |
| 1156 Eastlake (garage + building, Seattle) | 34 p, 2022-09 | 1.7.0 L3 soffit |
| 1175 Bothell STEM 4 (low-rise) | 13 p, 2022-06 | 1.2.0 L2 soffit |

Model files: `Alia/1256 - Alia - R22_detached.rvt`, `Eastlake/2021.05.06 - 1156 Model - Final.rvt`,
`Bothell Stem/2022.06.21 - 1175 Model - Final.rte` (a Revit *template* file — ask Adolfo whether that is the right file).

## What all three share (and Kalae too) — strong evidence
1. **Grid-to-grid string on every side of the plan, plus an overall** (outermost lane), with the slab edge
   located off the end grid (e.g. Bothell `1'-7 3/4"` edge→grid at each corner). Dim Soffit v2 does not
   do this yet (listed "not done" from the Kalae L7 sheet).
2. **Columns and beams centred on grids are not dimensioned** — sheet note "ALL COLUMNS / BEAMS ARE
   CENTERED ON GRID LINES U.N.O." Off-grid members get a face→grid offset (Bothell `1'-0"` each side of a beam).
3. **Openings: grid → edge | size | edge → grid** — a closed string between the two nearest grids, one per
   direction (Eastlake temp openings `10'-6 1/2" | 13'-11 1/4" | 5'-6 1/4"`), often with the grid-to-edge
   overall stacked outside it. Openings drawn with a red X and labelled `OPNG` / `TEMP OPNG` /
   `ELEVATOR SHAFT OPNG` — **no "R.O." suffix on any of the three** (Kalae L7 only).
4. **Rotated / skewed openings and edges: every corner located from a grid in both directions**, dims
   aligned to the grid, not to the edge (Eastlake rotated temp openings, Alia L3 skewed tower).
5. **Core / shaft openings dimensioned off the wall faces** (inside clear sizes + wall thickness labels
   `30" CIP WALL`), matching Kalae and the v2 "wall face is the anchor" decision.
6. **CJ lines are located** — `TO CJ` text suffix on the dim (Alia L3), confirms CJ = dimension it.

## New patterns not in the current rules
7. **Stacked baseline dims from one grid** (all measured from the same gridline, stepping outward) are
   at least as common as chains on Alia's tower and in Eastlake's slab corners (`15'-9 1/4"`,
   `19'-10 3/8"`, `22'-2 3/4"` all from grid A). Every point still locates off a grid, so it satisfies the
   rule — but v2 only plans chained strings. Alia's sawtooth lanai edge: each vertex gets its own
   stacked dim from the grid line, not an edge-to-edge chain.
8. **Text suffixes on dims:** `TO CJ`, `END DRIP` (drip edge ends, Alia tower), `TYP`. Arcs: `R = 2'-0"`
   label plus the **arc centre point located** from grids (orange dims/markers on Alia tower 1.9.0).
9. **Alia control plans (1.xC.x)** — a separate sheet per soffit plan, two views: "FOR VERTICAL Lx–Ly"
   (walls/columns below) and "FOR HORIZONTAL Ly" (slab edges). **Green dashed control lines** offset
   from grids (e.g. 6'-0" off T2) and stacked baseline dims from a control line to every column corner,
   wall end and edge. Kalae, Eastlake and Bothell have no control plans — Alia/Hawaii-office practice?
10. **Tower plans rotated to the tower grid** (Alia 1.9.0 view rotated so tower grids are orthogonal);
   podium-level sheet 1.3.1 keeps the skewed tower on the garage grid.
11. Colour conventions: **blue dims = changed per a submittal return** (note on sheet), **red `?-?`** =
   unknown, needs info (Bothell), orange = arc centres/drip points (Alia tower).

## Placement measurements — Kalae hand dims (2026-10-05)
`Claude outputs/audit_R26/measure_placement.py` (read-only; `OUT=...; execfile`) → `reference_study/placement_kalae.md/.csv`.
Run on all 32 Kalae soffit plans, 2,763 hand linear dims (ZZ test views skipped). Paper inches (model ft × 12 / view scale).
**Caveat:** this run went to the live Kalae model in Revit 2023 (MCP was attached to 2023, not the R26 rig) — read only,
model reported unmodified. Alia (saved in 2026) and Eastlake (2020) not measured yet: need the 2026 MCP session.
- **Row spacing between stacked parallel dims: 3/16"** on paper is the clear standard (p10 0.187", biggest bin
  0.1875–0.25" = 429, then 0.125–0.1875" = 244). Same on 1/8" and 3/32" sheets → detailers space in *paper* units.
- **First dim line off the object: median 1/4"** (p25 1/8", p75 7/16"). Core-wall views sit further out (5/16"–3/8"),
  falsework-layout views tighter (~1/8").
- **Stacked from one grid dominates:** 67% of dims share an end with a parallel dim (1,840 / 2,763); 85% are
  single-segment, only 15% are chains (median 2 segments). Supports "stacked default, chains as checks".
- **Text:** pulled off its segment on 30% of dims (819); text sits 1/64" off the line (type setting). Words on dims:
  R.O. ×21, TYP. ×7, TO COL CL, TO EOS, TO FACE, BM CL, FROM GL xx, SOFFIT STEP, ?'-?" (unknown) — rare overall (~3%).
- Dim types: 5/64" Arial Narrow (transparent/plain/opaque) carry 89%; witness extension 1/32", dim line extension 0.
- **vs Dim Soffit v2 now (`mcc_layout.CFG`):** first lane 1.5 ft and `LANE_STEP` 1.75 ft are *model* feet → 3/16" + 7/32"
  at 1/8" but 9/64" + 5/32" at 3/32". Hand sheets keep 1/4" + 3/16" on paper at any scale → set lanes in paper inches.

## Placement patterns seen on the PDFs (Alia, Eastlake, Bothell)
- Stacked rows step outward at an even spacing; the shortest dim is nearest the object (Eastlake grid-A stack, Alia lanai).
- Opening strings sit just outside the opening on the side toward the locating grid; overall stacked one row further out.
- Grid-to-grid + overall are the outermost rows, outside everything else (all sets).
- Core interior sizes go inside the shaft; wall-face anchors outside the core (Eastlake, Alia, = Kalae).
- Skewed objects: dims stay square to the grid, not to the edge (Eastlake rotated openings, Alia L3).

## Decisions from Adolfo (2026-10-05)
- **Grid-to-grid + overall strings:** covered by the `WIP/Dim Grids` button, not Dim Soffit v2.
  (Dim Grids does two sides of the plan; the issued sheets often show all four — check with Adolfo if it matters.)
- **Stacked dims from one grid are the default for locating edges**, with chained strings kept as
  double checks. Detailers don't always do it, but the button should; the user deletes unwanted dims on review.
- **"R.O." stays off by default** — the user adds it to the openings they choose.
- **Control plan tool: later, hold off.**
- **Bothell:** Adolfo will convert the `.rte` into a project file for testing.
