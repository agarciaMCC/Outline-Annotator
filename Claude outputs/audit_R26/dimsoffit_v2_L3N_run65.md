## Dim Soffit v2: ZZ CLAUDE TEST - L3 NORTH (auto-dim)
Features in crop: beam 25, bump 1, cj 31, corner 36, notch 2, opening/core 5, opening/penetration 2, opening/shaft 7, opening/void 4, run 76, step 4
Strings planned: **142** (120 locate, 22 check) - placed **130**, needs review **2**, created **127** (Revit removed 3 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 180
Stacks reordered shortest-nearest: 2 | dims joined end to end: 9 | intermediate beam dims with no room (left out): 1 | placed on a wider search: 3
Model: 5 lines from the view's cut plane skipped, 17 holes filled by other floors ignored, 13 curb/CMU walls ignored
### For an enlarged plan (5) - small openings/notches too crowded at this scale
notch#0, opening/core#125, opening/core#126, opening/penetration#127, opening/penetration#128
| plan notes | count |
| CJ on a beam side or slab edge (skipped) | 7 |
| anchor switched for consistency | 0 |
| beam continues in line past an end (no width dim at the joint) | 10 |
| beam in line with walls, capped by walls (skipped) | 4 |
| beam: angled (no grid family) | 1 |
| chains dropped (stack says it all) | 0 |
| chains kept as checks (edges only) | 13 |
| coincident witness line merged | 1 |
| dim collapsed to one witness line (dropped) | 1 |
| duplicate dim (same witness lines) dropped | 24 |
| duplicate dim (witness lines inside a longer string) dropped | 8 |
| duplicates dropped | 33 |
| jog check: gap beside a beam in a wall line (skipped) | 2 |
| merged through a gridline (edge | grid | edge) | 2 |
| no-grid chain off a wall kept as drawn (not stacked) | 1 |
| not stacked: a stacked dim would pass the 30 ft tape | 1 |
| notch around a column (skipped) | 1 |
| opening: no grid near, located off the wall it touches | 1 |
| opening: short edges off its grid set skipped (aligned grid near) | 1 |
| opening: too far from any grid | 1 |
| run: no grid family / grid | 2 |
| shaft sizes (slab edge | wall across a shaft) | 3 |
| slab edge on a column face (skipped) | 16 |
| small opening in a wall line (skipped) | 1 |
| small opening: near edge only off the grid | 8 |
| small openings/notches crowded together (left for an enlarged plan) | 5 |
| stacked dims added (from one anchor) | 19 |
| stepped opening: overall size added | 4 |
### Needs review (2) - not placed
| feature | string | blocked by | at | element |
| beam#232 | locate beam side|2|side             across 2/3..     side | 2'-5 3/4" | 2 | 1'-6" | side | outside crop | (126.7, 38.7) | 14184522 |
| beam#233 | locate beam side|3|side             across 2/3..     side | 3'-4" | 3 | 2'-8" | side | outside crop | (141.0, 28.7) | 14184524 |
Revit warnings: The References of the highlighted Dimension are no longer parallel. x3

visible dims: 126 | seconds: 23.1
