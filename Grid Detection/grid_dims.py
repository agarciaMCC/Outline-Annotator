"""Step 2: make called-out grid dimensions govern spacing.
usage: python grid_dims.py sheet.pdf grids.json out.json"""
import pymupdf, json, math, re, sys, collections
PDF,INJ,OUTJ=sys.argv[1:4]
S=72*3/32; TOL_FT=3/12          # dimension must be within 3" of measured gap
J=json.load(open(INJ)); ox,oy=J['origin_ft']; p=pymupdf.open(PDF)[0]; M=p.rotation_matrix
def val(t):
    m=re.fullmatch(r"(\d+)' ?- ?(\d+)(?:\s?(\d+)/(\d+))?\"",t)
    if not m: return None
    ft,i,n,d=m.groups(); return int(ft)+(int(i)+(int(n)/int(d) if n else 0))/12
dims=[]
for b in p.get_text('dict')['blocks']:
    for l in b.get('lines',[]):
        t=''.join(s['text'] for s in l['spans']).strip(); v=val(t)
        if v is None: continue
        r=pymupdf.Rect(l['bbox']); c=pymupdf.Point((r.x0+r.x1)/2,(r.y0+r.y1)/2)*M
        dx,dy=l['dir']; q=pymupdf.Point(dx,dy)*M - pymupdf.Point(0,0)*M
        dims.append(dict(text=t,v=v,x=c.x/S-ox,y=-c.y/S-oy,ux=q.x,uy=-q.y))
fi=lambda f:(lambda ft,i:f"{ft}'-{i:g}\"")(int(f+1e-9),round((f-int(f+1e-9))*12,3))
G=J['grids']; fams=collections.defaultdict(list)
for g in G:
    if '#' in g['label']: g['flags'].append('excluded: duplicate label'); continue
    fams[round(g['angle']/2.5)*2.5%180].append(g)
report=[]
for k,gs in fams.items():
    ang=sorted(g['angle'] for g in gs)[len(gs)//2]
    ang_s=round(ang) if abs(ang-round(ang))<0.05 else round(ang,2)
    th=math.radians(ang_s); nx,ny=-math.sin(th),math.cos(th); tx,ty=math.cos(th),math.sin(th)
    for g in gs: g['off']=g['start'][0]*nx+g['start'][1]*ny
    gs.sort(key=lambda g:g['off'])
    gaps=[]
    for a,b in zip(gs,gs[1:]):
        m=b['off']-a['off']; best=None
        for d in dims:
            along=abs(d['ux']*nx+d['uy']*ny)          # text runs across the grids
            o=d['x']*nx+d['y']*ny
            if along>0.95 and a['off']<o<b['off'] and abs(d['v']-m)<TOL_FT:
                if not best or abs(d['v']-m)<abs(best['v']-m): best=d
        gaps.append((a,b,m,best))
    # chain called-out values; anchor = grid through origin if present, else least-squares fit
    cum=[0.0]
    for a,b,m,d in gaps: cum.append(cum[-1]+(d['v'] if d else m))
    anch=[i for i,g in enumerate(gs) if abs(g['off'])<0.01]
    p0 = -cum[anch[0]] if anch else sum(g['off']-c for g,c in zip(gs,cum))/len(gs)
    for g,c in zip(gs,cum):
        new=p0+c; sh=new-g['off']
        for key in ('start','end'):
            x,y=g[key]; along=x*tx+y*ty; g[key]=[round(along*tx+new*nx,4),round(along*ty+new*ny,4)]
        g['angle']=ang_s; g['moved_in']=round(sh*12,2)
        if abs(sh)>1/12: g['flags'].append(f'moved {sh*12:+.2f}" to match dimensions')
    for a,b,m,d in gaps:
        report.append(dict(family=ang_s,pair=f"{a['label']}–{b['label']}",measured=fi(m),called_out=d['text'] if d else '',
                           used=d['text'] if d else fi(round(m*96)/96),status='dimension' if d else 'NO DIMENSION – measured value used'))
        if not d: a['flags'].append(f"no dimension to {b['label']} – spacing unverified")
    for g in gs: g.pop('off',None)
J['governed']=True; J['spacing']=report
json.dump(J,open(OUTJ,'w'),indent=1)
nd=sum(1 for r in report if r['called_out']); print(f"{nd}/{len(report)} gaps set by dimension")
for r in report:
    if not r['called_out']: print('  no dim:',r['family'],r['pair'],r['measured'])
