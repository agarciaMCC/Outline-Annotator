# Archive soffit study — past McClone soffit plans vs the Dim Soffit v2 rules (2026-10-06)

Source: the 1,188 soffit sheets in `Training Library/Soffit Plans/` (126 jobs, 1038–1308; see
`outline-training-library.md`). Two passes:

1. **Measured, all sheets** — `Training Library/analyze_dims.py` (reader: `dimgeom.py`). A dim counts when its text
   sits beside two tick marks whose spacing is that length at the sheet scale (scale found from the sheet itself),
   so elevation tags and labels are not counted. 100,634 dims on 1,089 sheets with ≥ 10 dims (42% of length
   texts matched; pulled-out text with leaders is missed). Grid lines found from their bubbles on 475 sheets.
   Per-sheet numbers: `Training Library/dim_stats.csv`; `python analyze_dims.py --summary` reprints the totals.
2. **Looked at, 24 sheets** — one per job, 8 from each era (1038–1099 ≈ 2017–19, 1100–1199 ≈ 2019–22, 1200+ ≈ 2022–26),
   4–6 close-up crops each, checked rule by rule. Reports and crops: `Claude outputs/archive_study/review_g1…g4.md`,
   brief `review_brief.md` (PNGs local only).

## Measured (all sheets)
| Measure | 1038–1099 | 1100–1199 | 1200+ | All | v2 now |
|---|---|---|---|---|---|
| Sheets / jobs | 501 / 43 | 400 / 53 | 188 / 25 | 1,089 / 121 | |
| Dims per sheet (median) | 76 | 69 | 85 | 74 | |
| Row spacing, most common | 3/16" | 3/16" | 3/16" | **3/16"** (13,597 of ~22k gaps) | `LANE_STEP_IN` 3/16" ✔ |
| First row off the element (median) | 0.25" | 0.25" | 0.25" | **0.25"** (quartiles 0.16–0.42") | `FIRST_GAP_IN` 1/4" ✔ |
| Rows per stack: 2 / 3 / 4+ | 90 / 8 / 2% | 89 / 9 / 2% | 80 / 13 / 7% | **87 / 10 / 3%** | max 2–3 ✔ |
| Stack lengths grow row by row | 97% | 98% | 94% | 96% | shortest nearest ✔ |
| Chains (2+ dims end to end) hold … of dims | 63% | 62% | 67% | **63%** | stacks default, chains as checks |
| Dims over 30 ft: grid-to-grid / one end on a grid / no grid | 24 / 1 / 7% | 21 / 2 / 13% | 18 / 7 / 7% | **21 / 3 / 9%** | locating ≤ 30 ft ✔ |
| Dim ends off a grid located straight off a grid | 29% | 40% | 56% | 38% (45% counting grid-anchored chains) | every point ✔ (stricter) |
| "R.O." on dims | ~140 | ~220 | ~310 | ~670 | off by default |

Notes: "grid-to-grid" = both ends on a grid line (Dim Grids' job); the 30 ft tape rule holds for locating dims
(3% over). The "located" share is a floor — grids are found only from paired bubbles, and points are matched
within an inch of paper. "Shortest row nearest the element" could be measured from witness lines on only some
exports (65% of 5,151 stacks) — the visual pass is the better evidence for it (below).

## Looked at (24 sheets)
**Rules the archive backs up (held on nearly every sheet):**
- **Rule 5, stacked rows:** the shortest dim is nearest the element and the overall sits outside its chain, on
  every sheet where stacks appear.
- **Rule 6, rows per object:** at most 2–3 rows. The only exceptions are Alder 9's control-line stacks (4–5 rows)
  and Intuit's Stair 2 (3–4 rows).
- **Rule 11, one side per direction:** an element's dims of one direction stay on one side of it, and its size
  joins its locating dim end to end.
- **Rule 15, text that doesn't fit:** it is pulled off the line with a leader.
- **Rule 14, crossings:** dims rarely cross each other, and dim lines don't sit on an edge running the same way.
- **Columns:** never dimensioned on any sheet. Columns get a size and height tag, and most sheets carry the note
  "COLUMNS / BEAMS CENTERED ON GRID LINES U.N.O.".
- **Angled wings:** always get their own grid set, with their own grid strings.
- **Locating dims over 30 ft:** rare. The long dims seen were grid-to-grid strings, overalls, or beam lengths from
  slab edges (Kaiser 1200).

**Where practice differs from v2:**
1. **Opening and shaft sizes inside the opening are normal**, not a last resort. 7 of 24 sheets do it: stair
   14'-8" × 8'-6", crane blockouts, shafts. The locating dims stay outside. v2 allows a size inside only when
   there is no room outside (`W_IN_SHAFT` 20).
2. **Cores and stairs are the main exception to rules 2, 9 and 10.**
   - Older sheets (2017–21) chain wall pieces and gaps through the core, off wall faces.
   - Newer sheets send the core to an enlarged plan (Platform 16, The Hudson, 405 Industrial boxes its cores).
   - v2's "enlarged plan for clutter" matches the newer practice.
3. **Chains vs stacks depends on the detailer, not the year.** Chains hold 63% of all dims. About half the
   sheets chain (grid | edge | edge | grid) and half stack from the grid. The 2022–26 sheets chain slightly more.
   v2's stacked-by-default choice (Adolfo, 2026-10-05) is one of two normal styles, not the house standard.
4. **Beams:**
   - One width dim, at one end. No sheet had a halfway width dim on a long beam.
   - "Both ends" was seen only on some CJs and slab edges.
   - Centred beams sometimes still get a split width (3'-0" | 3'-0" either side of the grid) despite the
     centred-on-grid note.
   - Burlingame locates off-grid beams with one chain across each bay at mid-span.
   - v2 (at the time): width at both ends over 20 ft, plus a halfway dim over 40 ft. **The halfway dim was dropped
     on 2026-10-06 because of this study**; both ends over 20 ft (`BEAM_BOTH`) stays, when both ends are in the crop.
5. **A dim at each end (rule 7)** is mixed. CJs are often located at one end only: 1119, 1128, Kaiser along a 58 ft
   run.
6. **Walls are dimensioned on about a third of the sheets.** These are mostly the older ones, plus Intuit (shear
   walls) and Copper River. Newer sheets leave walls to the wall plans, as v2 does.
7. **CJs** are located off a grid when off one, and get no dim when on a grid. "TO CJ" appears only on Platform 16;
   others use a red CJ line or a hatched "28 DAY DELAY CLOSURE STRIP". Closure and delay strips are dimensioned
   like elements.
8. **Grid strings (Dim Grids' job):** on 4 sides on 12 of 24 sheets, 2–3 sides on the rest. Zone sheets show 2.
   Some sheets have 3 rows: grid-to-grid, partial overalls, overall.

**Habits not in the rules (repeat across jobs):**
- **Elevation box at every beam end and slab area:** top, bottom and height, or "T: / B: / HT =" (Capitol Hill).
- **Labels on openings and edges:** "(R.O.)" / "RO", "OPNG" with an X, "(CLEAR)", "TO GRID", "EOS", "EOW",
  "SOFFIT STEP", "TOS STEP", "SLAB JOG", "DRIP EDGE", "CHAMFER CORNER NO DRIP EDGE".
- **Notes instead of repeated dims:** "DIMENSIONS SIMILAR (UNO) ALONG GRID K", "DIMENSIONS TYP ON PILASTERS ALONG
  GL A U.N.O.", "EDGE OF OPENING ON GRID F", "WALL FACE 10" OFF GRID".
- **Pour names / sequences** on the plan ("POUR 1"–"POUR 5").
- **Colours:** red for late changes or unknowns, blue for submittal returns or scope, pink X'd openings.
- **Degrees** on angled edges (The Hudson, newest).
- **RFI triangles and revision clouds** left on issued sheets.
- **Small slab-edge offsets** added to the end of the grid-string row.

## What this suggests for v2 (for Adolfo to decide)
Status 2026-10-07 is marked on each item; decisions are logged in `dim-soffit-v2-design.md`.
- **Keep:** paper spacing (3/16" rows, 1/4" first row), 2–3 rows, shortest-nearest, one side per direction, size
  joined to its locating dim, no column dims, 30 ft for locating dims, angled grid sets, enlarged plan for
  crowded cores.
- **Ask:**
  1. Opening / shaft overall size inside the opening as the normal spot, rather than only when there is no room?
     *Open.* Still a last resort (`W_IN_SHAFT` 20). One case answered: the L3N pocket's `12'-1"` may sit inside the
     pocket, with its text off the shaded wall (2026-10-07).
  2. Long beams: drop the halfway width dim? One end only, or both ends over 20 ft?
     *Answered 2026-10-06:* halfway dim dropped; both ends over 20 ft when both ends are in the view.
  3. Chains vs stacks: offer chained (grid | edge | edge | grid) as a setting, since about half the detailers draw it?
     *Open.* Stacked stays the default (Adolfo 2026-10-05).
  4. "(R.O.)" on openings: it is common and growing (≈310 on 2022–26 sheets) — turn it on by default?
     *Answered 2026-10-06:* on by default for the overall size of large openings (at least 4 ft both ways: stair and
     elevator shafts); never on small holes, pockets or dims off a grid (`RO_SUFFIX`, `RO_MIN`).
  5. CJs: one end enough when the CJ is straight?
     *Open.* v2 gives CJs over 40 ft (`TURN_BOTH`) a dim at each end; shorter ones one end, on the side with more
     open space (Adolfo 2026-10-06, the CJ pair off grid 5).
