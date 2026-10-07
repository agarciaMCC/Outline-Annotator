## Dim Soffit v2: ZZ CLAUDE TEST - L3 NORTH (auto-dim)
Features in crop: beam 25, bump 1, cj 31, corner 40, notch 2, opening/core 5, opening/penetration 2, opening/plain 1, opening/shaft 7, opening/void 5, run 81, step 4
Strings planned: **165** (137 locate, 28 check) - placed **145**, needs review **20**, created **144** (Revit removed 1 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 173
| plan notes | count |
| anchor switched for consistency | 0 |
| beam: angled (no grid family) | 1 |
| chains dropped (stack says it all) | 1 |
| chains kept as checks (edges only) | 24 |
| coincident witness line merged | 1 |
| dim collapsed to one witness line (dropped) | 1 |
| duplicate dim (same witness lines) dropped | 45 |
| duplicate dim (witness lines inside a longer string) dropped | 14 |
| duplicates dropped | 60 |
| merged through a gridline (edge | grid | edge) | 7 |
| opening: too far from any grid | 2 |
| run: anchor beyond LOC_MAX | 1 |
| run: no grid family / grid | 2 |
| stacked dim already planned (skipped) | 1 |
| stacked dims added (from one anchor) | 55 |
### Needs review (20) - not placed
| feature | string | blocked by | at | element |
| run#51 | locate run -> A                     across A/B..     A | 3'-2" | edge | over a wall | (236.1, 158.7) | 14169070 |
| run#201 | locate run -> BB                    across CC/BB..   edge | 16'-4" | BB | over a opening | (198.1, 81.7) | 14220571 |
| opening/void#99 | locate void edge -> 11              across 9/10..    edge | 4'-1 1/2" | 11 | over a wall | (353.5, 122.6) | 14169070 |
| opening/plain#119 | locate stack 1 -> 6                 across 2/3..     6 | 3'-11" | edge | over a wall | (221.4, 55.7) | 14169070 |
| opening/plain#119 | locate stack 2 -> 6                 across 2/3..     6 | 11'-4 7/8" | edge | over a wall | (221.4, 55.7) | 14169070 |
| opening/plain#119 | locate stack 3 -> 6                 across 2/3..     6 | 11'-11" | edge | over a wall | (221.4, 55.7) | 14169070 |
| opening/plain#119 | locate stack 4 -> 6                 across 2/3..     6 | 18'-6 5/8" | edge | over a wall | (221.4, 55.7) | 14169070 |
| opening/core#122 | locate stack 1 -> 6                 across 2/3..     6 | 3'-4" | edge | over a wall | (214.0, 78.6) | 14169070 |
| opening/core#122 | locate stack 2 -> 6                 across 2/3..     6 | 4'-9" | edge | over a wall | (214.0, 78.6) | 14169070 |
| opening/penetration#129 | locate stack 1 -> 7                 across 2/3..     7 | 10'-0 1/2" | edge | too close to a parallel string | (243.5, 56.2) | 14169070 |
| opening/penetration#129 | locate stack 2 -> 7                 across 2/3..     7 | 11'-2 1/2" | edge | too close to a parallel string | (243.5, 56.2) | 14169070 |
| opening/penetration#130 | locate stack 2 -> CC                across CC/BB..   edge | 5'-10 1/2" | CC | too close to a parallel string | (244.8, 56.4) | 14169070 |
| beam#246 | locate beam anchor|sides            across A/B..     A | 1'-3 3/8" | side | 1'-8" | side | over a wall | (266.7, 174.1) | 14171002 |
| beam#250 | locate beam anchor|sides            across 9/10..    side | 4'-0" | side | 0'-1 1/2" | 11 | over a wall | (338.7, 170.2) | 14181669 |
| beam#259 | locate beam end -> FF               across CC/BB..   end | 34'-10" | FF | outside crop | (141.0, 28.7) | 14184524 |
| beam#269 | locate beam anchor|sides            across 2/3..     6 | 0'-11" | side | 2'-0" | side | text over another line | (211.9, 85.9) | 14602325 |
| beam#270 | locate beam anchor|sides            across 2/3..     6 | 0'-11" | side | 2'-0" | side | over a wall | (211.9, 51.5) | 14602458 |
| beam#272 | locate beam anchor|sides            across CC/BB..   side | 2'-3" | side | 4'-6" | CC | text overlaps another text | (225.0, 56.4) | 14651535 |
| cj#280 | locate CJ -> 5 + CJ -> 5            across 2/3..     CJ | 6'-6 1/4" | 5 | 1'-2" | CJ | line through another text | (177.7, 77.2) | 20572294 |
| opening/penetration#129 | check penetration opening anchor|edges (chain check) across 2/3..     edge | 1'-2" | edge | text overlaps another text | (243.5, 56.2) | 14169070 |
Revit warnings: The References of the highlighted Dimension are no longer parallel. x1

visible dims: 144 | seconds: 17.8
