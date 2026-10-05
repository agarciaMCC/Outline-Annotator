import json,math,csv,sys
S=json.load(open('gov_struct.json'));A=json.load(open('gov_arch.json'))
sg={g['label']:g for g in S['grids'] if '#' not in g['label']};ag={g['label']:g for g in A['grids'] if '#' not in g['label']}
ss={r['pair']:r for r in S['spacing']};asp={r['pair']:r for r in A['spacing']}
rows=[]
for k in sorted(set(ss)|set(asp)):
    s,a=ss.get(k),asp.get(k)
    sv=s['used'] if s else '—';av=a['used'] if a else '—'
    if s and a and s['called_out'] and a['called_out']: st='match' if s['called_out']==a['called_out'] else 'DISAGREE – pick one'
    elif s and a: st='one sheet has no dimension'
    else: st='gap only on '+('structural' if s else 'arch')
    rows.append(['spacing',k,sv,av,st])
for k in sorted(set(sg)|set(ag)):
    if k in sg and k in ag:
        s,a=sg[k],ag[k];th=math.radians(s['angle']);nx,ny=-math.sin(th),math.cos(th)
        d=((a['start'][0]-s['start'][0])*nx+(a['start'][1]-s['start'][1])*ny)*12
        st=('match' if abs(d)<1/16 else f'match within 1/4" ({d:+.2f}")') if abs(d)<0.25 and s['angle']==a['angle'] else f'DISAGREE – {d:+.2f}" / angle {s["angle"]} vs {a["angle"]} – pick one'
        rows.append(['position',k,f"{s['angle']}°",f"{a['angle']}°",st])
    else: rows.append(['position',k,'yes' if k in sg else '—','yes' if k in ag else '—','grid only on '+('structural' if k in sg else 'arch')])
for r in rows:
    if r[4]!='match': print(r)
print(sum(r[4]=='match' for r in rows),'/',len(rows),'match')
with open('/mnt/user-data/outputs/Grid Detection/Arch vs Struct grid comparison.csv','w',newline='') as f:
    w=csv.writer(f);w.writerow(['Check','Grid / Gap','Structural','Architectural','Result']);w.writerows(rows)
