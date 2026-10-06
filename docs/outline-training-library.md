# Outline training library (past McClone outline sets)

Goal (Adolfo, 2026-10-06): gather the outline sets McClone issued on past jobs so the outline annotator can
learn from them. **Soffit plans first**; other sheet types (sections, wall elevations, enlarged plans, falsework)
later, for other skills.

## Where the sets come from
- `Z:\Shared\MCC Shared\Archives\Project Folders\<job> <name>\CONTRACT DOCS\MCC Drawings\Outlines\`
  (Adolfo: follow this folder convention for every job). Jobs **1038 and newer** only (`7400 - Yard` is not a job).
- 217 jobs have the folder. A few split MCC Drawings by building instead of having `Outlines\` (1050 "All Sheets",
  1053 Garage/Podium, 1153 Wyandot/Zuni) — for those the whole MCC Drawings folder is scanned.
  No MCC Drawings folder: 1091 - Block 18 (duplicate folder), 1109, 1129, 1188 (cont'd), 1234 Sand Box.
- Inside `Outlines\` a job has a full set (one multi-page PDF, often "<date> - Current Set - ... - Outlines"),
  individual sheets (`Individual Dwgs\`), or both. Folders named archive / superseded / old / void are skipped.
- The Z: drive is **only read**, never written.

## How it works (`Training Library/`)
1. `python inventory.py` — one row per PDF page in `inventory.csv`: file, page, sheet size, the **title block**
   text (the strip down the right edge of the sheet; big lines = sheet title, project name, sheet number) and the
   drawing's view-title-like lines. Re-running continues where it stopped. ~8 jobs scanned at once.
2. `python classify.py` — picks soffit plans and copies each sheet's newest clean issue, one page per PDF, to
   `Training Library/Soffit Plans/<job project>/<sheet> <title>.pdf`. Index of every hit in `soffit_index.csv`.
   `--no-copy` writes only the index.

Soffit plan = title block says SOFFIT ... PLAN / OUTLINE / VIEW (e.g. "LEVEL 3 NORTH - SOFFIT PLAN VIEW",
"LEVEL B2 SOFFIT/ MAT SLAB PLAN", "GROUND LEVEL - WEST - SOG & SOFFIT PLAN"), and not falsework, reshore,
shoring, insert layout, top of slab, section, detail or elevation. Enlarged soffit plans (5.X sheets, ENLARGED /
PARTIAL in the title) are kept and marked `kind=enlarged`.
- No title block text → view titles on the drawing; no text at all (scan) → file name, but only for a one-page PDF.
  Pages of **scanned full sets** are listed as `scanned set - check` and not copied (need a look or OCR).
- The same sheet often appears several times (full set + individual sheet + re-issues). Newest file wins;
  markups (MARKUP, RFI, CM, COMMENT, REDLINE, RETURNED in the path) only when nothing else has that sheet.

**Sheets titled by level only are not kept** (Adolfo, 2026-10-06): older sets often title the soffit plan
"LEVEL 2 - PLAN VIEW", "LEVEL 2 - AREA 1", "LEVEL 1 OUTLINES" etc.; those jobs (~48) are not in the library.

## Status
- 2026-10-06 first full run: 195 jobs with PDFs (22 of the 217 folders were empty), 6,017 PDFs, 21,864 pages.
  **1,188 soffit sheets copied (1.2 GB) from 126 jobs**, 43 of them enlarged plans. Spot check of random sheets:
  all real soffit plans.
- 187 pages in 20 jobs are scanned sets with no text (1041, 1044, 1046, 1056, 1063, 1070, 1096, 1105, 1107, 1112,
  1113, 1114, 1134, 1154, 1155, 1177, 1196, 1198, 1204, 1210) — listed, not copied. Most of those jobs also have
  text sheets that were copied.
- Jobs with no soffit plan: foundation/wall-only jobs (1092, 1221, 1239, 1241, 1243, 1247, 1249, 1265, 1272, 1273),
  core/canopy jobs (1157, 1205), TOS-only sets (1167, 1216), jobs whose plans are titled by level only, and a few
  to look at (1149, 1150, 1180, 1198, 1201, 1212, 1041 = scans).

## Open
- Scanned sets with no text: OCR or a visual pass.
- Other sheet types for later skills: the inventory already holds every page, so new classifiers only need
  `inventory.csv`.
