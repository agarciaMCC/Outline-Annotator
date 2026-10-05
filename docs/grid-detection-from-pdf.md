# Grid detection from PDF plan sheets

Goal: create Revit grids automatically from the PDF sets we receive, since we rarely get RVT or DWG files.

## Decisions (Adolfo)
- **Called-out dimensions govern grid spacing.** Measured geometry is only used to find the grids and, where no dimension exists, as a flagged fallback.
- **When the sheets disagree, the tool flags it and the user picks.** Neither sheet wins automatically, and the conflict has no default pick.
- When a gap is dimensioned on only one sheet, that sheet's dimension is used and the gap is noted, not treated as a conflict.

## The button: MCC tab > Setup > Grids from PDF (v0.1, built 2026-09-29, not yet run in Revit)
- `MCC.tab/Setup.panel/Grids from PDF.pushbutton/`: `script.py` (IronPython UI and grid creation), `ui.xaml`, and `pdfgrids/detect.py` (the CPython PDF engine).
- `lib/mcc_gridpdf.py`: applies the user's picks, chains the spacing, finds the reference intersection and transforms to model coordinates. It's pure Python and was tested against the Kalae results.
- **Why the extra Python:** pyRevit's IronPython can't load PyMuPDF, so the button runs the system's Python 3 (it tries `py -3`, `python`, and the usual install folders, and the path can be saved). The first run offers `pip install --user pymupdf`.
- **One window:** Sheet 1 (reference) and optional Sheet 2 with page numbers, plus scale (Auto reads it from the dimensions). **Read grids**, then the "Sheets disagree" picks (only when needed), then the grid list with notes (existing names skipped), **Open check PDF**, and placement (grid intersection → a picked point or the internal origin, rotation, grid type, even out grid ends). **Create grids** runs as one undoable transaction, and the new grids stay selected. Set as default remembers the options.

## Engine (detect.py)
1. Bubbles are circles of the most common size with a short label inside. Each grid line runs from the bubble through its center, following elbow leaders. Dash segments are joined (gap up to 7 bubble diameters).
2. Angle families are clustered within 0.6° and snapped to a clean angle.
3. **Auto scale:** measured gap ÷ called-out dimension, taking the mode and snapping to standard scales. If the scale is entered and the dimensions disagree with it, you get a warning.
4. **Spacing:** each gap uses the dimension between its two grids that runs across them and is within 3" of the measured gap. Undimensioned gaps keep the measured value, rounded to ⅛".
5. **Two sheets:** Sheet 2 is registered to Sheet 1 by rotation plus least-squares translation on the grids they share. Gaps are compared: called-out values that differ by more than 1/32" are a conflict. A family's placement is fit to each sheet, and a spread over ¼" is a conflict.
6. Output is `result.json` plus check PDFs in `%TEMP%\MCC_GridsFromPDF`.

## Kalae tests, 2026-09-29 (both 3/32")
- **S1.01A (struct):** 48 grids. All 42 gaps are set by called-out dimensions. Grid angles are 0/90/25/30/115/120°. The scale was read automatically from 41 dimensions.
- **A2.71A (arch slab edge):** 48 grids, and the busy content caused no false grids. A stray second "A1" bubble near F is excluded. The arch sheet has no grid 10.
- **Combined:** 0 conflicts, and the whole run takes about 2 seconds. Checked spacings: 27'-5", 20'-3", 9'-11", 28'-0", 29'-4", 17'-4". A faked 14'-3" vs 14'-2" came up as a pick with no default.
- Rotated-family placement comes from geometry (there's no tie dimension). Residuals are about ±¾" against the raw line points, and the two sheets agree within ¼".

## Earlier stand-alone scripts (`Grid Detection/` folder)
`grid_detect.py`, `grid_dims.py` and `grid_compare.py`, plus the CSV/JSON/check-PDF outputs from the first tests. They're superseded by the button's engine.

## Next steps
- First run in Revit on a Kalae copy.
- Check that overall dimensions equal the sum of their parts.
- Let the user pick sheets in a full set by sheet number, not page.
