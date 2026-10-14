# Agents and workflow

These agents support the Dim Soffit v2 iteration loop. Each is read-only and runs as a
subagent — none edits code, runs Revit, or changes docs on its own.

## Agent roster

| Agent | Model | When to use | What it does |
|---|---|---|---|
| `analyst` | opus | After Adolfo edits a test view | Groups his changes by rule, cross-checks "tried and reverted", proposes the next code changes |
| `compat` | sonnet | Before a Revit test run (big changes) | Checks IronPython 2.7, Revit 2023+2026 compat, transactions, conventions |
| `scorer` | haiku | After a run, before deciding to keep or revert | Reads scores across all test views, flags regressions |
| `scout` | sonnet | Before the first edit round on a new view | Characterizes the view's geometry, predicts where the tool will struggle |
| `docs-check` | haiku | Periodically, or before a handoff | Flags stale run numbers, contradictions, out-of-sync MCC-Testing copies |

**Model rationale:** opus for deep reasoning (analyst interprets edit intent and cross-references
rule history); sonnet for systematic checks with well-defined rules (compat, scout); haiku for
mechanical comparison (scorer reads numbers, docs-check compares files).

## The iteration loop

```
┌─────────────────────────────────────────────────────────────────┐
│  NEW VIEW                                                       │
│  1. Run the tool on the view (run_v2.py)                        │
│  2. scout → geometry profile, predicted issues                  │
│  3. Send Adolfo the PNG + study summary for his first edit round│
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  EDIT ROUND                                                     │
│  4. Snapshot before edits (snapshot_dims.py)                     │
│  5. Adolfo edits                                                │
│  6. Snapshot after edits                                         │
│  7. Compare (compare_snapshots.py + compare_segments.py)         │
│  8. analyst → grouped findings + proposed changes                │
│  9. Ask Adolfo questions (numbered options + pictures)            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  BUILD + VERIFY                                                 │
│  10. Build the clear fixes in code                               │
│  11. compat → catch IronPython / API issues                      │
│  12. dry_run.py or _sweep_score.py → test variants without       │
│      touching views                                              │
│  13. Real run (run_v2.py) on the test view                       │
│  14. scorer → compare all views vs baselines                     │
│      • regressed anywhere? → investigate, possibly revert        │
│      • safe? → commit, update docs                               │
│  15. docs-check → flag anything now stale                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                     Next edit round or next view
```

## How to call them

Each agent is called with `Agent(subagent_type="<name>")`. Point them at the right files
in the prompt — they find the rest themselves.

Examples:

```
# After Adolfo's edits
Agent(subagent_type="analyst", prompt="Analyse L3 North round 5.
  Compare: compare_L3N_round5.json, compare_segments_L3N_round5.json.
  Snapshots: snapshot_L3N_before_edits5.json, snapshot_L3N_after_edits5.json.
  Run report: dimsoffit_v2_L3N_run111.md.")

# After building fixes and running
Agent(subagent_type="scorer", prompt="Check scores after run 114 on L3 North.
  Also check L7, L4.5N, L4S haven't regressed.")

# Before a big commit
Agent(subagent_type="compat", prompt="Review the latest diff.")
Agent(subagent_type="docs-check", prompt="Check docs are current.")

# New test view
Agent(subagent_type="scout", prompt="Study L4 South run 3.
  Run report: dimsoffit_v2_L4S_run3.md.")
```

## Rules that apply to all agents

- Read-only — they never edit code, docs, or the Revit model.
- Plain English — Adolfo is a detailer, not a programmer.
- The design doc (`docs/dim-soffit-v2-design.md`) is the authoritative record of decisions.
- A score drop means "revert until investigated" — no agent overrides this.
