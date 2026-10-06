# Edit-diff analysis — L3N test view, round 4 (run 84 vs Adolfo's fourth edit round)

Read-only, 2026-10-06. Inputs: `compare_L3N_edits4.json` (id-based, 120 rows), `compare_L3N_edits4_segments.json`
(162 rows), `snapshot_L3N_before_edits4.json` (run 84, 119 dims) / `snapshot_L3N_after_edits4.json` (his, 118 dims),
`dimsoffit_v2_L3N_run84.md`, `analyst_L3N_round3.md`, the design-doc entries after round 3, `dimensioning-rules.md`,
`mcc_strings.py`, `mcc_layout.py`. Ids matched (clean round).

**Headline:** 119 tool dims → **70 unchanged (59%), 47 edited, 2 deleted; 1 added** (round 3: 78 / 39 / 2 / 4).
By segment 110 left / 48 moved / 3 deleted / 1 added. Fewer dims survived than in round 3, but almost all of the extra
edits are nudges: 30 of the 47 edits are ≤ 1/2" (18 ≈ 1/4", 12 ≈ 1/2"), and 11 of the 17 bigger ones trace to two
causes (§G1 framed-end beam widths, §G2 stack rows sliding into their opening). Scale 1/128: 1/4" = 2.7 ft.

**R.O.:** 11 of 11 kept; **1 restored** — `13'-7½"` (core#115) had its R.O. in run 75 and lost it in run 84 when the
layout joined it onto `CC | 8½" | edge` (`_join_collinear` copies the first string only; `suffix_pairs` are built by
`mark_ro` for planner chains, never for layout joins — `mcc_layout.py` ~987, ~1220). He put it back. The `18'-2"`
string field changing from `18'-2"R.O.` to `18'-2"` is a Revit artefact (ValueString carries the suffix on
multi-segment dims only) — he cut the chain to one segment, the suffix is still there. Fix: in `_join_collinear`,
carry a 2-ref partner's `suffix` into `ns.suffix_pairs` as `(a, b, suf)`.

---

## 1. Round-3 fixes and answers: what held, what regressed

| Built after round 3 | Held? | Evidence |
|---|---|---|
| (1) no home-side string inside its own element (`candidates` clamp) | **Half** | CJ / beam-end / chain strings: none inside. **Stack rows missed**: they have no home side (`outward=None` for core/shaft, `away = 0` in `do_opening` ~446; copied at `stack_from_anchor` ~1293) so the clamp (`if home and …`, ~822) never sees them. Three slid 1.3 ft inside again: `EE \| 7'-7½"` 20602746 (2nd time), `edge \| 7'-9" \| FF` 20602750 (**3rd**), `7 \| 13'-2¾"` 20602751 |
| (2) beam-end dim never along its own beam | **Yes** | `end \| 3'-6" \| C \| 8'-6⅜" \| end` 20602757, `end \| 15'-3" \| BB` 20602830 unchanged |
| (3) `W_BEAM_ROW` on group / collinear / align spots | **Yes for free ends** | 10 free-end widths unchanged (#220, #223, #226, #228, #230 ×2, #233, #249, #250); 3 nudged ≤ 0.35" (#232, #248, #222). All 5 big width moves are **framed** ends — §G1 |
| (4) `MIN_GAP_IN` 0.15" | **Openings only** | No opening row at 1/16". Still hugging and moved out: `end \| 6'-4" \| BB` 20602758 (0.06" → 0.25", **2nd time**), `CJ \| 4'-9" \| F` 20602795 (0.06" → other side 0.20"), jog `8"` 20602805 (0.06" → other side 0.26", **2nd time**). `evaluate` ~569 gates the MIN_GAP / W_GAP block on `f.kind == "opening"` |
| (5) dedupe after join | Yes | nothing deleted as a duplicate |
| (6) beam end at a column = framed; (7) `MINOR_EDGE` off; corner refs | **Yes** | no `1'-0½"` end dim, no sliver added (first round without it); `B \| 3'-11⅛" \| corner` produced and kept (moved onto row 1, §G3); `BB \| 12'-1⅜" \| corner` unchanged. The two corner dims he "didn't draw" (`A14 \| 1½"` 20602803, `B \| 3'-4¾"` 20602826) he **left** — keep them |
| (8) `W_GROUP` same element | Yes | grid-9 / grid-8 cluster unchanged (`19'-5⅛"`, `28'-8⅛"`, `5'-0"`); `8 \| 3'-0"` / `8 \| 7'-0"` nudged ≤ 0.08" |
| Answer 1: CJ pair may take the other end (`String.alt`) | **Half → §G5** | `7'-5½"` took the bottom; the chain `4'-5½" \| 3'-0"` stayed at the top and he moved it to the bottom — **4th round**. `W_ALT` 1.0 lets the two strings split across the ends; the pair is not coupled |
| Answer 2: framed-end width "over the band" | **Contradicted → §G1** | He reads it **across the beam, inside the end** (5 dims). Two of them (#224, #242 bottom) were inside in run 75 and he had left them there; run 84 pushed them 21–26 ft past the end and he put them back |
| Answer 3: one face on a column no longer skips a step | Yes | `BB \| 12'-1⅜" \| corner` kept |

---

## 2. Groups (by cause, largest first)

### G1. Beam width at a FRAMED end: across the beam, 2–6 ft inside the end (5 dims + 2 consequential) — `do_beam.at_end`, `candidates` clamp, `evaluate`
He moved every framed-end width off the "past the end" spot and onto the beam, just inside its end:
- `side \| 1'-0" \| side \| 13'-5½" \| 10` beam#229 20602768: 0.44" past → 3.4 ft inside (**3rd round**, round 2 M3, round 3 G2).
- `side \| 1'-7⅛" \| 7 \| 3'-10⅞" \| side` beam#242 top 20602774: 0.67" past (into beam#235) → 2.3 ft inside (2nd round).
- Same beam, bottom 20602848: `reordered` to **1.95" (21 ft) past** the end → 5.1 ft inside, exactly where run 75 had it (20600918, which he left in round 3).
- `side \| 4'-0" \| side \| 1½" \| 11` beam#224 20602812: `(-1, 5, -10)` wider search, 2.48" past → 3.8 ft inside, exactly run 75's spot (20600916, left in round 3).
- `side \| 2'-9" \| F \| 2'-9" \| side` beam#235 20602822: 0.34" past → 6.5 ft inside (it had been left in round 3; the free end there now carries `end \| 10⅞" \| A6` and beam#242's width — clutter).
- Consequential: run#7's `edge \| 3'-4½" \| 7` 20602847 and `7'-9½" R.O.` 20602849 pulled in one lane each once the beam width left from between them (`_order_stacks` had grouped the three as one stack — a beam width 16 ft from its beam end sorted by length against a slab edge's rows).

Mechanism: `at_end` (~661) makes the framed end's span "just past the end over the band"; the round-3 clamp (~822) deletes every spot inside the beam; `evaluate` ~552 hard-rejects "over a wall", so an end framed into a core wall (#242 bottom, #224) has **no legal spot near its end at all** and the width drifts 20+ ft until the slab is clear. Adolfo's answer 2b was recorded as "over the band"; his hand says across his own beam. **Contradicts the design-doc entry — Adolfo decides (question 1).**
Proposal (one change): in `at_end`, when the end is framed and no open slab lies within `FRAMED_CROSS`: `span = (e_st − 6, e_st − 1)` on the beam, `prefer = e_st − 3`, flag `s.inside_end = True`; exempt such strings from the clamp and from `W_OWN_BEAM` (~504) like intermediates. Free ends keep "past the end".

### G2. Stack rows slid into their opening — fix (1) missed home-0 strings (3 dims + 4 knock-on) — `candidates` ~822
Same disease as round-3 G1, same three spots, now only the stack rows: `EE \| 7'-7½" \| edge` 20602746 (shaft#102), `edge \| 7'-9" \| FF` 20602750 (shaft#118, 3rd time), `7 \| 13'-2¾" \| edge` 20602751 (shaft#119). The home-0 branch (~682) starts lanes at `edge ± FIRST_GAP` and the slide `k = −4` lands 1.3 ft inside; `W_OWN_SPAN` 2.5 is cheaper than whatever refused the k = 0 spot. Knock-on, as round 3 predicted: with the row inside, `W_SPLIT` sees side 0 and the size check goes wherever — `15'-7" R.O.` 20602825 to the other side (**4th round**, 2.12"), `23'-2½"` 20602747 re-stacked out (0.22"), shaft#119's `3'-0"` 20602828 and shaft#118's `3'-4" \| 8" \| 6` 20602838 moved to join their rows (§G3).
Proposal: apply the clamp to **locate** strings of openings whatever their home (`home == 0` included); keep the through-the-span `W_INSIDE` spots for size checks only.

### G3. An opening's size on the same line as its locating row (6 joins, ~8 dims) — `candidates` join / `evaluate`, `do_angled_corners`
He joined, by hand, in every case where the tool kept them apart:
- shaft#102: `EE \| 7'-7½" \| edge \| 15'-7" R.O. \| edge` on one line at x 289.0 (round 2 M1a, round 3 G3, now 4th).
- shaft#119, both directions: `7 \| 13'-2¾" \| edge \| 3'-0" \| edge` at y 48.5; `CC \| 8'-0½" \| edge \| 8" \| edge \| 3'-0" \| edge` at x 252.8 (20602840 + 20602839). The step chain `1'-2" \| 8" \| 1'-2"` 20602810 went to the other side (y 56.0, re-drawn to face refs), the `3'-8"` overall outside at x 255.3.
- shaft#118: `FF \| 7'-9" \| edge \| 3'-4" \| edge` at x 203.3 (3rd round for this hole).
- shaft#114: the corner call-out `B \| 3'-11⅛" \| corner` 20602846 from its own lane (`(-1, 'group', 0)`, 0.72") onto the first B row: `edge \| 7'-1¾" \| B \| 3'-11⅛" \| corner` (0.16"). The join candidate exists (same feature, shared witness line at B, `W_JOIN_SAME` −6) and was not taken — `late` placement meets the `9'-6¾" \| B \| 5'-3¼"` row already one lane out; the reject reason is unknown without a debug run (round-3 G3 asked for the same log).
- core#110: `18'-2" R.O.` moved to x 224.2 — the line of core#115's `CC \| 8½" \| 13'-7½" R.O.` — one vertical line for the two openings' sizes on the core's right side (different elements: rule 15 "share a line with a neighbour").
Four of the six fall out of G2 (the row inside the opening makes the join spot illegal). Then log the refused join for the corner and shaft#119's CC side.

### G4. First row at ~3/16", never 1/16" (10 + 3 dims) — `FIRST_GAP_IN`, `MIN_GAP` scope
- Lane-0 rows at 0.25–0.5" pulled in to **0.12–0.19"**: `8'-3" R.O. \| 11'-9"` 20602742 (0.25 → 0.12), `edge \| 1'-1½" \| 8` 20602748 (→ 0.16), beam#232 width 20602770 (→ 0.14), beam#248 width 20602775 (0.51 → 0.16), `8 \| 3'-0" \| CJ` 20602796 (→ 0.19), shaft#114 chain 20602820 (0.72 → 0.18, lane 1 → 0, round-3 G10 again), `7'-1¾" \| B` 20602844 (→ 0.16), `3'-4½" \| 7` 20602847 (→ 0.18), `3'-0"` 20602828 (→ 0.17), corner 20602846 (→ 0.16). Rows he left at 0.25" exist too (beam#220, #223 …), so his band is 0.12–0.25".
- Rows hugging at 1/16" pushed out to 0.20–0.26" (3, two of them repeats — table row 4).
Proposal: `FIRST_GAP_IN` 0.25 → 0.19 (= one `LANE_STEP`; one constant, check the 0.25" rows don't move), and the MIN_GAP / W_GAP block in `evaluate` for every feature with an extent (cj, beam, step), not `opening` only.

### G5. The CJ dims at the cross-CJ junction: bottom end, one line (2 dims + the 7'-11", 4th round) — `do_cj`
`5 \| 4'-5½" \| CJ \| 3'-0" \| CJ` 20602835 moved 35 ft to the bottom (y −25.8); `5 \| 7'-5½" \| CJ` 20602794 (already bottom via `alt`) pushed out one row (−28.2); his added `3 \| 7'-11" \| CJ` 20605253 sits **on the chain's line** (y −26.0). All three vertical CJs (20572303, 20572317, 20572305) end at the horizontal CJ 20572304 (y ≈ −23.4, whose own dims `CJ \| 13'-3" \| FF` stand at x 146.6 / 194.4): their dims go on one line 2.4 ft past that junction, the longer one outside. `natural_end` (~787) picks the end with no member 2 ft past it; `alt` lets each string choose separately, so the pair split.
Proposal: in `do_cj`, an end where the CJ meets a crossing CJ (T-junction) is the home end (over "open slab past it"); the pair's strings share that decision (drop `alt` when a junction end exists).

### G6. The elevator core (core#110 / #115 / #120): 5 dims — `stack_from_anchor`, `do_opening`
- `edge@wall \| 18'-2" R.O. \| edge \| 14'-10" \| CC` 20602741: the `14'-10" \| CC` leg **deleted** (rounds 1, 2, 4; left in round 3) and the `18'-2" R.O.` moved to the core's right side. Why the tool keeps it: `stack_from_anchor` tests "a stacked dim would pass the 30 ft tape" (~1252: 14.83 + 18.17 = 33 ft) **before** the core rule "near edge only off the outside grid" (~1265), so the chain is kept whole with the grid leg — the one firing of that note on L3N. But he does not want `CC \| 14'-10" \| edge` either (deleted as a stack row in rounds 1–2), while he keeps `8'-3" R.O. \| 11'-9" \| 7` on the same opening every round. The difference is not in the code's terms (both have `edge@wall`) — question 2 (is the opening's top edge on a wall too? then `hi_wall` should have fired and `flush` missed it).
- core#115's `8'-3" R.O. \| 11'-9" \| 7` 20602816: run 84 stacked it at `(1, 2, 3)` **3 ft from core#110's identical chain** (y 53.1 vs 49.9); he moved it 31 ft to y 84.5, the core's far end — where run 75 had it (20600920, left in round 3). Regression; the identical neighbour reads as a double. Proposal: an opening's chain never within 2 lanes of another opening's chain with the same values and offsets (treat as `W_SPLIT`-class clutter), or home side away from the neighbouring opening.
- core#120 `wall \| 5" \| edge \| 1'-5" \| edge` 20602843: to the other side of the hole (below 0.53" → above 0.20") — **3rd round, same move** (M1c). Its partner `edge \| 3'-3" \| edge \| 7" \| wall` 20602841 unchanged.
- core#115 `CC \| 8½" \| edge \| 13'-7½"` 20602833: 0.16 → 0.29" and the R.O. put back (see top).

### G7. NE corner cluster (3 dims) — `_order_stacks` grouping gap
`side \| 1'-0" \| side \| 1'-3½" \| 11` beam#222 20602763 in (0.77 → 0.58"), `edge \| 2'-3½" \| 11` void#109 20602755 out (0.44 → 0.81"): equal lengths, the beam-width chain inside and the single outside — exactly the `_order_stacks` tie rule, but the two were 1.76 lanes apart (gap limit 1.5) so never grouped. `A \| 1'-3⅜" \| side \| 1'-8" \| side` beam#221 20602762 stepped out 0.29" with them (consequential).

### G8. Jog checks (2) — `do_step`
`3'-11¾"` 20602804: 0.63 → 0.36", one row outside beam#232's width once that came in (consequential, order now right). `8"` 20602805 step#182: 0.06" one side → 0.26" the other side — **2nd round, same move** (round-3 G5); the side needs a picture, the gap is G4.

### G9. Angled shaft#114 (7 edits; answer to focus 1) — `do_opening`, `do_angled_corners`
The new corner dim and the `14'-10" R.O.` inside the shaft did **not** cause the moves: the `14'-10" R.O.` 20602814 he **left inside the shaft**; the B stack only nudged (`7'-1¾"` 0.34 → 0.16, `9'-6¾" \| 5'-3¼"` 0.53 → 0.65, `10'-2½" \| 7` slid 0.18"). The real moves: the corner call-out joined row 1 (§G3, 0.56"); the chain check `edge \| 2'-5" \| edge \| 12'-5" \| edge` 20602815 left the shaft's interior for the B stack's second row (0.53"); `edge@wall \| 4'-10¼" \| edge \| 3'-9¾"` 20602820 lane 1 → lane 0 (0.54", **2nd time**) with the `8'-8" R.O.` 20602818 following in (0.91 → 0.64"). Open since round 3: what blocks lane 0 for the 4'-10¼" chain (the 8'-8" text, probably).

### Singles / noise
`edge \| 16'-4" \| BB` 20602734 slid 0.15"; `3'-8"` 20602809 0.44 → 0.58" (re-stack); 20602841 text only.

---

## 3. Deletions (3 by segment)
| | tool dim | why | module |
|---|---|---|---|
| D-a | `14'-10" \| CC` segment of 20602741 | §G6 — the grid leg of a wall-located core opening (3 of 4 rounds) | `stack_from_anchor` order of tests; `do_opening` wall detection — question 2 |
| D-b | `edge \| 8" \| wall` 20602806, notch#0 | notch#0 is on the run report's "for an enlarged plan" list, yet `do_shaft_pockets` (~857) still makes a size string for its edge (it never consults `cluttered_small`). He deleted it and put the pocket's `12'-1" R.O.` where it stood. (Left in round 3 when the 12'-1" was elsewhere.) | `do_shaft_pockets`: skip edges of features in the enlarged-plan set |
| D-c | `C \| 8'-6 7/16" \| end` 20602813, beam#238 | placed on the wider search (`(-1, 2, -11)`: lane 2, 11 ft from the end). beam#249's chain `end \| 3'-6" \| C \| 8'-6⅜" \| end` (unchanged) states the same 8'-6⅜" off C — the two ends are in line. Left in round 3. Either "a repeat" (contradicts rule 2) or "too far from its beam to read" — question 3 | `do_beam` free ends / `place_one` wider search → review instead of place |

## 4. Additions (1)
| | his dim | what it is | module |
|---|---|---|---|
| A-a | `3 \| 7'-11" \| CJ` 20605253 at (145.3, −26.0), refs grid 3 ↔ CJ 20572305 | **4th time.** Grid 3 is at x 141.3 (from beam#233's `3'-4" \| 3 \| 2'-8"`), so the CJ is a vertical line at x ≈ 149.2 — the same x where the horizontal CJ 20572304 ends (its dim `CJ \| 13'-3" \| FF` stands 2.6 ft west, at x 146.6). The planner has 31 CJs and dims 23; the 7 "CJ on a beam side or slab edge (skipped)" + 1 on-grid are the rest, so 20572305 is one of the 7. No beam side is at x 149 (beam#233's are at 138.0 / 144.0); the likely hit is `flush(cj, slab_faces)` (~763) against a **floor-to-floor seam** — `slab_faces` is every edge of every floor element, seams included, and a seam gets no run dim of its own, so the CJ on it is located by nothing. `do_cj` cannot tell us: the note carries no id. | `do_cj`: (a) put the CJ id and the member hit into the note; (b) skip only when the flush edge is one the planner dimensions (a slab outline edge in a run/step feature), never a seam between two floors |

---

## 5. The 1/4" and 1/2" nudges — direction
- **Closer (15):** ten first rows to 3/16" (G4); shaft#114 chain + overall (G9); beam#222 (G7); jog `3'-11¾"` and run#7's rows after a neighbour left (G1, G8).
- **Further (11):** three rows off 1/16" (G4); re-stacks after a join or insert (`23'-2½"`, `3'-8"`, `9'-6¾" \| 5'-3¼"`, beam#221, void#109, `7'-5½"`, `8'-0½" \| CC`); core#115's chain (G6).
- **Onto the element (6):** five framed-end beam widths (G1) + the pocket's `12'-1" R.O.` 20602831 read **through the pocket** at x 235.7 like a shaft width (the tool stands it 0.34" beside the pocket; `do_shaft_pockets` gives it a home side, so the through-the-span spots never exist) — 4th round for this dim, a different spot each time but never beside the pocket.
- **Out of the element (4):** three stack rows (G2) + the shaft#114 chain check (G9).
- **Other side (8):** `15'-7" R.O.`, shaft#118's `3'-4" \| 8" \| 6`, shaft#119's step chain (G2/G3); CJ pair chain (G5); core#120 (G6); `18'-2" R.O.` (G6); `CJ \| 4'-9" \| F`, jog `8"` (G4).

---

## Proposed order of changes
1. **G1** — framed-end beam width across the beam inside its end (`at_end` span/prefer, clamp and `W_OWN_BEAM` exemption). 5 dims, three of them repeats, two of them run-75 placements he had accepted. Confirm with question 1 first — it reverses the recorded answer 2b.
2. **G2** — clamp home-0 locate rows of openings. 3 dims + 4 knock-on, two 3rd/4th-round repeats; most of G3 follows.
3. **G4** — `FIRST_GAP_IN` 0.19; MIN_GAP for cj / beam / step features. 13 dims, two constants and one `if`.
4. **R.O. on joins** — `suffix_pairs` in `_join_collinear`. 1 dim, cannot regress.
5. **G5** — CJ home end at a cross-CJ junction, pair coupled. 2 dims + the added one, 4th round.
6. **A-a** — `do_cj` note with ids; seam edges don't count as slab edges. 1 dim, 4th round.
7. **G6** — core trim before the 30 ft test (D-a), identical-chain spacing (core#115), core#120 side (3rd round); after question 2.
8. **D-b** — `do_shaft_pockets` honours the enlarged-plan set; the pocket size through the pocket (home 0). 2 dims.
9. **G3** — log the refused join for the corner → row 1 and shaft#119's CC side; **G7** `_order_stacks` gap 1.5 → 2 lanes; **D-c** after question 3; G9's lane-0 blocker; jog `8"` side (G8).

## Open questions for Adolfo (each answerable with one picture)
1. **Beam widths at framed ends** (picture: beam#242 at grid 7, both ends, and beam#229 at grid 10): the note from round 3 says "past the end, over the band it frames into" — this round you put all five across the beam itself, 2–6 ft inside the end. Rule: "at a framed end the width is read across the beam just inside the end; past the end only when the end is free"?
2. **The 18'-2" elevator opening** (picture: core#110 with the `14'-10" \| CC` leg): you cut the leg to CC three rounds out of four but keep `8'-3" R.O. \| 11'-9" \| 7` on the same opening. Is the opening's top edge also on a wall face (so the R.O. from wall to wall locates it, no grid needed up-and-down)? If yes the tool is missing that wall.
3. **`C \| 8'-6 7/16" \| end` at beam#238** (picture: the NE beams off grid C): you deleted it this round, left it last round. Is it a repeat of beam#249's `8'-6⅜"` (the two ends are in line), or was it simply too far from its beam (11 ft) to read?
4. **The `8"` jog check at the beam#231 end** (picture: step#182): twice now you have moved it from one side of the step to the other at 1/4". Which side, and why — away from the `6'-4" \| BB` end dim?
