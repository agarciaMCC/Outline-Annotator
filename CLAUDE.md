# Outline Annotator — MCC pyRevit extension

McClone Construction shop-drawing automation for Revit. The **MCC** tab (pyRevit extension `MCC.extension/`)
builds sheets, places tags and dimensions soffit plans the way McClone detailers do. Owner: Adolfo Garcia.

Design docs live in `docs/` (copied from the claude.ai "Outline Annotator" project on 2026-10-05).
**Read the relevant doc before changing a tool, and update it when a decision or status changes.**

## Hard constraints (don't break these)
- **IronPython 2.7** for everything that runs inside Revit (button `script.py`, `lib/*.py`): no f-strings,
  no type hints, no `print(..., end=)` tricks, no Python 3-only stdlib.
- **Revit 2023 is production; Revit 2026 is the dev/test rig.** Code must run on both:
  use `mcc_compat.eid_int(id)`, never `ElementId.IntegerValue` (gone in 2026).
- The PDF engines (`Setup.panel/*/pdfgrids/`, `pdfcols/`) are **CPython 3 + PyMuPDF**, run out-of-process
  via `lib/mcc_pyrun.py`. Keep them free of Revit imports.
- Each button's settings live in a CONFIG block at the top of its `script.py`.
- UI conventions Adolfo wants: one dialog per button with a "Set as default" tick box; **no end-of-run
  report** — alert only on problems. Sheet names and view titles are ALL CAPS.
- All model changes happen in one undoable transaction per run; use `transaction_with_log` (failure
  preprocessor) so Revit never shows a blocking commit dialog — that freezes Revit and the MCP link.

## Folder map
- `MCC.extension/MCC.tab/` — panels: Setup (Grids/Columns from PDF), Views & Sheets (Sheet Builder,
  Fit View Titles, View Range 3D), Dimensions (Dim Text), Diagnostics (Audit Dims, Dim Check,
  Inspect Model, Score Dims), WIP (Dim Soffit v1/v2, Dim Columns, Dim Grids, Fit Grids, Tag Soffit, Zones, ...).
- `MCC.extension/lib/` — shared modules. Dim Soffit v2 pipeline: `mcc_model.py` (recognize) →
  `mcc_features.py` → `mcc_strings.py` (string plan) → `mcc_layout.py` (placement);
  `mcc_coverage.py` / `mcc_score.py` for scoring; `mcc_place.py` (dedupe, text, transactions).
- `Claude outputs/audit_R26/` — headless runners (`run_v2.py`, `run_button.py`, `run_audit.py`) and run reports/PNGs.
- `Training Library/` — past jobs' outline sheets pulled from the Z: archive (`inventory.py`, `classify.py`); PDFs not on GitHub.
- `Test Library/` — PDF regression cases for Columns/Grids from PDF: `python run_library.py`.
- `MCC-DimText.extension/` — stripped-down Dim Text build shared with coworkers; keep in sync when Dim Text changes.
- `MCC-Testing.extension/` — "MCC Testing" tab shared with coworkers for buttons under test (Dim Soffit v2 so far).
  Its `lib/` holds copies of only the modules those buttons import; re-copy and rebuild
  `Setup Files/MCC-Testing.extension.zip` when they change.
- `RevitMCP.extension/` — third-party Revit MCP server, locally patched (see `docs/revit-mcp-setup.md`). Don't edit casually.
- `Reference Projects/<name>/` — models + issued PDFs, not on GitHub. `Kalae/1268 - Kalae (R26 TEST).rvt` is
  the dev/test model (the one the Revit MCP works on); Alia, Eastlake, Bothell Stem are other projects'
  detached copies for read-only study (see Testing below). `Revit_temp/` inside Kalae is Revit's own temp folder.
- `Test Inputs/` — loose PDFs and `Tester.rvt` used while building Grids/Columns from PDF (the curated
  regression set is `Test Library/`).
- `Setup Files/` — pyRevit installer, `MCC-Tools.extension.zip` (shared build).
- `Claude outputs/early runs/` — first screenshots; `Claude outputs/reference_study/` — other-projects study images.
- Models, `*_backup/` folders, PDFs, the installer — **never modify**. Never save over the R23 model.
  Backups are git commits — no more `*.bak` copies or staging folders (cleaned out 2026-10-05).

## Testing in Revit (Revit MCP)
- The `revit` MCP server talks to Revit 2026. **Edits and test runs: `1268 - Kalae (R26 TEST).rvt` only.**
- **Other projects' models (2026-10-05, Adolfo):** allowed for **read-only study** of how they were
  detailed (Audit Dims, reading views/dims). Only ever a **detached copy** (discard worksets) kept in
  `Reference Projects/`, **never** the original or the central/shared model; never save, never sync, close
  without saving (a Revit 2023 model opened in 2026 upgrades the copy — another reason it stays throwaway).
  Record findings in `docs/` and compare with Kalae.
- Read-only checks first; edit the model only in test runs Adolfo has agreed to, and only in the
  `ZZ CLAUDE TEST - ...` views (never the real zone views — dependents share the parent's annotations).
  See `docs/auto-dim-scoring.md` → "Test-view setup".
- `execute_revit_code` runs IronPython; add `MCC.extension\lib` to `sys.path` to import MCC modules.
  No transaction is opened for you. Calls time out at ~60 s but the run continues — read the report file it writes.
- After changing Routes/extension startup code, restart Revit (pyRevit Reload is not enough). Button
  script edits take effect on the next click.

## Domain rules (summaries — the docs are authoritative)
- **Sheet numbering** `series.level.index`: 1.X soffit/floor plans, 2.X member sections, 3.X elevations/building
  sections, 4.X wall elevations, 5.X partial plans, 14.X falsework. → `docs/sheet-standards.md`
- **Soffit plan views are hosted on the level whose slab they show**; phase New Construction;
  template `Plan - Outlines - Soffit View`. → `docs/kalae-model-config.md`
- **Dimensioning:** every edge/point must be locatable off a gridline (or an in-line wall face); never chain
  edge-to-edge as the only location; edge-to-edge dims are fine as checks. Primary metric is grid-location
  coverage, not match with the hand sheet. Max 2–3 lanes; ≤ 10 dims of cleanup per sheet is the target.
  → `docs/dimensioning-rules.md`, `docs/dim-soffit-v2-design.md`
- **Soffit plans dimension soffit elements only** — slab edges, beams, openings, CJs. Never dimension to walls,
  curbs (modeled as walls on Kalae) or columns; other plans cover those. Anchor to the **closest gridline**
  (even one running through an opening); a wall face only when no grid is within 30 ft.
- **30 ft max per dimension** — the field crew's tape. Stacked dims from one grid are the default; chains are checks.
- **A dimension at each end** of long CJs, slab edges and beams (> 20 ft), for ease of reading. Beam widths at
  beam ends. Line dims up with neighbours where possible.
- **Stacked rows: shortest nearest the element, longest furthest** — an overall goes outside its chain.
- **Nothing inside openings** (dim lines, text, leaders). Dims of one element that meet end to end on one line are
  joined into one string. Dim lines never sit on an edge running the same way.
- **Beams:** width dims just past a beam end (free end first; past a framed end out to open margin is fine); long
  beams (> 40 ft) also get one width dim halfway between the end dims. Other dims stay off beams.
- **An element's dims of one direction on one side of it**; its size joins its locating dim end to end; dims off the
  same gridline stack together. **Angled elements** use their own grid set; straight-grid dims to their corners only
  when no aligned grid is within 30 ft.
- **Not dimensioned here:** lines made by the view's cut plane (ramps), holes filled by other floors, voids in a
  wall line, beams in a wall line capped by walls (core-wall plans cover those). Curbs and CMU walls are not walls.
  Small openings (< 4 ft): near edge off the grid + size. Shafts in a core: off the core wall face.
- **Shafts:** only a shaft's overall size may go inside it, and only if there's no room outside; locating dims
  never. A shaft the slab wraps around (not a hole) still gets its overall size, slab edge to wall face.
- "Large Scale" detail items = CJ lines (dimension them); plain detail lines = QC points (ignore).
- Grids from PDF: called-out dimensions govern spacing; when sheets disagree, the user picks (no default).

## Doc index (`docs/`)
| Doc | What's in it |
|---|---|
| `dim-soffit-v2-handoff.md` | **Start here for Dim Soffit v2**: where each test view stands, the snapshot/compare/analyst routine, run numbers, hazards, open items |
| `dim-soffit-v2-design.md` | Current dimensioning rebuild — stages, status by run, open items, Adolfo's decisions |
| `dimensioning-rules.md` | The rules the dim tools must follow |
| `auto-dim-scoring.md` | Coverage metric, scoring runs, test-view setup |
| `dim-audit-findings.md` | How the hand-dimensioned Kalae sheets are actually dimensioned |
| `dim-soffit-architecture.md` | v1 pipeline (being replaced) |
| `annotation-style-observations.md` | What the issued Kalae Outlines set looks like |
| `sheet-standards.md` | McClone sheet series and what each sheet must include |
| `sheet-builder-design.md` | Sheet Builder (clone sheets across levels, split into zones) |
| `kalae-model-config.md` | Kalae model names: templates, title block, tags, levels |
| `fit-grids-rules.md` | Fit Grids behaviour |
| `grid-detection-from-pdf.md` | Grids from PDF engine and decisions |
| `columns-from-pdf-design.md` | Columns from PDF engine, schedule reader, test library |
| `revit-mcp-setup.md` | Revit MCP rig, local patches, ground rules |
| `other-projects-study.md` | How Alia, Eastlake, Bothell soffit plans are dimensioned vs Kalae; open questions |
| `archive-soffit-study.md` | 1,188 past soffit plans measured + 24 looked at vs the v2 rules; open questions |
| `outline-training-library.md` | Past jobs' outline sets gathered from the Z: archive for training (soffit plans first) |
| `project-readme.md` | Early (v0.3) button overview — partly outdated |

## Working style
- Adolfo is a construction professional, not a software developer: explain changes in plain terms, and
  say what to click/check in Revit when a manual test is needed.
- Use git commits for backups, never `*.bak` copies.
- Delivery workarounds in older docs (staging through `Revit_temp/`, md5 checks after commit) were for the
  cloud bridge; editing files directly here doesn't need them.
- Before any `execute_revit_code`, check which document is active (`doc.PathName`) — Revit may have the live
  Autodesk Docs Kalae model open (happened 2026-10-05). Anything but the TEST model or a Reference Projects copy: stop and ask.
