# Edit-diff analysis — L3N test view, round 5 (run 92 vs Adolfo's fifth edit round)

Read-only, 2026-10-06. Inputs: `compare_L3N_edits5.json` (117 rows), `compare_L3N_edits5_segments.json` (160 rows),
`snapshot_L3N_before_edits5.json` (= run 92) / `_after_edits5.json`, `snapshot_L3N_after_edits4.json` and
`snapshot_L3N_run84..92.json` (for "same spot as last round"), `dimsoffit_v2_L3N_run92.md`, `analyst_L3N_round4.md`,
design-doc entries of 2026-10-06, `mcc_strings.py`, `mcc_layout.py`. Ids match (clean round). Scale 1:128 (1/4" = 2.7 ft).

**Headline:** 117 tool dims → **86 unchanged (74%), 30 edited, 1 deleted, 0 added**; by segment 127 left / 32 moved / 1 deleted.
**The key fact: 24 of the 30 edits put the dim back within ~1 ft of where he put the same dim in round 4**, and for 14 of
those 24 the tool's spot in run 92 is identical to run 84 (it never learned the move). Round 5 is round 4's picture
re-drawn, not new information. The remaining 6 edits are ≤ 1/2" nudges or a 4 ft slide along an edge.

---

## 1. Today's L7-round changes on L3N — all left (confirmed for L3N)
| Change | L3N dims | Result |
|---|---|---|
| Run dim just past the corner when the margin is open (`margin` spots) | 20609128 `2'-5¾"`, 20609129 `1⅜"`, 20609131 `1⅜"` | all unchanged |
| Run located at both corners (gated by open margin below 40 ft) | run#38 (20609131 + 20609132), run#27 (20609128 + corner 20609194 `12'-1⅜"`) | all unchanged |
| Step `face \| grid \| face` | step#1 20609136 `step \| 4'-6" \| CC \| 7'-7" \| edge` | unchanged |
| No slide inside `MIN_GAP`; duplicate check by location | no row pushed off a 1/16" hug; nothing deleted as a repeat, nothing added | held |
| Regression traced to this batch | shaft#114's angled chain flipped sides at **run 91** (§G4) | his round-4 side lost |

Only two run dims were touched: run#7's `3'-4½"` (0.19", part of the pocket, §G2) and run#176's `edge | 16'-4" | BB`
20609133 slid 4.25 ft along its edge to x 193.6, beside run#206's `10'-1½"` at x 193.4 (line-up; he slid it in round 4 too
— taste).

---

## 2. Groups (by cause, largest first)

### G1. One opening's rows that meet end to end are not on one line (11 edits) — `mcc_layout._join_collinear`, `_order_stacks`, `candidates` clamp
He joined them by hand, the **same joins as round 4** (each within 0.7 ft of his round-4 line):
- shaft#118: `FF | 7'-9" | edge | 3'-4" | edge` at x 203.3 — 20609144 moved out of the hole's band onto the 3'-4" line (**4th round**); 20609229 text only.
- shaft#119 (pilaster hole), across: `7 | 13'-2¾" | edge | 3'-0" | edge` at y 47.9 — 20609145 out of the hole's band, 20609217 onto it (2nd round).
- shaft#119, up-down: `CC | 8'-0½" | edge | 8" | edge | 3'-0" | edge` at x 253.0 — 20609231 and 20609230 were placed **1 ft apart** (x 250.8 / 251.8) (2nd round).
- shaft#102: `edge | 1'-1½" | 8 | 16'-7½" | edge` on one line at y 50.6, `17'-9"` one row out — 20609238, 20609239, 20609240. Runs 84–92 always had these two 1 ft apart (2nd round).
- shaft#114: corner `B | 3'-11⅛" | corner` 20609243 onto row 1 with `7'-1¾" | B` 20609241 (same line to 0.01 ft; 2nd round).

Causes, from the code: (a) the locate row (cand `collinear`) lands **through the small hole's own band**, where the size
cannot join it (nothing inside openings) — 7'-9", 13'-2¾"; (b) `_order_stacks` "pushed out" gives every row its own lane even
when two rows don't overlap (shaft#102: the 17'-9" overlaps both and pulls them into one group); (c) a partner re-placed after
the join spot was taken (shaft#119 up-down, 1 ft off — `_join_collinear` needs ≤ 0.05 ft); (d) the `late` corner call-out
never gets the `W_JOIN_SAME` spot (round-3/4 open item).
**Proposal (no question needed — rule 14 already says it):** a last pass after `_order_stacks`: two placed strings of the same
feature that share a witness line, don't overlap, and stand ≤ 2 lanes apart on the same side are moved onto one station
(either one's) and joined if `evaluate` passes; and in `_order_stacks`, rows that don't overlap share a lane. Separately,
re-try the round-4 clamp on home-less opening rows **only for small openings** (≤ 8 ft across the row) — runs 85–88 failed
on the 17 ft opening, whose rows he does keep inside its band.

### G2. The pocket at the core wall, run#6 / run#7 (5 edits, 3 of the big moves) — `do_shaft_pockets`, `at_end`, side choice
Pocket ≈ x 229.5–237.3, y 57.5–69.6. Every dim lands where he put it in round 4:
- `12'-1"` 20609195 (edge | wall, up-down): from x 241.0 (beyond the wall face, over the core) **into the pocket**, x 236.3 — **5th round**. `do_shaft_pockets` already lets it sit inside (`own_voids`) but `prefer` is the edge midpoint and the outside spot wins.
- `7'-9½"` 20609207 (across): from below the pocket (y 53.9) to above it, y 74.1, one row outside run#7's `edge | 3'-4½" | 7` (20609127, nudged 0.19") — **1.9"**. Same feature, same direction, opposite sides in run 92 (rule 10 "one side"). Runs 84–92 flip it between y 53–54 and y 78–80: a near tie.
- beam#242's far width `side | 1'-7⅛" | 7 | 3'-10⅞" | side` 20609200: from y 80.2 (cand `(-1, 5, -10)`, **22.7 ft past the end, across the pocket**) to y 51.9, 5.6 ft inside the end — **2.66"**, his round-4 spot to 0.5 ft. `at_end` handles an end framed into a beam band but not an end at a wall / pocket, so `evaluate` rejects every spot near the end and the wider search takes the first clear slab.
- core#120 `wall | 5" | edge | 1'-5" | edge` 20609233: above the hole (y 85.9) → below (y 74.1) — **1.11", 4th round, same move**. y 74.12 is exactly the `7'-9½"`'s new line: he lined the two up. Above, it crowds core#115's `8'-3" R.O. | 11'-9"` (20609205, nudged 0.39" closer).

Proposals: (1) `do_shaft_pockets`: when the outside spot is beyond the wall face, the size goes inside the pocket (prefer
≈ 1 ft off the wall face) — consistent with "inside only if no room outside" if *behind the wall* counts as no room
(question 2). (2) `at_end`: an end framed into a wall or opening (nothing to stand on within `FRAMED_CROSS`) → width across
the beam 3–6 ft inside the end, exempt from the clamp (`mcc_layout` ~831) and `W_OWN_BEAM` — question 1. (3) The 7'-9½" and
core#120 should follow once the beam width leaves the pocket's top side; re-check before adding a rule for them.

### G3. Beam width at a wall-framed end moved onto the beam (beam#242 above + 1) — contradicts answer 2b, flagged
- beam#224 `side | 4'-0" | side | 1½" | 11` 20609159: 0.51" past the end → 7.3 ft back along the beam, on it (**3rd round**; within 1.9 ft of his round-4 spot). Round 4 recorded this end as framed into a core wall.
- beam#248 `3'-9" | 10 | 3'-9"` 20609169: left past the end, pulled 0.51" → 0.15" (his round-4 spot to 0.2 ft) — confirms "past the end" for its end.

He answered round 4 "disregard my edit — 2b stands", then made the same two moves again. 2b is about ends framed into a
**beam band**; both repeat cases are ends at a **core wall** (or the pocket), where there is no band to read across.
Not proposed silently — question 1.

### G4. Angled shaft#114: the `4'-10¼"` chain and `8'-8"` overall on the wrong side (2 big moves + 3) — side choice, regression
- `edge@wall | 4'-10¼" | edge | 3'-9¾" | edge` 20609244 (**2.21"**) and `8'-8"` 20609245 (**2.74"**): from the south face (y ≈ 124) to the north face (y ≈ 147–151), locate chain inside, overall outside — his round-4 spots to 0.5–0.8 ft. **Runs 84–90 put the chain on the north side; run 91 flipped it** (the L7 batch: `W_SPLIT` back to 8 with ungated both-corner run dims; run 92's gating did not bring it back).
- `2'-5" | B | 12'-5"` chain check 20609204 out of the shaft to the B stack's second row (0.84", same as round 4); `14'-10"` 20609203 slid inside the shaft (left inside, as in round 4); `10'-2½"` 20609142 slid 0.22".

Proposal: compare runs 90 and 91 for what made the south side cheaper (likely `W_SPLIT` against the B rows, or a
both-corner run dim on the north margin). No rule needed.

### G5. Pilaster-hole bump chain to the bump side; its 3'-8" deleted (1 edit + 1 deletion) — `do_opening` (stepped)
- `1'-2" | 8" | 1'-2"` 20609199: below the hole (y 47.6) → above it (y 54.8), the side where the 8" bump is (**2nd round**; round 4: y 56.0). Probable rule: a bump/step chain sits on the side of the bump — a side preference (`outward`) for the stepped chain in `do_opening`.
- **Deleted `3'-8"` 20609198** (stepped-opening overall, up-down). His up-down line is now `CC | 8'-0½" | edge | 8" | edge | 3'-0" | edge`: the chain `3'-0" | 8"` already spans the full 3'-8", so the overall is the sum of a two-piece chain standing 0.8 ft (0.07") outside it. Across, he **kept** the `3'-0"` overall, because it is the piece joined to the locating row (`7 | 13'-2¾" | 3'-0"`); the bump chain is on the other side. In round 4 he kept the 3'-8" (moved out to x 255.3). Possible rule: "no stepped-opening overall in a direction where the full step chain is already joined to the locating row" (`do_opening` ~620, or a check in `_dedupe_after_join`). Contradicts rule 9 ("an overall goes outside its chain") — question 3.

### G6. Nudges and taste (6 edits) — leave
core#110 `8'-3" R.O. | 11'-9"` 20609139 0.06"; core#115 20609205 0.39" closer (his round-4 spot); `end | 6'-4" | BB` 20609209
0.12" closer; run#176 `16'-4"` slide (section 1); jog `8"` 20609218 to the other side (**3rd round** — his answer: visibility,
no rule); core#120 vertical 20609232 text only.

---

## 3. The largest segment moves (≥ 1")
| Dim | Move | Cause |
|---|---|---|
| shaft#114 `8'-8"` (20609245) | 2.74" | G4 — side flip since run 91 |
| beam#242 width, 2 segs (20609200) | 2.66" | G2/G3 — wall/pocket-framed end; the wider search went 22.7 ft |
| shaft#114 `4'-10¼" \| 3'-9¾"`, 2 segs (20609244) | 2.21" | G4 |
| pocket `7'-9½"` (20609207) | 1.90" | G2 — split from its locating row; follows the beam width |
| core#120 `5" \| 1'-5"`, 2 segs (20609233) | 1.11" | G2 — 4th round, lined up with the 7'-9½" |

"Onto the element" (3): beam#242, beam#224 (G3, question 1), pocket 12'-1" (G2, question 2) — all rule-like (3–5 rounds).
"Other side" (6): shaft#114 ×2 (regression), pocket 7'-9½" and core#120 (G2), bump chain (G5, rule-like), jog 8" (taste).

## 4. Not rules
- No deletion this round is a mistake or a model problem.
- 0 added: the 5 review items (incl. the `3 | 7'-11" | CJ` he added in rounds 1–4) were not drawn in — question 4.

---

## Proposed order of changes
1. **G1 join pass** — after `_order_stacks`, snap end-to-end rows of one feature (≤ 2 lanes apart) onto one line and join; non-overlapping rows share a lane in `_order_stacks`. 11 edits, all repeats, no question needed.
2. **G4** — compare runs 90/91 for shaft#114's side. 5 edits, a regression.
3. **G2(1)** — pocket size inside the pocket (`do_shaft_pockets`), 5th round; after question 2.
4. **G2(2)/G3** — wall-framed beam end → width just inside the end (`at_end`); after question 1. Then re-check the 7'-9½" and core#120 before adding anything for them.
5. **Small-opening clamp** for home-less locate rows (≤ 8 ft) if step 1 does not already clear 20609144 / 20609145.
6. **G5** — bump chain on the bump side; the 3'-8" only after question 3.

**Another L3N round is not worth it.** He is re-drawing his round-4 layout. Score runs against
`snapshot_L3N_after_edits5.json` instead. After steps 1–4 the left-over is ~6 taste edits (G6), under the 10-dim target.
Spend his next round on L7.

## Open questions for Adolfo (one picture each)
1. **Beam ends at a core wall** (beam#242 at the pocket, beam#224 at grid 11): in round 4 you said "disregard my edit, past the end stands", but you put both on the beam again. Is the rule "past the end when the beam frames into another beam; just inside the end, across the beam, when it frames into a wall or a shaft"?
2. **The pocket's 12'-1"** (inside the pocket 5 rounds running): does "behind the core wall" count as no room outside, so the size goes inside the pocket?
3. **The pilaster hole's 3'-8"**: kept in round 4, deleted now. Is the overall needed when the `3'-0" | 8"` chain already spans the whole hole on the same line as its locating dim?
4. **The 5 review items** (incl. the 7'-11" CJ off grid 3 you added four rounds running): left out on purpose this time, or just not drawn in?
