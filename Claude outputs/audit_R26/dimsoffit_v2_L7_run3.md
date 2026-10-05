## Dim Soffit v2: ZZ CLAUDE TEST - L7 (auto-dim)
Features in crop: beam 4, corner 12, opening/core 4, opening/penetration 6, opening/plain 20, opening/shaft 2, run 24, step 10
Strings planned: **111** (101 locate, 10 check) - placed **99**, needs review **12**, created **99** (Revit removed 0 at commit, 0 failed)
Text boxes overlapping after creation: **0** of 181
| plan notes | count |
| anchor switched for consistency | 0 |
| coincident witness line merged | 1 |
| duplicate dim (same witness lines) dropped | 8 |
| duplicates dropped | 8 |
| opening: anchor beyond LOC_MAX | 4 |
| run: anchor beyond LOC_MAX | 1 |
### Needs review (12) - not placed
| feature | string | blocked by | at | element |
| opening/plain#57 | locate plain opening anchor|edges   across CC/BB..   edge | 2'-6" | edge | 33'-8 7/8" | CC | line through another text | (227.7, 27.0) | 14604435 |
| opening/plain#57 | locate plain opening anchor|edges|anchor across 5/6..     6 | 16'-6 1/8" | edge | 2'-4" | edge | 4'-0 7/8" | 7 | text over another line | (227.7, 27.0) | 14604435 |
| opening/plain#58 | locate plain opening anchor|edges|anchor across 5/6..     6 | 4'-8" | edge | 6'-3 1/2" | edge | 11'-11 1/2" | 7 | text over another line | (217.8, 17.0) | 14604435 |
| opening/plain#63 | locate plain opening anchor|edges|anchor across CC/BB..   CC | 17'-9 1/4" | edge | 2'-10" | edge | 15'-4 3/4" | BB | line through another text | (209.9, 81.2) | 14604435 |
| opening/plain#68 | locate plain opening anchor|edges|anchor across CC/BB..   FF | 15'-4 1/8" | edge | 2'-6" | edge | 18'-3 7/8" | EE | line through another text | (220.4, 6.5) | 14604435 |
| opening/penetration#70 | locate penetration opening anchor|edges across 5/6..     7 | 5'-0 1/8" | edge | 1'-9 1/4" | edge | text overlaps another text | (238.8, 102.8) | 14604435 |
| opening/penetration#76 | locate penetration opening anchor|edges across CC/BB..   edge | 1'-6" | edge | 5'-11" | wall | text over another line | (220.3, 48.6) | 14604435 |
| opening/penetration#76 | locate penetration opening anchor|edges|anchor across 5/6..     wall | 6'-8" | edge | 1'-5" | edge | 11'-11" | 7 | text over another line | (220.3, 48.6) | 14604435 |
| beam#78 | locate beam width (side on wall)    across 5/6..     side@wall | 2'-0" | side@wall | over a wall | (211.9, 85.9) | 18596173 |
| beam#79 | locate beam width (side on wall)    across 5/6..     side@wall | 2'-0" | side@wall | over a wall | (211.9, 51.5) | 18596174 |
| beam#80 | locate beam width (side on wall)    across CC/BB..   side@wall | 1'-9" | side@wall | over a wall | (224.0, 81.7) | 18596176 |
| beam#81 | locate beam width (side on wall)    across CC/BB..   side@wall | 2'-3" | side@wall | over a wall | (224.0, 56.4) | 18596177 |

visible dims: 99 | seconds: 21.0
