# L4 South edit round 1 (on run 2) — analyst report, 2026-10-07

Inputs: `snapshot_L4S_before_edits1.json` (run 2, 71 dims), `snapshot_L4S_after_edits1.json` (Adolfo, 74 dims),
`compare_L4S_edits1.json` (49 unchanged / 18 edited / 4 deleted / 7 added; moves: 9 closer, 3 other side, 3 further,
3 onto the element), `compare_L4S_edits1_segments.json` (71 left / 24 moved / 5 deleted / 6 added).
Adolfo: "overall I think it did very well". Of the 38 review strings he added only beam#232's two (and re-anchored
them to A3). No mistake / bad-geometry deletions. L3N view untouched (the 2 new corner dims there undecided).

## Moved
- **A. Far placements pulled back beside their element (9):** 20619627 `GG | 10'-5¼"`, 20619656 trench drain `5 | 3'-3"`,
  20619652 `10'-0" R.O. | 5'-9"`, 20619667 `3'-9" | G | 3'-9"`; shaft#178 `10'-0"` (20619650) + `12'-0"` to A6 (20619651)
  joined end to end at ~(254, -17) - `_align_end_to_end` refused it (trace); past-end widths pulled in 0.45 -> 0.15-0.2"
  (20619611, 20619657); one first-row tightening (taste).
- **B. Widths at an end framed into an ANGLED member moved onto the beam just inside the end (4):** 20619647 / 20619628
  (grid-4 beam 14223259), 20619640 (beam 14223261), 20619604 (grid-9 beam 14223247). Square framed ends kept past
  the end (20619610 grid 7, 20619611, 20619657). Contradicts the round-5 "past the end when framed into a beam".
- **C. The long G-parallel slab edge (16'-3⅛") located at its two ends only:** 20619631 moved 25 ft and re-pointed to the
  grid-11 beam end face; 20620410 added at the SW end. None of the ten cross-beam `end -> G 16'-3⅛"` review strings
  added (study fix 8).
- **D. Taste (4):** CJ -> 4 flipped (20619624), A7 CJ-pair row order reversed (20619662/664 vs width 20619663),
  20619655 pushed out.

## Deleted
- **E. Junction corners already located both ways (3):** 20619644 `skew corner -> G.7 15'-3¾"` (358.7, 19.3);
  20619660 / 20619661 `corner -> JJ 6'-7⅜" / 9'-9½"` (~147, -89), slab corners at the G band. Kept: JJ tip 25'-3½".
- **F. Slab edge hidden above a beam (1):** 20619601 `run -> 10 1'-5⅞"` to a FILL floor edge inside the grid-10
  beam's footprint (kept 20619637, a FILL edge outside the grid-7 beam) -> rule "edge inside a beam outline".

## Added (7)
- Beam#232 (14223276) SW band end: `G | 16'-3⅛"` (20620410), `A3 | 21'-10" | side | 5'-6" | side` (20620417/424), `27'-4"`
  off A3 (20620072). Tool and issued sheet used A2 (8'-8" away) -> question.
- Grid-11 beam 14223243 real south end `11 | 1'-0½" | 4'-0"` (20620398) - the tool thought no end was in view.
- Grid-7 beam 14223279: a second width where it runs out of the crop `1'-7⅛" | 7 | 3'-10⅞"` (20620351) -> question.
- Band 14223265 SW end corner off straight grid 7 `7 | 6'-6⅛"` (20620363) - ~5° kink, answer 4 "straight grids".

## New features
- Skew corners: 2 placed (JJ tip kept; G.7 deleted), 4 in review (none added), 1 drawn by him off grid 7.
- Crop-edge "(intermediate)" widths: both kept (20619603 grid 11, 20619609 grid 10).

## Proposed order
1. Grid-11 beam south end (`do_beam` `in_view` / `ends_ok`) + long G-parallel edge at its two ends, no mid-edge
   cross-beam repeats (study fix 8). 2. Drop junction corners located both ways (`do_angled_corners`,
   `do_skew_beam_corners`; keep L3N's `BB 12'-1⅜"`, `B 3'-11⅛"`). 3. Slab edge inside a beam outline: no dim (`do_run`).
4. Join shaft#178's 10'-0" / 12'-0". 5. After the questions: width inside a skewed framed end; beam#232 anchor;
   crop-edge second width; corner off straight grids. 6. Taste last.

## Questions for Adolfo
1. Beam#232 SW end located off A3 though A2 is 8'-8" away (issued sheet used A2): (a) A2, A3 one-off; (b) closest
   visible grid; (c) band ends also get the far face's own row.
2. Widths at an end framed into an angled member moved inside the end (4): (a) inside when the other member is at a
   skew; (b) inside whenever past the end lands on / across another beam; (c) taste.
3. Second width where a beam runs out of the crop (grid 7): (a) always; (b) only when the in-view part is long; (c) one-off.
4. Junction corners: (a) only off straight grids; (b) only where a line meeting there isn't already located; (c) both.
