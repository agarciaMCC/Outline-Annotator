# score L4S dry variants against his round-1 edit
python _sweep_score.py L4S snapshot_L4S_after_edits1.json | grep -E "^($1)"
