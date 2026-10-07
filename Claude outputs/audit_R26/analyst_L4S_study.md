# L4 South study - why Dim Soffit v2 produces so little of the issued sheet

Read-only, 2026-10-07. Inputs: `snapshot_L4S_hand.json` (176 dims), `dry_L4S_no_tags.json` / `_with_tags.json`,
`compare_dry_L4S_no_tags.json` (28 left / 36 moved / 42 tool-only / 157 hand-only), `compare_L4S_run1_vs_hand.json`,
`dimsoffit_v2_L4S_run1.md`, `L4S_ref_elements.json`, `L4S_run1_overview.png`, the design doc, `dimensioning-rules.md`,
`mcc_strings.py` / `mcc_features.py` / `mcc_model.py`. Coordinates are plan feet as in the snapshots (scale 1:128).

**Headline.** Tags are a small part of it: ignoring existing tags recovers only 8 hand segments (165 -> 157 missing).
Of the 157 hand-only segments, **73 are things the rules exclude** (grid-to-grid strings, columns, wall faces,
QC / record-soffit points, repeats), **53 are things no rule covers yet** (34 Beam Trim Void dims, 11 overall beam
widths, skewed beam ends), and only **31 are things the tool should already produce**. Two-thirds of those 31 come
from **six beams the tool never dimensions at all** (no string planned, none in review; 9 of the 29 beams on the sheet get no tool dim).

---

## 1. The 157 hand-only segments, by what they measure

| class | segs | examples | rules |
|---|---|---|---|
| Grid <-> grid strings | 38 | `2 \| 14'-2" \| 3 \| 28'-10" ...` (20618508), A1-A11 `20'-3" \| 36' x8` (20618511), 9 / 9c-9f chain (20618724); 26 are "Gridline Dimensions" type | ruled out (Dim Grids) |
| **Beam Trim Void** (Generic Models) sizes + locating | **34** | at every cross-beam / G-band junction: band -> void `3'-11 1/4"`, void `2'-8"` x `1'-8"`, `10"` each side (TV 17076537 at (320, -1), 17076588, 17076605, 17076622, 17076639, 17076554, 17076571); trench drain void 19605808 `1/2"` x4 | **not in any rule**; the model never reads Generic Models |
| Beams the tool never touches | 20 | 14223272 on grid 10: `2'-9" \| 10 \| 2'-9"` + `5'-6"` at both ends (370, 64) / (390, 20); 14223243 by grid 11: `11 \| 1'-0 1/2" \| 4'-0"`, `5'-0 1/2"` x2, end `16'-3 1/8"` off G; 14223254 / 14223252 (north pieces on grids 3 / 2): `3'-4" \| 3 \| 2'-8"` + `6'-0"`, `1'-6" \| 2 \| 2'-6"` at y -24.6; 14223245 `5'-6"` (35 deg, no grid family); 14223250 `5'-6"` at (183, 68) | covered |
| QC / record-soffit points (refs to elements no longer in the model) | 13 | `3 \| 21'-4"` + `GG \| 18'-5 5/8"` to the "RECORD SOFFIT ELEV" point at about (160, -64); `FF \| 5'-9 7/8"` + `7 \| 7'-9 5/8"` at about (240, -16); `F.2 \| 2 1/4"`, `3 1/2"` | ruled out (QC points ignored) |
| Overall beam width as an extra row | 11 | `7'-6"` outside the tool's `3'-9" \| A8 \| 3'-9"` on 14241552 (325, -20) - same on 14241581 / 592 / 572 / 561 / 14240997 / 14223268; `5'-6"` beside `2'-9" \| F \| 2'-9"` (14223265); `6'-0"` / `4'-0"` at the 9 3/4" -> 12 3/4" depth change on the grid 3 / grid 2 bands (y -73) | **contradicts L3N** (round 1: "overall beam widths added by mistake") |
| Beam ends | 9 | band SW end `A2 \| 6"` (130.9, -115.8); 14223265 end `A9 \| 6"`; band NE end `A9 \| 15'-4 3/8"` (tool: `A11 \| 15'-1 1/4"`); grid-2 beam 14223718's end against the angled band `G \| 3'-8 1/2"` + `JJ \| 25'-3 1/2"` (120, -113) | 4 covered (other end / other grid than the tool chose); 5 not covered (skewed framed end) |
| CJs | 9 | CJ pair spacing `4'-0"` x3 (20619224/20618925 at both ends, 20619227/28 by grid 8); `27'-8"` off A8 (tool: `8'-4"` off the closer A7); `5'-0"` / `10'-6"` drawn to the beam centreline = the tool's `CJ -> F` / `CJ -> 9` | 5 covered, 2 ruled out (farther grid), 2 not covered (CJ end off a cross grid, CJ -> beam side) |
| Columns | 6 | `FF \| 6'-2" \| col \| 1'-0"` (189, -15); `col \| 5'-0" \| CJ` x2 | ruled out |
| Angled beams off straight grids | 5 | 14223263: `GG \| 5'-2 1/2"`, `5 \| 3'-3 1/2"`; 14223261 `5 \| 2'-2 3/4"`; 14223257 `5 \| 2'-3 7/8"`, `7'-5 3/8"` | 2 covered (14223257 has no aligned family); 3 **contradict** "angled elements use their own grid" (F.2 is 4'-11" away) |
| Wall faces | 4 | 18" CIP wall 14217903 -> beam `3"`, `2'-10 1/8"`, `3 3/8"`, `1'-6 5/8"` (210-239, -7 to -14) | ruled out (Adolfo's L4.5 answer 6: possible later "skewed beam at a wall" check) |
| Second anchor / far side | 3 | `A9 \| 14'-8 1/2" \| side \| 7'-6" \| side \| 13'-9 1/2" \| A11` (14241123); `A2 \| 14'-2"` far side of 14223276 | ruled out (width + one anchor) |
| Half-width repeats along the G band | 3 | `3'-9"` side -> centreline at (304, -6), (242, -42), (178, -79) | ruled out (L4.5 answer 4: repeats left to the user) |
| Other | 2 | beam -> trench drain beam `21'-3 1/4"`; centreline label `6'-8 1/2"` off GG | - |

Totals: **ruled out 73**, **not covered 53** (34 trim voids + 11 overall widths + 5 skewed ends + 2 CJ + 1 beam-to-beam),
**covered 31** (20 untouched beams, 4 beam ends, 2 angled-beam corners, 5 CJ).

Side note: 55 of the 176 hand dims are the plain "5/64 Arial Narrow" type, not the "(Transparent)" type Adolfo uses on L3N.
29 of the 34 trim-void dims and 7 of the 9 CJ dims are that plain type. They may be a second detailer's pass, as on L4.5.

## 2. Why the tool misses the covered ones

| group | segs | most likely cause | where |
|---|---|---|---|
| 14223272, 14223243 (beams in the 9/10/11 wing) | 13 | **No string is planned and none goes to review.** Both run parallel to grids 10 / 11, and the tool uses grids 10 / 11 for slab edges right beside them, so the grid family exists. No plan note explains it. Possible causes: `_beams` drops a member with `b.d is None` or fewer than 2 sides (the geometry is cut by voids or joins); the feature fails the crop test; or `dedupe` folds it into the slab-edge strings on the same planes (`run -> 10` 2'-9" and `void edge -> 11` 5'-0 1/2" are this beam's side faces). **Needs a one-line trace in a dry run.** | `mcc_features._beams` / `_add`, `mcc_strings.do_beam`, `mcc_place.dedupe` |
| 14223254, 14223252 (north pieces of the grid 3 / grid 2 bands) | 5 | Each piece's south end continues in line into 14223270 / 14223718 (`continues()`), and its north end runs past the match line. So `ends_ok` is empty and `b_parts = []`: no width or side string. Or the whole feature is dropped because its midpoint is outside the crop (`_add`: `in_crop = _inside(f.mid())`; only CJs have the "an end inside" exception). Adolfo puts the dims just inside the match line (y -24.6). | `do_beam` (`ends_ok` / `in_view`), `mcc_features._add` |
| 14223245, 14223257 (angled, 35 deg / about 60 deg) | 3 | Run note "beam: angled (no grid family)" x2: `do_beam` returns. `do_angled_corners` only walks slab loops, never beams, so the beam corners get nothing off a straight grid. | `do_beam`, `do_angled_corners` |
| 14223250 | 1 | At (183, 68), far north. Probably outside the crop. | - |
| Beam ends | 4 | The tool dimensions the other end or another grid (14223265 end at A6, band NE end off A11 instead of A9). The band's SW end is probably treated as framed into 14223276. | `do_beam` `framed_ends` / `end_dir` |
| CJ pair spacing | 3 | `CJ_PAIR` is 4.0 ft and these pairs are exactly 4'-0" apart (7'-0" - 3'-0" off grid 8; 8'-4" - 4'-4" off A7). `abs(off2 - off) <= 4.0` fails on floating-point error. The A7 pair is also longer than `TURN_BOTH`, and `do_cj` only joins a spacing when `s1 - s0 <= TURN_BOTH`. Adolfo draws the spacing at **both** ends of the long pair. | `do_cj` |
| CJ / beam centreline | 2 | Not a miss. It is the same dimension drawn to the beam's centreline reference instead of grid F / 9, and the segments sit more than 8 ft apart, so `compare_segments.same_dim_elsewhere` can't pair them. | comparer |

**The 37 review items in run 1.** 27 say "text over a note/tag". With tags ignored (dry run), 28 still go to review.
Most belong to one group: **8 cross beams x `beam end -> G` at 16'-3 1/8", 6'-7 1/4" and 3'-11 1/4"** (beams #231,
#232, #238-#245).
- **16'-3 1/8":** the beams' far ends lie on the slab edge that runs parallel to G. Adolfo dimensions that edge once
  (`G | 16'-3 1/8"` on 14223243). Ten such strings are redundant (same planes).
- **3'-11 1/4" and 6'-7 1/4":** these are the faces the **Beam Trim Void** cuts into each cross beam's end. Adolfo
  dimensions the void instead (band -> void 3'-11 1/4" + void 2'-8").
- These strings run along the cross beam inside the band, so they have no room ("over a beam", text on the beam tags).

## 3. The 42 tool-only segments

| kind | segs | verdict |
|---|---|---|
| Same fact on another reference: slab edge flush with a beam face (`void edge -> 11` 5'-0 1/2", `void edge -> G` 16'-3 1/8" x2), CJ off grid F / 9 = Adolfo's off the beam centreline (5'-0" x2, 10'-6") | 6 | acceptable (comparer artefact) |
| Second-end beam widths, beams > 20 ft (`2'-9" \| F \| 2'-9"` on 14223265 at (234, -17), `2'-9" \| 4 \| 2'-9"` on 14223259 at (170, -88)) | 4 | acceptable (BEAM_BOTH rule; he drew one end) |
| Angled beam 14223263 off its own grid `F.2 \| 4'-11 5/16" \| 5'-6"` at both ends | 4 | per rule; he used grid 5 / GG / the wall (Q4) |
| The 10 x 10 ft opening at about (265, -17): chain + stack off G and A6 | 4 | he has no dim on it. Check whether it is a real opening |
| Slab-edge runs Adolfo doesn't dimension (`run -> 7` 1'-7" \| 6'-9" at the FILL by grid 7, `run -> 10` 1'-5 7/8" \| 2'-9", `run -> F.2` 3", `corner -> JJ` x2, `stack 1 -> G` 3'-9" = the band side) | 9 | mostly extras; the perimeter here is beam faces |
| Beam ends he doesn't draw or draws elsewhere (14223265 -> A6 8 1/2"; band -> A11; 14241123 at 6'-7 1/4" / 16'-3 1/8"; 14232215's second leg 25'-0 3/8"; trench drain beam -> 5 / 6 and its 1'-7" width) | 8 | 4 trim-void / slab-edge redundancies (fixed by fixes 2 and 8); rest extras |
| Beam 14232286 `6 \| 11"` | 1 | per rule (he used the wall, `3"`) |
| CJs: `CJ -> A7` 8'-4" x2 (he uses the 4'-0" spacing), `CJ -> FF` 29'-1 3/4" / 18'-0 3/8", `CJ -> 8` 5'-0", `CJ -> 5` 7'-2" + 3'-0" spacing | 6 | the A7 pair is fix 5; the rest are extras he didn't draw (CJ 20619328 he locates off a column) |

None of the 42 looks wrong by the rules. About 10 are true clutter.

The 36 moved segments are mostly within 2" of his line. The band's NE-end `3'-9" | G | 3'-9"` sits 24" away: he drew
it at the other station.

## 4. Fixes, ranked by expected gain

| # | fix | expected gain (hand segments) | needs Adolfo? | where |
|---|---|---|---|---|
| 1 | **Find why 14223272 / 14223243 get no string** (trace `_beams` -> `do_beam` -> `dedupe` for those ids in a dry run). Then let a beam that runs out of the crop count if an end is inside, as CJs do, and put its width just inside the crop edge when its only in-crop end is an in-line joint | up to 18 | no (covered) | `mcc_features._add` / `_beams`, `do_beam` (`ends_ok`) |
| 2 | **Beam Trim Voids**: read Generic Models named "Beam Trim Void" in `mcc_model`, add a feature in `mcc_features`, add `do_trim_void` in `mcc_strings` (size both ways + one locating dim off the band centreline / grid). Then the void-cut faces of a beam end are no longer separate "beam ends" | up to 34; also takes about 16 review strings away | **yes (Q1)**: new element class | `mcc_model.PlanModel.__init__`, `mcc_features._build`, new `Planner.do_trim_void`, `do_beam` free-end loop |
| 3 | **Overall width row** outside a `side \| grid \| side` beam string (and at a depth change along a band) | 8-11 | **yes (Q2)**: contradicts L3N | `do_beam` (an extra `check` string, stacked outside) |
| 4 | **AVOID_NOTES off** (already in the uncommitted `mcc_layout.py` change) | 8; 9 fewer review | decided ("it varies"); score L3N/L7 before committing | `Layout.__init__` |
| 5 | **CJ pairs**: `CJ_PAIR` tolerance (4.0 -> 4.0 + 1/96) and pairs longer than `TURN_BOTH` get the spacing at both ends | 3; 2 fewer extras | no | `do_cj` |
| 6 | **Skewed framed ends**: a beam meeting an angled band gets one dim off the angled grid at its end corner | 2-5 | **yes (Q3)** | `do_beam` `framed_ends` |
| 7 | **Angled beam with no grid family**: corners off the straight grids (as `do_angled_corners` does for slab corners) | 2-3 | no (rule: straight grids when no aligned grid) | `do_beam` / `do_angled_corners` |
| 8 | **Beam end on an already-located slab edge -> no beam end dim** (same planes) | 0 matched; 10 fewer review, 2 fewer extras | no (redundancy rule) | `do_beam` free-end loop (a `flush` with slab edges, as `do_cj` does) |
| 9 | Comparer: treat a beam-centreline ref as its grid, and a beam face flush with a slab edge as that edge; pair over more than 8 ft along the element | about 6 pairs move from both missing and extra to matched | no | `compare_segments.py` |

If fixes 1, 4, 5, 7 and 8 work as expected (no decision needed), matched segments go from about 64 to about 95-100 and
review drops by about 20. Fixes 2 + 3 (after Q1 / Q2) would add up to 45 more.

## 5. Questions for Adolfo

1. **Beam Trim Voids.** At TV 17076537, (320, -1), where cross beam 14241552 (A8) meets the G band 14223268, the
   sheet has `3'-11 1/4"` band -> void, `2'-8"` x `1'-8"`, and `10"` each side. The same pattern repeats at all 7 junctions.
   (a) dimension them like that (size both ways + one locating dim); (b) one locating dim only, size from the detail;
   (c) leave them off the soffit plan. Were these drawn by you? Most are the plain "5/64 Arial Narrow" type, not your
   Transparent one.
2. **Overall width beside a split width.** At beam 14241552, (325, -20), the sheet has `3'-9" | A8 | 3'-9"` plus
   `7'-6"` outside it (7 bands like this). On L3N you called overall beam widths a mistake.
   (a) never (L3N stands); (b) always, as the outer row, when a grid splits the beam; (c) only on the wide PT bands.
3. **Beam ending against the angled band.** At beam 14223718's south end on grid 2, (120, -113), the sheet has
   `G | 3'-8 1/2"` and `JJ | 25'-3 1/2"`. The tool treats the end as framed into the band and gives it no dim.
   (a) no dim (rule 8 stands); (b) one dim off the angled grid (G) to the end corner; (c) off both grids.
4. **Angled beam 14223263** (66x9 3/4, runs from about (245, -5) to (180, -35), parallel to F.2). The tool draws
   `F.2 | 4'-11 5/16" | side | 5'-6" | side` (own-grid rule). The sheet locates it off grid 5 (`3'-3 1/2"`), GG
   (`5'-2 1/2"`) and the 18" wall (`3 3/8"`, `1'-6 5/8"`). (a) own grid only (rule stands); (b) own grid + the
   straight grids at the corner where it meets the square part; (c) straight grids only there.
