## Dim Soffit v2: ZZ CLAUDE TEST - L4.5 NORTH (auto-dim)
Features in crop: beam 31, cj 14, corner 14, opening/plain 1, opening/void 3, run 67
Strings planned: **101** (98 locate, 3 check) - placed **91**, needs review **8**, created **91** (Revit removed 0 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 130
Stacks reordered shortest-nearest: 1 | dims joined end to end: 1 | intermediate beam dims with no room (left out): 0 | placed on a wider search: 5
Model: 0 lines from the view's cut plane skipped, 9 holes filled by other floors ignored, 1 curb/CMU walls ignored, 31 walls standing on the slab ignored
| plan notes | count |
| CJ halfway between two grids: dimensioned from both | 1 |
| CJ on a beam side or slab edge (skipped) | 3 |
| anchor switched for consistency | 0 |
| angled opening: far leg off a straight grid dropped | 1 |
| beam end at a column (framed, skipped) | 2 |
| beam in line with walls, capped by walls (skipped) | 4 |
| beam: angled (no grid family) | 2 |
| beam: too far from any grid | 2 |
| chains dropped (stack says it all) | 0 |
| chains kept as checks (edges only) | 3 |
| cj: angled | 2 |
| duplicate dim (same witness lines) dropped | 22 |
| duplicate dim (witness lines inside a longer string) dropped | 10 |
| duplicates dropped | 32 |
| merged through a gridline (edge | grid | edge) | 4 |
| non-90 corners located along the edge from a grid | 2 |
| opening: too far from any grid | 4 |
| run: no grid family / grid | 7 |
| shaft overall sizes marked R.O. | 0 |
| shaft sizes (slab edge | wall across a shaft) | 0 |
| slab edge on a column face (skipped) | 11 |
| small opening: near edge only off the grid | 3 |
| stacked dims added (from one anchor) | 3 |
| void edge: no anchor | 2 |
### Needs review (8) - not placed
| feature | string | blocked by | at | element |
| run#127 | locate run -> 11                    across 9/10..    edge | 1'-0 1/2" | 11 | outside crop | (378.0, 88.6) | 19670910 |
| opening/void#142 | locate void edge -> 2               across 2/3..     edge | 0'-6" | 2 | outside crop | (126.7, -8.9) | 19670910 |
| beam#175 | locate beam end -> FF               across CC/BB..   end | 28'-11 1/2" | FF | outside crop | (183.6, -26.5) | 14243462 |
| beam#186 | locate beam end -> 8                across 2/3..     8 | 28'-6 1/2" | end | line through another text | (305.2, 152.7) | 14271355 |
| beam#190 | locate beam anchor|sides            across CC/BB..   CC | 15'-11 1/2" | side | 4'-0" | side | over a wall | (261.3, 80.0) | 14353164 |
| beam#200 | locate beam anchor|sides            across A/B..     A | 1'-0 1/2" | side | 1'-4" | side | text overlaps another text | (208.7, 147.4) | 19387072 |
| beam#206 | locate beam anchor|sides            across 9/10..    side | 3'-0" | side | 5'-8 1/2" | 11 | inside an opening | (370.9, 89.2) | 19675280 |
| beam#207 | locate beam end -> 11               across 9/10..    end | 6'-4 1/2" | 11 | over a beam | (348.0, 146.6) | 19675327 |

visible dims: 90 | seconds: 29.3
