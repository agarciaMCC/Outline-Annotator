## Dim Soffit v2: ZZ CLAUDE TEST - L3 NORTH (auto-dim)
Features in crop: beam 25, bump 1, cj 31, corner 36, notch 2, opening/core 5, opening/penetration 2, opening/plain 1, opening/shaft 7, opening/void 5, run 76, step 4
Strings planned: **190** (161 locate, 29 check) - placed **162**, needs review **16**, created **159** (Revit removed 3 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 224
Stacks reordered shortest-nearest: 5 | dims joined end to end: 9 | intermediate beam dims with no room (left out): 3 | placed on a wider search: 8
Model: 5 lines from the view's cut plane skipped, 0 holes filled by other floors ignored, 13 curb/CMU walls ignored
| plan notes | count |
| anchor switched for consistency | 0 |
| beam in line with walls, capped by walls (skipped) | 4 |
| beam: angled (no grid family) | 1 |
| chains dropped (stack says it all) | 1 |
| chains kept as checks (edges only) | 23 |
| coincident witness line merged | 1 |
| dim collapsed to one witness line (dropped) | 1 |
| duplicate dim (same witness lines) dropped | 43 |
| duplicate dim (witness lines inside a longer string) dropped | 13 |
| duplicates dropped | 57 |
| merged through a gridline (edge | grid | edge) | 5 |
| notch around a column (skipped) | 1 |
| opening: short edges off its grid set skipped (aligned grid near) | 2 |
| opening: too far from any grid | 2 |
| run: no grid family / grid | 2 |
| shaft sizes (slab edge | wall across a shaft) | 3 |
| slab edge on a column face (skipped) | 16 |
| small opening: near edge only off the grid | 16 |
| stacked dim already planned (skipped) | 1 |
| stacked dims added (from one anchor) | 34 |
### Needs review (16) - not placed
| feature | string | blocked by | at | element |
| run#193 | locate run -> BB                    across CC/BB..   edge | 16'-4" | BB | inside an opening | (198.1, 81.7) | 14220571 |
| opening/plain#119 | locate stack 1 -> edge@wall         across CC/BB..   edge | 2'-3" | edge@wall | over a wall | (221.4, 55.7) | 14169070 |
| opening/plain#119 | locate stack 1 -> 6                 across 2/3..     6 | 3'-11" | edge | over a wall | (221.4, 55.7) | 14169070 |
| opening/plain#119 | locate stack 2 -> 6                 across 2/3..     6 | 11'-4 7/8" | edge | over a wall | (221.4, 55.7) | 14169070 |
| opening/plain#119 | locate stack 3 -> 6                 across 2/3..     6 | 11'-11" | edge | over a wall | (221.4, 55.7) | 14169070 |
| opening/plain#119 | locate stack 4 -> 6                 across 2/3..     6 | 18'-6 5/8" | edge | line through another text | (221.4, 55.7) | 14169070 |
| opening/core#122 | locate stack 1 -> wall              across 2/3..     wall | 0'-5" | edge | text inside an opening | (214.0, 78.6) | 14169070 |
| opening/void#98 | locate void edge -> CC              across CC/BB..   edge | 14'-4 3/4" | CC | inside an opening | (198.8, 67.0) | 14169070 |
| opening/void#98 | locate void edge -> CC              across CC/BB..   edge | 6'-9" | CC | over a wall | (198.8, 67.0) | 14169070 |
| beam#248 | locate beam side|5|side             across 2/3..     side | 4'-9" | 5 | 2'-9" | side | over a wall | (184.4, 95.6) | 14184520 |
| beam#249 | locate beam side|2|side             across 2/3..     side | 2'-5 3/4" | 2 | 1'-6" | side | outside crop | (126.7, 38.7) | 14184522 |
| beam#250 | locate beam side|3|side             across 2/3..     side | 3'-4" | 3 | 2'-8" | side | outside crop | (141.0, 28.7) | 14184524 |
| cj#271 | locate CJ -> 5 + CJ -> 5            across 2/3..     CJ | 6'-6 1/4" | 5 | 1'-2" | CJ | line through another text | (177.7, 77.2) | 20572294 |
| step#199 | check jog check                    across 2/3..     edge | 0'-8" | edge | inside an opening | (185.7, 90.8) | 14221225 |
| opening/plain#119 | check plain opening anchor|edges|anchor (chain check) across 2/3..     edge | 7'-5 7/8" | edge | 0'-6 1/8" | edge | 6'-7 5/8" | edge | text over another line | (221.4, 55.7) | 14169070 |
| opening/core#122 | check core opening anchor|edges|anchor (chain check) across 2/3..     edge | 1'-5" | edge | text inside an opening | (214.0, 78.6) | 14169070 |
Revit warnings: The References of the highlighted Dimension are no longer parallel. x3

visible dims: 158 | seconds: 31.9
