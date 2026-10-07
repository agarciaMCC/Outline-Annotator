import json,sys,subprocess
run=sys.argv[1]; hand=sys.argv[2]; out='compare_%s.json'%sys.argv[3]
subprocess.run([sys.executable,'compare_segments.py',run,hand,out],capture_output=True)
c=json.load(open(out,encoding='utf-8')); print(c['counts'])
for r in c['rows']:
    if not str(r['change']).startswith(('left','moved')):
        print(' ',r['change'], r.get('label'), round(r['value_ft'],2), r['at'], r.get('chain'))
