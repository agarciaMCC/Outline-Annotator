# Edit-diff analysis — L3N test view, round 2 (tool placement vs Adolfo's second edit round)

Read-only, 2026-10-06. Inputs: `compare_L3N_edits2_segments.json` (segment by segment; ids could not be matched),
`snapshot_L3N_synthetic_current.json` (tool, 122 dims) vs `snapshot_L3N_after_edits2.json` (his, 123 dims),
`snapshot_L3N_before_edits2.json`, the run 68/69 reports and PNG, `analyst_L3N_round1.md`, the design doc status
(2026-10-06 entries), `dimensioning-rules.md`, `mcc_strings.py`, `mcc_layout.py`.

**Baseline check first.** The synthetic layout matches the view he actually edited (`before_edits2`) segment for
segment: 163 on the same line, 0 moved, 2 absent. So every "moved" below is his hand, not a baseline artefact.
To see directions I drew the tool lines (blue) and his lines (red) on the run-69 PNG (mapping fitted on the grid
lines: 19.8 px/ft, image x = 19.79·X − 2126, y = 4482 − 19.8·Y); crops are in the session scratchpad only.

**Headline:** 169 tool segments → **91 left (54%), 66 moved, 8 deleted; 4 added.** The 66 moved rows are **46 dims**
(chains count once per segment): 42 rows / 27 dims within 0.45", 9 rows / 7 dims between 0.45" and 1", 15 rows /
12 dims over 1". Scale 1/128: 1 paper inch = 10.7 ft; 1/4" = 2.7 ft.

**"R.O." suffix:** 17 shaft/core overall sizes carried it from the parallel session's uncommitted `mark_ro`. The
snapshots store values and positions only, not suffix text — whether he kept or removed "R.O." cannot be judged
from this data. Ask him, or re-snapshot with `Dimension.Suffix`.

---

## 1. The 1/4" nudges — several causes, not one

The 1/4" values themselves are fine: wherever the tool actually reached its first row (`FIRST_GAP_IN` / `OPEN_OFFSET_IN`
/ `BEAM_END_GAP_IN` 1/4") he left the dim alone (18 of 25 beam-width rows, 20 of 31 CJ rows, all `anchor|edges|anchor`
rows of the main core openings). What he nudged are dims that **did not get row 0** — pushed out one lane or slid along
by the layout's bookkeeping — and dims **sitting on something** (a beam, a beam end face, a CJ line). Direction is
mixed, which is why no single constant explains it: beam widths moved *toward* the beam end; dims on beams/CJs moved
*away* from what they sat on.

### M2. Beam width dims pulled in to ~1/4" past the beam end — 6 dims, 10 rows (0.21–0.43")
−32 `side|9|side` 3'-9"|3'-9" (x 348, lane 0 but slid 3 ft along the beam: `cand (1,0,3)`), −33 `anchor|sides`
1'-4½"|1'-0" (lane 2!), −46 `side|9|side` ("group" lane), −35 `side|B|side` 6"|6", −38 `side|2|side` 2'-5¾"|1'-6"
(beam#232) which he **swapped** with the jog check −73 `3'-11¾"` so the beam's own width sits nearest its end and the
slab jog check outside it. Also −90, the angled shaft's `4'-10¼"|3'-9¾"` chain pulled in 0.53" once the 12'-8½" row in
front of it went (see D4).
Cause: `candidates()`/`evaluate()` in `mcc_layout` — `STATION_GAP` with a parallel CJ dim whose span overlaps, the
`W_GROUP` "stack beside a placed dim" bonus, and slides along the beam axis (`W_SLIDE` 0.5/ft is cheaper than any
lane) all beat the first row. Rule he applies: **a beam's width dim is the first row past its end; other strings
(jog checks, CJ dims) go outside it.** Proposal: give beam-width strings a hard "row 0 unless blocked by an obstacle"
(no slide/lane trade), and order strings at one station by the distance of their own element (beam end nearer than
the slab jog). Module: `mcc_layout.candidates` (beam_width strings), `evaluate` (W_GROUP / slide).

### M3. Dim lines on or over a beam, a beam end face or a column — moved off — 10 dims, 12 rows
- **Along a beam, over it (2):** −23 `C | 3'-6" | end` + `8'-6⅜"` (0.34" off the beam to the open side), −79 `BB | 15'-3" |
  end` (0.25" off beam 14184520 onto the slab). `W_BEAM` 4 is soft; the beam-end dims run along the beam and the
  candidate inside the beam's width won. Rule (CLAUDE.md): "other dims stay off beams" → make a dim line *along* a
  beam's own axis inside its width a hard reject for beam-end strings. Module: `mcc_layout.evaluate` (W_BEAM branch).
- **On the end face of a beam (2 + 1 twin):** −20 `void edge → 10` 3'-9" and −21 `void edge → 11` 4'-1½" sat on the
  beam end faces (`cand (1,0,-4)`: slid the full 4 ft onto the end); he moved both 0.36" out. −98 is the twin of −20
  34 ft away on the beam band — the compare matched it to the same his-dim 20598674, so it is really a **deletion**
  (doubled void-edge dim, the one over the beam). `_parallel_edges` does include beam polygon sides, so check why the
  `EDGE_CLEAR` test (line ~526) let these through (overlap vs `END_TRIM`? beam `poly` missing for these beams?).
- **At a beam end / column (2):** −52 `CJ → 8` 5'-0" touched the beam end and its 24×30 column; moved 0.29" away.
  −74 `8"` jog check over the 36×24 column at the CJ corner, moved 0.35" up. Rule 14: keep clear of columns — the
  dim's *ends* touching a column (`END_TRIM` 0.6 ft) are being allowed.
- **Width dim past a framed end — his answers disagree (3):** −45 `side|10|side` sat on the big B band the grid-10
  beam frames into; he moved it 0.34" to the band's far edge. −34 `10 | 13'-5½" | side | 1'-0" | side` moved 0.75" to
  the other side of the band. But −44 `side|7|side` 1'-7⅛"|3'-10⅞" went the **opposite** way: the tool crossed the
  band to open margin 14 ft below; he brought it back to ~1" past the beam end, over the band. So "cross the other
  beam to open margin" (`do_beam.at_end`, `ext` 8 ft) is right when the margin is near and wrong when it is far —
  open question 3.

### M4. Dim line lying on a CJ running the same way — 3 dims
−68 `CJ → 8` 7'-0" sat on a horizontal CJ (moved 0.31" up, onto the line of the 3'-0" `CJ → 8` dim — joined);
−72 `CJ → EE` 4'-6" ran 0.3 ft off the vertical CJ 20572342 (moved 0.31" into the bay); −70 `CJ → 4` 4'-6" at the
same CJ corner moved 0.31" beyond grid EE. **CJ lines are not in `_parallel_edges`** (slab faces + beam polys only),
so `EDGE_CLEAR` never sees them. Proposal: add CJ lines to `_parallel_edges` (treat like an edge, 1/16" clear).
Module: `mcc_layout._parallel_edges`.

### M5. Lined up with a neighbour — 1 dim (+ −68 above)
−51 `CJ → 9` 19'-5⅛" moved 0.20" onto the line of the `beam end → 9` 28'-8⅛" dim. `W_COLLINEAR` −0.75 vs 2 ft of slide
(1.0) lost. Proposal: `W_COLLINEAR` −1.5, or don't charge slide when it buys a collinear line. Module: `evaluate`.

---

## 2. Moves over 1" and the opening groups

### M1a. Check strings put on the far side of their feature — he joined them to the first stack row — 5 dims, 7 rows
- −96 `15'-7"` (shaft#102's edge-to-edge check) sat on the shaft's left; he put it on the **same line** as the
  `EE | 7'-7½"` row on the right (both at x 290.03 → `EE | 7'-7½" | edge | 15'-7" | edge`, exactly his round-1 dim
  20591798 which was then *left*) and pushed `23'-2½"` outside (−14 +0.42, −15 +0.49). **Regression vs round 1.**
- −87 `edges|B|edges` 2'-5"|12'-5" (angled shaft) moved 1.81" from the shaft's NW side to beside the B stack
  `9'-6¾"|5'-3¼"` on the SE side (−105 shifted 0.27" to make room).
`W_SPLIT` 8 was built for locate rows of one element (run 63); check strings are placed last and apparently on the
"other" side. Proposal: apply `W_SPLIT` to checks of the same feature and offer the join spot with row 1 first
(`W_JOIN_SAME` already −6; it needs the candidate). Module: `mcc_layout.evaluate` (W_SPLIT), `candidates`.

### M1b. Locate dim standing over its own small opening — moved beyond the side and joined — 2 dims
−18 `FF | 7'-9" | edge` (3'-4" hole at (206, −20)) stood over the hole's span 0.4 ft from its edge line; he moved it
beyond the side onto the `3'-4"` check line (x 204.3 — joined). −112 `CC | 8'-0½" | edge` over the pilaster hole's span,
moved 0.41" beyond its side (where the deleted 3'-8" was). `W_OWN_SPAN` 2.5 is soft; make it hard for openings under
`SMALL_OPEN` (4 ft) — there is always room beside a small hole. Module: `evaluate` (W_OWN_SPAN).

### M1c. Small hole in the core wall (1'-5" × 3'-3"): its dims go beside it, inside the core — 2 dims, 3 rows
−114 `wall | 5" | edge | 1'-5" | edge` moved 1.04" (11 ft) from outside the core (the CJ strip above) to just below
the hole, inside the core; −86 `3'-3"` moved 0.86" from outside the core's left wall to right beside the hole
(x 216.9, one row out from the `7"` he left at 215.4). Both tool spots had **witness lines crossing a core wall**.
Proposal: witness lines crossing a wall cost like `W_WITNESS_CROSS` (hard for openings under `SMALL_OPEN`).
Module: `evaluate` / `_witness_passes`.

### M1d. Pilaster hole (3'-0" × 3'-8"), re-joined differently from round 1 — 2 dims, 4 rows
Tool (as he drew it in round 1): `7 | 13'-2¾" | edge | 1'-2" | 8" | 1'-2"` on one line below the hole. Now: `13'-2¾" |
3'-0"` joined at y 48.9 (locate + overall) and the steps `1'-2" | 8" | 1'-2"` on the **other** side (y 56.4), the
`3'-0" | 8"` chain +0.23". Two sides for one direction contradicts "one side per direction" and his own round-1 version.
No change until he says which join he wants — open question 5.

### M6. Pocket shaft rows (B2, still open) — 3 dims, 4 rows
Same three edits as round 1: `12'-1"` (−99) from the right/wall side to the left, 2.3 ft outside the step chain;
the step chain `4'-6" | CC | 7'-7"` (−118) joined and pulled to **0.07"** off the pocket edge; `7'-9½"` (−85) 0.41"
nearer the opening edge (1/4" off the *slab edge*, not off the wall). The design doc's run 65–67 note stands: it
needs a per-feature extent for step strings; the `STATION_GAP` "<" test rejects the exact fit.

### M7. Angled shaft jog — 3 dims
−80 `edge | 10'-2½" | 7` moved 1.87" (20 ft) from above the whole shaft down to the jog's own level (y 131.8),
and its other leg `6 | 12'-8½" | edge` deleted (D4). The string's span was the opening's full extent, so "beyond
its sides" meant 20 ft away; he wants a minor jog located **at the jog**. Proposal: a minor-edge string gets the
jog's own extent (`_extent` / `span` in `do_opening`), not the opening's. The two stepped-opening overalls he did
not draw in round 1 were **kept**: `14'-10"` −0.26" tighter to the core wall, `8'-8"` −0.64" — moved **inside** the
shaft (allowed for an overall when there is no room outside; worth a look at the crop before accepting).

### M8. NE corner re-stack — 3 dims (0.19–0.35")
−120 `11 | 2'-3½" | void edge`, −29 `1'-0" | 4'-2½"`, −28 `1'-3⅜" | 1'-8"` each stepped one row out after he deleted
the `11 | 1'-0½" | beam end` (D6) and inserted `11 | 1½" | slab edge` (A3) nearest the corner. Consequential; no rule.

### M9. The two parallel CJs off grid 5 (3 ft apart) — 2 dims + 1 added, 36 ft moves
−88 `5 | 7'-5½" | CJ` moved 3.37" (36 ft) to the CJ's bottom end; −57 `5 | 4'-5½" | CJ` 0.64" to the top end's first
row; `CJ | 3'-0" | CJ` (A1) added at the bottom end inside the 7'-5½". This is round-1 B3 (opposite ends + spacing
chain) **done again by hand after he answered "no rule" to both** (design doc, answers 2 and 3). Open question 1.

### M10/M11. Singles
−1 `A | 1⅜" | edge` moved 1.11" (12 ft) along the former-curb edge to the SW corner where it meets beam#232 — rule 3
(at every turn): the run's call-out belongs at its corner, 2 ft in (`CORNER_IN`), not mid-run. −66 `CJ → F` 4'-9" slid
0.72" (7.7 ft) along a CJ parallel to the F band, still crossing the band — unexplained.

---

## 3. The 8 deletions — which built rule each argues against

| group | rows | tool dim | he deleted | rule it argues against | module |
|---|---|---|---|---|---|
| **D1. Opening edges lying on a core wall face need no grid dim** | 2 | −10 `CC \| 14'-10" \| edge` (chain leg to the lower-left opening's top edge), −17 `stack 2 → CC` 14'-4" (upper opening's bottom edge) | both; kept `CC \| 8½" \| edge \| 13'-7½" \| edge` (left) and the lower opening's size `18'-2"` (moved to x 224) | The two edges face each other across the core's 6" cross wall; rule 4 "an edge lying on a wall face is located by the wall". `stack_from_anchor` still makes a row to such an edge and `do_opening` chains CC to it. Round 1 he **kept** 14'-4" — a flip; ask (question 4). | `mcc_strings.stack_from_anchor`, `do_opening` |
| **D2. Band width dimensioned once per band, not per piece** | 2 | −40 `beam anchor\|sides` 4'-11¼" \| 5'-6" (beam 14185801, the F band) | yes | The band already has `side \| F \| side` 2'-9"\|2'-9" at (234, −16) 10 ft away and at (334, 42). `continues()` suppresses the dim at a joint but each piece still gets one at its other end. | `do_beam` (`continues`, `b_parts`) |
| **D3. "Stepped opening overall" when the step is at an end** | 1 | −78 `3'-8"` (pilaster hole: 3'-0" hole + 8" notch) | yes; kept the other direction's `3'-0"` over `1'-2" \| 8" \| 1'-2"` and even joined it to the locate dim | 3'-8" is hole + notch depth — a number the field never sets out; the chain `3'-0" \| 8"` already has the real size. Proposal: overall only when the chain has ≥ 3 segments (step inside the extent), or when no chain segment equals the main size. | `do_opening` ("stepped opening overall") |
| **D4. A single jog edge from the nearest grid only** | 1 | −80 `6 \| 12'-8½" \| edge` (angled shaft's 1'-6" jog, far leg) | yes; kept `edge \| 10'-2½" \| 7` | Third time (run 44 removal, round 1 re-add, run 55 `grid \| 9'-11" \| … \| 7`): one edge → nearest grid, not both (12'-8½" vs 10'-2½" differ by 2.5 ft; the "both grids" rule is `CJ_MID_TOL` 1.5 and CJ-only). | `do_opening` (minor-edge / `anchor` both sides) |
| **D5. Void edge lying on a beam side = located by the beam** | 1 (+ twin −98) | −95 `void edge → B` 3'-9" (= the B band's side, 7'-6" wide) | yes | `flush(e, beams)` marks runs as "beam face" but void edges are dimensioned edge by edge without that test. He kept −20/−21 (grid 10/11 void edges, same situation, at beam ends) — so skip only when the band's `side\|grid\|side` already gives that face nearby (< ~15 ft)? Ask (question 6). | `do_opening` (void branch), `flush` |
| **D6. Beam end at the corner column** | 1 | −119 `11 \| 1'-0½" \| beam end` (beam 14181349, NE corner) | yes — **same as round 1** ("bad model geometry"); and added `11 \| 1½" \| slab edge` again (A3) | The end sits at the 18×18 corner column → framed, not free (`free_ends` in `mcc_features` ~line 326). Propose: an end within ~1 ft of a column face counts as framed. | `mcc_features` (free/framed ends) |

## 4. The 4 additions

| | his dim | what | reading | module |
|---|---|---|---|---|
| A1 | 20599680 `CJ \| 3'-0" \| CJ` at (190, −26) | spacing of the two parallel CJs off grid 5, inner row at the bottom end | round-1 B3b again, after "no rule" — question 1 | `do_cj` |
| A2 | 20598996 `2 \| 2'-5¾" \| slab edge` at (126, 115) | the slab's vertical edge at x 122.8 is flush with beam#232's side (so "located by beam face", no dim) — but it runs 7 ft past the beam's end to the corner with the angled edge; he located that corner | an edge flush with a beam face is located only along the beam; past the beam's end (at a corner) it still gets its grid dim — rule 3 | `do_run` (`flush` → "beam face") |
| A3 | 20599104 `11 \| 1½" \| slab edge` at (325, 205) | NE corner sliver, **same as round 1** (20593461) | the straight-grid twin of the `A \| 1⅜" \| edge` call-outs built in run 68; blocked by "slab edge on a column face (skipped)" (16 on L3N). Propose: a slab edge within ~6" of a grid gets its call-out even on a column face. | `do_run` (column-face skip) |
| A4 | 20598835 `edge \| 3'-11⅛" \| B` at (223.5, 137.6) | angled shaft, **same as round 1** (20593985), still unexplained | not 5'-3¼" − 1'-6"; probably the edge the planner notes as "short edges off its grid set skipped (aligned grid near)" (1 on L3N). Question 7. | `do_opening` (MINOR_EDGE skip) |

## 5. Round 1 → round 2: what held, what he re-edited

**Held (he left them alone):** CJ halfway between grids from both (3 chains −108/−109/−110); far edge through grid BB
`edge | 9'-3⅞" | BB | 8'-4⅛" | edge` + `17'-8"`; elevator shaft off grids `8'-3" | 11'-9"` (3 rows); the `8½" | 13'-7½"`
join; the `5" | 1'-5"` join (kept joined, moved as one); curb call-outs `A | 1⅜"` / `6⅜"` (3 of 4); both jog checks kept
(`3'-11¾"`, `8"`, moved not deleted); the `7'-3⅛"` step dim off the 16'-4" line (witness-cross rule); slots core#125/126
to the enlarged plan (nothing drawn back); CJ dims past the end (20 of 31 CJ rows left); the beam#232 width past the
crop (kept, re-ordered); grids-before-walls at the core; `MIN_GAP` 1/16" (no opening row moved *out*).

**Re-edited / repeated from round 1 (he did the same thing twice):** pocket rows B2 (M6, 3 dims); the 12'-8½" leg
removed (D4); NE corner beam end deleted + 1½" sliver added (D6/A3); CJ pair at opposite ends + 3'-0" spacing
(M9/A1); `edge | 3'-11⅛" | B` (A4); the `10'-2½"` placed at the jog (M7).

**Regressions (round 1 fine, round 2 edited):** `EE | 7'-7½" | edge | 15'-7" | edge` — one dim he left in round 1,
now split into stack + far-side check (M1a).

**Flips (he changed his own mind):** `14'-4"` kept in round 1, deleted now (D1); the pilaster-hole join (M1d).

**Cannot judge:** "R.O." on 17 overalls (no suffix in the snapshots).

---

## Proposed order of changes

1. **M1a + M1b** — `W_SPLIT` for check strings of the same feature, join spot with row 1 offered first; `W_OWN_SPAN`
   hard for openings < 4 ft. 7 dims incl. the round-1 regression (15'-7"). Layout only.
2. **M4** — CJ lines into `_parallel_edges` so `EDGE_CLEAR` applies. 3 dims, a few lines.
3. **M2** — beam width = row 0 past the end unless an obstacle; order strings at one station by their own element's
   distance (beam before slab jog). 6–7 dims. Check also why −20/−21 passed `EDGE_CLEAR` on the beam end faces.
4. **M3 (on-beam part)** — hard reject for a beam-end dim running along its beam inside the beam's width; dim ends
   not on a column. 6 dims. Leave the "past a framed end" direction until question 3.
5. **D1** — no stack row / chain leg to an opening edge on a core wall face. 2 deletions; confirm with question 4 first
   (he kept 14'-4" in round 1).
6. **D3 + D4 + D2** — stepped overall only with ≥ 3 chain segments; single jog edge → nearest grid only; one width per
   in-line band. 4 deletions, planner only.
7. **D6 + A3 + A2** — beam end at a column = framed; sliver call-out off a straight grid despite a column face; run past
   a beam's end located at its corner. 3 items, all repeats from round 1.
8. **M7** — minor-jog string gets its own extent. 1 dim, plus the `4'-10¼" | 3'-9¾"` row that then comes in by itself.
9. **M1c** — witness lines through a wall (small holes in core walls). 2 dims.
10. **M5** — `W_COLLINEAR` stronger. 1–2 dims.
11. Wait for answers: M9/A1 (CJ pair), M1d (pilaster join), D5 (void edges on beam sides), A4 (3'-11⅛"), M6 (B2).

## Open questions for Adolfo

1. The two CJs 3 ft apart off grid 5: you answered "no rule" for opposite ends and for the CJ-to-CJ 3'-0", but you drew
   both again (7'-5½" at the bottom end, 4'-5½" at the top, 3'-0" inside the 7'-5½"). Is this the rule for parallel CJs
   closer than ~4 ft?
2. "R.O." on the 17 shaft/core overalls — did you keep it, remove it, or change where it goes? (The snapshot can't tell.)
3. Beam width past a framed end: at the grid-7 beam you pulled it back onto the F band (~1" past the end) instead of the
   open margin 14 ft away; at the grid-10 beam you moved it to the far edge of the band it crosses. Rule: "cross the
   other beam only if open slab is within N ft, else sit on it"? What N?
4. Elevator core: you deleted `CC | 14'-4"` (upper opening's bottom edge) and `CC | 14'-10"` (lower opening's top edge)
   — both edges on the 6" cross wall — but kept 14'-4" in round 1. Rule: an opening edge on a core wall face gets no grid
   dim, only the chain from the anchored edge?
5. Pilaster hole: round 1 you had `7 | 13'-2¾" | 1'-2" | 8" | 1'-2"` on one line; now `13'-2¾" | 3'-0"` below and the
   steps above. Which join, and is one direction on two sides OK here?
6. Void edges on beam sides: you deleted `B | 3'-9" | void edge` (the band's side, width already dimensioned) but kept
   `10 | 3'-9"` and `11 | 4'-1½"` at the beam ends. Keep a void edge dim only where no beam width dim is nearby?
7. `edge | 3'-11⅛" | B` at the angled shaft — second time you've added it. Which edge is it, and why off B?
8. The `8'-8"` overall of the angled shaft now sits inside the shaft (0.64" from where the tool had it outside). Intended
   ("no room outside"), or a slip?
