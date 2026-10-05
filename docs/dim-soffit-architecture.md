# Dim Soffit — the rebuilt dimensioning pipeline (2026-09-29)

Replaces the single-file `Dim Slab Edges` heuristic. Three stages in `MCC.extension/lib`, one button that runs them, one that scores the result.

## Stages
- **Recognize — `mcc_model.py`** `PlanModel(doc, view)` reads the view once: grids + direction families; slabs (perimeter edges and opening loops, each edge with its Revit reference, via `mcc_plan.soffit_loops`); beams / walls / columns as `Member`s with true plan outlines (convex hull of Fine-detail geometry, never bounding boxes), side faces and end faces with references; CJ lines = detail items of family `Large Scale`; obstacles = inflated outlines of all of the above plus openings. Model geometry is read with a Fine-detail `Options` (no view) so beams don't come back as stick lines; slabs and detail items use the view's options.
- **Decide — `mcc_rules.py`** `Rules(model).slab_edges() / openings() / beams() / walls() / cjs()` return `Intent`s: what to reference, measured across which grid family, with a home station range and a preferred station. Conventions encoded (from `dim-audit-findings.md`): one two-reference dim per fact; slab edge → nearest grid placed 2 ft in from a corner, both ends when the edge is over 20 ft; edges flush with a wall/beam face skipped; jogs ≤ 6 ft edge→edge; opening size across every step + near edge → nearest grid, or → wall face within 8 ft when closer than the grid; opening dims go on the side away from the other direction's grid so the two never cross, size and location share a line; beam width + near side → grid, or side|grid|side when centred; free beam ends → grid or column face within 4 ft, ends buried in a column/wall skipped; wall face → grid or face|grid|face; CJ → grid.
- **Place — `mcc_place.py`** `Placer.find_station` searches out from the preferred station in 1 ft steps: blocked by columns/walls/openings, other strings too close and overlapping (touching = allowed, so width + location dims align on one line), crossings with strings of other directions, and grids running along the dim line within 1.5 ft; a beam under the line is a soft penalty. Falls back to the preferred station and counts "placed over obstacle". Pulls short text off the line with a leader. Journals created ids per view (`script.get_document_data_file("mcc_autodims")`) so a rerun offers to replace them.

## Buttons
- **Dim Soffit** — tick passes (Slab edges, Openings, Beams, Walls, CJ lines) with "remember as default"; uses dimension type `5/64" Arial Narrow (Transparent)` when present; selected floors restrict the slab.
- **Score Dims** — pick the hand-dimensioned view and its auto-dimensioned duplicate; matches dims by the set of (kind, element id[, face]) they reference; reports recall / precision per category and lists missed and extra dims with values and element links.
- **Audit Dims** — read-only audit of hand dims (what they reference, standoff, patterns) → CSV. Its output is the spec.

## Not yet
- Columns stay with the existing Dim Columns button. Slab islands (floors inside floors) are treated as slabs, not beams. Angled (grid-less) edges are counted, not dimensioned. Wall ends / wall lengths not dimensioned.
- The old `Dim Slab Edges` button is still there for comparison; retire it once Dim Soffit scores better on L3 and L7.
