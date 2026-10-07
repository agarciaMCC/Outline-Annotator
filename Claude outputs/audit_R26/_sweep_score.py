import json, glob, subprocess, sys, os
tag, hand = sys.argv[1], sys.argv[2]
rows = []
for f in sorted(glob.glob('dry_%s_*.json' % tag)):
    name = f[len('dry_%s_' % tag):-5]
    out = 'compare_dry_%s_%s.json' % (tag, name)
    subprocess.run([sys.executable, 'compare_segments.py', f, hand, out], capture_output=True)
    c = json.load(open(out, encoding='utf-8'))['counts']
    m = json.load(open(f, encoding='utf-8'))['meta']
    rows.append((c.get('left', 0), name, c, m['count'], m['review']))
for r in sorted(rows, reverse=True):
    print('%-12s left %3d moved %3d extra %2d missing %2d | placed %d review %d' % (r[1], r[0], r[2].get('moved', 0), r[2].get('deleted', 0), r[2].get('added', 0), r[3], r[4]))
