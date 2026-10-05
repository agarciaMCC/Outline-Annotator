## Dim Soffit v2: ZZ CLAUDE TEST - L7 (auto-dim)
Features in crop: beam 4, corner 12, opening/core 4, opening/penetration 6, opening/plain 20, opening/shaft 2, run 24, step 10
Strings planned: **167** (99 locate, 68 check) - placed **141**, needs review **3**, created **141** (Revit removed 0 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 181
Stacks reordered shortest-nearest: 3 | dims joined end to end: 23 | intermediate beam dims with no room (left out): 0 | placed on a wider search: 10
Model: 0 lines from the view's cut plane skipped, 0 holes filled by other floors ignored, 0 curb/CMU walls ignored
| plan notes | count |
| anchor switched for consistency | 0 |
| beam in line with walls, capped by walls (skipped) | 4 |
| chains dropped (stack says it all) | 1 |
| chains kept as checks (edges only) | 58 |
| coincident witness line merged | 1 |
| duplicates dropped | 0 |
| merged through a gridline (edge | grid | edge) | 9 |
| shaft sizes (slab edge | wall across a shaft) | 0 |
| slab edge on a column face (skipped) | 3 |
| small opening: near edge only off the grid | 49 |
| stacked dim already planned (skipped) | 3 |
| stacked dims added (from one anchor) | 66 |
### Needs review (3) - not placed
| feature | string | blocked by | at | element |
| opening/plain#55 | locate stack 1 -> FF                across CC/BB..   edge | 4'-0 7/8" | FF | text over a note/tag | (201.5, -15.3) | 14604435 |
| opening/core#61 | check core opening anchor|edges|anchor (chain check) across 5/6..     edge | 1'-5" | edge | text over a note/tag | (214.0, 78.7) | 14604435 |
| opening/penetration#76 | check penetration opening anchor|edges|anchor (chain check) across 5/6..     edge | 1'-5" | edge | inside an opening | (220.3, 48.6) | 14604435 |

visible dims: 141 | seconds: 15.9
