## Dim Soffit v2: ZZ CLAUDE TEST - L3 NORTH (auto-dim)
Features in crop: beam 25, bump 1, cj 31, corner 40, notch 2, opening/core 5, opening/penetration 2, opening/plain 1, opening/shaft 7, opening/void 5, run 81, step 4
Strings planned: **208** (180 locate, 28 check) - placed **150**, needs review **41**, created **147** (Revit removed 3 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 194
Stacks reordered shortest-nearest: 5 | dims joined end to end: 4 | intermediate beam dims with no room (left out): 13
| plan notes | count |
| anchor switched for consistency | 0 |
| beam: angled (no grid family) | 1 |
| chains dropped (stack says it all) | 1 |
| chains kept as checks (edges only) | 22 |
| coincident witness line merged | 1 |
| dim collapsed to one witness line (dropped) | 1 |
| duplicate dim (same witness lines) dropped | 35 |
| duplicate dim (witness lines inside a longer string) dropped | 12 |
| duplicates dropped | 48 |
| merged through a gridline (edge | grid | edge) | 6 |
| not stacked: a stacked dim would pass the 30 ft tape | 1 |
| notch around a column (skipped) | 1 |
| opening: short edges off its grid set skipped (aligned grid near) | 2 |
| opening: too far from any grid | 2 |
| run: no grid family / grid | 2 |
| shaft sizes (slab edge | wall across a shaft) | 3 |
| slab edge on a column face (skipped) | 16 |
| stacked dim already planned (skipped) | 1 |
| stacked dims added (from one anchor) | 51 |
### Needs review (41) - not placed
| feature | string | blocked by | at | element |
| run#192 | locate run -> CC                    across CC/BB..   edge | 7'-8 11/16" | CC | inside an opening | (198.1, 54.3) | 14220571 |
| run#194 | locate run -> CC                    across CC/BB..   edge | 13'-6" | CC | inside an opening | (198.1, 48.5) | 14220571 |
| run#201 | locate run -> BB                    across CC/BB..   edge | 16'-4" | BB | too close to a parallel string | (198.1, 81.7) | 14220571 |
| run#201 | locate run -> BB                    across CC/BB..   edge | 16'-4" | BB | inside an opening | (198.1, 81.7) | 14220571 |
| opening/core#111 | locate core opening anchor|edges|anchor across CC/BB..   edge@wall | 18'-2" | edge | 14'-10" | CC | inside an opening | (217.0, 38.1) | 14169070 |
| opening/plain#119 | locate stack 1 -> edge@wall         across CC/BB..   edge | 2'-3" | edge@wall | over a wall | (221.4, 55.7) | 14169070 |
| opening/plain#119 | locate stack 2 -> edge@wall         across CC/BB..   edge | 2'-11" | edge@wall | over a wall | (221.4, 55.7) | 14169070 |
| opening/plain#119 | locate stack 1 -> 6                 across 2/3..     6 | 3'-11" | edge | over a wall | (221.4, 55.7) | 14169070 |
| opening/plain#119 | locate stack 2 -> 6                 across 2/3..     6 | 11'-4 7/8" | edge | over a wall | (221.4, 55.7) | 14169070 |
| opening/plain#119 | locate stack 3 -> 6                 across 2/3..     6 | 11'-11" | edge | over a wall | (221.4, 55.7) | 14169070 |
| opening/plain#119 | locate stack 4 -> 6                 across 2/3..     6 | 18'-6 5/8" | edge | too close to a parallel string | (221.4, 55.7) | 14169070 |
| opening/core#122 | locate stack 1 -> CC                across CC/BB..   CC | 15'-0" | edge | inside an opening | (214.0, 78.6) | 14169070 |
| opening/core#122 | locate stack 2 -> CC                across CC/BB..   CC | 18'-3" | edge | inside an opening | (214.0, 78.6) | 14169070 |
| opening/core#122 | locate stack 1 -> 6                 across 2/3..     6 | 3'-4" | edge | over a wall | (214.0, 78.6) | 14169070 |
| opening/core#122 | locate stack 2 -> 6                 across 2/3..     6 | 4'-9" | edge | over a wall | (214.0, 78.6) | 14169070 |
| opening/penetration#129 | locate stack 2 -> 7                 across 2/3..     7 | 11'-2 1/2" | edge | too close to a parallel string | (243.5, 56.2) | 14169070 |
| opening/penetration#130 | locate stack 1 -> CC                across CC/BB..   edge | 5'-4 1/2" | CC | too close to a parallel string | (244.8, 56.4) | 14169070 |
| opening/penetration#130 | locate stack 2 -> CC                across CC/BB..   edge | 5'-10 1/2" | CC | too close to a parallel string | (244.8, 56.4) | 14169070 |
| opening/void#98 | locate void edge -> CC              across CC/BB..   edge | 14'-4 3/4" | CC | inside an opening | (198.8, 67.0) | 14169070 |
| opening/void#98 | locate void edge -> CC              across CC/BB..   edge | 6'-9" | CC | over a wall | (198.8, 67.0) | 14169070 |
| opening/void#98 | locate void edge -> BB              across CC/BB..   edge | 8'-9" | BB | inside an opening | (198.8, 67.0) | 14169070 |
| opening/void#99 | locate void edge -> 11              across 9/10..    edge | 4'-1 1/2" | 11 | over a wall | (353.5, 122.6) | 14169070 |
| beam#246 | locate beam anchor|sides            across A/B..     A | 1'-3 3/8" | side | 1'-8" | side | text overlaps another text | (266.7, 174.1) | 14171002 |
| beam#246 | locate beam anchor|sides            across A/B..     A | 1'-3 3/8" | side | 1'-8" | side | over a wall | (266.7, 174.1) | 14171002 |
| beam#250 | locate beam anchor|sides            across 9/10..    side | 4'-0" | side | 0'-1 1/2" | 11 | over a wall | (338.7, 170.2) | 14181669 |
| beam#250 | locate beam anchor|sides            across 9/10..    side | 4'-0" | side | 0'-1 1/2" | 11 | over a wall | (338.7, 170.2) | 14181669 |
| beam#257 | locate beam side|5|side             across 2/3..     side | 4'-9" | 5 | 2'-9" | side | over a wall | (183.8, 96.5) | 14184520 |
| beam#258 | locate beam side|2|side             across 2/3..     side | 2'-5 3/4" | 2 | 1'-6" | side | outside crop | (126.7, 38.7) | 14184522 |
| beam#259 | locate beam side|3|side             across 2/3..     side | 3'-4" | 3 | 2'-8" | side | outside crop | (141.0, 28.7) | 14184524 |
| beam#268 | locate beam side|7|side             across 2/3..     side | 1'-7 1/8" | 7 | 3'-10 7/8" | side | text overlaps another text | (234.0, 24.4) | 14211982 |
| beam#269 | locate beam anchor|sides            across 2/3..     6 | 0'-11" | side | 2'-0" | side | over a wall | (211.9, 85.9) | 14602325 |
| beam#270 | locate beam anchor|sides            across 2/3..     6 | 0'-11" | side | 2'-0" | side | over a wall | (211.9, 51.5) | 14602458 |
| beam#271 | locate beam anchor|sides            across CC/BB..   side | 1'-9" | side | 15'-5" | BB | over a wall | (225.0, 81.7) | 14651533 |
| beam#272 | locate beam anchor|sides            across CC/BB..   side | 2'-3" | side | 4'-6" | CC | over a wall | (225.0, 56.4) | 14651535 |
| beam#273 | locate beam anchor|sides            across 9/10..    side | 4'-0" | side | 0'-1 1/2" | 11 | outside crop | (374.8, 92.8) | 14895549 |
| cj#280 | locate CJ -> 5 + CJ -> 5            across 2/3..     CJ | 6'-6 1/4" | 5 | 1'-2" | CJ | line through another text | (177.7, 77.2) | 20572294 |
| cj#286 | locate CJ -> EE                     across CC/BB..   CJ | 13'-0 1/2" | EE | too close to a parallel string | (221.1, 13.0) | 20572300 |
| step#208 | check jog check                    across 2/3..     edge | 0'-8" | edge | inside an opening | (185.7, 90.8) | 14221225 |
| opening/core#122 | check core opening anchor|edges|anchor (chain check) across 2/3..     edge | 1'-5" | edge | text inside an opening | (214.0, 78.6) | 14169070 |
| opening/penetration#129 | check penetration opening anchor|edges|anchor (chain check) across CC/BB..   edge | 0'-6" | edge | text overlaps another text | (243.5, 56.2) | 14169070 |
| opening/penetration#130 | check penetration opening anchor|edges (chain check) across CC/BB..   edge | 0'-6" | edge | too close to a parallel string | (244.8, 56.4) | 14169070 |
Revit warnings: The References of the highlighted Dimension are no longer parallel. x3

visible dims: 147 | seconds: 38.0
