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
- `Test Library/` — PDF regression cases for Columns/Grids from PDF: `python run_library.py`.
- `MCC-DimText.extension/` — stripped-down Dim Text build shared with coworkers; keep in sync when Dim Text changes.
- `RevitMCP.extension/` — third-party Revit MCP server, locally patched (see `docs/revit-mcp-setup.md`). Don't edit casually.
- `Revit_temp/`, `_to_delete/`, `*.bak` — old staging copies and retired buttons. Ignore unless asked.
- `*.rvt`, `*_backup/`, PDFs, the pyRevit installer — **never modify**. Never save over the R23 model.

## Testing in Revit (Revit MCP)
- The `revit` MCP server talks to Revit 2026 on **`1268 - Kalae (R26 TEST).rvt` only**.
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
- "Large Scale" detail items = CJ lines (dimension them); plain detail lines = QC points (ignore).
- Grids from PDF: called-out dimensions govern spacing; when sheets disagree, the user picks (no default).

## Doc index (`docs/`)
| Doc | What's in it |
|---|---|
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
| `project-readme.md` | Early (v0.3) button overview — partly outdated |

## Working style
- Adolfo is a construction professional, not a software developer: explain changes in plain terms, and
  say what to click/check in Revit when a manual test is needed.
- Prefer git commits over `*_before_x.py.bak` copies for backups.
- Delivery workarounds in older docs (staging through `Revit_temp/`, md5 checks after commit) were for the
  cloud bridge; editing files directly here doesn't need them.
