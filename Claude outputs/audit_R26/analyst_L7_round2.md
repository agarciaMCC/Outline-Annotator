# L7 edit round 2 (on run 31) — analyst report, 2026-10-07

Inputs: `snapshot_L7_before_edits2.json` (run 31), `snapshot_L7_after_edits2.json` (Adolfo), `compare_L7_edits2.json`
(72 unchanged / 57 edited / 6 deleted / 4 added — really 59 edited: 20609343 and 20609344 have no tool tag and were
missed), `compare_L7_edits2_segments.json` (130 left / 60 moved / 6 deleted / 3 added; core#49's deleted `4'-5"`
20609331 is wrongly matched to pen#77's `4'-5"`).

**Headline:** 68 of the 83 segments he edited or added sit within 3/16" of where he had them in round 1 — he put
them back. Run 31 predates `3f3d8b3` (`_align_end_to_end`) and `8ccadeb` (stepped overall 3+ segments, text off
walls): re-run L7 on today's code before building anything.

Grids (ft): 5 x 184.23, 6 x 209.98, 7 x 232.89; AA y 130.52, BB 98.02, CC 62.02, EE 26.02, FF -10.19.

## Rule-like groups
- **A. Opening locate + size end to end on one line** — 14 pairs (~22 dims). Tool put stack 1 and the size on
  different lines / sides, so `_join_collinear` never saw them. Three were also slid far out on the wider search
  (20609368 15 ft, pen#76 `9'-7"` 23 ft, 20609446 12 ft). `_align_end_to_end` (built after run 31) can't do the
  cases where he moved both to a third line (#52, #68 horizontal).
- **B. West sawtooth step strings on the notch side**, jog check one row further out — 14 dims. Tool always picks +y;
  wrong for the upper face of each recess (steps 0,1,3,5,7,9). Chain ~1.5–2 ft off the face, jog ~1.5 ft further.
  → `Planner.do_step`: home side into the notch; jog linked as stack rank 1.
- **C. Step-to-grid strings in the west margin** just past the outer face (x 180.85) — 4 dims (20609362, 327, 389, 396).
  → `do_step`: prefer outer end minus `BEAM_END_GAP`, `free` via `free_end`.
- **D. ½" edge off CC at core#48 never dimensioned** — he added `½"` (20612463). Likely `mcc_place.dedupe(tol=1/24)`
  merging the face into the grid. → tol 1/96 ft; confirm by printing the merged pair.
- **E. Far-edge rows that shouldn't exist:** shaft#46 `stack 2 -> EE 21'-2"` (20609330, deleted both rounds — the
  core-wall-shaft rule tests `"edge@wall" in s.names`, which misses the vertical string; test the opening instead);
  core#49 `7 | 4'-5" | edge@wall` (20609331; grid through the opening — no stacked row to a face on a wall).
  → `stack_from_anchor`.
- **F. Stepped shaft#51:** bump chain on the bump's own side (20612369 added at y 54.7); `13'-2¾"` joined with the
  `3'-0"` overall; `3'-8"` overall deleted (already fixed by `8ccadeb`). → `do_opening`, `_join_collinear`.
- **G. Edges never dimensioned:** the 39 ft top edge above AA (one `1'-3¼"` at the west corner, 20610848) and
  `5'-1"` off 7 (20610855). Probably `do_run`'s `flush(e, walls)`. Needs a model look.
- **H.** run#18 `1'-1½" | 8` (20609390) moved 2.5 ft past the corner. Low priority.

## Taste / one-offs
First rows tightened 0.1–0.15" (3/16" first row already tried and reverted on L3N); 3 text-only moves; knock-ons of
his own joins (20609405, 432, core#48's string to the open side); plain#52 and #62 sides swapped vs round 1 (not a
rule); shaft#46 `8'-3" R.O. | 11'-9" | 7` moved inside the shaft (20609379) — against the "nothing inside
openings" rule, flagged. He did not re-add round 1's `36'-2½"`, `29'-9¾"`, `23'-4"` off EE.

## Compared with earlier rounds
Same: joins (A) biggest group again; sawtooth, shaft#51, ½", 39 ft edge, `21'-2"` repeats. Better: 72 untouched
(round 1: 42), additions 23 → 4. New: far-edge rows deleted at #50/#56/#58 (kept in round 1); second-grid leg cut
at core#48 (vs L3N round-4 answer 2); one dim on the 39 ft edge instead of two; shaft string inside the shaft.

## Proposed order (keep each only if the score vs `snapshot_L7_after_edits2.json` holds; L3N as regression)
0. Re-run L7 (run 32) on today's code; score; count `notes_aligned` / `notes_unjoined`.
1. Step strings on the notch side + jog as next row (~18–21 segments).
2. Step-to-grid strings in the margin (6 segments).
3. Remaining join refusals: fresh first-row line for both; stack 1 and size on one side (up to ~20).
4. `dedupe` tol ½" → 1/8" (the `½"`; check L3N for new tiny dims).
5. Core-wall-shaft rule checks the opening, not the string (`21'-2"` gone).
6. Grid-through opening: no stacked row to a wall face (`4'-5"` gone).
7. Stepped chain on its own side; locating row joins the overall (~5).
8. Model look: why `do_run` skips the 39 ft edge and the `5'-1"` edge.
9. Run dim past the corner when only the near strip is blocked (1).

## Questions sent to Adolfo (pictures `L7_edits2_q1/q2/q3a/q4.png`)
1. Far-edge row of a plain opening — deleted at #50/#56/#58, kept at #60 and in round 1.
2. core#48 second-grid leg `23'-6½"` to BB cut — vs L3N round-4 answer "keep the leg".
3. Side for an opening's dims — moved toward the grid locating the other direction (#65, #66, #68) vs rule 12.
4. 39 ft top edge — one dim at the outer corner, or both ends.
