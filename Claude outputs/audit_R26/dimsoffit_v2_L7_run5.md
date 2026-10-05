## Dim Soffit v2: ZZ CLAUDE TEST - L7 (auto-dim)
Features in crop: beam 4, corner 12, opening/core 4, opening/penetration 6, opening/plain 20, opening/shaft 2, run 24, step 10
Strings planned: **224** (154 locate, 70 check) - placed **182**, needs review **42**, created **182** (Revit removed 0 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 249
| plan notes | count |
| anchor switched for consistency | 0 |
| chains kept as checks | 60 |
| coincident witness line merged | 1 |
| duplicate dim (same witness lines) dropped | 8 |
| duplicates dropped | 8 |
| merged through a gridline (edge | grid | edge) | 9 |
| opening: anchor beyond LOC_MAX | 4 |
| run: anchor beyond LOC_MAX | 1 |
| stacked dim already planned (skipped) | 5 |
| stacked dims added (from one anchor) | 122 |
### Needs review (42) - not placed
| feature | string | blocked by | at | element |
| opening/core#49 | locate stack 2 -> edge@wall         across 5/6..     wall | 24'-5" | edge@wall | line through another text | (233.4, 63.6) | 14604435 |
| opening/plain#53 | locate stack 2 -> wall              across CC/BB..   edge | 12'-10 1/4" | wall | text over another line | (230.9, 43.6) | 14604435 |
| opening/plain#53 | locate stack 3 -> 7                 across 5/6..     wall | 20'-0" | 7 | text over another line | (230.9, 43.6) | 14604435 |
| opening/plain#55 | locate stack 1 -> FF                across CC/BB..   edge | 4'-0 7/8" | FF | text over a note/tag | (201.5, -15.3) | 14604435 |
| opening/plain#55 | locate stack 2 -> FF                across CC/BB..   edge | 6'-2 7/8" | FF | text over a note/tag | (201.5, -15.3) | 14604435 |
| opening/plain#57 | locate stack 1 -> CC                across CC/BB..   edge | 33'-8 7/8" | CC | too close to a parallel string | (227.7, 27.0) | 14604435 |
| opening/plain#57 | locate stack 2 -> CC                across CC/BB..   edge | 36'-2 7/8" | CC | too close to a parallel string | (227.7, 27.0) | 14604435 |
| opening/plain#58 | locate stack 2 -> 6                 across 5/6..     6 | 10'-11 1/2" | edge | text over another line | (217.8, 17.0) | 14604435 |
| opening/core#61 | locate stack 1 -> wall              across CC/BB..   edge | 0'-6" | wall | text over a note/tag | (214.0, 78.7) | 14604435 |
| opening/core#61 | locate stack 2 -> wall              across CC/BB..   edge | 3'-9" | wall | text over a note/tag | (214.0, 78.7) | 14604435 |
| opening/plain#62 | locate stack 1 -> 6                 across 5/6..     edge | 6'-8 3/4" | 6 | text over a note/tag | (201.0, 74.7) | 14604435 |
| opening/plain#62 | locate stack 2 -> 6                 across 5/6..     edge | 11'-2 7/8" | 6 | text over a note/tag | (201.0, 74.7) | 14604435 |
| opening/plain#63 | locate stack 1 -> BB                across CC/BB..   edge | 15'-4 3/4" | BB | line through a note/tag | (209.9, 81.2) | 14604435 |
| opening/plain#63 | locate stack 2 -> BB                across CC/BB..   edge | 18'-2 3/4" | BB | line through a note/tag | (209.9, 81.2) | 14604435 |
| opening/plain#74 | locate stack 2 -> EE                across CC/BB..   edge | 14'-8 3/8" | EE | text over a note/tag | (196.4, 11.8) | 14604435 |
| opening/penetration#76 | locate stack 1 -> wall              across CC/BB..   edge | 5'-11" | wall | text over another line | (220.3, 48.6) | 14604435 |
| beam#78 | locate beam width (side on wall)    across 5/6..     side@wall | 2'-0" | side@wall | text over a note/tag | (211.9, 85.9) | 18596173 |
| beam#79 | locate beam width (side on wall)    across 5/6..     side@wall | 2'-0" | side@wall | text over a note/tag | (211.9, 51.5) | 18596174 |
| beam#80 | locate beam width (side on wall)    across CC/BB..   side@wall | 1'-9" | side@wall | text over a note/tag | (224.0, 81.7) | 18596176 |
| beam#81 | locate beam width (side on wall)    across CC/BB..   side@wall | 2'-3" | side@wall | text over a note/tag | (224.0, 56.4) | 18596177 |
| opening/core#47 | check core opening anchor|edges (chain check) across CC/BB..   wall | 7'-0 7/8" | edge | 17'-8" | edge | too close to a parallel string | (217.0, 98.5) | 14604435 |
| opening/core#49 | check core opening anchor|edges|anchor (chain check) across 5/6..     wall | 16'-7 1/2" | edge | 7'-9 1/2" | edge@wall | too close to a parallel string | (233.4, 63.6) | 14604435 |
| opening/plain#50 | check plain opening anchor|edges|anchor (chain check) across CC/BB..   FF | 18'-9 1/8" | edge | 1'-5 7/8" | edge | 15'-11" | EE | too close to a parallel string | (224.2, 9.4) | 14604435 |
| opening/shaft#51 | check shaft opening anchor|edges (chain check) across 5/6..     7 | 13'-2 3/4" | edge | 1'-2" | edge | 0'-8" | edge | 1'-2" | edge | too close to a parallel string | (247.6, 52.7) | 14604435 |
| opening/plain#53 | check plain opening anchor|edges|anchor (chain check) across CC/BB..   EE | 16'-4 3/4" | edge | 2'-4" | edge | 10'-6 1/4" | wall | too close to a parallel string | (230.9, 43.6) | 14604435 |
| opening/plain#53 | check plain opening anchor|edges|anchor (chain check) across 5/6..     wall | 16'-3" | edge | 3'-7" | edge | 0'-2" | 7 | too close to a parallel string | (230.9, 43.6) | 14604435 |
| opening/plain#55 | check plain opening anchor|edges (chain check) across CC/BB..   edge | 2'-2" | edge | 4'-0 7/8" | FF | text over a note/tag | (201.5, -15.3) | 14604435 |
| opening/plain#57 | check plain opening anchor|edges (chain check) across CC/BB..   edge | 2'-6" | edge | 33'-8 7/8" | CC | too close to a parallel string | (227.7, 27.0) | 14604435 |
| opening/plain#57 | check plain opening anchor|edges|anchor (chain check) across 5/6..     6 | 16'-6 1/8" | edge | 2'-4" | edge | 4'-0 7/8" | 7 | too close to a parallel string | (227.7, 27.0) | 14604435 |
| opening/plain#58 | check plain opening anchor|edges|anchor (chain check) across 5/6..     6 | 4'-8" | edge | 6'-3 1/2" | edge | 11'-11 1/2" | 7 | text over another line | (217.8, 17.0) | 14604435 |
| opening/core#61 | check core opening anchor|edges|anchor (chain check) across CC/BB..   CC | 15'-1" | edge | 3'-3" | edge | 0'-6" | wall | text over a note/tag | (214.0, 78.7) | 14604435 |
| opening/core#61 | check core opening anchor|edges|anchor (chain check) across 5/6..     wall | 0'-5" | edge | 1'-5" | edge | 18'-2" | 7 | text over another line | (214.0, 78.7) | 14604435 |
| opening/plain#62 | check plain opening anchor|edges|anchor (chain check) across 5/6..     5 | 14'-6 1/8" | edge | 4'-6 1/8" | edge | 6'-8 3/4" | 6 | text over a note/tag | (201.0, 74.7) | 14604435 |
| opening/plain#63 | check plain opening anchor|edges|anchor (chain check) across CC/BB..   CC | 17'-9 1/4" | edge | 2'-10" | edge | 15'-4 3/4" | BB | text over a note/tag | (209.9, 81.2) | 14604435 |
| opening/plain#63 | check plain opening anchor|edges (chain check) across 5/6..     edge | 1'-7" | edge | 0'-3" | wall | text over a note/tag | (209.9, 81.2) | 14604435 |
| opening/plain#66 | check plain opening anchor|edges|anchor (chain check) across CC/BB..   wall | 5'-9" | edge | 2'-2" | edge | 7'-6" | BB | too close to a parallel string | (228.1, 89.4) | 14604435 |
| opening/plain#66 | check plain opening anchor|edges|anchor (chain check) across 5/6..     wall | 14'-3 3/4" | edge | 1'-9 3/8" | edge | 3'-10 7/8" | 7 | line through another text | (228.1, 89.4) | 14604435 |
| opening/plain#68 | check plain opening anchor|edges|anchor (chain check) across CC/BB..   FF | 15'-4 1/8" | edge | 2'-6" | edge | 18'-3 7/8" | EE | too close to a parallel string | (220.4, 6.5) | 14604435 |
| opening/plain#74 | check plain opening anchor|edges (chain check) across CC/BB..   edge | 0'-10 1/2" | edge | 13'-9 7/8" | EE | text over a note/tag | (196.4, 11.8) | 14604435 |
| opening/penetration#76 | check penetration opening anchor|edges (chain check) across CC/BB..   edge | 1'-6" | edge | 5'-11" | wall | text over another line | (220.3, 48.6) | 14604435 |
| opening/penetration#76 | check penetration opening anchor|edges|anchor (chain check) across 5/6..     wall | 6'-8" | edge | 1'-5" | edge | 11'-11" | 7 | too close to a parallel string | (220.3, 48.6) | 14604435 |
| opening/penetration#77 | check penetration opening anchor|edges (chain check) across CC/BB..   edge | 0'-11" | edge | 10'-2" | AA | too close to a parallel string | (227.9, 119.9) | 14604435 |

visible dims: 182 | seconds: 41.4
