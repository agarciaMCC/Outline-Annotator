## Dim Soffit v2: ZZ CLAUDE TEST - L3 NORTH (auto-dim)
Features in crop: beam 25, bump 1, cj 31, corner 40, notch 2, opening/core 5, opening/penetration 2, opening/plain 1, opening/shaft 7, opening/void 5, run 81, step 4
Strings planned: **117** (114 locate, 3 check) - placed **103**, needs review **14**, created **102** (Revit removed 1 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 161
| plan notes | count |
| anchor switched for consistency | 1 |
| beam: angled (no grid family) | 1 |
| coincident witness line merged | 1 |
| dim collapsed to one witness line (dropped) | 1 |
| duplicate dim (same witness lines) dropped | 46 |
| duplicate dim (witness lines inside a longer string) dropped | 11 |
| duplicates dropped | 58 |
| merged through a gridline (edge | grid | edge) | 6 |
| opening: anchor beyond LOC_MAX | 1 |
| opening: too far from any grid | 2 |
| run: anchor beyond LOC_MAX | 1 |
| run: no grid family / grid | 2 |
### Needs review (14) - not placed
| feature | string | blocked by | at | element |
| run#51 | locate run -> wall                  across A/B..     wall | 2'-4 1/8" | edge | over a wall | (236.1, 158.7) | 14169070 |
| run#201 | locate run -> wall                  across CC/BB..   edge | 10'-0" | wall | too close to a parallel string | (198.1, 81.7) | 14220571 |
| opening/void#97 | locate void edge -> wall            across F/G..     edge | 3'-2" | wall | over a wall | (352.0, 67.3) | 14169070 |
| opening/void#99 | locate void edge -> wall            across 9/10..    edge | 3'-3 1/2" | wall | over a wall | (353.5, 122.6) | 14169070 |
| opening/shaft#115 | locate shaft opening anchor|edges   across A/B..     wall | 4'-7 3/8" | edge | 2'-5" | edge | 12'-4 15/16" | edge | over a wall | (216.8, 138.8) | 14169070 |
| opening/shaft#115 | locate opening far edge -> wall     across A/B..     wall | 19'-5 5/16" | far edge | over a wall | (216.8, 138.8) | 14169070 |
| beam#272 | locate beam width (side on wall)    across CC/BB..   side@wall | 2'-3" | side@wall | text overlaps another text | (225.0, 56.4) | 14651535 |
| beam#246 | locate beam anchor|sides            across A/B..     wall | 0'-5 1/2" | side | 1'-8" | side | over a wall | (266.7, 174.1) | 14171002 |
| beam#250 | locate beam width (side on wall)    across 9/10..    side | 4'-0" | side@wall | over a wall | (338.7, 170.2) | 14181669 |
| beam#259 | locate beam end -> FF               across CC/BB..   end | 34'-10" | FF | outside crop | (141.0, 28.7) | 14184524 |
| beam#269 | locate beam width (side on wall)    across 2/3..     side@wall | 2'-0" | side@wall | over a wall | (211.9, 85.9) | 14602325 |
| beam#270 | locate beam width (side on wall)    across 2/3..     side@wall | 2'-0" | side@wall | over a wall | (211.9, 51.5) | 14602458 |
| beam#271 | locate beam width (side on wall)    across CC/BB..   side@wall | 1'-9" | side@wall | text overlaps another text | (225.0, 81.7) | 14651533 |
| cj#280 | locate CJ -> 5 + CJ -> 5            across 2/3..     CJ | 6'-6 1/4" | 5 | 1'-2" | CJ | line through another text | (177.7, 77.2) | 20572294 |
Revit warnings: The References of the highlighted Dimension are no longer parallel. x1

visible dims: 102 | seconds: 17.4
