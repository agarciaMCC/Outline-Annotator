# L4.5 North study — how the hand sheet is dimensioned vs Dim Soffit v2 run 1

Read-only, 2026-10-06. Inputs: `snapshot_L45N_hand.json` (207 dims, 228 segments), `snapshot_L45N_run1.json` (70 dims),
`compare_L45N_run1_vs_hand.json` (18 left / 32 moved / 49 tool-only / 182 hand-only segments), `dimsoffit_v2_L45N_run1.md`,
`dim_audit_soffit_sheets.csv` (gives the element kind behind every hand reference), `snapshot_L3N_after_edits3.json`,
the design doc status, `dimensioning-rules.md`, `mcc_strings.py` (`do_beam`, `do_run`, `do_cj`, `do_opening`).
Scale 1/128: 1 paper inch = 10.7 ft.

**Headline.** The 18 matched segments are all beam dims; nothing else matched. But the real gap is smaller than "182 missing"
says: about **21 of the 49 tool-only segments and ~25 of the hand-only ones are the same dimension drawn to a different
element** (beam centreline instead of the grid, the 12" slab instead of the 10" slab, CJ lines copied into the test view with
new ids). The remaining difference is style: this sheet dimensions **to columns (36 refs), walls (23) and model lines (8)**,
repeats beam-side dims at 2–3 stations along long bands, and uses 8 dims longer than 30 ft. None of that is in Adolfo's L3N
version (0 column refs, 3 wall refs, longest 28.7 ft). It reads as another detailer's hand, or a revision pass — 32 of the 207
dims are of the type "REV Missing Dimensions" and 127 are plain "5/64 Arial Narrow" (Adolfo's L3N: 117 of 121 "Transparent").

---

## 1. Beams: hand rule vs the tool's rule

Hand sheet, 31 beams in the crop, 28 referenced, 102 beam segments. Classified by the dim's direction against the beam axis:

| hand beam dims | count | what it is |
|---|---|---|
| beam side → grid, ACROSS the beam | 37 | each side located off the nearest grid, mostly as **two single dims to the same grid** (stack), sometimes as `side \| grid \| side` (9 chains) |
| width, beam face → beam face | 22 | 12 true widths + **10 half-widths to the beam's centreline** (3'-9" + 3'-9", 2'-9" + 2'-9") where the beam is centred on a grid — same fact as the tool's `side \| grid \| side`, different reference |
| beam end → grid, ALONG the beam | 15 | free ends off a grid, as the tool does |
| beam side → column face | 9 | the beam's sides to a column standing in or beside the band (3'-0 3/4", 2'-5" / 3'-7", 11 3/4" / 1'-6 1/4", 1/2") |
| beam end → column face | 5 | the end located off the column it frames into (2'-4 1/2", 1'-7 1/2", 6 3/8", 6", 10'-2 1/8") |
| beam side → wall face | 6 + 1 end | beam beside a core wall: 1'-10", 2'-8", 2'-7", 7 1/2", 2'-10 1/2", 12'-0" (a width measured wall to beam face) |
| beam ↔ slab edge, CJ, line | 6 + 3 + 1 | incl. two **0"** dims (beam face flush with the slab edge, REV type) |

**Where the widths sit.** Not only at the ends. On the long PT bands the sheet repeats the width/side dims at every
"event" along the band — a CJ, a column, a wall crossing, the other end — typically **2–3 stations, 20–45 ft apart**:

| beam | hand | tool run 1 |
|---|---|---|
| **14263921** 90x21¼ PT BM (7'-6" wide, N–S at x≈147, on grid 3) | `4'-1" \| 3 \| 3'-5"` chain **plus** a separate 7'-6" width at **three** stations: y −24, 55, 90 (6 dims) | nothing placed: one string, beam#181, review "text over a note/tag" at (141, 1.7) |
| **14243432** 72x72 PT BM (6 ft, N–S on grid 5, y −25…140) | 14 dims: `3'-7" \| 5 \| 2'-5"` at y 113, single 2'-5" off 5 at y 82, sides to the 24" round column 3'-0¾" ×2 (y 99, 128), sides to the 24x36 column 3'-7" / 2'-5" (y −12), ends 1'-5¾" → AA (×2), 12'-2⅛" → BB, 23'-9⅞" → CC, 10'-2⅛" and 2'-4½" → column faces, 1'-10" / 2'-8" / 10'-0½" → 18" wall | `3'-7" \| 5 \| 2'-5"` at both ends (y 140 and 83 — one left, one 2.5–2.8" off his), end → BB 12'-2⅛" (0.7" off), end → BB 10'-1" (he has 10'-2⅛" to the column face instead) |
| **14243458** 144x82 PT BM (12 ft band on grid 7) | chain `5'-4½" \| 7 \| 6'-7½"` at y 11; the same two values as **singles** at y 30; 5'-4½" again at y −8; 12'-0" width wall-face → beam; end 1'-9" → EE | chain at y 30 (left) and y −15.6 (0.7–2.5" off), end → EE 1'-9" (left). Closest match on the sheet; his extra station at y 11 / −8 and the wall width are the only misses |
| **14353164** 48x64 BM (4 ft, E–W at y≈80, x 243–276) | **no width dim** — each side to its own grid: 16'-0½" → BB and 15'-11½" → CC (both at x 251); end 3'-0" → 8; sides to the 18x48 column 11¾" / 1'-6¼"; 7½" → 36" wall, 2'-10½" → 21" wall; 18'-9⅛" → a model line | `CC \| 15'-11½" \| 4'-0"` (2.3" off, width segment not on his sheet), end → 8 3'-0" (left); second width string beam#190 to review (note/tag) |
| **14271037** 48x24 BM (4 ft, N–S at x≈297) | `8 \| 27'-0½"` + `4'-0"` + `16'-11"` to the next beam at y 156; 31'-0½" off 8 at y 47.6 (other side); end 11'-7¼" → CC; end 1'-7½" → column; ½" side → column | `8 \| 27'-0½" \| 4'-0"` at y 157 (left) and y 47.8 (10" from his 31'-0½" row); end → CC 11'-7¼" (1" off); end → AA 24'-2¼" — he draws the **same value to the 12" slab edge** (17339469) that the beam end sits on |

So: hand = **each side off the grid (stacked singles), repeated at several stations, plus column/wall faces as anchors**;
tool = width + ONE anchor at the ends, nothing between (Adolfo's L3N rule, confirmed 2026-10-06 "no width dim every N ft").
Tool beam strings: 48 segments — 18 left, 32 moved, 27 tool-only (10 of those are the centreline half-widths, see §5).

## 2. The 36 column references — exactly what is dimensioned to columns

38 hand segments touch a column (25 named columns + 10 nested-instance refs `b4e4bc1a…:INSTANCE:…:SURFACE`, 142138xx ids,
which the audit CSV did not resolve; 16x36, 24x36, 18x48, 12x24, 12x72, 12x36 COL, 24" round, 24x124 PILASTER):

| pattern | count | examples |
|---|---|---|
| **column face → grid** (locating the column) | 17 | 2'-9¾" → 11 (×4, two columns, both faces), 2'-0⅜" → 10, 5'-2" → FF, 6'-7½" → 7 (pilaster), 11'-9⅜" → 7 + 1'-4¼" → AA (16x36 at 222, 135), 4'-6½" / 1¼" / 5'-6" → AA / BB / FF, 4⅝" → 9 (REV) |
| **beam side → column face** | 9 | listed in §1 — the column stands inside or beside the band and its offset from the beam faces is given |
| **beam end → column face** | 5 | the beam end is located off the column it frames into |
| CJ → column face | 3 | 5'-0" (×2), 1'-10" |
| column ↔ Beam Trim Void (generic model) | 2 | 3'-0", 2'-8⅝" |
| column → model line / wall | 2 | 14'-0", 4'-3¾" |

No slab edge is dimensioned to a column here (the tool skipped 10 "slab edge on a column face" — those edges carry no hand dim
either, consistent with L3N). What contradicts L3N is (a) **columns located off grids on the soffit plan** (Dim Columns'
job per `dimensioning-rules.md` 5 / "never to columns" 2026-10-05) and (b) **column faces used as anchors for beam ends and
beam sides** — rule 8 says a beam end framing into a column needs no dim; the tool skipped 2 such ends ("beam end at a
column (framed, skipped)") and the hand sheet dims 5.

## 3. Slab-edge dims (10" + 12" PT SLAB + grid, 36 dims / 40 segments)

Floors referenced: 10" PT SLAB 14243653 (39 refs, the main slab), 12" PT SLAB 14268828 (6) and 17181793 (5) — the two
thicker floors the task calls "beams modelled as floors" — plus 20030453 (3), 19670910 (2). By the audit's edge grading:

| group | count | what | tool |
|---|---|---|---|
| **void / opening edges** of 14243653 (audit kind "opening edge") | 15 dims | the centre void's edges off the nearest grid, each edge its own dim, both ends of long edges: 20'-10½" → AA (×2, x 218 / 260), 17'-6" → AA, 13'-2½" → 7, 5'-10½" → 8, 2'-2¼" → AA, 1'-0½" → A (×3, three different corners), 2'-7" → 5 (×2), 15'-0¼" → EE (×2), 6" → 6; and the **stair opening at (280, 35)**: `17'-9" × 15'-7"` sizes + 7'-7½" → EE + 1'-1½" → 8 | 5 void-edge segments + 1 chain check, none on his line (the 1'-0½" → A at (125, 110) is his 17066202 drawn to a different floor); the stair opening and the void's other 13 edges have no tool dim. Report: "opening/void 3, core 1", "opening: too far from any grid 4", "void edge: no anchor 1", **"9 holes filled by other floors ignored"** — needs a model look: did the big void or the stair hole get dropped as filled (the L5 floor above is visible — four hand dims read "TO L5 EOS ABOVE")? |
| **perimeter edges** (kind "slab edge") | 10 + 3 "edge not matched" | 1'-11" → 8 (×3, the slab edge beside grid 8), 8" → FF, 35'-6" → EE, 2'-4" → 2 (×2), 3'-9" → 4 (×2), 9'-7" → 5, 3'-3⅞" → 4 | 4 run segments (6'-2¾" → EE ×2, 21'-10" → 8, 1'-0½" → 11) — all four are **his values drawn to another element** (12" slab 17181793 / beam end). 67 run features → 5 strings: `do_run` returns silently for an edge flush with a wall, beam or column (`located_by` "wall face" / "beam face") and most of this perimeter sits on walls / under the PT bands |
| **12" PT SLAB edges** (14268828, 17181793) | 9 dims / 11 segs | `8 \| 21'-10" \| 35'-0"` (both edges of 17181793 from grid 8), 56'-10" → 8, 6'-2¾" → EE (×2); 14268828: 51'-11½" → 8, 1'-11" → 8, 11'-7¼" → CC, 7'-0⅜" → CC, 24'-2¼" → AA, 53'-10½" edge → edge | **0 tool references** to either floor. These are soffit steps (12" vs 10") but the features list has no step/bump at all (beam 31, cj 14, corner 14, opening 4, run 67) — the thick floors probably overlap the main slab in plan rather than abut it, so no step feature forms. Model look needed |
| slab edge ↔ wall ↔ grid chains | 4 | `4 \| 3'-6" TO \| 3"` (×2), `edge \| 11⅞" \| 13'-10⅛" TO L5 EOS`, `edge \| 1'-0" \| 11" TO L5 EOS ABOVE` — the L5 slab edge above located through the wall | not a soffit-plan fact under the L3N rules |
| 10 dims with no audit row (added after 2026-10-01) | 10 | 2'-7" → 5, 6" → 6, 15'-0¼" → EE, 13'-2½" → 7, 20'-10½" → AA… (void edges, counted above) | |

Eight hand segments exceed the 30 ft tape: 46'-8" (grid–grid), 52'-0", 56'-10", 53'-10½", 35'-0", 36'-5", 31'-0½", 35'-6" —
six of them locate the 12" slab / beam edges from grid 8. The L3N rule (`LOC_MAX` / `MAX_DIST` 30) would never draw them.

## 4. The 15 review items, by cause

| cause | n | items | note |
|---|---|---|---|
| text over a note / tag | 4 | beam#181 (14263921), #190 (14353164), #206 (19675280), #207 (19675327) | three of the four are beams whose hand dims sit at other stations — the tool's one spot (past the end) is where the sheet's notes are |
| inside an opening | 3 | beam#187 (14345337 `7 \| 6'-3" \| side \| 3'-0"`), cj#213, cj#225 | the CJ ones at (162, −19) / (174, 8) are at the slab's bottom edge — "inside an opening" there suggests a hole the model layer kept that the sheet treats as slab (the beam-as-floor region?) |
| over a wall | 2 | beam#182 (14265390 `3'-9" \| 4 \| 3'-9"`), #193 (14353344 `3'-2" \| 6" \| 8`) | the hand sheet has both (3'-9" ×3 stations; `3'-2" \| 6"` at (272, 11)) — it puts them on/over the wall band |
| text overlaps another text | 2 | beam#188 (14345487, second end), #200 (19387072) | #188's hand version exists (3'-2⅜" + 9⅝" at x 244) |
| outside crop | 2 | void#142 (6" → 2 at (127, −9)), beam#175 (14243462 end → FF at (184, −27)) | the hand's 2'-7" → 5 / 6" → 6 sit at y −9 inside his annotation crop |
| over a beam | 1 | run#53 (`edge \| 1'-11" \| 8 \| 28'-6½" \| end` across the 12" slab 14268828) | the hand draws 1'-11" → 8 three times, as singles |
| text over another line | 1 | beam#191 (14353214 `2'-10¼" \| EE \| 1'-1¾"`) | hand has both values as singles at x 276 |

## 5. The 49 tool-only segments — what kinds

| kind | n | of which the hand has the same value on another reference |
|---|---|---|
| beam side `side \| grid \| side` halves | 10 | **10** — 14243430 (3'-9" ×4), 14243446 (2'-9" ×4), 20048256 (3'-9" ×2): the sheet references the **beam centreline** (3 beam refs, no grid) |
| CJ → grid | 10 | **5** by value (6'-7" → E / FF, 12'-8¼" → CC ×2, 10'-8" → FF); ids can never match — the test view's CJ lines are copies (20603xxx) of the sheet's detail items |
| beam end → grid | 9 | 2 (24'-2¼" → AA drawn to the 12" slab edge; 1'-0½" → A/11 drawn as side dims); the rest: ends he locates off a column (10'-1" → BB vs his 10'-2⅛" → column) or does not dimension (14353344 → FF ×2, 19387072 → 9, 20048256 → A) |
| beam `anchor \| sides` | 8 | 0 — three 4'-0" widths of the 48x64 beams he gives as two sides-to-grid instead; the 36x14 transition beams (20604316 `2 \| 2'-4" \| 3'-0"`, 20604347 `C \| 15'-0"`) he dims off grid D / the slab edge; 19387072 `A \| 1'-0½" \| 1'-4"` he dims 13'-11½" → B |
| run → grid | 4 | **4** (6'-2¾" → EE ×2, 21'-10" → 8, 1'-0½" → 11 — on the 12" slab / beam end) |
| void edge → grid (+ stack, chain) | 6 | 1 (1'-0½" → A) |
| corner → grid | 2 | **1** (11'-6⅝" → BB: he dims to a model **line** at that corner, 19697281) |

So ~21 of 49 are the same dimension on a different element — a comparison artefact, not a planning difference.
Of the hand's 182 missing segments, the same artefact covers ~25 (10 centreline halves, 8 CJ → grid, 4 run, 2–3 beam ends).

## 6. Rule changes, in order of segments recovered — and which need Adolfo's word

| # | change | segments recovered | contradicts an L3N decision? | where |
|---|---|---|---|---|
| 1 | **Compare by value + geometry, not element id**, for CJ lines (copied ids), overlapping floors (10"/12" sharing an edge) and beam centreline references | ~21 tool-only + ~25 hand-only reclassified as matches — no tool change | no | `compare_segments.py` |
| 2 | **12" PT SLAB / PT BM floors as soffit steps**: detect a thicker floor overlapping (not abutting) the main slab and give its edges run/step strings; investigate "9 holes filled by other floors" and the stair opening at (280, 35) | 11 + ~15 void/opening segments | no (steps and openings are already in the rules) — but needs a **model look** first | `mcc_model.py` `_drop_filled_holes`, `mcc_features.py` step detection |
| 3 | **Beam sides as stacked singles** (`grid → side` and `grid → side` as two dims, not one chain) and **each side to its own nearest grid** when the beam sits between two grids (16'-0½" → BB + 15'-11½" → CC, no width) | ~15 (the 37 side→grid dims minus those the chain already covers) | **partly** — Adolfo chose "width + one anchor" (2026-10-05) and `STACK_KINDS` excludes beams; ask | `do_beam`, `stack_from_anchor` |
| 4 | **Beam dims repeated at intermediate stations** (CJ, column, wall crossing) on bands > ~40 ft | ~12 | **yes** — "no width dim every N ft, every job is unique" (2026-10-06); only the one halfway dim over `BEAM_MID_OVER` exists | `do_beam` `at_end` / intermediates |
| 5 | **Columns on the soffit plan**: column faces → grid (17) | 17 | **yes** — "never to columns" (2026-10-05), Dim Columns covers it; ask whether this sheet is simply an older convention | would be `Dim Columns`, not Dim Soffit |
| 6 | **Column faces as anchors** for beam ends (5) and beam sides (9), CJ → column (3) | 17 | **yes** — rule 8 (framed end = no dim), 2026-10-06 "beam end at a column (framed, skipped)" | `do_beam` free/framed ends, `anchor()` |
| 7 | **Wall faces as anchors with a grid near** (beam side → wall 7, wall → grid 5, slab → wall 4) | 16 | **yes** — `WALL_ANCHOR_IF_NO_GRID` (2026-10-05) | `anchor()` |
| 8 | CJ extras: CJ → CJ spacing (4'-1", 13'-7⅝"), CJ → beam face (7'-11", 5'-2", 3'-9"), CJ → slab edge (1'-10", 15'-3") | 7 | partly — `do_cj` skips a CJ on a beam side; CJ–CJ chain "no rule" (2026-10-06 answer 3) | `do_cj` |
| 9 | Model **lines** as references (8) and L5 EOS chains (4), 0" / ½" dims (3), grid–grid (4) | 19 | out of scope (QC lines are ignored per the audit findings; grid strings → Dim Grids) | — |

Items 1–2 are safe and recover the most. Items 3–7 are the real question: **this sheet locates columns, beam ends at columns,
and beam sides off walls, and repeats beam dims along bands — every one of those was decided the other way on L3N.** If it
was drawn by another detailer, Adolfo's L3N rules stand and the honest score for L4.5 is "about 60 matched of ~130 comparable
segments" after item 1, not 18 of 226.

## Open questions for Adolfo
1. Was the L4.5 soffit plan dimensioned by you or by someone else (and are the 32 "REV Missing Dimensions" a later pass)?
2. Columns located off grids on this soffit plan (17 dims) and beam ends located off column faces (5): keep the L3N rule
   (none on the soffit plan) for L4.5 too?
3. Beam sides each to their own grid as two dims (and no width) — e.g. the 48x64 beam at y 80: 16'-0½" → BB and
   15'-11½" → CC — is that acceptable, or do you want `CC | 15'-11½" | 4'-0"` as the tool draws?
4. The 7'-6" PT band on grid 3 (14263921) has `4'-1" | 3 | 3'-5"` at three stations ~35 ft apart. Still "no repeats", as on L3N?
5. The 12" PT SLAB floors (14268828, 17181793): are they beams or thickened slab, and should their edges be dimensioned as
   soffit steps? Six of the sheet's eight > 30 ft dims locate them from grid 8.
6. The 36" / 27" / 24" core wall faces → grid (5 dims) and the "TO L5 EOS ABOVE" chains (4): soffit-plan content or not?
