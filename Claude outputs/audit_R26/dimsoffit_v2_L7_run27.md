## Dim Soffit v2: ZZ CLAUDE TEST - L7 (auto-dim)
Features in crop: beam 4, corner 12, opening/core 4, opening/penetration 6, opening/plain 20, opening/shaft 2, run 24, step 10
Strings planned: **160** (93 locate, 67 check) - placed **138**, needs review **2**, created **138** (Revit removed 0 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 175
Stacks reordered shortest-nearest: 5 | dims joined end to end: 20 | intermediate beam dims with no room (left out): 0 | placed on a wider search: 11
Model: 0 lines from the view's cut plane skipped, 0 holes filled by other floors ignored, 0 curb/CMU walls ignored
### For an enlarged plan (1) - small openings/notches too crowded at this scale
opening/penetration#70
| plan notes | count |
| anchor switched for consistency | 0 |
| beam in line with walls, capped by walls (skipped) | 4 |
| chains dropped (stack says it all) | 0 |
| chains kept as checks (edges only) | 57 |
| coincident witness line merged | 1 |
| duplicates dropped | 0 |
| merged through a gridline (edge | grid | edge) | 9 |
| shaft sizes (slab edge | wall across a shaft) | 0 |
| slab edge on a column face (skipped) | 3 |
| small opening: near edge only off the grid | 47 |
| small openings/notches crowded together (left for an enlarged plan) | 1 |
| stacked dim already planned (skipped) | 2 |
| stacked dims added (from one anchor) | 65 |
### Needs review (2) - not placed
| feature | string | blocked by | at | element |
| opening/core#61 | check core opening anchor|edges|anchor (chain check) across 5/6..     edge | 1'-5" | edge | text over a note/tag | (214.0, 78.7) | 14604435 |
| opening/penetration#76 | check penetration opening anchor|edges|anchor (chain check) across 5/6..     edge | 1'-5" | edge | inside an opening | (220.3, 48.6) | 14604435 |

visible dims: 138 | seconds: 15.8
