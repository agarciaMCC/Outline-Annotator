# Edit-diff analysis — L3N test view, round 1 (run 50 vs Adolfo's hand edits)

Read-only dry run, 2026-10-06. Inputs: `compare_L3N_edits.json`, `snapshot_L3N_before_edits.json` / `_after_edits.json`,
`dimsoffit_v2_L3N_run50.md` / `run52.md`, `docs/dim-soffit-v2-design.md` (Status, 2026-10-05 "learning from Adolfo's hand edits"),
`docs/dimensioning-rules.md`, `MCC.extension/lib/mcc_strings.py`, `mcc_layout.py`.

Run 50 placed 147 dims. Adolfo: **55 left, 60 moved/edited, 32 deleted, 30 added** (122 changes). Scale 1/128 → 1 paper inch = 10.7 ft.

## Totals

| | explained by a rule already built | explained by a rule proposed below | his edit contradicts / stretches a built rule | model geometry (his words) | mistake (his words) | nudge < 0.15 in (noise) | unexplained |
|---|---|---|---|---|---|---|---|
| moved / edited (60) | 30 | 13 | 5 | 2 | – | 8 | 2 |
| deleted (32) | 13 | 13 | – | 3 | – | – | 3 |
| added (30) | 4 | 8 | – | 2 | 4 | – | 12 |
| **all 122** | **47** | **34** | **5** | **7** | **4** | **8** | **17** |

The 2026-10-05 entry already covers 47 of the 122 (TURN_BOTH 20→40, CJ dims past the end, cluttered small openings → enlarged plan,
`drop_wall_where_grid`, `MIN_GAP_IN` 1/4", no CJ merge through a grid, review items the tool reported). Everything below the first
section is what those changes do **not** cover, or where the built reading looks off.

---

## A. Already covered by the rules built on 2026-10-05 (47)

| group | count | ids (examples) | built rule |
|---|---|---|---|
| CJ dims moved off the CJ line to ~1/4" past its end | 15 moved | 20591739/740 (cj#252 4'-6½"), 20591753 (cj#264), 20591766 (cj#302) | `Planner.do_cj` — `BEAM_END_GAP_IN` 1/4", end with open slab past it |
| CJ merged-through-grid string split into singles | 2 added (+1 deleted, below) | 20592713 CJ→FF 18'-0⅜", 20592720 FF→CJ 13'-2 15/16" (cj#264) | CJs no longer `merge_through_anchor` |
| opening / jog dims pushed out from ~1/16" to 1/4"–1/2" | 7 moved | 20591696 (shaft#119 8'-0½", 0.06→0.37 in), 20591697 (core#120 7"), 20591770 (jog check) | `mcc_layout` `MIN_GAP_IN` 1/4" (hard) |
| beam end-width dims pulled in toward the end | 6 moved | 20591721 (beam#232, 0.37→0.14 in), 20591736 (beam#248 0.51→0.13), 20591737 | `do_beam` `BEAM_END_GAP_IN` 1/4" |
| "doubled" run / CJ dims = two end dims of 20–40 ft edges | 4 deleted + 2 survivors slid along | deleted 20591677 (run#176 16'-4"), 20591685 (run#206), 20591749 (cj#260), 20591752 (cj#264); survivors 20591676, 20591684 moved 6–11 ft along | `TURN_BOTH` 20→40 (`end_parts`) |
| core-wall dims of edges a grid already locates | 2 deleted + 1 ref removed | 20591691 (26'-3" edge@wall→wall), 20591692 (24'-8⅞"), 20591800 (wall ref dropped from `wall | 7'-0⅞" | edge | 17'-8" | edge`) | `Planner.drop_wall_where_grid()` |
| notch#0 + penetrations #127/#128 by the core → enlarged plan | 7 deleted | 20591686, 20591801, 20591811 (notch#0); 20591812, 20591785, 20591822 (#127); 20591821 (#128) | `Planner.cluttered_small()` |
| the 2 "needs review (outside crop)" beam widths, placed by hand | 2 added | 20592635 (beam#232 `side | 2'-5¾" | 2 | 1'-6" | side` at y −33.8), 20592623 (beam#233) | reported, not placed — see open question 7 |

Note on the survivors of the TURN_BOTH twins: with one dim per edge the built rule leaves it at the preferred end; he slid 20591676 toward
the middle of the 16'-4" run and 20591684 11 ft the other way (out of the edge's span, 1.03 in). No single position rule fits both — leave.

---

## B. Not covered — grouped by cause, largest first

### B1. Small openings in the core walls were deleted wholesale (6 deleted) — the clutter rule skips "core" kinds
core#125 (2'-0" × 6") and core#126 (6" wide) sit in the top core wall next to notch#0 / penetrations #127–128. He deleted every dim of both:
20591699 (`edge | 4'-7 13/16" | wall`), 20591779 (`2'-0"` chain), 20591795 (`6"`), 20591814 (`7 | 1'-0⅛" | edge`), 20591784 (`6"`), 20591788 (`edge | 3'-4 13/16" | wall`).
`cluttered_small()` (mcc_strings.py line 862) explicitly skips `sub in ("core", "shaft")`, so these two survived run 52 while their
neighbours went to the enlarged plan. His explanation ("small openings by the core are too cluttered — enlarged plan") covers them.
**Proposal:** decide "small" by size, not by sub-kind — any opening under `SMALL_OPEN` 4 ft both ways joins the clutter count, core/shaft
included. (The real core/shaft openings are all > 4 ft, so nothing else changes.) Module: `mcc_strings.Planner.cluttered_small`.

### B2. Pocket shaft at the core's lower right: sizes taken out of the pocket, rows pulled in (4 moved)
20591782 `wall | 12'-1" | edge` (run#6) moved from inside the pocket to beside it (0.86 in → "below 0.25 in"); 20591815 `edge | 7'-9½" | wall`
0.91→0.38 in; 20591816 `edge | 3'-4½" | 7` 0.37→0.16 in; 20591806 `step | 4'-6" | CC | 7'-7" | edge` 1.03→0.78 in. Order stays shortest
nearest; he just wants them tight and outside. The inside spot is allowed at `W_IN_SHAFT` 20 via `String.own_voids`; the outside spot
evidently cost more than 20 or was blocked.
**Proposal:** for a wrapped-around pocket (`do_shaft_pockets`), try the outside lanes with the wider search (`SLIDE_MAX` ×3) before
the inside option, and make inside a last resort for pockets. Module: `mcc_layout.evaluate` (own_pocket branch) / `candidates`.

### B3. Neighbouring parallel CJs: dims at opposite ends, spacing joined to the locate dim (3 moved, 1 added)
- cj#253 and cj#255 run 2 ft apart (14'-2¾" and 16'-1¼" off CC). The tool stacked both dims at the same end (x 177.4 / 175.4). He put
  20591741 at x 160.7 (one end, past it) and 20591743 at x 189.0 (the other end, other side) — one CJ dim at each end, nothing stacked.
- cj#263 and cj#277 (4'-5½" and 7'-5½" off grid 5, 3 ft apart): he added 20592807 `CJ | 3'-0" | CJ` on the same line as 20591751
  (y −25.77 — joined end to end: `5 | 4'-5½" | CJ | 3'-0" | CJ`) and pushed the longer 20591761 outside (0.19→0.49 in). Chain inside,
  longer single outside: the stack-order rule applied to CJs.
**Proposal (do_cj):** (a) two parallel CJs within ~4 ft off the same grid get their dims at opposite ends when both ends are open;
(b) add a `grid | CJ | CJ` chain (role check) for parallel CJs within ~5 ft so the spacing joins the shorter locate dim (`W_JOIN_SAME`
already rewards it in layout; the chain string just doesn't exist yet). Module: `mcc_strings.Planner.do_cj`.

### B4. CJ roughly mid-bay gets a dim from BOTH grids (2 added)
20592706 `EE | 18'-1⅝" | CJ` added for CJ 20572341, which already had `CJ | 18'-0⅜" | FF` (kept, 20591753 / new 20592713); 20592069
`4 | 7'-6¾" | CJ` added for cj#254, which has `CJ | 6'-6¼" | 5` (kept, 20591742, 3.4 ft away). In both the CJ is within ~1 ft of the
middle of the bay. The nearest-grid rule picks one; he wants both so the sum checks the grid spacing.
**Proposal (do_cj):** when the two candidate anchors differ by less than ~1.5 ft, dimension from both (one per end on a long CJ).
Open question 2 — this is my reading, not his words.

### B5. Intermediate beam-width dims slid far along the beam (2 moved, 1 added)
beam#226: 20591714 moved 24 ft along (from 33 ft to 57 ft off its end dim). beam#238: 20591732 moved 53 ft along and he added a new
`side | 3'-9" | 10 | 3'-9" | side` (20593806) 1.6 ft from the old spot — i.e. two intermediates on a ~150 ft band (at ~41 ft and ~94 ft).
Both beams are pieces of bands that continue in line (`continues()` in `do_beam`); the halfway point is computed on the piece (`L = s1 − s0`),
not on the band the reader sees.
**Proposal:** compute intermediate spots over the whole in-line band (pieces joined by `continues()`), one about every 50 ft, instead
of one halfway per piece. This half-reverses run 48 ("one halfway dim") for very long bands — open question 3. Module: `mcc_strings.Planner.do_beam`.

### B6. One side per direction / chain joined to its locate dim — rules exist but were out-weighed (3 moved, 1 added)
- core#115: chain `CC | 8½" | edge | 13'-7½" | edge` (20591804) was placed on the far side of the opening from the overall `CC | 14'-4" | edge`
  (20591693). He moved it 14.6 ft to the other side, one lane inside the overall. `W_SPLIT` 3 (soft) lost to whatever the other side cost.
- core#120: chain check `edge | 1'-5" | edge` (20591818, 3.1 in out) moved 11 ft onto the line of `wall | 5" | edge` (20591793, y 74.87) —
  joined end to end. `W_JOIN_SAME` −6 applies only when the candidate line is offered; the check string never got that spot.
- shaft#119 (pilaster hole): chain `1'-2" | 8" | 1'-2"` (20591776) moved to the other side and he added the overall `3'-0"` (20593194)
  outside it — "an overall goes outside its chain"; the planner makes no overall-size string when a chain exists.
**Proposal:** `W_SPLIT` 3 → ~8 for same-feature rows (hard unless no room on that side); offer the join spot for check strings of the
same feature in `candidates()`; `do_opening` adds an overall-size check for stepped openings. Module: `mcc_layout.evaluate/candidates`, `mcc_strings.do_opening`.

### B7. Opening with a grid running through it: far edge off the through-grid (1 added)
shaft#102 (the 17'-9" opening): he added `edge | 8'-4⅛" | BB | 9'-3⅞" | edge` (20592468) and kept the EE dims (`7'-7½" | 15'-7"`,
`23'-2½"`). This is the same string he drew in the run 30–35 clean-up (design doc: "9'-3⅞" | 8'-4⅛" through the grid on its right") — the
second time he has asked for it. `do_opening` takes the through-grid only when it is closer than the outside anchor for the near edge
(EE 7'-7½" < BB 8'-4⅛"), so the far edge ends up 23'-2½" off EE instead of 9'-3⅞" off BB.
**Proposal:** pick the anchor per edge: if a grid through the opening is closer to the far edge than the outside anchor, add the
`edge | grid | edge` string (keep the outside stack too — he kept both). Module: `mcc_strings.Planner.do_opening` / `stack_from_anchor`.

### B8. Slivers south of the core (4 deleted) — not in any rule
run#194 `edge | 1½" | EE` (20591680), run#196 `edge | 8'-3¾" | EE` (20591683), shaft#129 `EE | 2⅜" | edge` (20591700) and its `5"` chain
check (20591797), all at (204–214, 16–26). A 5"-wide "shaft" 2⅜" off a grid and a slab edge 1½" off the same grid are modelling slivers
along the core's south wall, not soffit edges. The void-in-a-wall-line rule skips `void` kinds only, and `_drop_filled_holes` needs 80% cover.
**Proposal:** an opening narrower than ~6" in either direction, or a slab edge under 6" from a wall face along its whole length, is a
sliver — skip, and list it in the report so he can check the model. Module: `mcc_features._opening_kind` / `mcc_strings.do_run`.

### B9. Tiny jog checks inside the cluttered zone (2 deleted) + one duplicate (1 deleted)
20591769 `edge | 1'-9⅜" | edge` and 20591791 `edge | 6⅛" | edge` (steps #2/#1 at (229–237, 54–56), right by notch#0 and the pocket).
He said "jog checks stay" — the one he kept (20591770, 3'-11¾") is elsewhere; these two are in the enlarged-plan zone. **Proposal:** let
`cluttered_small()` count small steps/bumps (< 2 ft) too, so their checks go with the openings. 20591805 `step | 4'-6" | CC` (step#2) is the
same 4'-6" segment as the joined `step | 4'-6" | CC | 7'-7" | edge` (step#1, kept) — a duplicate across two features that `mcc_place.dedupe`
missed because the join happens later in layout. **Proposal:** dedupe single-segment strings against joined strings after `_join_collinear`.

### B10. Beam#233's intermediate with "no room" placed as two singles (2 added)
20592609 `side | 3'-4" | 3` and 20592616 `3 | 2'-8" | side` on one line (y 51.2) — the intermediate width dim the report listed as
"intermediate beam dims with no room (left out): 1". **Proposal:** when a `side | grid | side` string has no room, try it as two single
dims on one line (each side of the grid). Module: `mcc_layout.run` (the `notes_optional` branch).

---

## C. Where the built rule may be the wrong reading (5 moved)

1. **`MIN_GAP_IN` 1/4" as a hard rule.** Three opening dims he moved out himself ended *closer* than 1/4": 20591793 `wall | 5" | edge` at
   0.20 in, 20591798 `EE | 7'-7½" | edge | 15'-7" | edge` at 0.17 in, 20591799 `edge | 1'-1½" | 8 | 16'-7½" | edge` at 0.10 in; and he pulled
   20591813 `7 | 13'-2¾" | edge` (shaft#119) *in* from 1.11 in to 0.14 in. The hard 1/4" would now reject four of his own placements. The
   first-row 3/8" trial in run 51 already moved 21 dims he had left alone. Reading that fits all of it: "not touching the edge" (≥ ~1/8"),
   and the first row as close as the text allows — not a fixed 1/4". Suggest `MIN_GAP_IN` 1/8" hard + `FIRST_GAP_IN` 1/4" soft.
2. **CJ dim "past the end".** Two CJ dims he moved stayed across the CJ, not past its end: 20591748 (cj#260 `CJ | 13'-0½" | EE`, slid 4 ft
   toward where its deleted twin was) and 20591756 (cj#271, slid 9.7 ft, still inside). Together with B3 (opposite ends for neighbours) the
   end choice is not only "the end with open slab past it". Keep the built rule, but it is 15 of 21 CJ moves, not 21.

---

## D. Model geometry and mistakes (his words — not rules)

- **Bad model geometry (7):** beam#238 `C | 8'-6 7/16" | end` deleted (20591787); beam#249's second `8'-6 7/16"` end ref removed from
  20591702; beam#221 `end | 1'-0½" | 11` (20591819) and the void edge `edge | 2'-3½" | 11` (20591820) deleted; beam#221's `A | 1'-3⅜" | side`
  nudged 1.8 ft (20591708); and in their place two tiny call-outs added: `A | 1⅜" | slab edge` (20593426) and `11 | 1½" | element 19128000`
  (20593461) at the NE corner (326, 204). Not a rule; worth a Dim Check note that an edge 1–2" off a grid is probably a modelling error.
- **Mistakes (4 added):** overall beam widths `6'-0"` ×2 (beam#233, 20592589 / 20593694), `7'-6"` (beam#231, 20593687), `3'-11¾"` (beam#232, 20593701).

## E. Unexplained (17) — need Adolfo

- **Angled core area, 9 added dims to elements the tool never references:** 20591965 `10'-2⅝"` and 20591979 `2'-10⅜"` from element 19128186,
  20591972 `10'-3⅞"` from 19129335, 20592008 `CJ 20572291 | 4'-3¼" | 14100054`, 20591958 `edge | 2'-0" | edge`, 20593952 `edge | 3'-9¾" | edge | 4'-10¼" | 14104554`,
  20593985 `edge | 3'-11⅛" | B`, 20593998 `edge | 10'-2½" | 7`, 20591951 `edge | 12'-1⅜" | BB` (x 119.6, west of beam#232). Elements 19128186 /
  19129335 / 14100054 / 14104554 / 19128000 are not grids, slab or beams — probably the angled core walls or columns. **20593998 (10'-2½" to grid 7)
  is the dim the angled-openings rule removed in run 44** ("shaft#115: the 12'-8½" / 10'-2½" went") — he has put it back by hand, so that rule
  may be too broad. Needs his reading before any code change.
- **beam#231 south end (1 deleted, 2 added):** `side | 4'-9" | 5 | 2'-9" | side` (20591718) replaced by `side | 4'-9" | 5` (20592569) and
  `5 | 1'-2" | CJ 20572318` (20592576) on one line at the beam end. The far side's 2'-9" is gone and a CJ the tool never planned is dimensioned.
- **beam#242 by the core (1 deleted, 1 moved, 1 added):** top end width (20591810, y 46.5) deleted and redrawn 5 ft further north (20593159, y 51.8);
  bottom end width (20591733) moved 12 ft *onto* the beam. Local clutter (pilaster strings, pocket) is the likely reason; no rule I can name.
- **beam#220 intermediate** `A | 1'-3⅜" | side | 1'-8" | side` deleted (20591707) while he kept/added intermediates on beams #226/#238.
- **run#195** `6 | 11" | edge` (20591681) moved 0.9 in off the edge's span.

---

## Proposed order of changes

1. **B1** — size-based clutter test (`cluttered_small` counts core/shaft openings < 4 ft). 6 deletions, one-line change, no risk to real cores.
2. **C1** — `MIN_GAP_IN` 1/4" hard → 1/8" hard + 1/4" soft first row. Fixes 4 of his placements the current rule would reject; re-check the 21 "left alone" dims.
3. **B6** — `W_SPLIT` stronger for same-feature rows; join spot offered to check strings; overall-size check for stepped openings. 4 items, layout only.
4. **B7** — per-edge anchor with a through-grid (`do_opening`). 1 item, but the second time he has drawn it.
5. **B3 + B4** — CJ rules in `do_cj`: opposite ends for close parallel CJs, `grid | CJ | CJ` spacing chain, both grids when mid-bay. 7 items; confirm B4 first (question 2).
6. **B2** — pocket shafts: outside first, inside last resort. 4 items.
7. **B8 + B9** — slivers and small steps skipped / counted as clutter; dedupe after join. 7 deletions.
8. **B5 + B10** — intermediate beam dims over the whole band every ~50 ft; split intermediate into two singles when there is no room. Confirm question 3 first.
9. Leave E (angled core, beam#231, beam#242) until Adolfo explains them.

## Open questions for Adolfo

1. The 5"-wide "shaft" and the 1½" edge south of the core (B8): modelling slivers to ignore, or real?
2. CJs 20572341 (18'-0⅜" / 18'-1⅝") and cj#254 (6'-6¼" / 7'-6¾"): did you add the second grid because the CJ is mid-bay, or for another reason?
3. Beams #226 / #238: you moved the halfway width dims 24 and 53 ft and added one — do very long bands (> ~100 ft) get a width dim every ~50 ft?
4. 10'-2½" to grid 7 at the angled core (20593998) is the dim the angled-opening rule removed in run 44. Is the rule wrong, or is this spot special?
5. Elements 19128186, 19129335, 14100054, 14104554 (angled core) — what are they, and should soffit plans dimension to them?
6. beam#231 south end: why drop the far side 2'-9" and dimension CJ 20572318 (1'-2" off grid 5) instead?
7. The two beam widths outside the annotation crop (beams #232/#233 at y −33.8): widen the annotation crop, or let the tool place dims up to 4 ft past it?
8. Opening dims you moved to 0.10–0.20 in from the edge: is 1/4" a minimum you want enforced, or is "not touching, as close as the text allows" the rule?
