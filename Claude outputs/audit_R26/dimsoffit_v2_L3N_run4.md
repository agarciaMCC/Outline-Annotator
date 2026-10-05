## Dim Soffit v2: ZZ CLAUDE TEST - L3 NORTH (auto-dim)
Features in crop: beam 25, bump 1, cj 31, corner 40, notch 2, opening/core 5, opening/penetration 2, opening/plain 1, opening/shaft 7, opening/void 5, run 81, step 4
Strings planned: **137** (133 locate, 4 check) - placed **102**, needs review **35**, created **101** (Revit removed 1 at commit, 0 failed)
Text boxes overlapping after creation: **3** of 138
| plan notes | count |
| anchor switched for consistency | 1 |
| beam: angled (no grid family) | 1 |
| coincident witness line merged | 1 |
| dim collapsed to one witness line (dropped) | 1 |
| duplicate dim (same witness lines) dropped | 43 |
| duplicates dropped | 44 |
| opening: anchor beyond LOC_MAX | 1 |
| opening: too far from any grid | 2 |
| run: anchor beyond LOC_MAX | 1 |
| run: no grid family / grid | 2 |
### Needs review (35) - not placed
| feature | string | blocked by | at | element |
| run#51 | locate run -> wall                  across A/B..     wall | 2'-4 1/8" | edge | over a wall | (236.1, 158.7) | 14169070 |
| run#151 | locate run -> wall                  across A/B..     wall | 2'-1" | edge | over a wall | (325.0, 200.5) | 14183132 |
| run#201 | locate run -> wall                  across CC/BB..   edge | 10'-0" | wall | too close to a parallel string | (198.1, 81.7) | 14220571 |
| step#1 | locate step -> wall                 across CC/BB..   wall | 2'-3" | step | text overlaps another text | (237.1, 57.5) | 14169070 |
| step#2 | locate step -> wall                 across CC/BB..   wall | 2'-3" | step | over a wall | (230.4, 57.5) | 14169070 |
| notch#150 | locate notch across                 across 9/10..    10 | 14'-9 1/2" | leg | 1'-6" | leg | 0'-2 1/2" | wall | over a wall | (324.6, 201.4) | 14183132 |
| opening/void#97 | locate void edge -> wall            across F/G..     edge | 3'-2" | wall | outside crop | (352.0, 67.3) | 14169070 |
| opening/void#99 | locate void edge -> wall            across 9/10..    edge | 3'-3 1/2" | wall | over a wall | (353.5, 122.6) | 14169070 |
| opening/shaft#103 | locate shaft opening anchor|edges   across 2/3..     7 | 36'-2 1/2" | edge | 17'-9" | edge | crosses another string | (278.0, 41.4) | 14169070 |
| opening/void#110 | locate void edge -> wall            across 9/10..    edge | 1'-5 1/2" | wall | over a wall | (313.4, 190.5) | 14169070 |
| opening/core#111 | locate core opening anchor|edges|anchor across 2/3..     edge@wall | 8'-3" | edge | 11'-9" | 7 | crosses another string | (217.0, 38.1) | 14169070 |
| opening/shaft#115 | locate shaft opening anchor|edges   across A/B..     wall | 4'-7 3/8" | edge | 2'-5" | edge | 12'-4 15/16" | edge | over a wall | (216.8, 138.8) | 14169070 |
| opening/shaft#115 | locate opening far edge -> wall     across A/B..     wall | 19'-5 5/16" | far edge | over a wall | (216.8, 138.8) | 14169070 |
| opening/plain#119 | locate plain opening anchor|edges|anchor across 2/3..     wall | 1'-0" | edge | 7'-5 7/8" | edge | 0'-6 1/8" | edge | 6'-7 5/8" | edge | 4'-4 3/8" | 7 | text overlaps another text | (221.4, 55.7) | 14169070 |
| opening/core#122 | locate core opening anchor|edges|anchor across 2/3..     wall | 0'-5" | edge | 1'-5" | edge | 18'-2" | 7 | text overlaps another text | (214.0, 78.6) | 14169070 |
| opening/core#127 | locate core opening anchor|edges|anchor across 2/3..     7 | 1'-0 1/8" | edge | 2'-0" | edge | 1'-4 7/8" | wall | text overlaps another text | (234.9, 76.0) | 14169070 |
| opening/penetration#129 | locate penetration opening anchor|edges across 2/3..     wall | 2'-7 1/2" | edge | 1'-2" | edge | line through another text | (243.5, 56.2) | 14169070 |
| beam#246 | locate beam anchor|sides            across A/B..     wall | 0'-5 1/2" | side | 1'-8" | side | over a wall | (266.7, 174.1) | 14171002 |
| beam#248 | locate beam anchor|sides            across 9/10..    side | 1'-0" | side | 0'-5 1/2" | wall | over a wall | (327.4, 195.3) | 14181382 |
| beam#250 | locate beam anchor|sides            across 9/10..    side | 4'-0" | side | 0'-1 1/2" | 11 | over a wall | (338.7, 170.2) | 14181669 |
| beam#257 | locate beam side|5|side             across 2/3..     side | 4'-9" | 5 | 2'-9" | side | over a opening | (183.8, 96.5) | 14184520 |
| beam#258 | locate beam side|2|side             across 2/3..     side | 2'-5 3/4" | 2 | 1'-6" | side | over a wall | (126.7, 38.7) | 14184522 |
| beam#259 | locate beam side|3|side             across 2/3..     side | 3'-4" | 3 | 2'-8" | side | over a opening | (141.0, 28.7) | 14184524 |
| beam#259 | locate beam end -> FF               across CC/BB..   end | 34'-10" | FF | outside crop | (141.0, 28.7) | 14184524 |
| beam#269 | locate beam anchor|sides            across 2/3..     6 | 0'-11" | side | 2'-0" | side | text overlaps another text | (211.9, 85.9) | 14602325 |
| beam#270 | locate beam anchor|sides            across 2/3..     6 | 0'-11" | side | 2'-0" | side | text overlaps another text | (211.9, 51.5) | 14602458 |
| beam#271 | locate beam anchor|sides            across CC/BB..   side | 1'-9" | side | 15'-5" | BB | over a wall | (225.0, 81.7) | 14651533 |
| beam#272 | locate beam anchor|sides            across CC/BB..   side | 2'-3" | side | 4'-6" | CC | over a wall | (225.0, 56.4) | 14651535 |
| cj#305 | locate CJ -> BB                     across CC/BB..   CJ | 6'-4" | BB | over a opening | (198.1, 91.7) | 20572319 |
| cj#280 | locate CJ -> 5                      across 2/3..     CJ | 6'-6 1/4" | 5 | crosses another string | (177.7, 77.2) | 20572294 |
| cj#286 | locate CJ -> EE                     across CC/BB..   CJ | 13'-0 1/2" | EE | over a wall | (221.1, 13.0) | 20572300 |
| cj#288 | locate CJ -> EE                     across CC/BB..   CJ | 10'-1 1/2" | EE | over a opening | (198.5, 15.9) | 20572302 |
| cj#300 | locate CJ -> B                      across A/B..     CJ | 3'-8 15/16" | B | text over another line | (270.7, 165.9) | 20572314 |
| cj#306 | locate CJ -> 6                      across 2/3..     6 | 0'-11" | CJ | text over another line | (210.9, 87.7) | 20572320 |
| step#17 | check jog check                    across 2/3..     edge | 3'-11 3/4" | edge | over a wall | (126.7, 104.0) | 14169070 |
Revit warnings: The References of the highlighted Dimension are no longer parallel. x1

visible dims: 101 | seconds: 12.8
