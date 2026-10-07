# Dim Soffit v2 — session handoff (written 2026-10-07)

Read this first, then the dated status entries in `dim-soffit-v2-design.md` (2026-10-06 and 2026-10-07 are the
long ones). The design doc is the authoritative log of every rule and every decision Adolfo gave; this page is
the "how we work" and "where things stand" summary.

## Where things stand
- **L3 North** (`ZZ CLAUDE TEST - L3 NORTH (auto-dim)`, 1:128): five edit rounds by Adolfo. Latest run **98** (same score as 95; the view holds 98)
  (`Claude outputs/audit_R26/dimsoffit_v2_L3N_run95.md`): 135 strings / 115 placed / 5 review / 0 overlaps.
  Against his round-5 version (`snapshot_L3N_after_edits5.json`): 123 segments on his line / 34 off / 0 extra /
  2 missing (the 5 review items are intentional — he left them out). The analyst's verdict after round 5: **what
  is left on L3N is placement taste, not rules; another round adds little.** Round-by-round "untouched" counts:
  55 → 70 → 78 → 70 → 86 of ~117 dims.
- **L7** (`ZZ CLAUDE TEST - L7 (auto-dim)`, 1:96, orthogonal): two edit rounds. Round 2 (on run 31): 72 unchanged /
  59 edited / 6 deleted / 4 added (round 1: 42 untouched); analyst `analyst_L7_round2.md`; answers in the design doc
  (2026-10-07). Latest run **40**: 127 placed / 0 review / 0 overlaps; vs his round-2 version
  (`snapshot_L7_after_edits2.json`) **140 / 52 / 1 / 4** (run 32 before the changes: 129 / 61 / 5 / 3). The 39 ft edge
  above AA and the `5'-1"` edges off 7 are dimensioned now. What's left is mostly placement within 1".
- **L4.5 North** (`ZZ CLAUDE TEST - L4.5 NORTH (auto-dim)`, 1:128, rotated wing, centre of the footprint is OPEN
  at this level): latest run **5**: 101 / 91 placed / 8 review / 0 overlaps (run 1: 87 / 71 / 15). Adolfo's answers to
  the L4.5 study (`analyst_L45N_study.md`) changed no rule. The 2026-10-07 review pass fixed two model readings
  (partly filled slab hole; walls standing on the slab) - see the design doc. The 8 review items left are crop-edge /
  congestion cases, no rule. Still missing vs the hand sheet: 20 slab edge -> grid dims (worth a look), the rest is
  columns / repeats / wall faces he ruled out.
- Hand-sheet baselines: `snapshot_L3N_after_edits5.json` (use this, not the issued sheet), `snapshot_L7_after_edits1.json`,
  `snapshot_L45N_hand.json` (parent view's dims inside the north crop; the issued L4.5 sheet, with Adolfo's
  one-offs), `snapshot_L7_hand.json` (issued L7 sheet — NOT a good yardstick: grid overalls, perimeter chain).

## The routine (what worked)
1. **Before he edits:** snapshot the test view (`snapshot_dims.py`, `TAG_LAYOUT=True`) → `snapshot_<tag>_before_editsN.json`;
   commit. **Never run the tool on a view he is editing**; nothing clears a test view until he says "done".
2. **After:** snapshot `_after_editsN`; `compare_snapshots.py` (id-based, needs Revit) + `compare_segments.py`
   (CPython, by value + position, tolerant of a different reference); commit.
3. **Analyst:** `Agent(subagent_type="edit-diff-analyst")` with both compare files, the snapshots, the run report and the
   design doc. It groups the edits by cause and proposes changes; keep its questions for Adolfo few and send
   pictures (`crop_png.py` on the run's exported PNG — mapping notes below).
4. **Build the clear fixes, run, snapshot, score** with `agree_with_edits.py <run.json> <his.json>` (by segment).
   **Keep a change only if the score against his latest version does not drop**; several "obvious" fixes scored
   worse and were reverted (listed in the design doc: 3/16" first row, clamp on home-less rows, seam CJs, junction
   end, tight first rows, W_SPLIT 5). Record tried-and-reverted things in the doc so they aren't retried.
5. Ask Adolfo with pictures; his answers go into the design doc as dated decisions. He answers in one line each
   ("1c", "2b", "disregard my edit", "correct rule") — give him numbered options.
6. **`revit-compat-reviewer`** agent for IronPython 2.7 / Revit 2023+2026 checks before a run when the change is big.

## Running
- Headless: `execute_revit_code` with `RUN=n` (+ `VIEW_NAME`, `TAG` for L7 / L45N) and `execfile(run_v2.py)`. It
  clears the view's dims, runs the button, writes `dimsoffit_v2_<TAG>_runN.md` + a PNG. **It refuses a run number
  whose report already exists** (guard added after a parallel session wiped the view) — always use a new number.
  Latest numbers: L3N 98, L7 31, L45N 5.
- Always `assert "R26 TEST" in doc.PathName` first. ~20–45 s per run; the MCP call can time out at 60 s while
  the run completes — read the report file.
- Image crops: the FitToPage export covers the model crop plus grid bubbles; derive px/ft from two grid bubbles
  (L7 run 28: 53.6 px/ft, grid 5 at x 944 px; L3N runs 76+: ~22.3 px/ft from the model crop bbox). The annotation
  crop is now computed from the model crop + the view's four annotation offsets (`mcc_coverage.annotation_crop_poly`)
  because Revit returned nonsense after the offsets were changed. The button widens the annotation crop by the
  overshoot of dims placed up to `CROP_OUT` 4 ft past it (plan views only).

## Hazards
- **A parallel Claude session** worked on this repo on 2026-10-06 (R.O. suffix, Training Library). It ran the L3N
  test view while Adolfo was starting an edit round. Check `git status` / recent commits for another session's
  uncommitted work before committing shared modules; coordinate on the test views.
- `mcc_strings.py` / `mcc_layout.py` are large and shared; keep edits surgical and run after each.
- New CFG keys: check the name isn't already in the dict (`W_GAP` was silently overwritten once, 2026-10-07).
- Per-string span is a search window for home-side strings, not the element — use `_extent(feature, gi)` for
  anything geometric (this bit us twice).

## Open items (in rough priority)
1. L7 leftovers: core/shaft far-side choices (shaft#51's bump chain done 2026-10-07); a third L7 round only if
   Adolfo wants one (round 2 was mostly him restoring round-1 positions, now built).
2. L4.5: the 20 slab edge -> grid dims the hand sheet has and the tool doesn't (void + perimeter edges).
3. The CJ pair off grid 5 (he puts both at the bottom end; the tool at the top — "more open space" is his reason).
4. The pocket rows (B2, five rounds); beam widths `anchor | sides` at framed ends (~0.4" from his, every round).
5. Milestone 3 proper: whole views on L2/L4, a cleanup count per sheet (target ≤ 10; L3N round 5 was 31 edits).
6. Rules recorded but not built: a beam meeting a wall at a skew gets a check dim off the wall face (L4.5 answer 6).
7. Share with coworkers: `MCC-Testing.extension` carries Dim Soffit v2 — re-copy `lib/` and rebuild the zip after
   today's changes (see CLAUDE.md folder map).
