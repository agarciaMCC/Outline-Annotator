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
- **2026-10-05 — shaft sizes inside, same-element order (runs L3N 36, L7 20).**
  - **Inside a shaft "if absolutely necessary", overall size only** (Adolfo): in `evaluate()`, a string whose refs
    are all opening edges (a size string) of a shaft/core opening may sit inside *its own* opening at `W_IN_SHAFT` 8.0;
    every other dim stays out (locating dims never inside).
  - **2'-0" / 3'-0 1/8" (opening core#127, the small opening in the top core wall) broke the stack rule** because the
    two rows ended up ~5 ft apart on opposite sides of the core wall; the order check only looked at rows within
    1.6 lanes. Rows of the **same feature** are now ordered at any distance (`evaluate` W_ORDER) and grouped up to
    4× the gap in `_order_stacks`. Now 2'-0" (size) is nearest, 3'-0 1/8" outside. `core_v2_run36.png`.
  - **Missing dims on the shaft at the core's lower right:** it is NOT a slab opening — the slab outline runs around
    it (left edge = run#7 at x 229.5, core wall on its right, beam#268 below), so it is read as slab edges, each
    located off a grid (3'-4½" from 7, 7'-7" from CC). No size string exists for it; its width (4'-5") used to come
    from the left edge being dimensioned to the core wall, which the soffit-only rule removed (grid 7 is near).
    Open: treat a slab pocket closed by walls as a shaft and give it an overall size.
  - L3N run 36: 182 / 137 / 42 / 0 overlaps, 26 s; L7 run 20: 220 / 174 / 28 / 0, 24 s.
- **2026-10-05 — shafts the slab wraps around (runs L3N 37–39, L7 21–22).** `Planner.do_shaft_pockets()`: a slab
  outer edge (≥ `SHAFT_MIN_EDGE` 2 ft, not on a wall / column / beam) whose open side faces a parallel wall face
  across open space (no slab sampled at ¼, ½, ¾ of the gap; gap ≤ `SHAFT_MAX` 15 ft; the wall face covers ≥ half
  the edge) gets an overall-size string `edge | wall face`, role `check`, owned by that edge's run/corner feature —
  the one case a dim goes TO a wall (Adolfo approved). The pocket rectangle is added to `model.obstacles` as an
  "opening" (`Obst(eid=-1, raw=rect)`), so only the pocket's own size strings (`String.own_voids`) may sit inside;
  locating dims move out. Layout: home-less strings may now try spots along their whole span, not only ±4 ft of
  the middle. L3N core shaft (slab 14169070 edges x 229.52 / y 69.61, core walls 14217916 / 14113930): **7'-9½" ×
  12'-1"**, locating dims (3'-4½" from 7, 7'-7" | 4'-6" from CC) outside it. `core_v2_run39.png`.
  - L3N run 39: **184 (156 / 28) / 139 placed / 42 review / 0 overlaps, 30 s**; L7 run 22: 220 / 174 / 28 / 0, 24 s
    (no such pockets on L7).
- **2026-10-05 — Adolfo's cleaned-up examples → beams, joins, angled openings (runs L3N 40–45, L7 23–25).**
  - **Beams** (`do_beam`): width strings sit just *past* an end (`OPEN_OFFSET` beyond it, span extended 8 ft into the
    open), the free end if one; > `TURN_BOTH` both ends; > `BEAM_MID_OVER` 40 ft also intermediate width strings
    across the beam about every `BEAM_MID_EVERY` 35 ft, each searching its own stretch (`String.intermediate`) — a
    reading aid: one with no room (a beam under a wall its whole length) is left out, not reviewed
    (`Layout.notes_optional`, 13 on L3N). `String.beam_width`. Layout: `W_BEAM` 1 → 4 (stay off beams),
    `W_OWN_BEAM` 4 when an end width dim crosses its own beam; edge clearance now includes all four sides of a beam.
  - **Size joins its locating dim** (`candidates`: same-feature end-to-end spot at any distance, `W_JOIN_SAME` −6) and
    **one side per direction** (`W_SPLIT` 3 when the element already has dims of that family on its other side).
    An opening's dims prefer standing beyond its sides (`W_OWN_SPAN` 2.5); a dim line continuing an edge's line from
    its end costs `W_EDGE_LINE` 3 (the 7'-7 1/2" sat on the opening's edge line, so 15'-7" couldn't join).
    `W_IN_SHAFT` 8 → 20 (8 lost to the join bonus). L3N 17'-9" opening: `7'-7 1/2" | 15'-7"` one chain + 23'-2 1/2"
    outside — on the left (Adolfo's version had them right). `opening17_v2_run45.png`.
  - **Grouping:** a string off the same gridline (same family) as a placed one, overlapping it, gets spots one lane
    beside it (`W_GROUP` −0.5). Beam width 3'-9" | 3'-9" now stacks outside the 6" | 6" past the slab edge.
    `beams_v2_run45.png`.
  - **Angled openings** (`do_opening`): own grid set = dominant family + the one square to it; edges in another family
    shorter than `MINOR_EDGE` 3 ft get no straight-grid dims while an own-set grid is within `LOC_MAX` (Adolfo: those
    are allowed only when no aligned grid is near). L3N shaft#115: the 12'-8 1/2" / 10'-2 1/2" went; everything stacks
    outside along the angled grids. `angled_v2_run44.png`.
  - Not done: "prefer spots where text fits without a leader" — whether a segment's text is pulled depends on the
    segment length, not on where the string sits, so position can't change it.
  - L3N run 45: **208 (180 / 28) / 148 placed / 41 review / 0 overlaps, 38 s**; L7 run 25: **220 / 168 / 29 / 0, 31 s.**
- **2026-10-05 — Adolfo's card review of run 45's 42 review items (28 right calls, 14 wrong) → runs L3N 46–47, L7 26.**
  Review page: `Claude outputs/audit_R26/review_page/` (`review_items.py` dumps the review list with each string's
  intended line, `review_export.py` exports the ZZ view with two green calibration crosses inside the model crop,
  `review_crops.py` maps plan → pixels from them and draws each card's line in violet). Answers live in the
  artifact's `verdicts` collection. What changed:
  - `mcc_model`: **lines from the view's cut plane skipped** — a ramp floor (9" MS SLAB 14220571, bottom 111.4 ft)
    crossing the cut plane (115.67) gives soffit-loop edges whose reference is a Face, not an Edge (items 1–2);
    **holes filled by other floors dropped** (`_drop_filled_holes`: ≥ 80% of a sample grid covered by a floor shown
    in the view at the slab's height ±1 ft — the L4 ramp piece counts — or a wall or beam; 17 on L3N incl. the PT
    slab's 33 × 113 ft hole holding the ramp, items 4 / 38 / 39, and the 14.6 × 2.9 ft "opening" by the core that is
    a wall + beam cut, items 6–11); **curb / CMU walls ignored** by every wall rule (`model.soft_walls`, type name
    contains CURB or CMU; 13 on L3N; items 22 / 24 / 26).
  - `mcc_strings`: **small openings** (< `SMALL_OPEN` 4 ft across the family) get only the near edge off the grid
    plus the size (items 16–18); **voids in a wall line skipped** (centroid within 1 ft of a wall; items 19–21);
    **beams capped by walls at both ends with a side in the wall line skipped** — core-wall plans cover them
    (items 33–34; 4 on L3N); **core / shaft openings anchor to the core wall face** even with a grid near
    (`anchor(..., force_walls=True)`, item 14).
  - `mcc_layout`: **wider search before review** — unplaced strings retry with `SLIDE_MAX` ×3 and two more lanes,
    both sides (items 3, 12, 23, 30, 36, 37, 41; `notes_harder`: 5 on L3N, 10 on L7).
  - Left as is: hard-to-reach grids (8–10, "some nuance"), item 42 (enlarged view), outside-crop beams (28, 29).
  - L3N run 47: **181 (153 / 28) / 167 placed / 2 review (both outside crop) / 0 overlaps, 22 s.**
    L7 run 26: **167 (99 / 68) / 141 placed / 3 review / 0 overlaps, 16 s.**
- **2026-10-05 — run L3N 48: one halfway beam dim.** Adolfo: "every ~35 ft" was a little much — beams over
  `BEAM_MID_OVER` 40 ft now get ONE intermediate width dim, halfway between the end dims (`BEAM_MID_EVERY` removed).
  169 planned / 156 placed / 2 review (outside crop) / 0 overlaps, 18 s.
- **2026-10-05 — run L3N 49: beams continuing in line.** Adolfo: a band's end width dim sat mid-band by the CJ. The band is
  two beams end to end (14895567, 16 ft, with the 24x30 column, + 14181407); the joint counted as an end, so 14181407's
  "end" dim went at the joint and 14895567's real-end dim was deduped as its duplicate (same two sides). `do_beam`
  now checks each end for a beam continuing in line with the same side offsets (`continues()`) — no width dim at
  such a joint; the piece's other end gets it. `beamjoint_v2_run49.png`.
- **2026-10-05 — run L3N 50: CJs on a beam side skipped.** The third "3'-9"" at that band end was CJ 274 to grid B,
  3'-8 15/16" (shown rounded) — the CJ runs along the beam side 1/16" away, so the beam width already locates it.
  `do_cj` skips a CJ `flush()` with a beam side or a slab edge (7 on L3N). 164 / 151 placed / 2 review / 0 overlaps.
  `beamjoint_v2_run50.png`.
- **2026-10-05 — learning from Adolfo's hand edits of the L3N test view (runs L3N 51–52, L7 27).** `snapshot_dims.py`
  records every dim in a view (refs, line, segments, text), tagged with the planner string it came from (matched by
  referenced elements + values); `compare_snapshots.py` classifies each change against the element's extent.
  Run 50 vs his edit: 55 left as is, 60 edited (21 CJ dims moved ~1/4" past the CJ's END; openings moved out from
  ~1/16" to ~3/8"; beam end widths pulled in to ~1/4"), 32 deleted, 30 added (`compare_L3N_edits.json`).
  His explanations: overall beam widths added by mistake; small openings / the notch by the core are too cluttered —
  enlarged plan; core-wall dims of edges a grid already locates are doubles; jog checks stay; "doubled" run / CJ dims
  were the two end dims of 20–40 ft edges landing 8–18 ft apart; two beam end dims dropped for bad model geometry.
  Changes: `TURN_BOTH` 20 → 40 (`BEAM_BOTH` 20 keeps beams); `do_cj` places CJ dims just past an end
  (`BEAM_END_GAP_IN` 1/4", end with open slab past it; both ends > 40 ft) and CJs no longer merge through a grid;
  `Planner.cluttered_small()` sets small openings / notches with ≥ 2 others within `CLUTTER_R` 8 ft aside
  "for an enlarged plan" (report section); `drop_wall_where_grid()`; layout `MIN_GAP_IN` 1/4": an opening's dim
  never closer to it (hard). Tried first row 3/8" (run 51): moved 21 dims he had left alone — back to 1/4".
  Agreement with his version (within 3/16" of his spot): left-as-is 55 → 43 of 55, moved 16 → 20 of 60, added 1 → 3
  of 30. L3N run 52: 148 / 141 placed / 2 review / 0 overlaps; L7 run 27: 160 / 138 / 2 / 0.
- **2026-10-06 — agents join the loop; runs L3N 53–54.** Two read-only agents in `.claude/agents/`: `edit-diff-analyst`
  (groups Adolfo's hand edits by the rule they point at; first report `Claude outputs/audit_R26/analyst_L3N_round1.md`:
  of his 122 changes 47 were covered by the 2026-10-05 rules, 34 by proposed ones, 17 unexplained — 8 open questions
  for Adolfo at its end) and `revit-compat-reviewer` (IronPython 2.7 / Revit 2023+2026 check of a diff before a run).
  `agree_with_edits.py` (CPython) scores a run snapshot against `snapshot_L3N_after_edits.json`: same dim within 3/16"
  / same dim further off / dims he doesn't have / his dims the tool lacks. First two changes from the analyst:
  - **Slots → enlarged plan** (`cluttered_small`, `SLOT_MAX` 1 ft): an opening narrower than 1 ft one way is clutter with
    just ONE other small one near it, core/shaft-labelled or not (the pair of 2'-0" × 6" holes in the L3N core wall he
    deleted, core#125/#126, 22 ft from the other clutter). Tried "size alone, ignore the core/shaft label" first (run 53):
    it also sent the 3' × 3'-8" pilaster hole (shaft#119) to the enlarged plan, which he had kept — reverted.
  - **Opening gap 1/8" hard, 1/4" preferred** (`MIN_GAP_IN` 0.125, `W_GAP` 2.0 tapering to 0 at `FIRST_GAP`): three
    opening dims he placed himself sit 0.10–0.20" off the edge and he pulled 13'-2¾" in to 0.14" — the hard 1/4" would
    have rejected his own spots. First row still aims at 1/4".
  - L3N run 54: **142 (120 / 22) / 135 placed / 2 review (outside crop) / 0 overlaps, 19 s.** Against his version:
    run 52 → 54: same-dim-within-3/16" 64 → 65, further off 50 → 48, dims he doesn't have 23 → 18, his dims missing 27 → 28.
- **2026-10-06 — Adolfo's answers to the analyst's questions 1–3 → run L3N 55.**
  - **Gap to an opening: "as close as the text allows, not touching when it's really tight; a slight touch in very
    rare cases."** `MIN_GAP_IN` 1/8" → 1/16" hard (same as `EDGE_CLEAR`, a line ON the edge is still rejected); the
    `W_GAP` taper to 1/4" stays, so the first row still aims at 1/4" and comes in only when that buys something.
  - **Angled core (shaft#114 by the L3N core): no gridline parallel to its long sides within 60 ft, and one long side
    lies on the core wall → dimension off that wall; its straight jog off grids 7 / B.** Two changes in `do_opening`:
    (a) a family with no grid within `MAX_DIST` is no longer skipped ("too far from any grid") when an edge of that
    family lies on a wall — the nearest grid of the family, however far, lends its frame and the wall face is the
    anchor (`edge@wall | 4'-10¼" | edge` + the 3'-9¾" check, as Adolfo drew `edge | 3'-9¾" | edge | 4'-10¼" | wall`);
    (b) the "minor edge of an angled opening" skip (run 44) now needs the opening's *dominant* family to have a grid
    within `LOC_MAX`, not just the family square to it — the 1'-6" jog now gets `… | edge | 10'-2½" | 7`.
  - **No "width dim every N ft" on long bands** — "every job is unique". The ONE halfway dim over `BEAM_MID_OVER` stays;
    the analyst's B5 (every ~50 ft) is dropped.
  - L3N run 55: **145 (122 / 23) / 139 placed / 2 review (outside crop) / 0 overlaps, 25 s.** Against his version
    (`agree_with_edits.py`): within 3/16" 65 → 62, further off 48 → 51, dims he doesn't have 18 → 22, his dims missing
    28 → 29 — the angled-shaft dims are now the ones he drew but grouped differently (his one 3-ref chain to the wall
    vs our stack + check; his separate 10'-2½" vs our `grid | 9'-11" | edge | 10'-2½" | 7`), and the key-based score
    counts those as misses. One real loss: the 2'-5½" first row off grid 6 moved 0.28" from his spot (gap relaxation).
    One real gain: the 14'-4" stack row by the core now sits on his line (was 1.74" off).
- **2026-10-06 — "I want the chain as I drew it" (runs L3N 56–57).** An opening located off a wall because no grid of
  that direction is near (`String.keep_chain`, set in `do_opening`'s no-grid fallback) is not split by
  `stack_from_anchor`: `edge | 3'-9¾" | edge | 4'-10¼" | wall` stays one string. Tried for *every* wall-anchored chain
  first (run 56, 9 strings): lost 5 dims of his at the main core openings (7", 3'-3", 5", 17'-8", 8½" | 13'-7½" — he
  keeps the stacks off the core walls there) and gained 1 (his `18'-2" | 8'-1"` chain at (223, 29)) — narrowed to
  the no-grid case. L3N run 57: **144 (122 / 22) / 138 placed / 2 review / 0 overlaps, 20 s**; score unchanged from
  run 55 except 1 fewer dim he doesn't have. Crops: `angled_shaft_v2_run55.png` (stack + check) vs `_run57.png` (chain).
  Image mapping for crops of the FitToPage export: 20.16 px/ft, image centre = model-crop centre (6000 × 5599 px).
  - Open: his `18'-2" | 8'-1"` chain off the core wall at (223, 29) vs the stacks he kept at the other core openings —
    ask what makes that one a chain.
- **2026-10-06 — core openings: grids before walls (runs L3N 58–59).** Adolfo, on the tool's `7'-0⅞"` / `24'-8⅞"`
  off the core wall at the L3N elevator shaft: "there's grids nearby, no need to dimension off the walls; the stacking
  convention isn't followed either (the 24'-8⅞" sat nearer the shaft than the 17'-8"); avoid crossing dim lines of the
  same orientation so dims don't get mistaken". `do_opening` no longer forces wall anchors for core/shaft openings
  (card 14 of 2026-10-05 withdrawn) — `anchor()`'s own rule applies: a wall face only when no grid of the family is
  within `LOC_MAX`. Now `edge | 9'-3⅞" | BB | 8'-4⅛" | edge` + 17'-8" outside, exactly his. Run 58 overshot: the
  1'-5" × 3'-3" hole in the top core wall went 15'-0" off CC / 3'-4" off 6 (he dims it 7" / 5" / 3'-3" off the walls)
  → `CORE_WALL_NEAR` 1 ft: a core/shaft opening with a core wall face that close is dimensioned off that wall.
  L3N run 59: **142 (121 / 21) / 135 placed / 2 review (outside crop) / 0 overlaps, 18 s.** Score: within 3/16" 65,
  further off 48, dims he doesn't have 18, his dims missing 28 — best so far. Crops `core_shaft_v2_run57.png` (before)
  / `_run59.png` (after).
  - Open: his `8½" | 13'-7½"` chain at the elevator shaft (223, 62) comes out as two dims (13'-7½" placed on the
    far side of the core); "either is fine, chained looks cleaner". The same-orientation crossing rule needs a
    definition (witness line of one dim crossing another dim's line of the same direction?) — ask with an example.
- Next: the analyst's remaining groups in its proposed order (B6 one-side/join weights, B7 through-grid far edge, B3/B4 CJ
  rules after Adolfo answers Q2, B2 pocket shafts, B8/B9 slivers, B5/B10 band intermediates after Q3); the 8 open
  questions; a second edit round; then Dim Check on the hand sheets (milestone 1 close-out); then milestone 3 (whole view, L7, L4.5).

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
