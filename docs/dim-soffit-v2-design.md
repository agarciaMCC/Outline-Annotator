# Dim Soffit v2 — design (2026-10-02)

Goal (Adolfo): a button that produces a finished soffit sheet needing only light cleanup, and that makes a detailer faster. No shipping deadline; do it properly.

## Status
- **2026-10-02 — Stage 1 (features) first pass: `lib/mcc_features.py`.** Runs on L3 North in ~2 s; every slab edge ≥ 6" lands in exactly one feature (373/373, none in two). In crop: 81 runs, 40 corners, 1 bump, 2 notches, 4 steps, 20 openings (5 core, 7 shaft, 5 void, 2 penetration, 1 plain), 25 beams, 31 CJ lines. Table: `Claude outputs/audit_R26/features_L3N_core.md`. Refinements pending: merge sub-foot "runs" between steps into their step/bump features; two slabs sharing an edge give duplicate runs (de-duped at plan level); core vs shaft label of the outer elevator shafts.
- **2026-10-02 — Stage 2 (string plan) first pass: `lib/mcc_strings.py`.** L3 North: **137 strings (133 locate, 4 check), plan coverage 82%** (180/217 edges located, 13 none) vs hand sheet 46% (corrected — see `auto-dim-scoring.md`) and v1's 75% with 224 dims. Core strings match sheet 1.3.0 line for line at the key spots: middle elevator `CC | 8½" | edge | 13'-7½" | edge | 4'-6" | wall`; shafts `edge@wall | 8'-3" | edge | 11'-9" | 7`; pilaster hole `7 | 13'-2¾" | edge | 1'-2" | edge | 8" | edge | 1'-2" | edge`. Dump: `Claude outputs/audit_R26/strings_L3N_core.md`. Decisions in the plan: an opening edge lying on a wall face is the anchor on that side; far-edge dims only for one-sided openings wider than 6 ft; **beams get width + ONE anchor (nearest), per the hand sheets**.
- **2026-10-02 — Stage 3 (layout) first pass: `lib/mcc_layout.py`, buttons `WIP/Dim Soffit v2` and `Diagnostics/Dim Check`.** Run 4 on the L3 North test view: 137 planned → **102 placed, 35 to review, 101 created, 3 estimated text overlaps of 138, 13 s.** Core crop (`Claude outputs/audit_R26/core_v2_run4.png`) now reads like the hand sheet: shaft strings 8'-3" | 11'-9" inside the shafts, 4'-6" | 13'-7½" | 8½" beside the core, pilaster 1'-2" | 8" | 1'-2" + 13'-2¾". Headless runner: `Claude outputs/audit_R26/run_v2.py` (RUN=n; clears the test view, runs, exports PNG; MCP call times out at 60 s but the run completes and writes `dimsoffit_v2_L3N_runN.md`).
  - Fixed during bring-up: a string anchored to a wall face has its dim line END at that wall → only the trimmed interior of the dim line (END_TRIM 0.6 ft) is tested against obstacles; text over a member/opening and text clipped by the crop are soft penalties, not rejections; `d.Id` must be captured before commit (Revit may delete dims at commit); rect prefilters cut runtime from 186 s to 13 s.
- **2026-10-02 — Runs 5–10 (layout tuning) and Dim Check marks.** Run 5: 135 planned → 105 placed / 30 review / 2 overlaps, 11.7 s (beam side flush with a wall → width-only string; core strings kept inside the core). Three layout changes then took it to **run 10: 114 placed / 21 review / 2 estimated overlaps (of 161 boxes), 20 s; Dim Check on the result: 155/217 edges located (71%)**, all 16 beam ends located:
  - "crosses another string" is now a **soft** penalty (`W_CROSS` 1.5) — perpendicular dim lines cross on every hand sheet; text collisions stay hard.
  - Strings with no home side (core/shaft openings) get **mid-span candidates through their own opening** (`W_INSIDE` 1.0), which is where the hand sheet puts the shaft widths.
  - **Unblock pass** (`Layout._unblock`): a string that still has no spot lifts one nearby placed string, places itself, re-places the neighbour, keeping the cheapest total. Lifting *pairs* of neighbours and re-trying "poor" (cost > 8) placements were tried (run 9) and switched off: 60 s and 7 real overlaps vs 2, because moved neighbours land where the text model is wrong. CFG `UNBLOCK_PAIRS` / `UNBLOCK_COST` keep them available.
  - Coverage: a witness line standing on a wall-face plane now grades WALL whatever element it references (`mcc_coverage._wall_stations`) — matches how the hand sheets dimension elevator openings off the shaft wall.
  - **Dim Check marks** (Adolfo: the old link "just zooms out to full extents"): each unlocated edge gets a red detail line along the edge plus a small red "DIM?" note 9" off it (view-specific graphic overrides, smallest TextNoteType ≥ 1/16", nothing added to the model); the report link zooms to the line; rerun refreshes, answering "No" clears. `run_v2.py` clears marks before each run.
  - Remaining review (21): 12 "over a wall" (short wall-anchored runs and beam widths whose only lanes sit on the core walls), 5 outside crop, 4 text collisions. Images: `core_v2_run5.png`, `core_v2_run5_marks.png`, `core_v2_run7.png` (same as run 10), `core_v2_run11.png`.
  - **Run 11 — one text rule for layout and creation.** `Layout.text_plan()` decides every segment's text spot (on the line, or pulled past the nearer end with a leader, stacking outward) and `apply_text_plan()` sets `TextPosition` to exactly that; `pull_short_text` is no longer used by v2 (it was also being handed the dim direction and the outward vector swapped). Text side is Revit's rule (above the line in reading orientation, TextPosition ≈ the text's base, lift 0.2 × text size — measured on created dims). Result: **113 placed / 22 review / 0 actual text overlaps of 160**, 24 s. `core_v2_run11.png`.
  - **Run 12 — pull side (Adolfo):** pulled-out text goes on the far side of the dim line from the element being dimensioned, never in the gap between them (a line running through its own span keeps Revit's text side). 114 placed / 21 review / 0 overlaps of 162, 20 s. `core_v2_run12.png`.
  - **Run 13 — leaders, alignment, crossings (Adolfo):** each pulled text now carries its leader (segment midpoint on the dim line → text) in the layout model: text on another string's leader and a leader through another text are hard rejections; a dim line or leader crossing another leader costs `W_CROSS_LEADER` 3. Pulled texts of one string share an inner edge (aligned column) and a string with pulled text gets extra candidates that line its first pulled row up with a neighbour's (`W_ALIGN` 0.5, same family, within 30 ft along). `W_CROSS` raised to 2.5 so two crossings cost more than switching to the other side (`W_SIDE` 4) — the "dimension near elements on opposite sides" rule. 114 placed / 21 review / 0 overlaps, 24 s. `core_v2_run13.png`.
  - **Runs 14–15 — plan de-dup across grids and by containment.** `mcc_place.dedupe` now compares witness lines in the family frame (strings anchored to different grids of one family used to look different) and drops a string whose witness lines all appear, consecutively, inside a longer string with an overlapping span (an opening edge that is also a beam face: `edge | 10` inside `side | side | 10`). 11 more strings dropped on L3 North: **123 planned / 102 placed / 21 review / 0 overlaps**, Dim Check 156/217 located (71%) — same coverage with fewer dims. Checked the rotated NE wing (`ne_v2_run15.png`): dims follow the rotated grid families, the doubled 13'-5½" / 3'-9" strings are gone.
- **2026-10-02 — L7 (milestone 3 start).** Test view `ZZ CLAUDE TEST - L7 (auto-dim)` = duplicate-with-detailing of `LEVEL 7 TO 25 - SOFFIT PLAN` (sheet 1.7.0, 93 hand dims) with the dims deleted; `run_v2.py` takes `VIEW_NAME`/`TAG`. Hand sheet grades only 25% located by Dim Check — its west sawtooth is one running chain of slab edges anchored at the slab, plus grid-to-grid overalls (86'-0", 176'-6"), and openings are labelled "R.O.". Four things learned from it, all now in v2:
  - **Annotation crop, not model crop, decides where a dim may go** (`mcc_coverage.annotation_crop_poly`). L7's annotation crop is 18 ft wider than the model crop on the west; the layout had been rejecting everything in that margin as "outside crop" (17 of 29 review items). L7: 82 → 99 placed.
  - **Margin lanes** (`String.free`, `Planner.free_end`, `Layout.candidates` "margin"): a run whose edge ends at open margin (nothing within 6 ft past the end, either side) gets lanes in that margin past the end with no outside-span cost (`W_MARGIN` −0.5, `MARGIN_IN` 2.5 ft), and extra candidates lined up with any same-family string already in that margin — the hand sheet's column of dims beside the sawtooth.
  - **Existing annotation is an obstacle** (`Layout._existing_annotations`): text notes, tags, generic annotations, keynotes, spot dims in the view (bounding boxes ≤ 60 ft) — text over them or a dim line / leader through them is rejected. Fixes dims laid over section tags and the "7½\" PT SLAB" note.
  - **`W_INSIDE` 1.0 → 3.5**: a core/shaft string goes through its own opening only when the lanes outside are taken (hand sheets on both floors put the shaft lengths beside the shaft, widths above/below it).
  - **Merge through a gridline** (`Planner.merge_through_anchor`): two locate strings off the same grid, one each side, with overlapping spans become `edge | grid | edge` (3'-4½" | 1'-7½" at every sawtooth step, 9 on L7, 6 on L3N).
  - Result **L7 run 4: 102 planned / 85 placed / 17 review (7 over a note/tag) / 0 overlaps, 23 s; Dim Check 106/172 located (61%)** vs hand 25%. **L3N run 16: 117 / 103 / 14 / 0, 17 s; 162/217 located (74%).** Images `L7_core_hand.png`, `L7_core_auto4.png`, `L7_west_hand.png`, `L7_west_auto4.png`, `core_v2_run16.png`.
  - Not done from the L7 hand sheet: grid-to-grid overall strings (→ Dim Grids, decided 2026-10-05); "R.O." suffix (off by default, decided 2026-10-05); the running perimeter chain style.
  - **Open (next):** the 12 "over a wall" strings (allow a wall-anchored width string to sit on its own wall, or pull the lane inward); the 13 plan-NONE edges (stubs, angled beam faces); a 1" void edge next to a wall should count as flush; feature refinements listed under Stage 1.
- **2026-10-05 — Paper-unit spacing + stacked dims (runs L3N 17, L7 5).** From the hand-dim measurements
  (`other-projects-study.md`): `mcc_layout.CFG` now sets spacing on paper — `LANE_STEP_IN` 3/16", `FIRST_GAP_IN`
  1/4", `STATION_GAP_IN` 0.16" — converted with the view scale in `Layout.__init__`; `mcc_strings` `OPEN_OFFSET_IN`
  1/4" and `LANE_STEP_IN` likewise (`Planner.__init__`). New `Planner.stack_from_anchor()` (after dedupe/merge):
  each locate chain of an opening / bump / notch / beam with an anchor end gets one dim per edge from the
  anchor nearest its object (`String.stack = (group, rank, size)`, rank 0 shortest), the chain becomes role
  `check`; stacked dims identical to an existing locate string are skipped. Layout places a stack in rank order;
  `candidates()` offers the next row one/two `LANE_STEP`s further out from the previous row (`W_STACK` −1.0).
  - L3N run 17: **179 planned (146 locate, 33 check) / 154 placed / 25 review / 0 overlaps of 198, 29 s**
    (run 16: 117 / 103 / 14). 62 stacked dims, 30 chains → checks. Core: 13'-2 3/4" | 14'-4 3/4" | 15'-0 3/4" |
    16'-2 3/4" stack beside the core reads like the hand sheet. `core_v2_run17.png` vs `core_v2_run16_same_crop.png`.
  - L7 run 5: **224 planned (154 / 70) / 182 placed / 42 review / 0 overlaps of 249, 41 s** (run 4: 102 / 85 / 17;
    hand sheet 93 dims). 122 stacked, 60 chains → checks — dense; Adolfo deletes extras on review (decision).
  - Toggle: `mcc_strings.CFG["STACK"]`, `["STACK_KINDS"]` (beams included — earlier decision was width + one anchor; confirm).
- **2026-10-05 — Adolfo's review of run 17 → runs L3N 18, L7 6.** (1) **Beams back to width + one anchor**
  (`STACK_KINDS` = opening, bump, notch). (2) **Always the closest gridline:** `do_opening` now uses a grid running
  *through* an opening when it is closer to the edges than any outside anchor → `edges | grid | edges` (the
  L3N shaft was dimensioned 36'-2½" / 53'-11½" off grid 7 with grid 8 1'-1½" inside it); `stack_from_anchor`
  takes an anchor from anywhere in the string (grid) and picks the one nearest its object; `CONSISTENCY` 1.25 → 1.0
  (no switching to a farther "neighbours'" grid). (3) **No doubled dims:** the chain kept as a check drops its
  anchor (its first segment repeated stack 1 — 36'-2½" ×2, 13'-2¾" ×2); a check identical to another string is
  dropped; the separate "opening far edge" dim is off while openings stack (stack 2 is the same dim).
  - L3N run 18: **168 planned (141 / 27) / 151 placed / 17 review / 0 overlaps of 178, 17 s.** `core_v2_run18.png`.
  - L7 run 6: **223 planned (154 / 69) / 196 placed / 27 review / 0 overlaps of 214, 19 s.**
- **2026-10-05 — run L3N 19: beams always tie to a grid.** A beam side lying on a wall face (wall below,
  dashed) got the width only ("beam width (side on wall)") — the wall isn't dimensioned on the soffit plan, so
  the beam was never located (Adolfo: beam 14184522 at grid 2). `do_beam` drops that case: grid through the
  beam → `side | grid | side`, else width + one anchor, **grids only** (`anchor(..., walls=False)`).
  Now `side | 2'-5¾" | 2 | 1'-6" | side`. 169 / 151 placed / 18 review / 0 overlaps, 17 s. `beam_v2_run19.png`.
- **2026-10-05 — soffit elements only + 30 ft tape (runs L3N 20–22, L7 7–9).**
  - **Dims go TO slab edges, beams, openings, CJs only — never to walls, curbs, columns** (shown on other plans).
    Kalae curbs are *walls* ("8.5 x 4 CURB"): L3N had 41 wall-face refs (12 to curbs), L7 35. `anchor()`
    now allows a wall face only when **no grid of the family is within `LOC_MAX` on either side**
    (`CFG["WALL_ANCHOR_IF_NO_GRID"]`); stacked dims and chain checks never target a wall face. Now 0 wall refs.
  - **`LOC_MAX` 20 → 30 ft, `MAX_DIST` 40 → 30 ft** — the field crew's tape. A stack whose longest dim would pass
    30 ft isn't stacked (the chain is measured piece by piece, every piece < 30 ft). Longest single segment now
    28.7 ft (L3N) / 28.4 ft (L7).
  - L3N run 22: **162 (135 / 27) / 143 placed / 19 review / 1 overlap of 172, 17 s.**
    L7 run 9: **215 (148 / 67) / 191 placed / 24 review / 0 overlaps of 207, 17 s.**
- **2026-10-05 — slab edges on column faces skipped (runs L3N 23, L7 10).** Dims that looked like column dims
  were slab edges where a floor (7 1/2" PT SLAB, FILL 9 3/4") is cut around a column — the edge lies on the
  column face. Treated like wall-flush edges: `do_run` and void edges skip an edge `flush()` with a column;
  `Planner.on_column()` skips a bump / notch / step with any edge on a column face. L3N: 16 edges + 1 notch
  skipped, L7: 3. **FILL floors are soffit** (Adolfo: unusual modeling, keep dimensioning them).
  L3N run 23: **150 (124 / 26) / 132 placed / 18 review / 1 overlap, 18 s**; L7 run 10: **213 / 189 / 24 / 0, 18 s.**
- **2026-10-05 — beam dims at ends, aligned dims, "a dimension at each end" (runs L3N 24–25, L7 11–12).**
  - **Beam width strings sit at a beam end** (`do_beam`: `prefer` 2 ft inside the free end, else the low end;
    `outward` toward that end), not mid-span.
  - **Aligned dims** (`mcc_layout`): `candidates()` adds a "collinear" spot on the same line as any placed parallel
    dim of the family within `COLLINEAR_REACH` 4 ft (`W_COLLINEAR` −0.75). Dims sharing a line: L3N 39 / 128,
    L7 107 / 189 (run 24 / 11).
  - **A dimension at each end for ease of reading** (Adolfo's rule): `Planner.end_parts()` — CJs, runs and beams
    longer than `TURN_BOTH` (20 ft) get one string per end, each with its own half span. Runs were *meant* to do this
    already but `dedupe` folded the two (same witness lines, overlapping span) — the halves keep them apart.
    L3N: 12 CJs, 12 beams, 4 runs now dimensioned at both ends; L7: 7 runs. `ne_v2_run25.png` (CJ 6'-10" both ends).
  - L3N run 25: **182 (156 / 26) / 149 placed / 33 review / 1 overlap, 23 s**; L7 run 12: **220 / 196 / 24 / 0, 21 s.**
- **2026-10-05 — stack order: longest furthest from the element (runs L3N 26–29, L7 13–16).** Adolfo's rule
  applies to *any* rows standing side by side, not only one stack group (his example: overall `2'-3½"` from a void
  edge sat inside the beam chain `1'-0" | … | 1'-3½"` at grid 11 / A). Three parts in `mcc_layout`:
  - `evaluate()`: `W_ORDER` 3.0 penalty when a row would sit nearer the element than a shorter overlapping parallel
    neighbour (or further than a longer one), within 1.6 lanes; equal lengths → the chain (more refs) inside, the
    overall outside. `Placed.side` / `Layout.elem_side()` say which way the element lies (0 = line inside its span).
  - `_order_stacks()` (end of `run()`): groups rows of one family, same element side, overlapping, ≤ 1.5 lanes apart;
    hands their stations out again shortest-nearest; if that breaks a hard rule (the corner chain's text hit the
    `1'-3⅜"` text), keeps the shortest row and pushes each longer row out past the previous one (1–2 lanes).
  - Report line "Stacks reordered shortest-nearest". `corner_v2_run29.png`.
  - L3N run 29: 182 / 149 placed / 33 review / 1 overlap, 24 s (4 stacks reordered); L7 run 16: 220 / 196 / 24 / 0,
    22 s (7). Read-only check before the push-out step: 6 of 24 neighbouring pairs out of order on L3N, 4 of 29 on L7
    — some are unrelated rows (a small chain check beside a long locate dim), not true stacks.
- **2026-10-05 — Adolfo's cleaned-up opening → no-go openings, joined strings, edge clearance (runs L3N 30–35,
  L7 17–19).** His fix of the L3N opening by the core (8'-3" | 11'-9" above it, 9'-3⅞" | 8'-4⅛" through the grid
  on its right, 17'-8" outside, the void's 8'-9" off to its own element) gave these rules:
  - **Openings are no-go zones** for dim lines, text and leaders — including the opening's own dims. Bug found:
    opening obstacles carry the slab's element id, so every slab string skipped them (`o.eid in s.owners`); and
    `mcc_model.Obst` now keeps the opening's true outline (`raw`) — the inflated convex hull of an L-shaped
    opening (slab 14169070, 7-vertex loop) covered solid slab beside the core wall. `_box_poly_overlap()` for
    text vs an n-vertex outline (`_polys_overlap` assumes 4 corners). Shaft / core sizes can no longer sit inside
    the shaft (earlier hand-sheet choice, run 10) — they go outside the core walls or to review.
  - **Joined strings:** `_join_collinear()` (end of `run()`, before `_order_stacks`) merges two placed dims of the
    **same feature** on one line, end to end on a shared witness line, into one string; `candidates()` offers that
    line with `W_JOIN` −1.5 (reach ×2). Same-feature only — joining across features dragged the void's 8'-9" to
    the opening. `stack_from_anchor` ranks targets per side of a mid-string grid (dims on opposite sides of the
    grid are end to end, not a stack).
  - **Edge clearance:** `Layout._parallel_edges()` — a dim line may not lie within `EDGE_CLEAR_IN` 1/16" (paper)
    of a slab / opening / beam edge running the same way over more than `END_TRIM` (the tool had 8'-3" drawn on
    the opening's top edge).
  - Void-edge strings are placed after the other opening strings (they took the spot beside the opening).
  - L3N run 35: **182 / 137 placed / 42 review / 0 overlaps, 25 s** (review: 17 over a wall, 10 opening, 8 too close);
    L7 run 19: **220 / 174 / 28 / 0, 23 s** (17 text over a note/tag). `opening_v2_run35.png` matches Adolfo's version.
- Next: Adolfo reviews run 35 / 19, the open items above, then Dim Check on the hand sheets (milestone 1 close-out); then milestone 3 (whole view, L7, L4.5).

## Decisions from Adolfo (2026-10-02)
- **Cleanup target:** ≤ 10 dims moved/deleted per sheet is the goal (depends on project size).
- **Lanes:** 2 to 3 stacked rows out from an object, no more.
- **Unplaceable strings:** report list for now; marker in the view to be iterated on later.
- **Pilaster/bump convention confirmed:** one string across the bump faces (run face | bump face | … , e.g. 1'-2" | 8" | 1'-2"), one anchor dim to the bump face in the other direction, the run itself located at each corner.
- **Leaders are obstacles:** dim text must not sit on another dim's leader; avoid dim lines crossing leaders of pulled-out text (2026-10-02).
- **Pulled-out text aligned** where several are near each other, for a cleaner look (2026-10-02).
- **Crowded areas:** avoid dim lines crossing; dimension nearby elements on opposite sides instead (2026-10-02).
- **Pulled-out text** sits on the far side of the dim line from the element, not between the line and the element (2026-10-02).
- **Stacked dims from one grid = default locating style** (2026-10-05, after `other-projects-study.md`): each edge point gets its own dim from the grid, stepping outward; chained strings stay as double checks; the user deletes extras on review. Not built yet — v2's planner only makes chains.
- **"R.O." off by default** (2026-10-05); the user adds it to openings themselves.
- **Grid-to-grid + overall strings belong to `Dim Grids`**, not Dim Soffit v2 (2026-10-05).
- **Dim Check must show where** the unlocated edge is in the view, not just link to the element (2026-10-02) — done with the DIM? marks.

## Why v1 can't get there
v1 (`dim-soffit-architecture.md`) decides three things at once, per pass, per edge: what to dimension, how to group it, where to put it. Nothing sees the whole plan. Result on L3 North: the same pilaster gets four separate grid dims, neighbours pick different grids, strings run through the core, text collides. Each rule added to fix one symptom fights another. Coverage went up while the sheet got messier — the metric doesn't measure "reads well".

## v2: three stages, each with a checkable output
```
PlanModel (keep) → 1 FEATURES → 2 STRING PLAN → 3 LAYOUT → create dims (one transaction)
                       ↓              ↓               ↓
                  feature list    coverage report   collision report + review list
```
Nothing is drawn until the plan is complete and checked. Each stage's output is a plain data structure that can be dumped, compared with the hand sheet and reviewed with Adolfo before the next stage is built.

### Stage 1 — Features (`lib/mcc_features.py`)
Input: `PlanModel` (grids, slabs with join cuts removed, members, CJs, crop). Output: `Feature` objects, each owning its edges, with a type that decides its dimensioning pattern:
- **Run** — a straight perimeter slab edge between two turns; long runs know their corners.
- **Bump / Notch / Step** — a short chain of perimeter edges that leaves a run and comes back (pilaster, notch at a column, soffit step). Found by walking each outline loop: perpendicular turn, short leg(s), return turn. Owns the whole chain. (Bump = outward, notch = inward, from the loop's winding.)
- **Corner** — two runs meeting (dimension at every turn, rule 3).
- **Opening**, classified: `core` (walls facing at least all-but-one side within 25 ft — elevator/stair cores; tested against each wall's whole outline because joined walls' side faces come back chopped), `shaft` (a Shaft Opening element about the size of the hole), `penetration` (≤ 2 ft), `void` (> 20 ft; dimensioned edge by edge), `plain`. Small **stepped** openings (the 3'x3'-8" pilaster hole, 8 edges) stay `plain`/`shaft` with `stepped=True` so they get one string per direction with every step in it — not per-edge dims.
- **Beam** (sides, free ends; ends framed into members marked located), **CJ line**.
- Features carry: owner element ids, edges grouped by grid family, extent, whether inside the crop.
Checks: every slab edge belongs to exactly one feature (passes on L3 North); feature counts vs. a hand count on the core.

### Stage 2 — String plan (`lib/mcc_strings.py`)
Turns features into **strings** (`String(Intent)`: ordered witness references + grid family/frame + extent + preferred station/side + role + feature), using the agreed rules (`dimensioning-rules.md`):
- **Anchor per side**: for each feature and grid family, the nearest grid or facing wall face on each side, ≤ 20 ft (LOC_MAX). One string per direction: `anchor | edge … edge | anchor`. An outer edge lying on a wall face is itself the anchor on that side (`edge@wall`). One-sided → `anchor | edges`, plus `anchor | far edge` only when the opening is wider than 6 ft. Voids (> 20 ft) → each edge locally from its nearest anchor.
- **Runs**: `anchor | edge` 2 ft in from the corner, both ends when over 20 ft. **Bump/notch**: `anchor | leg | leg | anchor` across + `anchor | top`. **Step**: `anchor | step face` + a `jog check` (run face | run face). **Beam**: width + nearest anchor (`anchor | side | side`), or `side | grid | side` when centred, width only when a side is flush with a wall; free ends `anchor | end`. **CJ**: `anchor | CJ`.
- **Anchor consistency**: features that overlap in station along the same family prefer the same grid when the alternative is within 1.25× the distance.
- **Located-by-member** (no string): edges on a grid, flush with a wall/beam face, beam ends framed into a member.
- **Roles**: `locate` vs `check` (jog checks, width-only strings). Plan-level de-dup via `mcc_place.dedupe`.
- **Coverage on paper**: `Planner.coverage_rows()` feeds `mcc_coverage.grade()` with the planned strings, so the plan is scored exactly like real dims before anything is drawn.
Output doubles as the **Dim Check** button: run the plan against an existing hand-dimensioned view's dims and list (and mark in the view) edges that aren't located.

### Stage 3 — Layout (`lib/mcc_layout.py`)
Places all strings of a view together, text-aware:
- **Candidates** per string: side (home side first — away from the partner string; alternate side allowed) × lane (0–2, LANE_STEP 1.75 ft; 3 only as a last resort) × slide (±4 ft in 1 ft steps); strings with no home side also get mid-span candidates through their own span. Candidates are evaluated in base-cost order and the search stops once no cheaper candidate remains.
- **Text model**: segment values are known from the witness offsets → format as feet-inches → text box = `mcc_place.text_width` × the type's text size × view scale; segments too short for their text get a pulled-out box past the nearer end of the string.
- **Hard**: dim line outside the crop, over a parallel grid line (GRID_CLEAR 1.5 ft), its trimmed interior crossing a column/wall/opening, too close to an overlapping same-direction string (STATION_GAP 1.6 ft), text overlapping another text or line. **Soft**: crossing another string, over a beam, text over any obstacle, text clipped by the crop, lanes, off-home side, slide, outside the home span, through its own span.
- **Order**: `locate` strings (runs → bumps/steps → openings → beams → CJs) then `check`; last-resort lane 3 for leftovers; unblock pass (lift one neighbour) for what is still unplaced; 2 improvement passes re-placing the worst fifth.
- **Review list**: unplaced strings with the constraint that blocked them most often. **Create** in one transaction through the warning handler (`transaction_with_log`); then `actual_overlaps()` counts overlapping text boxes from the created dims' `TextPosition` — the per-run "mess" metric.

### Reused from v1
`PlanModel` (recognize), join-cut filter, crop helpers, `dedupe`, `transaction_with_log`, text pull-out, CJ references, journal/rerun cleanup, coverage check (`mcc_coverage.py`), Score Dims, the headless runner and the image-crop comparison. `mcc_rules.py` and `Placer.find_station` are replaced. v1 stays in WIP as "Dim Soffit (v1)" until v2 beats it on L3 North and L7.

## Milestones (each ends with a review against the hand sheets)
1. **Features + plan, no drawing.** Dump the feature list and string plan for L3 North; compare the core and the pilaster with sheet 1.3.0; agree grouping. Dim Check button working on hand sheets. *(Features, plan and Dim Check button written 2026-10-02; Dim Check marks added; not yet run on the hand sheets.)*
2. **Layout on the L3 North core crop.** Same image comparison as this week; target: no overlapping text, no strings through the core, ≤ 2 lanes. *(Runs 4–11 on 2026-10-02 — 0 text overlaps on run 11; open items above.)*
3. **Whole L3 North**, then L7 (orthogonal) and L4.5 (rotated wing). Measure: coverage, actual-overlap metric, and a cleanup count (dims a detailer moved/deleted) on each.
4. L2/L4 and a detailer's review; retire v1.

## Measures of done (per view)
- Coverage: every crop-interior edge located (grid/wall) or located-by-member; unlocatable edges listed.
- Actual overlaps (from Revit bounding boxes): 0 text-on-text, 0 text-on-dim-line.
- Cleanup count ≤ 10 (scaled to project size).
