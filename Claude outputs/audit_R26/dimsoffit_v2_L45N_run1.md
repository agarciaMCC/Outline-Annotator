## Dim Soffit v2: ZZ CLAUDE TEST - L4.5 NORTH (auto-dim)
Features in crop: beam 31, cj 14, corner 14, opening/core 1, opening/void 3, run 67
Strings planned: **87** (86 locate, 1 check) - placed **71**, needs review **15**, created **71** (Revit removed 0 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 100
Stacks reordered shortest-nearest: 2 | dims joined end to end: 0 | intermediate beam dims with no room (left out): 0 | placed on a wider search: 7
Annotation crop widened to show dims past it: bottom 1.5 ft, top 2.5 ft
Model: 0 lines from the view's cut plane skipped, 9 holes filled by other floors ignored, 1 curb/CMU walls ignored
| plan notes | count |
| CJ halfway between two grids: dimensioned from both | 1 |
| CJ on a beam side or slab edge (skipped) | 3 |
| anchor switched for consistency | 0 |
| beam end at a column (framed, skipped) | 2 |
| beam in line with walls, capped by walls (skipped) | 4 |
| beam: angled (no grid family) | 2 |
| beam: too far from any grid | 2 |
| chains dropped (stack says it all) | 0 |
| chains kept as checks (edges only) | 1 |
| cj: angled | 2 |
| duplicate dim (same witness lines) dropped | 17 |
| duplicate dim (witness lines inside a longer string) dropped | 9 |
| duplicates dropped | 26 |
| merged through a gridline (edge | grid | edge) | 2 |
| non-90 corners located along the edge from a grid | 2 |
| opening: too far from any grid | 4 |
| run: no grid family / grid | 7 |
| shaft overall sizes marked R.O. | 0 |
| shaft sizes (slab edge | wall across a shaft) | 0 |
| slab edge on a column face (skipped) | 10 |
| small opening in a wall line (skipped) | 3 |
| small opening: near edge only off the grid | 1 |
| stacked dims added (from one anchor) | 1 |
| void edge: no anchor | 1 |
### Needs review (15) - not placed
| feature | string | blocked by | at | element |
| run#53 | locate run -> 8 + beam end -> 8     across 2/3..     edge | 1'-11" | 8 | 28'-6 1/2" | end | over a beam | (268.3, 154.4) | 14268828 |
| opening/void#142 | locate void edge -> 2               across 2/3..     edge | 0'-6" | 2 | outside crop | (126.7, -8.9) | 19670910 |
| beam#175 | locate beam end -> FF               across CC/BB..   end | 28'-11 1/2" | FF | outside crop | (183.6, -26.5) | 14243462 |
| beam#181 | locate beam side|3|side             across 2/3..     side | 4'-1" | 3 | 3'-5" | side | text over a note/tag | (141.0, 1.7) | 14263921 |
| beam#182 | locate beam side|4|side             across 2/3..     side | 3'-9" | 4 | 3'-9" | side | over a wall | (170.1, 4.2) | 14265390 |
| beam#187 | locate beam anchor|sides            across 2/3..     7 | 6'-3" | side | 3'-0" | side | inside an opening | (240.6, 138.7) | 14345337 |
| beam#188 | locate beam side|AA|side            across CC/BB..   side | 0'-9 5/8" | AA | 3'-2 3/8" | side | text overlaps another text | (259.8, 131.7) | 14345487 |
| beam#190 | locate beam anchor|sides            across CC/BB..   CC | 15'-11 1/2" | side | 4'-0" | side | text over a note/tag | (261.3, 80.0) | 14353164 |
| beam#191 | locate beam side|EE|side            across CC/BB..   side | 2'-10 1/4" | EE | 1'-1 3/4" | side | text over another line | (262.0, 25.2) | 14353214 |
| beam#193 | locate beam anchor|sides            across 2/3..     side | 3'-2" | side | 0'-6" | 8 | over a wall | (268.7, 11.2) | 14353344 |
| beam#200 | locate beam anchor|sides            across A/B..     A | 1'-0 1/2" | side | 1'-4" | side | text overlaps another text | (208.7, 147.4) | 19387072 |
| beam#206 | locate beam anchor|sides            across 9/10..    side | 3'-0" | side | 5'-8 1/2" | 11 | text over a note/tag | (370.9, 89.2) | 19675280 |
| beam#207 | locate beam end -> 11               across 9/10..    end | 6'-4 1/2" | 11 | text over a note/tag | (348.0, 146.6) | 19675327 |
| cj#213 | locate CJ -> 4                      across 2/3..     CJ | 7'-11" | 4 | inside an opening | (162.2, -18.8) | 20603365 |
| cj#225 | locate CJ -> EE                     across CC/BB..   CJ | 18'-1 5/8" | EE | inside an opening | (174.0, 7.9) | 20604078 |

visible dims: 70 | seconds: 44.7
