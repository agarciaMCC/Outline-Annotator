# How the current Kalae Outlines set (2025.08, 26 sheets) is dimensioned and annotated

Source: "Current Set - 1268 - Outlines.pdf". Studied 1.7.0 (Level 7-38 tower soffit plan) and 1.5.0 (podium) closely.

## Sheet composition (1.X.0)
- Main plan at 1/8" with north arrow; partial plans / core plans / typical column details / pilaster details on the same sheet as separate viewports, each with a titled view number.
- Schedules on the sheet: COL HEIGHT table (top level / base level / col ht / qty) and TOWER ELEVATION DATUM (level / NAVD / datum) — a typical-level sheet covers Levels 7-38 with one plan.
- Legend (S1. SOFFIT PLAN) and general notes on the cover; not repeated on every plan.
- Blue = information above/hidden (EOS above, dashed opening outlines above, blue dims to EOS above). Red = revision-clouded items and "DIMENSIONS, COLUMNS – Confirm …" coordination notes with leaders — RFI-style QA callouts. Everything else black.

## Grid dimensions
- Outermost tier at the top and side of the plan: grid-to-grid string across all grids (25'-9", 22'-11", 37'-4") with an overall (86'-0") above it. Same on the vertical side (36'-0", 36'-2" … 176'-6" overall).

## Perimeter / edge of slab (EOS)
- Dimensions are strings running along the outside of the plan, perpendicular to the grids: e.g. across the top "17'-10" | 5'-1"" (grid 6 → jog → grid 7) and a second tier "41'-3 1/2"" (grid 7 → EOS). Jogs are chained in one string, not dimensioned individually.
- Tiered: tier 1 (closest to slab) = local edge/jog dims, tier 2 = span to grid or overall. Witness lines stay short; dim lines never cross the slab.
- Short offsets (1'-1 1/2", 3'-4 1/2" column pilaster projections) are dimensioned once per condition, from the nearest grid.
- Left side: vertical strings outside the slab stacked in 2-3 tiers (local, 28'-5 3/8" tier, 36'-0" grid tier).

## Openings / blockouts
- Every opening: from the nearest grid → near edge → far edge in BOTH directions (e.g. "1'-3" | 4'-1 1/4"" horizontally, "1'-9 1/4"" vertically to the top edge then size). Exactly the rule already implemented.
- Strings sit immediately beside the opening (within ~1-2 ft), outside its outline; small openings share a common dim line where they line up (e.g. "5'-0 1/8" | 1'-9 1/4"" chains two blockouts).
- Openings drawn with blue dashed X / hatch; blockouts also get a wider chained string when several fall on one line (14'-3 3/4" / 11'-7 3/4" / 2'-8").

## Columns
- Each column gets: (a) location dims from the two nearest grids to the column FACE (not centerline), small local strings right at the column ("3'-4 1/2"", "1'-3 1/4"", "4'-2 5/8""), (b) a column tag box with leader and dot: `10x72 COL / T: 77'-4" / B: 68'-3" / COL HT: 9'-1"`, with the slab thickness ("7 1/2"") written beside the box, (c) the column size written as two numbers on its edges (10 and 72) in grey.
- Round columns: "24Ø" beside, tag "24"Ø COL".
- Column tags are placed in open slab area, leader to the column, consistently on the same side where possible.

## Beams
- Beam tag box: `48x64 BM / T/BM: 48'-3" / B/BM: 46'-9" / CLR HT: ±7'-8"` with leader; width and depth numbers on the beam edges (e.g. "18" / "72"); beam width dimensioned with a short dim across it. Section markers (2.5.0 series) cut each beam type.
- Beam ends located to grid with a dim ("72x72 beam end from grid" is a red confirm note when missing).

## Slabs
- One slab tag per slab region: `7 1/2" PT SLAB / T/SLAB: 77'-11 1/2" / B/SLAB: 77'-4"` with leader and dot, thickness beside. Placed in open area, never on top of an opening or a column tag.
- Slab transitions labelled ("9 SLAB TRANSITION") with the transition edge dimensioned; depressed slabs hatched (pink) with their own tag.

## Walls
- Wall thickness text along the wall ("18" CIP WALL", "24" - 20" CIP WALL"), wall elevation markers (4.1.x) on the working face, wall length and location from grid as red-when-unconfirmed dims, and a wall tag box (T / B / HT) for core walls.
- Wall section markers at each wall type.

## Style details
- Dim text 5/64" Arial Narrow, fractions to 1/8", opaque background; dims chained (not baseline). Overall strings placed on the outermost tier.
- Consistent tiers: local → grid → overall, each tier offset a fixed distance. Nothing sits inside an opening or across a column.
- Column/slab/beam values are all elevation-based (T/B in project datum), matching the 3-Box tag families in the model.

## Gap vs the extension today
| Set does | Extension does | Change needed |
|---|---|---|
| Grid-to-grid + overall strings outside | nothing | new: Dim Grids (easy) |
| Perimeter chained per side, tiered | one string per edge past a corner | rework: chain all perpendicular edges per side into tiers |
| Openings: nearest grid → near → far both ways | same | keep; add sharing a dim line for aligned openings |
| Column face-to-grid location dims + tag box | tag box only (Tag Soffit) | new: Dim Columns |
| Beam width dims + tag | tag only | later |
| Slab tag in open area | tag at bbox center | improve placement (avoid openings/columns) |
| Wall text + markers | wall tag only | later |
| Red confirm notes | manual | out of scope (maybe QA list) |
