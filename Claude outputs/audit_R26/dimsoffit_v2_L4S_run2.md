## Dim Soffit v2: ZZ CLAUDE TEST - L4 SOUTH (auto-dim)
Features in crop: beam 29, cj 20, corner 47, opening/shaft 2, opening/void 2, run 70
Strings planned: **115** (109 locate, 6 check) - placed **71**, needs review **38**, created **71** (Revit removed 0 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 100
Stacks reordered shortest-nearest: 6 | dims joined end to end: 4 | intermediate beam dims with no room (left out): 0 | placed on a wider search: 8
Annotation crop widened to show dims past it: top 3.4 ft
Model: 5 lines from the view's cut plane skipped, 24 holes filled by other floors ignored, 6 curb/CMU walls ignored, 4 walls standing on the slab ignored
| plan notes | count |
| CJ on a beam side or slab edge (skipped) | 2 |
| anchor switched for consistency | 0 |
| beam continues in line past an end (no width dim at the joint) | 4 |
| beam corners at a skewed junction located off grids | 9 |
| beam width just inside the crop (no end in view) | 2 |
| beam: angled (no grid family) | 2 |
| chains dropped (stack says it all) | 0 |
| chains kept as checks (edges only) | 5 |
| cj: angled | 1 |
| duplicate dim (same witness lines) dropped | 13 |
| duplicate dim (witness lines inside a longer string) dropped | 8 |
| duplicates dropped | 21 |
| merged through a gridline (edge | grid | edge) | 6 |
| non-90 corners located along the edge from a grid | 4 |
| opening: near edge only off the grid (no far-edge row) | 2 |
| parallel CJs: dims at one shared end, spacing joined | 2 |
| run: no grid family / grid | 1 |
| shaft overall sizes marked R.O. | 2 |
| shaft sizes (slab edge | wall across a shaft) | 0 |
| slab edge on a column face (skipped) | 2 |
| small opening: near edge only off the grid | 2 |
| stacked dims added (from one anchor) | 6 |
### Needs review (38) - not placed
| feature | string | blocked by | at | element |
| opening/void#174 | locate void edge -> G               across F/G..     G | 16'-3 1/8" | edge | text over a note/tag | (180.9, -67.4) | 14221718 |
| opening/void#174 | locate stack 1 -> G                 across F/G..     G | 16'-3 1/8" | end | text over a note/tag | (180.9, -67.4) | 14221718 |
| beam#232 | locate beam end -> G                across F/G..     G | 16'-3 1/8" | end | text over a note/tag | (142.8, -113.2) | 14223276 |
| beam#239 | locate beam end -> G                across F/G..     G | 16'-3 1/8" | end | line through a note/tag | (365.6, 19.8) | 14241123 |
| beam#238 | locate beam end -> G                across F/G..     G | 16'-3 1/8" | end | text over a note/tag | (350.3, 8.7) | 14240997 |
| beam#240 | locate beam end -> G                across F/G..     G | 16'-3 1/8" | end | text over a note/tag | (319.1, -9.3) | 14241552 |
| beam#241 | locate beam end -> G                across F/G..     G | 16'-3 1/8" | end | text over a note/tag | (287.9, -27.3) | 14241561 |
| beam#242 | locate beam end -> G                across F/G..     G | 16'-3 1/8" | end | text over a note/tag | (256.7, -45.3) | 14241572 |
| beam#243 | locate beam end -> G                across F/G..     G | 16'-3 1/16" | end | text over a note/tag | (225.6, -63.3) | 14241581 |
| beam#226 | locate beam anchor|sides            across F.2/G.7.. F.2 | 4'-11 5/16" | side | 5'-6" | side | text over a note/tag | (216.2, -23.7) | 14223263 |
| beam#226 | locate beam anchor|sides            across F.2/G.7.. F.2 | 4'-11 5/16" | side | 5'-6" | side | text over a note/tag | (216.2, -23.7) | 14223263 |
| beam#232 | locate beam anchor|sides            across A9/A11..  side | 5'-6" | side | 8'-8" | A2 | text over a note/tag | (142.8, -113.2) | 14223276 |
| beam#234 | locate beam side|2|side             across 2/3..     side | 1'-6" | 2 | 2'-6" | side | text overlaps another text | (127.6, -65.3) | 14223718 |
| beam#235 | locate beam end -> FF + beam end -> FF across FF/GG..   end | 7'-1 15/16" | FF | 25'-0 3/8" | end | text over a note/tag | (184.2, -1.2) | 14232215 |
| beam#238 | locate beam end -> G                across F/G..     G | 6'-7 1/4" | end | text over a note/tag | (350.3, 8.7) | 14240997 |
| beam#238 | locate beam end -> G                across F/G..     G | 3'-11 1/4" | end | text over a note/tag | (350.3, 8.7) | 14240997 |
| beam#239 | locate beam anchor|sides            across A9/A11..  A11 | 13'-9 1/2" | side | 7'-6" | side | text over a note/tag | (365.6, 19.8) | 14241123 |
| beam#240 | locate beam end -> G                across F/G..     G | 6'-7 1/4" | end | over a beam | (319.1, -9.3) | 14241552 |
| beam#240 | locate beam end -> G                across F/G..     G | 3'-11 1/4" | end | over a beam | (319.1, -9.3) | 14241552 |
| beam#241 | locate beam end -> G                across F/G..     G | 6'-7 1/4" | end | text over a note/tag | (287.9, -27.3) | 14241561 |
| beam#241 | locate beam end -> G                across F/G..     G | 3'-11 1/4" | end | text over a note/tag | (287.9, -27.3) | 14241561 |
| beam#242 | locate beam end -> G                across F/G..     G | 6'-7 1/4" | end | over a beam | (256.7, -45.3) | 14241572 |
| beam#242 | locate beam end -> G                across F/G..     G | 3'-11 1/4" | end | over a beam | (256.7, -45.3) | 14241572 |
| beam#243 | locate beam end -> G                across F/G..     G | 6'-7 1/4" | end | text over a note/tag | (225.6, -63.3) | 14241581 |
| beam#243 | locate beam end -> G                across F/G..     G | 3'-11 1/4" | end | text over a note/tag | (225.6, -63.3) | 14241581 |
| beam#245 | locate beam end -> G                across F/G..     G | 16'-3 1/8" | end | text over a note/tag | (163.2, -99.3) | 14241601 |
| beam#245 | locate beam end -> G                across F/G..     G | 6'-7 1/4" | end | text over a note/tag | (163.2, -99.3) | 14241601 |
| beam#245 | locate beam end -> G                across F/G..     G | 3'-11 1/4" | end | text over a note/tag | (163.2, -99.3) | 14241601 |
| beam#250 | locate beam anchor|sides            across FF/GG..   FF | 2'-8 1/4" | side | 1'-7" | side | text over a wall | (199.1, -6.7) | 19603329 |
| cj#257 | locate CJ -> 8                      across 2/3..     8 | 5'-0" | CJ | outside crop | (275.2, 87.0) | 20618915 |
| cj#269 | locate CJ -> 9                      across 9/10..    CJ | 10'-6" | 9 | outside crop | (325.1, 69.3) | 20618927 |
| cj#287 | locate CJ -> 5                      across 2/3..     5 | 10'-2 1/16" | CJ | over a wall | (194.4, -4.2) | 20619334 |
| run#98 | locate corner -> G + beam end -> G  across F/G..     corner | 3'-8 5/16" | G | 6'-7 1/4" | end | text over a note/tag | (196.7, -77.8) | 14221718 |
| beam#223 | locate skew corner -> G + beam end -> G across F/G..     corner | 3'-9" | G | 3'-11 1/4" | end | text over a note/tag | (186.5, -53.1) | 14223257 |
| beam#224 | locate skew corner -> G + beam end -> G across F/G..     corner | 3'-9" | G | 16'-3 1/8" | end | text over a note/tag | (170.1, -50.9) | 14223259 |
| beam#224 | locate skew corner -> G + beam end -> G across F/G..     corner | 3'-9" | G | 3'-9" | end | text over a note/tag | (170.1, -50.9) | 14223259 |
| beam#224 | locate skew corner -> JJ            across FF/GG..   corner | 1'-1 5/8" | JJ | text over a note/tag | (170.1, -50.9) | 14223259 |
| opening/void#174 | check void edge -> G + beam end -> G (chain check) across F/G..     edge | 20'-0 1/8" | end | text over a note/tag | (180.9, -67.4) | 14221718 |

visible dims: 71 | seconds: 52.5
