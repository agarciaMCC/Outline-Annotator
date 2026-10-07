# Brief: review past McClone soffit plans against the Dim Soffit v2 rules

You are reviewing issued soffit plan sheets (PDFs exported from Revit) that McClone Construction detailers
dimensioned by hand on past jobs. The goal is to learn whether the rules our automatic dimensioning tool
(Dim Soffit v2) follows match what detailers actually do, and to spot common habits the rules don't cover.
Read-only: never modify the PDFs.

## How to look at a sheet
Python 3 with PyMuPDF (`import pymupdf`) is installed. Render a whole sheet first, then zoom into 4-6 busy areas
(slab perimeter corners, an opening or core, beams, construction joints (CJs), a stair or ramp):
```python
import pymupdf
pg = pymupdf.open(PDF)[0]
pg.get_pixmap(dpi=40).save(OUT_FULL)                                  # whole sheet
r = pg.rect                                                            # crop by page fractions (as viewed)
clip = pymupdf.Rect(r.x0 + fx0*r.width, r.y0 + fy0*r.height, r.x0 + fx1*r.width, r.y0 + fy1*r.height)
pg.get_pixmap(dpi=150, clip=clip).save(OUT_CROP)
```
Note `page.rotation` may be non-zero; `pg.rect` is the as-viewed size and clip uses as-viewed coordinates
on recent PyMuPDF — if a crop looks wrong, call `pg.set_rotation(0)` first and crop in the unrotated frame.
Look at the PNGs with your Read tool. Save the crops you cite into the output folder you are given, named
`<job>_<short-desc>.png`.

Vocabulary: grid lines are the dash-dot lines with letter/number bubbles. A *chain* is several dims end to end
on one line. A *stack* is parallel dims that share one end (usually a grid line), each reaching a different
point, stepping outward. An *overall* is one long dim across many points.

## The rules to check (answer each: FOLLOWED / MOSTLY / MIXED / NOT FOLLOWED / NOT SEEN, with counts and examples)
1. **Every slab edge / point is located off a grid line** (or, for openings in a core, off a wall face).
   Edge-to-edge chains alone are not enough; chains are fine as checks.
2. **Anchor to the closest grid line**, even one running through an opening; a wall face only when no grid
   is within ~30 ft.
3. **30 ft max per dimension** (the field crew's tape) — are locating dims over 30 ft common? Note whether long
   dims are grid-to-grid strings / overalls (a different tool covers those) or locating dims.
4. **Stacked dims from one grid are the default** way of locating several points; chains used as checks.
   Or do detailers mostly chain (grid | edge | edge | grid)?
5. **Stacked rows: shortest nearest the element, longest furthest**; an overall goes outside its chain.
6. **At most 2-3 rows (lanes)** of dims out from an object.
7. **A dimension at each end** of long CJs, slab edges and beams (> ~20-40 ft).
8. **Beams:** width dimensioned just past a beam end (free end first); beams > 40 ft also get one width dim
   halfway. Beams centred on a grid are not dimensioned (look for a note like "BEAMS / COLUMNS CENTERED ON GRID
   U.N.O."). Other dims stay off beams.
9. **Nothing inside openings** (dim lines, text, leaders) — except a shaft's overall size when there is no room
   outside.
10. **Soffit plans dimension soffit elements only** (slab edges, beams, openings, CJs) — never walls, curbs or
    columns (other plans cover those).
11. **An element's dims of one direction stay on one side of it**; its size joins its locating dim end to end.
12. **CJs (construction joints) are located** off a grid (often with a "TO CJ" note).
13. **Small openings (< 4 ft):** near edge off the grid + the size. Crowded small openings → enlarged plan.
14. **Dim lines never lie on an edge running the same way**; dims don't cross each other where avoidable;
    witness lines don't cross other parallel dim lines.
15. **Text that doesn't fit** is pulled off the line with a leader.
16. **Grid-to-grid strings + overall** around the plan (handled by a separate tool) — present? on how many sides?

## Also record
- **Habits not in the list above** that repeat across sheets (labels such as R.O. / OPNG / TYP / U.N.O.,
  elevation tags, symbols, how openings are marked, how angled/curved edges are located, notes, colour use,
  where dims sit relative to the plan, dims to column faces, etc.).
- Anything that differs between older and newer sheets.

## Report
Write a markdown report to the given path: one section per sheet (job, sheet, scale if visible, 3-6 short
findings with crop file names), then a table: rule number × sheet with the verdicts, then "Habits not in the
rules". Keep it factual and specific (what you saw, where). Your final message: the table and the top 5
takeaways, under 400 words.
