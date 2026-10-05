# MCC shop drawing sheet standards (from Adolfo, 2026-09-28)

Sheet numbers are **series.level.index** (e.g. 1.3.0 = series 1, Level 3, sheet 0; 2.2.1 = Level 2 sections, sheet #1; suffix letters like 14.5.0A for splits).

## 1.X.0 — Soffit or Top of Slab (Floor) plan view
Includes:
- Plan view of structure with north arrow (no 3-legged)
- All soffit / top-of-slab elevations with slab thicknesses, beam width and thickness, column/pilaster sizes. Top of column & wall elevations for "Floor" plans (or separate vertical elevation sheet if congested)
- All dimensions from grid lines required to build. Tie (reference) elements and edges back to nearest gridline. Close-out dimension strings
- All individual member section cuts (sheet series 2.X.0) for every different condition (clockwise around perimeter, right-to-left interior)
- Shade all beams (beam shade); walls and columns (wall/column shade). Revit floor plans: VERT only shaded when it extends to next floor, else hidden lines; short walls/curbs no shading
- All wall elevation references, viewed from the direction the field crew builds / side of most detail
- **A one-level building section showing at least one bay with slab thickness and shoring height from slab below (consider 3 floors: working level plus level above and below)**
- Isometric of the structure (if room)
- Key plan if partial plan
- Legend and typical notes

## 2.X.0 — Sections (beams, slab edges, slab transitions)
- Individual member sections at 1/2"–1" scale; all dimensions of surfaces to be formed
- Show rebar/embeds that penetrate form surfaces; reference structural details / approved rebar shops — MCC drawings don't indicate reinforcing
- Shading: horizontal (light) vs vertical (dark) members; none beyond concrete
- 1 sheet of sections per level (2.2.1 = Level 2 sections, sheet #1)
- Locate sections on plan where possible (1.X.0 series)

## 3.X.0 — Elevation views, building sections of ramps / multilevel features
- Multilevel building section as large as fits; floor-to-soffit and slab thickness dims; top of footing/slab to slab soffit dims

## 4.X.0 — Wall elevations and details
- Wall elevation showing/dimensioning openings, beam pockets, intersections, reveals; vertical dims of all wall pours; wall thicknesses; vertical construction joints; spot elevations per top-of-wall
- Predominant working face (exterior for cores/exterior walls; interior for OSW and below-grade)
- Wall section plan view directly under the elevation; full wall section with pour heights to the right when space permits
- Most wall details at 1/4" scale

## 5.X.0 — Partial plans / large-scale details of congested areas
- Plan of congested area at large scale, full sections, individual member sections

## Implications for the extension
- Sheet builder: `1.{level}.0` is correct. Sheet name convention still to confirm (check name of existing 1.3.0 in Kalae).
- Sheet builder roadmap items straight from the 1.X.0 list: north arrow, legend + typical notes, key plan (partial plans), one-level building section per level, isometric.
- Pre-issue QA check = the 1.X.0 "includes" list as an audit.
- Kalae model has sheets in a "14.x" series not in this convention — ask what that is.
