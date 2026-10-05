## Dim Soffit v2: ZZ CLAUDE TEST - L3 NORTH (auto-dim)
Features in crop: beam 25, bump 1, cj 31, corner 36, notch 2, opening/core 5, opening/penetration 2, opening/shaft 7, opening/void 4, run 76, step 4
Strings planned: **169** (141 locate, 28 check) - placed **156**, needs review **2**, created **153** (Revit removed 3 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 211
Stacks reordered shortest-nearest: 5 | dims joined end to end: 10 | intermediate beam dims with no room (left out): 1 | placed on a wider search: 4
Model: 5 lines from the view's cut plane skipped, 17 holes filled by other floors ignored, 13 curb/CMU walls ignored
| plan notes | count |
| anchor switched for consistency | 0 |
| beam in line with walls, capped by walls (skipped) | 4 |
| beam: angled (no grid family) | 1 |
| chains dropped (stack says it all) | 0 |
| chains kept as checks (edges only) | 22 |
| coincident witness line merged | 1 |
| dim collapsed to one witness line (dropped) | 1 |
| duplicate dim (same witness lines) dropped | 39 |
| duplicate dim (witness lines inside a longer string) dropped | 11 |
| duplicates dropped | 51 |
| merged through a gridline (edge | grid | edge) | 5 |
| notch around a column (skipped) | 1 |
| opening: short edges off its grid set skipped (aligned grid near) | 2 |
| opening: too far from any grid | 2 |
| run: no grid family / grid | 2 |
| shaft sizes (slab edge | wall across a shaft) | 3 |
| slab edge on a column face (skipped) | 16 |
| small opening: near edge only off the grid | 15 |
| stacked dims added (from one anchor) | 30 |
### Needs review (2) - not placed
| feature | string | blocked by | at | element |
| beam#232 | locate beam side|2|side             across 2/3..     side | 2'-5 3/4" | 2 | 1'-6" | side | outside crop | (126.7, 38.7) | 14184522 |
| beam#233 | locate beam side|3|side             across 2/3..     side | 3'-4" | 3 | 2'-8" | side | outside crop | (141.0, 28.7) | 14184524 |
Revit warnings: The References of the highlighted Dimension are no longer parallel. x3

visible dims: 152 | seconds: 17.8
