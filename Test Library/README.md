# Columns from PDF: test library

These are real contract-drawing sheets from 11 McClone jobs plus Kalae (1268). Each job folder holds the column schedule sheet(s) and one or two framing plans, all copied from the current structural set on Egnyte (`CONTRACT DOCS/Contract Drawings/Structural`). The library gives the Columns from PDF / Grids from PDF code a fixed set of drawing styles to check against after every change.

## Running it
From this folder, with the same Python + PyMuPDF the MCC buttons use:

```
python run_library.py            # run every case and compare with baseline/
python run_library.py --checks   # also write the plan check PDFs into each job folder
python run_library.py --update   # accept the current results as the new baseline
python schedule_check.py 1313/schedule.pdf 1313/schedule_check.pdf
```

A full run takes about 6 minutes. Any case whose result differs from `baseline/` is listed with its differences.

## Files in each job folder
- `schedule*.pdf`: the schedule sheet(s).
- `plan_<level>.pdf`: the framing plan.
- `schedule_check.pdf`: what the schedule reader understood. A red box with text means "level: size read"; a blue box means empty (the column continues from below) or gray (no column).
- `plan_<level>_check.pdf`: the plan check. A green box is a column read. An orange dashed box is a gray shape with no mark, which isn't placed. A red or blue circle is a flagged column.

## Verification status
Only Kalae (1268) is marked `verified` in `cases.json`. Every other baseline was checked by spot views only, not cell by cell. To verify a case, look over its two check PDFs. If they're right, set `"verified": true`. If something is wrong, note it in the case's `style` text.

## Cases (Sept 30, 2026)

| Job | Schedule style | Schedule read | Plan read |
|---|---|---|---|
| 1268 Kalae | Baldridge grid; TC marks; T-types | 53 marks | L1: 99 columns, 7 flagged |
| 1215 Landing parking | grid; hyphen marks (C-1); shared header C-5/C-5A | 11 marks x 10 levels | L1: 55 columns, 4 flagged. PC-# pile caps are ignored because they're not schedule marks |
| 1215 Landing office | **steel** W-shape gravity schedule | read as steel, not placed | 0 columns (steel) |
| 1256 Alia | Baldridge; L1/L6 labels; level ranges (L34 TO L38, L39 TO ROOF); letter types | 69 marks | L2: 98 columns, 2 flagged |
| 1276 Kent Station | small 3-mark grid; labels centered in merged cells | 3 marks x 4 levels | plans have no column marks |
| 1281 ICS Delta | **steel graphical** schedule keyed by grid location | not supported | not tested |
| 1282 Mercy Housing | list; WIDTH/DEPTH columns; marks like C18X24-1 | 4 marks | plans have no column marks |
| 1305 Launiu | Baldridge; bare level numbers under a LEVEL header | 43 marks x 41 levels | L2: 100 columns, 5 flagged. Columns are a darker gray (0.5) |
| 1313 Waldorf | grid; labels hung under the level lines; SHX font draws Ø as S | 16 marks x 7 levels | L1: 38 columns, 0 flagged |
| 1324 NVIDIA | CC sizes in a COLUMN SIZE row under the table; SC = steel | 5 concrete + 9 steel | P1/L1: SC steel marks, no concrete placed |
| 1326 Kinect | DCI graphical; mark row at the bottom; rotated text | 26 marks x 5 levels | L2: 82 columns, 5 flagged. Columns are drawn as outlines |
| 1332 Horizon House | MKA grid; B-levels; tower + podium tables | 30 marks x 41 levels | B7: 43 columns (11 extended into walls). B2: 8 columns, 43 unmarked |

## Known gaps (not handled yet)
- **Steel columns:** W and HSS sizes are recognised and flagged, but not placed. There's no steel family setup yet.
- **Graphical steel schedules keyed by grid location** (1281): a column is identified by where it sits, e.g. "C1-CC", not by a mark.
- **Unmarked columns:** plans where most columns carry no mark (1332 B2), or where the mark is only given on another level. A stacking check against the level below would carry the marks over.
- **Letter detail types** (Alia A...FF, Horizon House [1]...[28]): they're read, but mapping them to bullnose or round families is project-specific.
- **Column sizes only in column sections or elevations** instead of a schedule (1246 Founders Place S504).
- **Sheets with two plans on one page** (1215 parking S2.1): both are read, and they share one grid fit.
