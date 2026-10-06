# L7 edit round 1 — what Adolfo changed and why (run 28, scale 1:96)

View: `ZZ CLAUDE TEST - L7 (auto-dim)`, 2026-10-06. Clean round: the view he edited is run 28, so dim ids match.
By dim: 42 unchanged / 76 edited / 1 deleted / 23 added. By segment: 100 left / 67 moved / 2 deleted / 13 added.
Grid positions used below: 5 x 184.23, 6 x 209.98, 7 x 232.89, 8 x 270.23; AA y 130.52, BB 98.02, CC 62.02, EE 26.02, FF -10.19, GG about -46.2.

**A problem with the segment comparison.** `compare_segments.py` matches a segment by its two elements and its value. On L7 the same values repeat (ten `3'-4½" | 5 | 1'-7½"` chains on the west sawtooth; pen#70 has the same `5'-0⅛" | 1'-9¼"` as pen#72). So 10 of his new dims were counted as "left" or "moved", not "added". The real number of new dims is 23 (the id-based count), not 13. Fix: match by position as well as value.

**Most of his additions copy the issued hand sheet exactly**, within about 1 ft: the 29'-9¾", 1'-3¼", 5'-1", the pocket-shaft group, and the run dims he moved. Where the hand sheet and the L3N decisions disagree, that is flagged below.

---

## 1. West sawtooth: a located dim at every step — about 27 dims (planning + placement)

- **What the tool did:** one merged string `edge | 3'-4½" | 5 | 1'-7½" | edge` per tooth face (runs #10, 24, 26, 28, 30, 32), placed in the margin about 2 ft from one corner. The 5'-0" jog check sat at each step. The step face strings (`step | 4'-8⅞" | FF | 10'-4⅛" | step` etc., ids 20606084–87) were 1 ft (1/8") off the slab edge.
- **What he did:**
  - He put one `3'-4½" | 5 | 1'-7½"` at **every one of the 10 steps**, 1.1–2.5 ft from the step face (paper 0.14–0.31", median about 0.19"). Some are one dim, some are two dims on one line.
  - He also put a single 3'-4½" at each far end of the sawtooth (y -42.7 and 133.3).
  - To do this he moved the 5 existing chains (ids 20606069, 79, 80, 81, 82) and added 8 new dims (20606331, 422, 491, 548, 652, 659, 672, 20607545).
  - He moved 9 of the 10 jog checks (20606106–113, 115) to sit about 3/16" outside the new chain. This is the existing rule for equal lengths: the chain sits inside, the overall outside.
  - He pushed the four step-face strings out from 1/8" to 1/4" (x 179.85 → 178.80).
  - He moved step#3's `10¾"` (20606130) from inside the slab (x 189.85) to the edge (x 180.3). The hand sheet has it in the step column.
- **The rule it points to:** dimensioning-rules #3, "dimension at every turn". At each step, both run faces that meet there are located off the grid crossing the step: `face a | grid | face b`, in the first row from the step face, with the jog check one row outside. The hand sheet does the same at 6 of the 10 steps; he did all 10.
- **Where:** `mcc_strings.Planner.do_step` adds the located string next to the jog check (the code path `merge_through_anchor` already builds the right shape). `do_run` then doesn't need its own dim at an end that is a step.
- **Why the step strings sat at 1/8":** in `mcc_layout.Layout.candidates`, a string with no home side (`home == 0`, which includes step strings) slides 1 ft at a time *toward or away from* its element. One slide at 1:96 is 1/8". The 1/4" floor (`MIN_GAP` / `W_GAP`) only applies to openings.

## 2. An opening's locating dim and its size, end to end on one line — 11 pairs, about 22 dims (placement)

- **What he did:** in 11 places he put an opening's locating dim and its size on the **same line, end to end, as two separate dims**:
  - plain#50 `15'-11"` + `1'-5⅞"`; #52 `4'-0⅜"` + `1'-10⅛"`; #53 `16'-4¾"` + `2'-4"`; #57 `2⅞"` + `2'-6"`
  - #59 `4'-6¾"` + `5⅝"`; #68 twice; pen#72 `5'-0⅛"` + `1'-9¼"`; pen#77
  - shaft#51 `13'-2¾"` + `3'-0"`; shaft#46 `3'-6"` + `17'-8" R.O.`; core#61 `3'-3"` + `6"`
  - In run 28 none of these pairs shared a line. The size stood one lane out, or on the other side of the opening.
- This one cause explains most of the "closer" moves (0.5–2.1" in to 0.10–0.28") and 6 of the 18 "to the other side" moves: plain#50, #53 and #68 (×2), shaft#51 `3'-0"`, and pen#76's `9'-7"`, which he lined up with the review item `1'-5"`.
- **Rule:** already decided ("size joins its locating dim end to end", `W_JOIN_SAME`). On L7 it did not happen for small openings, where the planner makes `stack 1 -> grid` plus the size check.
- **Where:** `mcc_layout.Layout._join_collinear`. When the merged string is refused, the second dim is re-placed elsewhere with joins off (`_no_join`). His version keeps the two dims end to end as separate dims. Proposal: when the join is refused, keep the spot as two dims rather than moving one away. First count how often the refusal fires on L7 (`notes_unjoined` is not in the report).
- **Spacing at 1:96 is right.** His first rows are 0.10–0.28" (median about 0.21") and his second rows sit about 0.19" further out. That matches `FIRST_GAP_IN` 1/4" with the `W_GAP` taper and `LANE_STEP_IN` 3/16". The paper-inch settings carried over from 1:128 fine. Settings still in feet behave differently at 1:96:
  - `SLIDE_STEP` 1 ft (see group 1)
  - `CORNER_IN` 2 ft
  - `MARGIN_IN` 2.5 ft
  - `CLUTTER_R` 8 ft (see group 6)

## 3. Run dims moved past the end of their edge — 9 dims (placement; one bug)

- **Ids:**
  - run#17 `AA | 28'-4⅜"` ×2 (20606072/73)
  - run#18 `1'-1½" | 8` ×2 (20606074/75)
  - run#19 `1½"` (20606076), run#21 `16'-4⅞"` (20606077), run#12 `9'-6"` (20606070), run#22 `8"` (20606138), run#20 `1'-6½"` (20606133)
- All 9 were "inside" the edge's length. He moved each past an end of its edge (moves of 4–86 ft along the edge). All 9 now sit where the hand sheet has them.
- **Bug (run#17 and run#18):** the two "one dim at each end" dims landed **in the middle of the edge, 2–3 ft apart** (y 73.3 / 75.3 on a 175 ft edge).
  - `Planner.end_parts` returns `outward` = -1 for the low end and +1 for the high end.
  - `Planner.do_run` throws that away and sets `outward=(1 if k == 0 else -1)`, which is the reverse.
  - `Layout.candidates`' margin lane then measures from the inner end of each half span (`end = s_hi` for the low half), and both dims meet in the middle. Fix: pass `end_parts`' own `outward` through.
- **The rule for the 5 single dims:** a run dim sits just past the end of its edge, at the corner (the first row past the corner), like CJ end dims (`BEAM_END_GAP_IN` 1/4"). It should not sit `CORNER_IN` 2 ft inside the edge.
- **Where:** `do_run` (`prefer` / `outward`) and the margin lanes in `candidates`.

## 4. Core shafts: the L3N pocket pattern, through-grids ignored — about 11 dims (planning)

- **What he added:** `3'-4½"` off 7, `7'-9½" R.O.` (edge to wall 18596162), `7'-7"` off CC, `½"` CC → edge and `12'-5" R.O.`. This is the same group as the L3N core pocket (3'-4½" off 7, 7'-7" off CC) and the same as the hand sheet. He deleted the `28'-5"` to BB.
- **Cause, core#49:** grid 7 runs through it in x and CC runs through it in y. `do_opening` only looks for a grid through the opening `if not (lo_wall or hi_wall)`. core#49 has a face on the core wall, so the tool reached out instead: `6 | 19'-6½" | edge | 7'-9½" | wall` (went to review: text over a note) and `wall | 12'-1" | edge | 28'-5" | BB` (placed; he cut the 28'-5"). Fix: in `mcc_strings.Planner.do_opening`, let a grid through the opening anchor the free side even when the other side is `edge@wall`. That gives `edge | 3'-4½" | 7 | … | wall` and `CC | 7'-7" | edge`. This is "always the closest gridline" (2026-10-05).
- **core#48** (review: `CC | 12'-5½" | edge | 23'-6½" | edge`): he drew `CC | ½" | edge | 12'-5" R.O. | edge`. The tool's string is missing the bottom face ½" off CC. It probably counted as located by the core wall face. **This needs a look at the model.**
- **shaft#46:**
  - He deleted `stack 2 -> EE 21'-2"` (far edge).
  - He moved `3'-6"` and `17'-8" R.O.` out of the shaft to 0.17" beside it. The tool had put them inside the shaft (`W_IN_SHAFT`) because the 21'-2" row took the outside spot.
  - He moved the `8'-3" R.O. | 11'-9" | 7` strings of shaft#46 and core#48 closer (1.12" → 0.21").
- **Where:** `stack_from_anchor`, the "near edge only off the outside grid" branch (`sub == "core"`).
  - Proposal: also apply that branch to a shaft with a face on a core wall.
  - **Flag:** the L3N round-2 note keeps the far row for "shafts outside a core (the 23'-2½" off EE)". shaft#46 is labelled `shaft` but sits in the core (8'-3" off the wall), so this is consistent if "in a core" means "has a face on a core wall". Confirm with Adolfo.

## 5. "To the other side" moves not explained by joins — about 9 dims (no single rule; ask)

- **Rule 12 mostly holds.** Of the opening dims he did not move, 45 sit on the side away from the other direction's grid (rule 12, `do_opening`'s `away`) and 4 sit toward it. 10 of his flips went from "away" to "toward" and 3 went the other way, so this is not a new side rule.
- **Split stacks (3):** he put an opening's far-edge or overall row on the **opposite side** of the opening from its near-edge chain, each at about 1/4":
  - plain#62: `11'-2⅞"` below, `4'-6⅛" | 6'-8¾"` above
  - plain#58: `10'-11½"` below, `4'-8" | 6'-3½"` above
  - plain#59: `5'-0⅜"` left, `4'-6¾" | 5⅝"` right
  - shaft#51 is the same idea: the `1'-2" | 8" | 1'-2"` step chain is above, and the `3'-0"` overall (joined to `13'-2¾"`) is below.
  - **This contradicts** `W_SPLIT` 8 (one side per direction, L3N run 63) and "an overall goes outside its chain". Flagged, not proposed.
- **Single flips with no clear cause (5):** plain#64 H chain, #65 H chain, #66 V chain, #50 H (chain + stack 2), and run#20. These are probably local clutter: #64's chain moved to make room for pen#70's new string. Ask with a picture before writing a rule.
- **One stack in the wrong order:** plain#60 `10'-2¼"` (far edge) sat nearer than the `5'-0"` size; he swapped them. `_order_stacks` reported 0 reorders on L7.

## 6. What he added that the tool never placed — 10 dims (missing coverage)

| What | Ids | What it is | Should a rule have made it? |
|---|---|---|---|
| `1'-3¼"` ×2 at (178.8, 131.2) and (217.4, 131.2) | 20606679, 20606693 | Top-left slab edge just above AA, about 39 ft long, located at both ends (hand sheet: one, at x 178.5) | Yes, by `do_run`. The tool made **no** string for this edge. Some skip must have fired (wall, column or beam flush). Needs a model look. Two dims 38 ft apart **contradicts `TURN_BOTH` 40** (flag). |
| `5'-1"` at (230.4, 161.1) | 20606700 | Vertical edge at x 227.8 located off 7 (hand sheet: at y 161 and 141) | Yes, by `do_run`. Also never planned; same model look. |
| `36'-2½"` 7 → east edge, same line as the 5'-1" | 20608233 | The east edge (already `1'-1½"` off 8) measured again off 7 | No. It is over the 30 ft tape, not off the closest grid, and not on the hand sheet. **Contradicts** the 30 ft and closest-grid rules (flag). |
| `29'-9¾"` FF → bottom edge at (175.6, -25) | 20607538 | West end of the bottom edge, outer column of the west strings (hand sheet: same) | Not by today's rules: GG (6'-0¼", which the tool had at the east end) is closer. Both ends of a 35 ft edge again goes against `TURN_BOTH` 40 (flag). |
| `7 \| 5'-0⅛" \| edge \| 1'-9¼"` and `edge \| 1'-10" \| edge \| 3'-10⅝" \| BB` at (238.8, 102.8) | 20607070, 20607137 | pen#70 in full | The tool set it aside "for an enlarged plan": `Planner.cluttered_small`, with pen#72 and plain#64 within `CLUTTER_R` 8 ft. At 1:96, 8 ft is 1" on paper; at 1:128 it was 0.75". **Goes against the L3N clutter rule** (flag). Possible fix: set `CLUTTER_R` in paper inches (0.75" = 6 ft here, which leaves pen#70 with one neighbour). |
| `11"` 6 → plain#63 left edge at (209.5, 78.4) | 20608220 | plain#63 had only its `1'-7"` size; nothing tied it to grid 6 | **Yes, this is a bug.** `stack_from_anchor`'s `have` check holds only family + offsets. plain#63's `6 \| 8"` matched run#22's `6 \| 8"` 107 ft away on the same line, so it was skipped ("stacked dim already planned (skipped)": 2). That goes against rules #2 (don't assume repeated conditions). Fix: add where along the grid the dim sits to the check. |
| `23'-4"` EE → pen#76 top edge, and `1'-5"` (pen#76 size) | 20608372, 20608359 | Both were review items (`CC \| 12'-8"`: text over a note; `1'-5"`: inside an opening). He used EE (farther) and put `1'-5"` on one line with `9'-7"` | Layout. Using the farther grid when the closer one is blocked by a note **goes against "closest gridline"**; ask. |

## 7. Deletions (2 segments)

- `stack 2 -> EE 21'-2"` (20606088, shaft#46 far edge): see group 4. This is a planning rule.
- `28'-5"` to BB, cut from `12'-1" R.O. | 28'-5"` (20606127, core#49): replaced by `CC | 7'-7"`, see group 4. Planning (anchor choice).
- He gave no mistake or bad-geometry explanations this round.

## Rules that went against an L3N decision (for Adolfo, not proposed)

1. `TURN_BOTH` 40: dims at both ends of the 39 ft top edge (`1'-3¼"`) and the 35 ft bottom edge (GG + FF). On L3N he deleted second end dims on 20–40 ft edges.
2. `cluttered_small`: pen#70 dimensioned in full at 1:96.
3. `W_SPLIT` / "overall outside its chain": 4 openings with rows split across both sides.
4. The 30 ft tape / closest grid: `36'-2½"` off 7, `29'-9¾"` off FF, `23'-4"` off EE.
5. Shaft far-edge row: kept for shafts outside a core on L3N, deleted for shaft#46 here (consistent only if shaft#46 counts as "in the core").

## Proposed order of changes

1. **`do_run` end-dim direction bug** (`outward` from `end_parts`). Then **run dims just past the end** of their edge instead of `CORNER_IN` inside it. 9 dims; the hand sheet agrees.
2. **`stack_from_anchor` duplicate check includes where along the grid the dim sits** (`have` / `fam_offs`), so the same offset at another element isn't skipped. 1–2 dims; a clear bug.
3. **`do_opening`: a grid through the opening anchors the free side when the other side is `edge@wall`.** Gives the core#49 pocket dims and clears 2 review items.
4. **`do_step`: a located `face | grid | face` string at every step, with the jog check one row outside.** In `Layout.candidates`, a string with no home side may not slide closer than about 3/16" to its element. About 27 dims, the largest group.
5. **`_join_collinear`: keep a refused join as two dims end to end on one line.** First check how often the refusal fires on L7. About 22 dims.
6. **`stack_from_anchor`: near edge only for shafts with a face on a core wall** (after Adolfo confirms item 5 above).

## Open questions for Adolfo (a picture settles each)

1. The 39 ft top edge (`1'-3¼"`) and the 35 ft bottom edge (GG `6'-0¼"` + FF `29'-9¾"`) got a dim at both ends. On L3N you removed second end dims on 20–40 ft edges. Is the difference that these edges end at outer corners of the building, or should `TURN_BOTH` come down?
2. The pen#70 cluster (3 small holes within 8 ft): on L3N similar clusters went to an enlarged plan. Is it the scale (1:96 has more room), or should only holes in or against a core wall count as clutter?
3. plain#58, #59, #62 and shaft#51: the far-edge or overall row on the opposite side from the near-edge chain. Is that a rule (each row in the first lane on its own side), or just what fitted here?
4. `36'-2½"` from 7 to the east edge, which is already `1'-1½"` off 8: an overall check you want the tool to make, or a one-off?
5. `23'-4"` from EE for pen#76 when CC (12'-8") is closer but blocked by a note: should the tool fall back to the next grid, or keep CC and flag the note?
6. shaft#46 (an elevator shaft with one face on the core wall): treat it like a core opening (near edge + size only)?
