## Dim Soffit v2: ZZ CLAUDE TEST - L7 (auto-dim)
Features in crop: beam 4, corner 12, opening/core 4, opening/penetration 6, opening/plain 20, opening/shaft 2, run 24, step 10
Strings planned: **223** (154 locate, 69 check) - placed **196**, needs review **27**, created **196** (Revit removed 0 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 214
| plan notes | count |
| anchor switched for consistency | 0 |
| chains dropped (stack says it all) | 1 |
| chains kept as checks (edges only) | 59 |
| coincident witness line merged | 1 |
| duplicate dim (same witness lines) dropped | 8 |
| duplicates dropped | 8 |
| merged through a gridline (edge | grid | edge) | 9 |
| run: anchor beyond LOC_MAX | 1 |
| stacked dim already planned (skipped) | 4 |
| stacked dims added (from one anchor) | 123 |
### Needs review (27) - not placed
| feature | string | blocked by | at | element |
| opening/core#49 | locate stack 2 -> edge@wall         across 5/6..     wall | 24'-5" | edge@wall | line through another text | (233.4, 63.6) | 14604435 |
| opening/plain#53 | locate stack 2 -> wall              across CC/BB..   edge | 12'-10 1/4" | wall | text over another line | (230.9, 43.6) | 14604435 |
| opening/plain#53 | locate stack 3 -> 7                 across 5/6..     wall | 20'-0" | 7 | text over another line | (230.9, 43.6) | 14604435 |
| opening/plain#55 | locate stack 1 -> FF                across CC/BB..   edge | 4'-0 7/8" | FF | text over a note/tag | (201.5, -15.3) | 14604435 |
| opening/plain#55 | locate stack 2 -> FF                across CC/BB..   edge | 6'-2 7/8" | FF | text over a note/tag | (201.5, -15.3) | 14604435 |
| opening/plain#58 | locate stack 2 -> 6                 across 5/6..     6 | 10'-11 1/2" | edge | text over another line | (217.8, 17.0) | 14604435 |
| opening/core#61 | locate stack 1 -> wall              across CC/BB..   edge | 0'-6" | wall | text over a note/tag | (214.0, 78.7) | 14604435 |
| opening/core#61 | locate stack 2 -> wall              across CC/BB..   edge | 3'-9" | wall | text over a note/tag | (214.0, 78.7) | 14604435 |
| opening/plain#62 | locate stack 1 -> 6                 across 5/6..     edge | 6'-8 3/4" | 6 | text over a note/tag | (201.0, 74.7) | 14604435 |
| opening/plain#62 | locate stack 2 -> 6                 across 5/6..     edge | 11'-2 7/8" | 6 | text over a note/tag | (201.0, 74.7) | 14604435 |
| opening/plain#63 | locate stack 1 -> BB                across CC/BB..   edge | 15'-4 3/4" | BB | line through a note/tag | (209.9, 81.2) | 14604435 |
| opening/plain#63 | locate stack 2 -> BB                across CC/BB..   edge | 18'-2 3/4" | BB | line through a note/tag | (209.9, 81.2) | 14604435 |
| opening/penetration#76 | locate stack 1 -> wall              across CC/BB..   edge | 5'-11" | wall | text over another line | (220.3, 48.6) | 14604435 |
| beam#78 | locate beam width (side on wall)    across 5/6..     side@wall | 2'-0" | side@wall | text over a note/tag | (211.9, 85.9) | 18596173 |
| beam#79 | locate beam width (side on wall)    across 5/6..     side@wall | 2'-0" | side@wall | text over a note/tag | (211.9, 51.5) | 18596174 |
| beam#80 | locate beam width (side on wall)    across CC/BB..   side@wall | 1'-9" | side@wall | text over a note/tag | (224.0, 81.7) | 18596176 |
| beam#81 | locate beam width (side on wall)    across CC/BB..   side@wall | 2'-3" | side@wall | text over a note/tag | (224.0, 56.4) | 18596177 |
| opening/core#49 | check core opening anchor|edges|anchor (chain check) across 5/6..     wall | 16'-7 1/2" | edge | line through another text | (233.4, 63.6) | 14604435 |
| opening/plain#53 | check plain opening anchor|edges|anchor (chain check) across 5/6..     wall | 16'-3" | edge | 3'-7" | edge | too close to a parallel string | (230.9, 43.6) | 14604435 |
| opening/plain#55 | check plain opening anchor|edges (chain check) across CC/BB..   edge | 2'-2" | edge | text over a note/tag | (201.5, -15.3) | 14604435 |
| opening/plain#58 | check plain opening anchor|edges|anchor (chain check) across 5/6..     edge | 6'-3 1/2" | edge | text over another line | (217.8, 17.0) | 14604435 |
| opening/core#61 | check core opening anchor|edges|anchor (chain check) across CC/BB..   edge | 3'-3" | edge | text over a note/tag | (214.0, 78.7) | 14604435 |
| opening/core#61 | check core opening anchor|edges|anchor (chain check) across 5/6..     edge | 1'-5" | edge | text over a note/tag | (214.0, 78.7) | 14604435 |
| opening/plain#63 | check plain opening anchor|edges|anchor (chain check) across CC/BB..   edge | 2'-10" | edge | text over a note/tag | (209.9, 81.2) | 14604435 |
| opening/plain#63 | check plain opening anchor|edges (chain check) across 5/6..     edge | 1'-7" | edge | text over a note/tag | (209.9, 81.2) | 14604435 |
| opening/plain#66 | check plain opening anchor|edges|anchor (chain check) across 5/6..     wall | 14'-3 3/4" | edge | 1'-9 3/8" | edge | line through another text | (228.1, 89.4) | 14604435 |
| opening/penetration#76 | check penetration opening anchor|edges (chain check) across CC/BB..   edge | 1'-6" | edge | text over another line | (220.3, 48.6) | 14604435 |

visible dims: 196 | seconds: 18.5
