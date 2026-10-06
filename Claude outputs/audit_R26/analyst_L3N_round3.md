# Edit-diff analysis — L3N test view, round 3 (run 75 vs Adolfo's third edit round)

Read-only, 2026-10-06. Inputs: `compare_L3N_edits3.json` (id-based, 123 rows), `compare_L3N_edits3_segments.json`
(165 rows), `snapshot_L3N_before_edits3.json` (run 75, 119 dims) / `snapshot_L3N_after_edits3.json` (his, 121 dims),
`dimsoffit_v2_L3N_run75.md`, `analyst_L3N_round2.md`, the design-doc status entries of 2026-10-06, `dimensioning-rules.md`,
`mcc_strings.py`, `mcc_layout.py`. Ids matched this time (same view), so every row below is his hand.

**Headline:** 119 tool dims → **78 unchanged (66%), 39 edited, 2 deleted; 4 added** (round 2: 54% left by segment).
Of the 39 edits, 2 are text-only (pulled text put back on the line), 2 are slides along the element, 35 are real moves:
15 ≈ 1/4", 12 ≈ 1/2", 8 over 3/4". Scale 1/128: 1 paper inch = 10.7 ft; 1/4" = 2.7 ft.

**R.O.:** all **12 kept**, none added, none removed, no value or string changed (`suffix` field identical before/after
on every segment; the three `8'-3"` chains carry it on the width segment only, as built). Closed.

---

## 1. What held from round 2, what he re-edited

| Round-2 change (design doc 2026-10-06) | Held? | Evidence |
|---|---|---|
| Core openings: outside anchor → near edge + size only (14'-4" / 14'-10" gone) | **Yes** | `core opening anchor\|edges\|anchor` 3/3 unchanged, stepped overalls 4/4 unchanged, nothing drawn back |
| Angled far leg off a straight grid dropped (12'-8½") | **Yes** | not re-added; `edge \| 10'-2½" \| 7` unchanged |
| R.O. threshold 4 ft | **Yes** | 12/12 identical |
| Beam width = first row (`W_BEAM_ROW`) | **Half** | the 14 width dims placed through plain lane candidates were all left; the 7 he edited all came from the `group` / `collinear` / `align` candidate families, which **do not add `W_BEAM_ROW`** (`candidates()` lines ~732–789: only `W_COLLINEAR` / `W_GROUP` / `W_ALIGN` + side + outside). Last round 8 at ~0.43"; now 7, at 0.16–0.38" (plus 2 framed-end ones over 0.8", §3) |
| Beam-END dim never along a beam | **No** | the two dims the rule was written for, `end \| 3'-6" \| C \| 8'-6⅜" \| end` (20600860) and `end \| 15'-3" \| BB` (20600914), were moved off the beam **again** (0.38" each). Both lie on the string's **own** beam — the rule at `evaluate` ~534 says "along *another* beam"; the own beam is not an obstacle to its own strings |
| CJ lines as edges (`EDGE_CLEAR`) | **Mostly** | CJ dims 21 unchanged / 8 edited (round 2: 20 of 31 rows left); the 8 edits are the slide and pair problems below, not on-CJ |
| CJ pair: one shared end + spacing | **Half** | he kept the join `4'-5½" \| 3'-0"` with `7'-5½"` outside, but moved both **35 ft to the bottom end** — third round running (doc: "Open: he chose the bottom end there, the tool the top") |
| `elem_side` from the feature extent (`W_SPLIT` for the 15'-7") | **No** | 15'-7" went to the far side again (2.06"). Its stack row `EE \| 7'-7½"` was slid 4 ft **into** the opening's span (side 0), so `W_SPLIT` had nothing to compare with |

**Repeated from round 2, no fix built yet (he did the same thing a second or third time):** pocket B2 (`12'-1"` to the left,
step chain pulled in), core-wall hole M1c (`wall | 5" | edge | 1'-5" | edge` moved into the core beside the hole, 1.07"),
small-opening M1b (`FF | 7'-9"` beyond the hole's side, 0.34"), beam#232 width ↔ jog-check swap (M2), run → A call-out to the
corner (M10, 1.10"), beam end at the corner column deleted + 1⅜" sliver added (D6/A3, third time), `edge | 3'-11⅛" | B`
added (A4, third time), framed-end widths brought back onto the beam (M3/Q3, both now the same way).

---

## 2. Groups (by cause, largest first)

### G1. Dim slid INTO its own element (9 dims) — layout, `mcc_layout.candidates`
`SLIDE_MAX` 4 ft is bigger than `FIRST_GAP` (1/4" = 2.7 ft), and a slide costs `W_SLIDE` 0.5/ft (2.0 for 4 ft) — cheaper
than a lane (2.0) plus anything else — so `cand (…, 0, ±4)` lands 1.3 ft inside the element. Nothing hard stops it:
`W_OWN_SPAN` (2.5, soft) exists for openings only; CJs and beam ends have no own-span test at all.
- CJ dims inside the CJ's length, moved to ~1/4" past the end: `CJ | 7'-0¼" | EE` 20600889 (−4, +0.39"), `CJ | 13'-3" | FF`
  20600892 (−4, +0.40"), `8 | 7'-0" | CJ` 20600900 (+4, +0.42").
- Opening stack rows inside the opening's span, moved beyond its side: `EE | 7'-7½" | edge` 20600852 (shaft#102, −4,
  +0.37", then the 15'-7" joined onto it — §G3), `edge | 7'-9" | FF` 20600856 (shaft#118, the 3'-4" hole, −4, +0.34" —
  round-2 M1b, same spot x 204.3).
- Beam-end dims lying on their own beam (own beam not an obstacle): 20600860 (−4) and 20600914 (`collinear`), +0.38" each.
- Also "inside" by the classifier but a different cause: `5 | 7'-5½" | CJ` 20600917 (CJ pair, §G4) and `A | 1⅜" | edge`
  20600838 (corner, §G8).
Proposal (one change, 7 dims): in `candidates()`, for a string with a home side drop every candidate whose station lies
inside `_extent(s.feature, s.gi)` (CJ line, beam, opening) — clamp the slide, don't price it. For `end` strings make the
own beam an obstacle in `evaluate` (~534) so a beam-end dim can never lie along its own beam.

### G2. Beam width dims stacked beside a neighbour instead of first row past their end (7 dims) — `candidates` group/collinear/align
He pulled each toward its own beam end; none went to a uniform 1/4" because other rows sit between:
- `group` candidates (one lane beside a placed dim off the same grid): `9 | 1'-4½" | side | 1'-0" | side` 20600913
  (0.98" → 0.60"), `side | 3'-9" | 9 | 3'-9" | side` 20600880 (0.77" → 0.46"), `side | 1'-0" | side | 1'-3½" | 11`
  20600866 (0.81" → 0.65").
- `collinear` (same line as a placed parallel dim): beam#232 `side | 2'-5¾" | 2 | 1'-6" | side` 20600874 (0.37" → 0.10")
  **swapped again** with the jog check `3'-11¾"` 20600905 (0.06" → 0.29") — round-2 M2 exactly.
- Framed-end widths (round-2 M3 / open question 3, now both the same way): `side | 1'-0" | side | 13'-5½" | 10` beam#229
  20600870 (`collinear`, 0.44" past the framed end → **across the beam**, 0.80") and `side | 1'-7⅛" | 7 | 3'-10⅞" | side`
  beam#242 20600878 (`align`, 1.08" out in the open margin → across the beam, 1.37" = 14.6 ft; round 2 he did the same).
  Reading: when a beam's end is framed and the open margin is far, the width is read across the beam near that end — not
  pushed out to the margin.
- Consequential: `A | 1'-3⅜" | side | 1'-8" | side` 20600865 (+0.34") stepped out after he inserted the 1⅜" sliver
  nearest the corner (§G7) — shortest nearest; no rule.
Proposal: add `lane_equiv * W_BEAM_ROW` (distance from the string's own `prefer` in lanes) to the `group`, `collinear`
and `align` candidates of `beam_width` strings, and the plain `abs(st − prefer) * W_SLIDE` to `group` (it has none).
For a framed end with no open margin within ~6 ft, offer "across the beam, 1–2 ft inside the end" as the home candidate
instead of `ext` 8 ft out (`do_beam.at_end` in `mcc_strings`).

### G3. An opening's size check joins its locating row on one line beside the opening (4 openings, 8 dims) — `candidates` join / `evaluate`
Each pair shares a witness line, so the `(0, "join", 0)` candidate (`W_JOIN_SAME` −6) existed; the tool still put them on
separate lines 1–3 ft apart or on opposite sides. He joined every one:
- shaft#102: `EE | 7'-7½" | edge` + `edge | 15'-7" | edge` 20600931 (2.06", "to the other side") → one line at x 289.4,
  `EE | 23'-2½" | edge` 20600853 pushed outside (0.25" → 0.69"). Round-2 M1a, third round.
- core#120 (the 1'-5" × 3'-3" hole in the core wall): `edge | 7" | wall` 20600857 (0.06" → 0.21") + `edge | 3'-3" | edge`
  20600912 (0.34" → 0.21") → one line at x 217.0; and the other direction `wall | 5" | edge | 1'-5" | edge` 20600951 moved
  1.07" into the core beside the hole (M1c, second time).
- shaft#123 (1'-5" wide): `6 | 2'-5½" | edge` 20600941 + `edge | 1'-5" | edge` 20600942 → one line on the **other** side
  (0.06" / 0.16" one side → 0.16" the other side, 0.36" / 0.45").
- core#115 pocket edge: `CC | 8½" | edge` 20600855 (0.06" → 0.16") onto the line of `13'-7½"` at x 222.8 — the join the
  design doc already lists as his.
Three of the four stack rows were sitting at `MIN_GAP` 1/16" (`W_GAP` taper) and the check 1 ft further out; the join
station was not taken. Proposal: log the reject reason of the `join` candidate for these four pairs (one debug run of
`Layout.evaluate`) before changing weights — the cause is a hard reject (text box or `STATION_GAP`), not the −6.
Then: a check string whose join candidate exists must take it unless hard-blocked, and a stack row at `MIN_GAP` should
prefer the `FIRST_GAP` spot its check will join.

### G4. The CJ pair off grid 5: bottom end, third time (3 dims) — `mcc_strings.do_cj` (`natural_end`)
`5 | 4'-5½" | CJ | 3'-0" | CJ` 20600944 (−3.32") and `5 | 7'-5½" | CJ` 20600917 (−2.89") both moved 35 ft to the bottom
end; the join and the order (chain inside, 7'-5½" outside) he kept. `natural_end` picks the end with open slab past it
(top); the bottom end is where the pair meets the horizontal CJ 20572304 (`CJ | 13'-3" | FF` stands at x 190.4, y −23.4,
right beside his dims at y −26/−28). Likely rule: **CJ dims go at the end where the CJ meets another CJ (its layout
start), lined up with that CJ's dim** — question 1.

### G5. Rows hugging at 1/16" moved out to 3/16"–1/4" (5 dims) — `MIN_GAP` / `W_GAP`
20600857 `7"`, 20600855 `8½"`, 20600861 `end | 6'-4" | BB` (0.06" → 0.20"), 20600906 jog check `8"` (0.06" → 0.28", other
side of the step), 20600941 `6 | 2'-5½"`. Three are the joins in G3; the two others say the same: nothing at 1/16".
Round 2 reported "MIN_GAP 1/16": no opening row moved out" — no longer true. Proposal: `MIN_GAP_IN` 0.0625 → 0.15 (his own
rows sit 0.10–0.20").

### G6. Pocket shaft B2 (3 dims, still open since round 1) — `do_opening` step strings / `STATION_GAP`
`wall | 12'-1" | edge` 20600935 to the left side next to the `8½" | 13'-7½"` stack (1.39"); `step | 4'-6" | CC | 7'-7" |
edge` 20600953 pulled in 0.24" (1.03" → 0.79"); the loose duplicate `step | 4'-6" | CC` 20600952 **deleted** (D-a).
Same three edits as rounds 1 and 2.

### G7. NE corner: beam end at the column deleted, sliver call-out added (3 items, third time) — `mcc_features` free ends, `do_run` column-face skip
`end | 1'-0½" | 11` 20600954 **deleted** (D-b, beam 14181349 ends at the 18×18 corner column → framed, not free);
`A | 1⅜" | edge` 20601549 **added** at (326, 205) — the same sliver he added in rounds 1 and 2 as `11 | 1½" | slab edge`,
this time off angled grid A (either grid is fine for him; the blocker is "slab edge on a column face (skipped)", 16 on
L3N). `edge | 2'-3½" | 11` 20600955 and `side | 1'-0" | side | 1'-3½" | 11` re-stacked after it (+0.38", −0.16").

### G8. Run call-out at the actual corner (1 dim, second time) — `do_run` (`CORNER_IN`, `end_parts`)
`A | 1⅜" | edge` 20600838 moved 1.10" (11.8 ft) along the angled edge to the SW corner at (123, 110) where the edge meets
the vertical edge flush with beam#232. The tool's home station `cand (1,0,0)` is 2 ft in from run#28's start, so run#28
starts ~10 ft short of the geometric corner (the stretch next to it is a located-by edge — column face or beam face).
Proposal: `pref` = 2 ft in from the slab outline's **turn**, not from the feature's first edge, when the neighbouring edge
is collinear and "located by member".

### G9. The grid-9 / grid-8 clusters: each dim nearest its own element (4 dims) — `_order_stacks`, `W_GROUP`
`CJ | 19'-5⅛" | 9` 20600885 (0.53" → 0.13", slide −3 away from the CJ end), `end | 28'-8⅛" | 9` 20600859 (0.16" → 0.31"),
`8 | 3'-0" | CJ` 20600899 (0.31" → 0.12", `group`), `8 | 5'-0" | CJ` 20600887 slid 7.7 ft **along** its CJ out of the
3'-0"/7'-0" stack (its CJ continues past the others' end). Dims of different elements off one grid are not one stack:
he puts each at ~1/8–1/4" past its own element and lets them land where they land. `_order_stacks` / `group` treat them
as a stack. Proposal: `group` only for rows of the same element (or same end station within `STATION_GAP`).

### G10. Angled shaft#114 chain `edge@wall | 4'-10¼" | edge | 3'-9¾" | edge` 20600926 (1 dim)
0.72" → 0.18" (lane 1 → lane 0, `cand (−1,1,−3)`). Round 2 said it would come in once the 12'-8½" leg went; the leg is
gone but the row still took lane 1. Check what blocks lane 0 (probably the `8'-8"` overall's text).

### Singles / noise
`edge | 16'-4" | BB` 20600842 slid 0.09"; pulled text of `8"` (20600947) and `1'-1½"` (20600938) put back on the dim
line (0.11") — he reads a short segment's text on the line, not lifted; `W_ALIGN` text lift for 2-character texts could go.

---

## 3. Deletions (2)
| | tool dim | why | module |
|---|---|---|---|
| D-a | `step \| 4'-6" \| CC` 20600952 | duplicate: the same 4'-6" is the first segment of the joined `step \| 4'-6" \| CC \| 7'-7" \| edge` next to it (both `cand reordered`). The join is made by `_join_collinear` after `dedupe`, so the loose copy survives. | `mcc_layout._join_collinear` → drop a placed string whose refs are all inside a joined string |
| D-b | `end \| 1'-0½" \| 11` 20600954 | beam end at the corner column — third time (round-1 D6) | `mcc_features` free ends: an end within ~1 ft of a column face is framed |

## 4. Additions (4)
| | his dim | what it is | module |
|---|---|---|---|
| A-a | `edge \| 3'-11⅛" \| B` 20600958 at (225.5, 137.8), refs floor edge `…:25933:LINEAR` ↔ grid B | **third time.** The angled shaft#114's fourth edge in the B direction: 3'-11⅛" off B on the `5'-3¼"` side, i.e. a **1'-4⅛" jog** between that edge and the 5'-3¼" edge. The planner's note "opening: short edges off its grid set skipped (aligned grid near)" fires exactly once on L3N — `do_opening` ~386: edges shorter than `MINOR_EDGE` 3 ft in a family that is not the shaft's own are marked "located" when the dominant family has a grid near. He wants it off B every time (rule 3, every turn). | `do_opening`: don't skip minor edges when their family has a grid within `LOC_MAX`; or `MINOR_EDGE` 3 → 1 ft |
| A-b | `3 \| 7'-11" \| CJ` 20601175 at (145, −27), CJ 20572305 (vertical) ↔ grid 3 | this CJ has **no tool dim at all**; the issued hand sheet has it (`score_L3N_run1.md`: 17603703 grid > detail 7'-11"). It meets the horizontal CJ 20572304 (`CJ \| 13'-3" \| FF`) there. One of the planner's 7 "CJ on a beam side or slab edge (skipped)" or outside `MAX_DIST` — needs one look at the model. | `do_cj` (`flush` skip) |
| A-c | `A \| 1⅜" \| edge` 20601549 at (326, 205) | NE corner sliver, third time (G7) | `do_run` column-face skip: a slab edge within ~6" of a grid gets its call-out even on a column face |
| A-d | `BB \| 12'-1⅜" \| edge` 20601659 at (117.3, 104–108), floor edge `…:25562:LINEAR` ↔ BB | the horizontal face of the 3'-11¾" jog (step#17) west of beam#232, 6 ft past the beam's end (`BB \| 6'-0" \| end`). The tool has only the jog check `3'-11¾"` there — the face itself is skipped: likely "slab edge on a column face" (Adolfo's 2026-10-05 decision: a cut around a column is the column face, no dim) or "notch around a column (skipped)" (1). He located it anyway — **contradicts that decision**; question 3. | `do_run` / step strings |

---

## 5. The 1/4" and 1/2" nudges — direction and strings
- **Toward the element (9):** beam widths out of a `group`/`collinear` lane (4, G2); CJ dims slid away from the end
  (`19'-5⅛"`, `3'-0"`, G9); the shaft#114 chain (G10); the pocket step chain (G6); the `3'-3"` check joining its row (G3).
  Rule behind all of them: **a dim's first row is past its own element**; stacking beside a neighbour's dim is not worth a lane.
- **Away from the element (8):** three were hugging at 1/16" (G5); three are consequential re-stacks after a join or an
  inserted dim (`23'-2½"`, `2'-3½"`, `A | 1'-3⅜" | 1'-8"`); the jog check `3'-11¾"` swapped outside its beam width (G2);
  `end | 28'-8⅛" | 9` out one row when the CJ dim took the first (G9).
- **Out of the element to beside it (9):** G1 (7) + CJ pair (1) + corner (1).
- **To the other side (7):** joins on the far side (15'-7", shaft#123 ×2, core#120 ×1 — G3), CJ pair (1), pocket 12'-1" (1),
  jog check 8" (G5).

---

## Proposed order of changes
1. **G1** — clamp slides so no candidate station lies inside the string's own element; own beam is an obstacle for
   `end` strings. 7 dims, one place (`candidates`, `evaluate` ~534). Also unblocks the 15'-7" (`W_SPLIT` gets a side).
2. **G2** — `W_BEAM_ROW` (and a slide cost) on `group` / `collinear` / `align` candidates of `beam_width` strings. 4 dims +
   the beam#232/jog swap. Framed-end "across the beam" home candidate: 2 dims (confirm with question 2 first).
3. **G3** — debug the refused `join` candidates on the four pairs, then make the join win unless hard-blocked. 8 dims,
   three of them third-round repeats.
4. **G5** — `MIN_GAP_IN` 1/16" → ~0.15". 2–5 dims, one constant.
5. **G7 + D-b + A-c** — beam end within 1 ft of a column = framed; sliver call-out despite a column face. Third-round repeats.
6. **A-a** — minor-edge skip off when the family has a grid near. Third-round repeat, planner only.
7. **D-a** — dedupe after `_join_collinear`. 1 dim.
8. **G8** — run call-out at the slab's turn. 1 dim, second time.
9. **G9** — `group` only for the same element. 3–4 dims.
10. **G4** — CJ pair end (after question 1); **G6** pocket B2 (per-feature extent for step strings, open since run 65);
    **A-b** (model check); **A-d** (after question 3); G10 (lane-0 blocker).

## Open questions for Adolfo (each answerable with one picture)
1. **CJ pair off grid 5** (picture: the pair and the horizontal CJ they meet at the bottom): you put both dims at the
   bottom end three rounds running, where the pair meets the 13'-3" CJ. Is the rule "CJ dims at the end where the CJ meets
   another CJ, lined up with that CJ's dim"?
2. **Beam width past a framed end** (picture: beam#242 at grid 7 and beam#229 at grid 10): both times you read the width
   across the beam near its framed end instead of out in the open margin 8–14 ft away. Rule: "width across the beam within
   ~2 ft of a framed end, unless open slab is within ~6 ft"?
3. **The 12'-1⅜" off BB** (picture: the jog west of beam#232): is that face a cut around a column? On 2026-10-05 you said
   column-face edges get no dim. Keep that rule, or does a jog face that long (3'-11¾") get located even on a column?
4. **`edge | 3'-11⅛" | B`** (picture: the angled shaft's SE jog): the 1'-4⅛" jog's edge off B, added three times — confirm
   that every edge of an angled shaft gets its row off the angled grid, however short.
