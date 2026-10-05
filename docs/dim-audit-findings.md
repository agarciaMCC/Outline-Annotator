# Dimension audit — how the Kalae soffit plans are actually dimensioned

Source: Audit Dims button run 2026-09-29 on the 10 hand-dimensioned soffit plan views (L2 N/S, L3 N/S, L4 N/S, L4.5 N/S, L5, L7-25). 1,844 dimensions, 4,115 witness lines. CSV: `PDFs/dim_audit.csv`; sheets: `PDFs/Combined Outlines.pdf`.

## Re-run 2026-10-01 (Revit 2026, via MCP, R26 TEST model)
Headless run of Audit Dims through the Revit MCP connection on the **14 views placed on 1.x soffit sheets** (adds L3 NE callout, L6, L26-38, Roof to the 10 above). **1,886 dims, 4,661 witness lines.** Files: `Claude outputs/audit_R26/dim_audit_soffit_sheets.csv` + `_report.md`; runner `Claude outputs/audit_R26/run_audit.py` (stubs the pick/save dialogs; ~2 s for all 14 views). Findings below hold; numbers from this run:
- Singles still dominate: **1,599 of 1,886 (85%)** one-segment dims; 230 two-segment; chains of 3+ are rare (57).
- Witness lines: grid 1,674 · beam face 1,125 · slab edge 362 · detail items 330 · opening edge 282 · column face 261 · wall face 213 · shaft openings 145 · lines 109 · generic models 100.
- **Anchor = nearest grid for about half of every object type** (beam 49%, slab edge 68%, column 44%, opening 52%, wall 42%, detail items 55%, shaft openings 78%); the rest is object-to-object of the same kind (beam 38%, slab edge 26%, opening 38%, wall 31%). Generic models are the exception (65% to themselves — Beam Trim Void sizes).
- Top patterns: beam>beam 177 · grid>beam 113 · slab>grid 111 · beam>grid 102 · grid>detail items 79 · grid>slab 77 · beam>grid>beam 70 · opening>opening 48 · grid>opening 47 · grid>column 45.
- Standoff medians (dim line from the object): slab edge 1.7 ft · generic models 1.7 · opening 1.9 · column 2.7 · lines 2.4 · wall 3.7 · detail items 3.7 · beam face 7.8 (beam width dims sit anywhere along the beam) · shaft openings 14.8.
- Text overrides on 49 dims (2.6%). 820 dims inside the slab, 1,066 outside.
- Dim types: 5/64" Arial Narrow (Transparent) 996 · 5/64" Arial Narrow 632 · (Opaque) 107 · Gridline Dimensions 87 · REV Missing Dimensions 27.

## Headline: detailers use short, single dims — not chains
- **85% of all dimensions have ONE segment** (two references). Chains of 3+ segments are almost all grid strings ("Gridline Dimensions" type). Per view the single-dim share is 78–92%.
- Of the non-grid-string dims, **995 reference exactly one grid, 720 reference no grid at all** (object-to-object: beam face to beam face, opening edge to edge, column to beam, edge to wall).
- So the auto-dim model should be: *one small 2-reference dim per fact*, placed right beside the object — not a chained string per side of the plan with tiers.

## What gets referenced (witness lines)
| referenced | witness lines |
|---|---|
| grid | 1,462 |
| beam face | 1,095 |
| detail items ("Large Scale" family — 320; stressing blockouts 7) | 330 |
| slab perimeter edge | 262 |
| column face | 256 |
| opening edge | 253 |
| wall face | 208 |
| lines (model/detail lines) | 109 |
| generic models (Beam Trim Void 67; CIP wall generic models) | 71 |
| shaft openings | 11 |

## Patterns per object type (single dims unless noted)
**Beams (186 beams referenced)** — the most-dimensioned thing on the sheets.
- `beam > beam` width across the beam: 201 dims. Values are the standard widths (3'-9" ×48, 5'-6" ×34, 2'-9" ×28, 7'-6" ×28, 4'-0" ×21, 6'-0" ×16).
- one face to the nearest grid: `grid > beam` / `beam > grid` 223 dims, median length 4'-11".
- beam centred on a grid: `beam > grid > beam` (face | grid | face) 89 dims.
- typical combo per beam: width dim + one face-to-grid dim, OR face|grid|face alone.
- beam to column face (`beam > column`) 59, beam to wall 38, beam to beam-trim-void 11.
- the width dim sits anywhere along the beam (39 within 3 ft of an end, 46 at 3–8 ft, 114 farther) — placement along the beam is free; it goes where there is room.

**Openings (per opening)**
- `opening > opening` size: 47 dims (85 opening/edge combos are size-only).
- one edge to nearest grid: 82 dims; to a wall face when a wall is right there: 22 dims (`wall > opening` / `opening > wall`).
- occasional `opening > opening > grid` (15) and `grid > opening > opening > grid` (6) chains for stepped openings.
- standoff of the dim line from the opening: median 1'-10", p75 2'-9".

**Slab edges**
- edge to nearest grid: 120 dims (median length ~5–6 ft).
- edge to edge (jog width): 26; edge to column face: 19; edge to wall: some.
- standoff from the edge: median 1'-2", p75 2'-4". Very local.

**Columns**
- face to nearest grid: 94 dims (median length 9'-3" — columns are often a bay away from a grid on the rotated wing).
- beam-to-column 59, column-to-detail-item 12.
- standoff median 2'-8".

**Walls**
- face to grid 59, wall to wall 15, wall to beam 38, wall to opening 22. Standoff median 3'-8".

**Detail items / lines** (330 + 109 refs) — `grid > detail items` 102, detail-to-detail 45. "Large Scale" detail family = CJ (construction joint) lines → dimension them; plain detail lines are hand-drawn QC control points → ignore (Adolfo, 2026-09-29).

## Grid directions (zones)
Every view uses 4–6 grid direction families, e.g. L3 North: 2..8 (134), AA..FF (96), 10..9 (88), A..F.2 (77), F alone (27). The rotated wing families (A..F.2, A11..A9, F..J, 10..9) carry as many dims as the orthogonal ones. Grid "F" and "F.2/G.7" sit at their own angles and form their own families.

## Dimension types used
5/64" Arial Narrow (Transparent) 2,112 refs · 5/64" Arial Narrow 1,242 · Gridline Dimensions 355 · 5/64" Arial Narrow (Opaque) 271 · REV Missing Dimensions 60 · others <40. Text overrides/prefix/suffix on 111 witness rows (~3%).

## What this changes for the buttons
1. Replace "chained strings per side of the plan, tiered" with **one 2-reference dim per fact, placed within ~1–3 ft of the object**.
2. Beams are first-class: width dim + face-to-nearest-grid (or face|grid|face when centred). Beam ends to grid where a beam stops short.
3. Openings: size dim + one edge to nearest grid, or to a wall face when the opening abuts a wall.
4. Slab edges: each edge to its nearest grid, locally; jog widths edge-to-edge.
5. Columns: face to nearest grid each direction (Dim Columns already does this — check its output against the 94/59 pattern).
6. Use "5/64\" Arial Narrow (Transparent)" as the default type; "Gridline Dimensions" for grid strings.
7. Scorer: run the tool on a copy of a hand-dimensioned view and compare (ref-kind pair, element ids) sets against this CSV.
