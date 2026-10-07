# Dimensioning rules (Adolfo) — what the MCC buttons must follow

Collected from review of test runs on 1268 Kalae, Level 7/8 soffit, 2026-09-28; extended 2026-10-01.

## Locating
1. **Every slab edge is located directly from a grid.** Never locate an edge off another edge — tape errors compound with each subsequent string measurement in the field. The chained edge-to-edge string may stay as a double-check, but each edge also gets its own grid → edge dimension.
   - 2026-10-01: same for **soffit steps** — the distance between two soffit steps (edge → edge) is fine to dimension as a double check, but each step edge must be locatable off a gridline. "The dimensioning isn't always perfect but the most important thing is being able to locate an edge/point off of a gridline."
   - → Scoring consequence: the primary metric is **grid-location coverage** — share of edges/points that have a dim tying them to a grid — not precision vs the hand sheet. Edge-to-edge dims the detailer didn't draw are acceptable extras, not errors.
2. **Don't assume repeated conditions.** An edge that looks identical to one elsewhere on the slab still gets its own dimension; the field can't infer it from another area. (Applies to aligned repeats too, e.g. the 9'-6 5/8" step gaps 36 ft apart on L3 North — each is dimensioned.)
3. **Dimension at every turn.** Wherever the slab edge changes direction, the edges meeting there are located from the nearest grid right at that corner — even if the same edge is already dimensioned somewhere else, especially on long edges where that dimension is far from the next turn. (e.g. pilaster bump: at its top and bottom, one string slab face | grid | bump face.)
4. **Openings, drops, beams inside the footprint** — agreed 2026-10-01 after comparing the L3 North core with the hand sheet: **each edge is located from the nearest anchor on its own side** (anchor = nearest grid, or the facing wall face, e.g. an elevator core's inner wall). One string per direction: **anchor | edge | edge | anchor** — every outer edge sits next to an anchor (no chaining), the edge-to-edge segment is the size check, and dims stay short. Not one grid for every edge (that produced long stacked dims across the core).
   - One-sided (no anchor within ~20 ft on the far side): anchor | edge | edge. **No separate anchor → far edge dim** (2026-10-07, L7 round 2: the near-edge dim plus the size, end to end, is enough). Once an opening is located from the nearer grid, **no second leg to the next grid** either.
   - Big or stepped voids (> 20 ft across, or > 2 faces in a direction): each edge located locally from its nearest anchor, like slab edges — never one long chained string.
   - Small penetrations (≤ 2 ft): one compact string per direction. Dimension them (they may be "layout by others"; the user deletes if not wanted).
   - **Elevator openings:** when an opening face is in line with a wall edge, it is dimensioned **off the wall face**, so the rough opening stays the same all the way up the building. Grid dims are still added where possible. An opening edge dimensioned to an in-line wall face counts as located.
   - An edge lying on a wall face is located by the wall; dimension the opening's other edges and its full size.
5. **Columns**: from nearest grid in each direction, to centerline or face (user choice per run). A column centred on a grid needs no dim in that direction.
6. Grid-to-grid and overall strings are a separate button (Dim Grids), not mixed into edge strings.
7. **Walls are located on their own sheets** (4.x wall elevations / 5.x core walls), not on soffit plans (2026-10-01). Wall faces are not targets on soffit plans, but they are valid anchors. Dim Soffit's wall pass is off by default on soffit plans.
8. **Beam ends** that frame into a column or wall are located by that member — no dim. Free beam ends are located off a grid (not off a nearby column face).
9. **Only dimension what is inside the view's crop** (zone views): the other zone's sheet covers the rest; never reach 35 ft into the next zone for a grid. Locating dims should stay under ~20 ft where an anchor exists.

## Redundancy (2026-10-01)
- Dims whose witness lines fall on the **same planes** (different elements sharing one face/edge line — slab pieces at a joint, an opening edge on a slab jog) are redundant; keep one. Dim Soffit de-duplicates before placing (`mcc_place.dedupe`).
- Aligned repeats at different places (rule 2) are **not** redundant.
- Joined columns/beams/walls cut their outline out of the slab's soffit face — those holes are **not openings** (no dims).

## Placement
10. Perimeter strings sit **outside** the slab; hierarchy from the slab outward: chain check → grid→edge strings (shortest first) → grid-to-grid → overall.
11. Strings sit close to the object they dimension (≈1 ft), not scattered.
12. An opening's string goes on **whichever side has room and doesn't interfere with other dimensions** (2026-10-07, L7 round 2 — replaces "away from its partner string"). The locating dim and the size stay together on that side. (The tool starts from the side away from the partner string and switches when that side costs a row more or a crossing; it only breaks ties.)
13. Nearer objects take the lane nearest the grid; farther ones are pushed out.
14. Never sit inside an opening; keep clear of columns, walls, beams and crossing gridlines (no dim line along/over a grid line).
15. Share a line with a neighbouring string in the same direction where they don't overlap.
16. No crossing dimension lines; no crossing leaders.
17. Dims must fall inside the view's annotation crop (otherwise Revit hides them).

## Text
18. Text that doesn't fit its segment is pulled off the line with a visible leader — far enough to read the leader clearly — toward the nearer end of the string so neighbouring leaders diverge; stack rows rather than overlap.

## Style reference
See `annotation-style-observations.md` (from the Current Set - 1268 - Outlines PDF).
