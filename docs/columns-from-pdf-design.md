# Columns from PDF (MCC tab > Setup): v0.5, 2026-09-30, first Revit runs under way

Places Revit structural columns on one level from that level's PDF plan plus the column schedule PDF.

## Decisions (Adolfo, 2026-09-30)
- **Scope and height:** one level per run, one story per column. Base at the level with 0'-0" offset; top at the level above, attached to the slab above.
- **Mark** = the schedule mark. Nothing extra is written.
- **Family** comes from the schedule DETAIL-TYPE:
  - T9 → Bullnose
  - T10 / T11, or a diameter size → Circular
  - Everything else → Rectangular
- The user can switch any mark's family in the review list, e.g. to force Bullnose.
- **Bullnose:** placed lined up with its drawn outline; the rounded end isn't auto-oriented. They're flagged "flip if needed", and the user flips by hand.
- **"Create all types from schedule"** makes every size in the schedule (all pages and levels) as a column type up front.
- **Families are picked in the window** from every loaded family in the Structural Columns category. The names don't have to match exactly; each picker is pre-selected by the best name match, and the choices are remembered.
  - On the test model the loaded families are "Concrete-Rectangular-Column", "Concrete-Round-Column" and "Structural - Columns - Concrete Bullnose (R22)".
- **Flagged columns** get a #number that is circled on the check PDF (red = check it, blue = bullnose flip). The same number appears in the list notes.
- **Check dimensions** (option, on by default): a dimension from each placed column's center to the nearest grid in each direction. It's skipped in a direction where the column is centered on the grid. The dimension line sits beside the column, 3/8" on paper past the column face, so it doesn't run over the column or its text. It's for a quick check against the contract drawings.
- **Schedules:** the button must read different column schedule layouts (Adolfo, 2026-09-30). See "Schedule reader" below.

## Family parameters (McClone families)
- **Rectangular / Bullnose:** "Column Width" = schedule W, "Column Length" = schedule D. For example, type "12X24 COL" is Width 1'-0" and Length 2'-0".
- **Bullnose:** "Column Nose Radius" is set to W/2.
- **Types** are named "12X24 COL", matched case-insensitively. Existing types with matching sizes are reused.
- **Assumed:** Column Width runs along the family's local X, and the button rotates the column so Width lies along the matching drawn side. This still needs confirming in Revit.

## Files
- `MCC.tab/Setup.panel/Columns from PDF.pushbutton/`: `script.py`, `ui.xaml`, `pdfcols/columns.py` (plan reader + build), and `pdfcols/schedule.py` (schedule reader). The CPython engine imports `../Grids from PDF.pushbutton/pdfgrids/detect.py`.
- `lib/mcc_colpdf.py`: the alignment fit, placement and center_dims maths (pure Python, tested).
- `lib/mcc_pyrun.py`: finds Python 3 and PyMuPDF and runs the engine.

## How it works
- **Engine:** reads the plan's grids (same frame as Grids from PDF) and scale, then:
  - takes each column's true outline from the clip path of its gray fill;
  - matches labels to columns one-to-one: shortest leader first, and a label moves to its next candidate if its first column is already taken. Duplicate overprinted labels are merged;
  - skips legend samples (near "INDICATES…");
  - reads the schedule at the chosen level.
- **Revit side:** fits sheet → model with a rigid 2D fit on the grid intersections found in both. On the Kalae test: 793 points, rotation recovered exactly, residual 0.03".
- **Check dimensions:** from the grid reference to the column's Center (Left/Right) or Center (Front/Back) family reference, made in the active plan view with a selectable linear dimension type.

## Schedule reader (v0.4, 2026-09-30): `pdfcols/schedule.py`
Reads several schedule layouts. One sheet can hold several tables (for example the Horizon House tower and podium tables), and each table is read separately.
- **Grid:** marks across the top, levels down the side. Kalae S3.11 and S3.12, and Horizon House S-4.03, are both this layout.
  - A size in a level's row runs up until the next size. An empty cell continues from below. A gray cell, or one reading "-", "N/A" or "NONE", means no column.
  - Rows are found from the table's ruling lines: each level label owns the band that ends at the first rule below it. Where there are too few rules, it falls back to the old rule (label at the bottom of its row).
  - Marks printed only in the bottom header row are picked up too (Kalae TC27).
- **Transposed:** levels across the top, marks down the side. The same rules apply, turned 90°.
- **List:** one row per mark (MARK | SIZE | ...), with optional FROM/TO, BASE/TOP or LEVELS columns. Mark cells like "C3-C5" or "C6, C7" are expanded. If there are no level columns, the size applies at every level.
- **Levels are text keys.** "LEVEL 01", "L1" and "LVL 1" all read as "1"; B7, P2, ROOF and MACHINE ROOM also work. The button pre-fills the schedule level from the Revit level name ("LEVEL B7" → B7), and the box accepts text. If the level isn't in the schedule, a warning lists the levels that are.
- **Sizes it reads:** 24x24, 24"x24", 18 X 24, 2'-0"x3'-0", 24"Ø, Ø24" and 24" DIA. The first size in reading order wins.
- **Detail types it reads:** T9, [9] and TYPE 9. The bullnose/round mapping (T9, T10, T11) applies to T-types only, so Horizon House's [9] isn't treated as a bullnose.
- **Regression on Kalae:** same results and the same 34 types, except Level 38. The old parser read the ROOF row as Level 38 (for example TC8 came out 18x24 instead of 18x72); the new result is correct.
- **Horizon House B7 test:** all 43 marked columns get schedule sizes (they were all "not found" before), giving 9 types.

## Columns in walls (v0.4, 2026-09-30, Adolfo's call)
Where a column is partly inside a wall, the plan's gray outline shows only the visible part. For these the button keeps the faces that are visible and extends the column into the wall until it reaches its schedule size.
- **Finding the wall side:** points 2.5 pt outside each face of the drawn outline are tested against the rendered sheet (the same gray the walls and columns use). A face with gray beyond it is against a wall. This is `WallProbe` / `into_wall` in `columns.py`.
- **Which schedule side goes where:** both ways round are tried, and the smallest extension that only grows toward the wall side(s) wins. Buried in a wall corner, the column extends along both axes from the visible corner.
- **Flags:** a column extended this way gets a blue info note ("in a wall - drawn 10x24, hidden part extended 14" into the wall to 24x24"), and the check PDF shows its full outline dashed blue.
- **Still red:** a wall on both sides of the visible part (the column is extended both ways), an extended face that lands outside the wall, no wall against the short side, or a schedule size smaller than the drawn shape.
- **B7 result:** 11 of the 12 mismatches were extended into walls (C6, C8 ×3, C9, C20 ×5, C33). C25 at 24x250 is a wall with a label on it and stays red. On a copy of the sheet turned 90° the result is the same, and Kalae L1 is unchanged (7 flags).
- Synthetic list, transposed and centered-label test PDFs pass. No real sample of those layouts yet.

## Test library + v0.5 generalisation (2026-09-30)
Adolfo pointed me at Egnyte: `/Shared/<area>/Projects/<job> <name>/CONTRACT DOCS/Contract Drawings/Structural`. The areas are HI, NCA, UT, WA and CO (CO uses `PROJECTS`), and the current set there is named `yyyy.mm.dd - Current Set - <job> - Struct.pdf`. The first batch of jobs he chose: 1256, 1305, 1326, 1332, 1276, 1313, 1282, 1246, 1281, 1324 and 1215.
- **Library location:** `Outline Annotator/Test Library/`, next to MCC.extension. It holds the schedule and plan pages, plus `cases.json`, `baseline/` and `run_library.py`, which re-runs every case against the engine and lists any that changed. `schedule_check.py` draws the schedule reading over the sheet. Only Kalae is marked verified; the other baselines guard against regressions only.
- **Schedule reader:**
  - level labels as bare numbers under a LEVEL header;
  - level ranges ("L34 TO L38", "L39 / TO ROOF", "L24-L25");
  - two labels in one block (the upper one is only the top);
  - labels hung under the level line (the band belongs to the label below);
  - mark row as the table footer (DCI);
  - a table's end taken from its run of ruling lines;
  - a COLUMN SIZE property row that applies to all levels;
  - short 2–3 mark tables when the row says MARK;
  - shared headers ("C-5, C-5A");
  - list tables with WIDTH/DEPTH columns, picking the size column by what parses;
  - marks like C18X24-1;
  - letter types from the DETAIL-TYPE row;
  - SHX "24\"S" read as a diameter;
  - steel sections (W14X48, HSS...) detected as steel and not placed; they're no longer misread as 14x48.
- **Plan reader:**
  - gray fill accepted from 0.3 to 0.92 (1305 uses 0.5);
  - outline-drawn columns: white-masked or stroked closed shapes of column size with no text inside, used when gray fills match under half the labels;
  - only marks whose prefix appears in the schedule (so PC-1 pile caps are ignored).
- **Grid engine (detect.py):** polyline-circle bubbles, square grid tags, and the printed view scale as a fallback when the dimensions give no scale or an odd one. Parsing of odd-scale labels is also fixed. Grids on the Kalae and Horizon House sheets are unchanged.
- **Results:** 1256 L2 98 columns / 2 flagged; 1305 L2 100 / 5; 1313 L1 38 / 0; 1326 L2 82 / 5; 1215 parking L1 55 / 4; Kalae and Horizon House unchanged.
- **Not handled yet:** steel families; graphical steel schedules keyed by grid location (1281); unmarked columns (1332 B2) — a stacking check or carrying marks from the level below would cover these; per-project mapping of letter types to families; sizes only given in column sections (1246); two plans on one sheet.
- **Deployed** via `Revit_temp/cols_engine_v8.py`, `cols_schedule_v8.py` and `grids_detect_v8.py`, with md5s verified. script.py was not touched; another session had changed it (R2026 fix).

## Kalae Level 1 test (engine)
- 100 unique labels (one of them the legend sample) matched one-to-one to 99 columns.
- 27 unmarked gray shapes (walls) are listed and not placed.
- 7 flags: 6 bullnose "flip if needed" (C21, C22), and one C12 drawn at 12x16 vs the schedule's 12x18.
- 34 distinct types across S3.11 and S3.12.

## Delivery note
- Committing files straight into the extension folder has silently failed several times. The reliable route is to commit to `Revit_temp/` under a new name, copy the file into place on the PC, then check the md5 on the PC. v0.4 went in as `Revit_temp/cols_*_v6.*`, and the wall update as `cols_engine_v7.py` / `cols_script_v7.py`, with md5s verified.

## Open / next
- Confirm the Width orientation, top attachment, the circular family's parameters and the check dimensions in Revit.
- C23's schedule header sits inside a revision cloud, so C23 isn't read.
