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

## Decisions from Adolfo (2026-10-05)
- **Grid-to-grid + overall strings:** covered by the `WIP/Dim Grids` button, not Dim Soffit v2.
  (Dim Grids does two sides of the plan; the issued sheets often show all four — check with Adolfo if it matters.)
- **Stacked dims from one grid are the default for locating edges**, with chained strings kept as
  double checks. Detailers don't always do it, but the button should; the user deletes unwanted dims on review.
- **"R.O." stays off by default** — the user adds it to the openings they choose.
- **Control plan tool: later, hold off.**
- **Bothell:** Adolfo will convert the `.rte` into a project file for testing.
