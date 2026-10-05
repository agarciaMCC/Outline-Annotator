## Dim Soffit v2: ZZ CLAUDE TEST - L7 (auto-dim)
Features in crop: beam 4, corner 12, opening/core 4, opening/penetration 6, opening/plain 20, opening/shaft 2, run 24, step 10
Strings planned: **220** (153 locate, 67 check) - placed **174**, needs review **28**, created **174** (Revit removed 0 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 208
Stacks reordered shortest-nearest: 6 | dims joined end to end: 18
| plan notes | count |
| anchor switched for consistency | 0 |
| chains dropped (stack says it all) | 1 |
| chains kept as checks (edges only) | 57 |
| coincident witness line merged | 1 |
| duplicates dropped | 0 |
| merged through a gridline (edge | grid | edge) | 9 |
| shaft sizes (slab edge | wall across a shaft) | 0 |
| slab edge on a column face (skipped) | 3 |
| stacked dim already planned (skipped) | 4 |
| stacked dims added (from one anchor) | 115 |
### Needs review (28) - not placed
| feature | string | blocked by | at | element |
| opening/core#48 | locate core opening anchor|edges|anchor across CC/BB..   CC | 12'-5 1/2" | edge | 23'-6 1/2" | edge | too close to a parallel string | (217.0, 68.3) | 14604435 |
| opening/core#49 | locate core opening anchor|edges|anchor across 5/6..     6 | 19'-6 1/2" | edge | 7'-9 1/2" | edge@wall | text over a note/tag | (233.4, 63.6) | 14604435 |
| opening/plain#50 | locate stack 2 -> EE                across CC/BB..   edge | 17'-4 7/8" | EE | too close to a parallel string | (224.2, 9.4) | 14604435 |
| opening/plain#53 | locate stack 2 -> EE                across CC/BB..   EE | 18'-8 3/4" | edge | too close to a parallel string | (230.9, 43.6) | 14604435 |
| opening/plain#55 | locate stack 1 -> FF                across CC/BB..   edge | 4'-0 7/8" | FF | text over a note/tag | (201.5, -15.3) | 14604435 |
| opening/plain#55 | locate stack 2 -> FF                across CC/BB..   edge | 6'-2 7/8" | FF | text over a note/tag | (201.5, -15.3) | 14604435 |
| opening/plain#60 | locate stack 1 -> FF                across CC/BB..   edge | 3'-2 5/8" | FF | over a wall | (225.2, -13.9) | 14604435 |
| opening/plain#60 | locate stack 2 -> FF                across CC/BB..   edge | 4'-2 3/8" | FF | over a wall | (225.2, -13.9) | 14604435 |
| opening/core#61 | locate stack 2 -> CC                across CC/BB..   CC | 18'-4" | edge | text over a note/tag | (214.0, 78.7) | 14604435 |
| opening/core#61 | locate stack 1 -> 6                 across 5/6..     6 | 3'-4" | edge | text over a note/tag | (214.0, 78.7) | 14604435 |
| opening/core#61 | locate stack 2 -> 6                 across 5/6..     6 | 4'-9" | edge | text over a note/tag | (214.0, 78.7) | 14604435 |
| opening/plain#62 | locate stack 1 -> 6                 across 5/6..     edge | 6'-8 3/4" | 6 | text over a note/tag | (201.0, 74.7) | 14604435 |
| opening/plain#62 | locate stack 2 -> 6                 across 5/6..     edge | 11'-2 7/8" | 6 | text over a note/tag | (201.0, 74.7) | 14604435 |
| opening/plain#63 | locate stack 1 -> BB                across CC/BB..   edge | 15'-4 3/4" | BB | line through a note/tag | (209.9, 81.2) | 14604435 |
| opening/plain#63 | locate stack 2 -> BB                across CC/BB..   edge | 18'-2 3/4" | BB | line through a note/tag | (209.9, 81.2) | 14604435 |
| opening/plain#69 | locate stack 2 -> 7                 across 5/6..     7 | 13'-5 13/16" | edge | text over another line | (245.0, 79.8) | 14604435 |
| opening/penetration#76 | locate stack 1 -> CC                across CC/BB..   edge | 12'-8" | CC | text over a note/tag | (220.3, 48.6) | 14604435 |
| opening/penetration#76 | locate stack 2 -> CC                across CC/BB..   edge | 14'-2" | CC | text over a note/tag | (220.3, 48.6) | 14604435 |
| opening/penetration#76 | locate stack 1 -> 6                 across 5/6..     6 | 9'-7" | edge | text over a note/tag | (220.3, 48.6) | 14604435 |
| opening/penetration#76 | locate stack 2 -> 6                 across 5/6..     6 | 11'-0" | edge | text over a note/tag | (220.3, 48.6) | 14604435 |
| beam#78 | locate beam anchor|sides            across 5/6..     6 | 0'-11" | side | 2'-0" | side | text overlaps another text | (211.9, 85.9) | 18596173 |
| beam#79 | locate beam anchor|sides            across 5/6..     6 | 0'-11" | side | 2'-0" | side | text over a note/tag | (211.9, 51.5) | 18596174 |
| beam#80 | locate beam anchor|sides            across CC/BB..   side | 1'-9" | side | 15'-5" | BB | too close to a parallel string | (224.0, 81.7) | 18596176 |
| beam#81 | locate beam anchor|sides            across CC/BB..   side | 2'-3" | side | 4'-6" | CC | text over a note/tag | (224.0, 56.4) | 18596177 |
| opening/plain#50 | check plain opening anchor|edges|anchor (chain check) across 5/6..     edge | 6'-11 1/2" | edge | text over another line | (224.2, 9.4) | 14604435 |
| opening/plain#55 | check plain opening anchor|edges|anchor (chain check) across CC/BB..   edge | 2'-2" | edge | text over a note/tag | (201.5, -15.3) | 14604435 |
| opening/plain#63 | check plain opening anchor|edges|anchor (chain check) across CC/BB..   edge | 2'-10" | edge | text over a note/tag | (209.9, 81.2) | 14604435 |
| opening/penetration#76 | check penetration opening anchor|edges|anchor (chain check) across 5/6..     edge | 1'-5" | edge | inside an opening | (220.3, 48.6) | 14604435 |

visible dims: 174 | seconds: 23.7
