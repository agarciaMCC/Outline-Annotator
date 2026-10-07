## Dim Soffit v2: ZZ CLAUDE TEST - L3 NORTH (auto-dim)
Features in crop: beam 25, bump 1, cj 34, corner 36, notch 2, opening/core 5, opening/penetration 2, opening/shaft 7, opening/void 4, run 76, step 4
Strings planned: **135** (116 locate, 19 check) - placed **115**, needs review **5**, created **113** (Revit removed 2 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 157
Stacks reordered shortest-nearest: 2 | dims joined end to end: 13 | intermediate beam dims with no room (left out): 0 | placed on a wider search: 1
Model: 5 lines from the view's cut plane skipped, 17 holes filled by other floors ignored, 8 curb/CMU walls ignored
### For an enlarged plan (5) - small openings/notches too crowded at this scale
notch#0, opening/core#125, opening/core#126, opening/penetration#127, opening/penetration#128
| plan notes | count |
| CJ halfway between two grids: dimensioned from both | 3 |
| CJ on a beam side or slab edge (skipped) | 7 |
| anchor switched for consistency | 0 |
| angled opening: far leg off a straight grid dropped | 1 |
| beam continues in line past an end (no width dim at the joint) | 10 |
| beam end at a column (framed, skipped) | 2 |
| beam in line with walls, capped by walls (skipped) | 4 |
| beam: angled (no grid family) | 1 |
| chains dropped (stack says it all) | 0 |
| chains kept as checks (edges only) | 13 |
| coincident witness line merged | 1 |
| core opening: near edge only off the outside grid (size covers the rest) | 1 |
| dim collapsed to one witness line (dropped) | 1 |
| duplicate dim (same witness lines) dropped | 23 |
| duplicate dim (witness lines inside a longer string) dropped | 5 |
| duplicates dropped | 29 |
| jog check: gap beside a beam in a wall line (skipped) | 2 |
| merged through a gridline (edge | grid | edge) | 2 |
| no-grid chain off a wall kept as drawn (not stacked) | 1 |
| non-90 corners located along the edge from a grid | 4 |
| not stacked: a stacked dim would pass the 30 ft tape | 1 |
| notch around a column (skipped) | 1 |
| opening: no grid near, located off the wall it touches | 1 |
| opening: too far from any grid | 1 |
| parallel CJs: dims at one shared end, spacing joined | 2 |
| run: no grid family / grid | 2 |
| shaft overall sizes marked R.O. | 10 |
| shaft sizes (slab edge | wall across a shaft) | 2 |
| slab edge on a column face (skipped) | 16 |
| small opening in a wall line (skipped) | 1 |
| small opening: near edge only off the grid | 8 |
| small openings/notches crowded together (left for an enlarged plan) | 5 |
| stacked dims added (from one anchor) | 18 |
| step: faces located off the grid between them | 1 |
| stepped opening: overall size added | 1 |
### Needs review (5) - not placed
| feature | string | blocked by | at | element |
| beam#242 | locate beam side|7|side             across 2/3..     side | 1'-7 1/8" | 7 | 3'-10 7/8" | side | text overlaps another text | (234.0, 24.4) | 14211982 |
| cj#265 | locate CJ -> 3                      across 2/3..     3 | 7'-11" | CJ | line through another text | (149.2, -38.0) | 20572305 |
| cj#277 | locate CJ -> 5                      across 2/3..     5 | 7'-5 1/2" | CJ | text overlaps another text | (191.7, -3.7) | 20572317 |
| cj#283 | locate CJ -> A7                     across A9/A14..  CJ | 4'-4" | A7 | over a column | (280.6, -5.9) | 20572323 |
| cj#284 | locate CJ -> A7                     across A9/A14..  CJ | 8'-4" | A7 | over a column | (284.0, -3.9) | 20572324 |
Revit warnings: The References of the highlighted Dimension are no longer parallel. x2

visible dims: 113 | seconds: 18.6
