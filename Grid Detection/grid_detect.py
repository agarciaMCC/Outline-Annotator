"""Detect grid lines + bubble labels from a vector PDF plan sheet -> grids.json (feet, Revit XY)."""
import pymupdf, math, json, sys, collections
PDF = sys.argv[1] if len(sys.argv)>1 else 'g.pdf'
SCALE_PT_PER_FT = 72*3/32          # 3/32" = 1'-0"
GAP = 250                          # max gap (pt) between dashes along one grid
d=pymupdf.open(PDF);p=d[0];M=p.rotation_matrix
dr=p.get_drawings();words=p.get_text('words')
# 1. bubbles = circles of the most common diameter with short text inside
circles=[]
for x in dr:
    it=x['items'];r=x['rect']
    if it and all(i[0]=='c' for i in it) and len(it)>=4 and abs(r.width-r.height)<0.5 and r.width>10:
        circles.append(r)
diam=collections.Counter(round(r.width) for r in circles).most_common(1)[0][0]
bub=[]
for r in circles:
    if abs(r.width-diam)>1: continue
    c=((r.x0+r.x1)/2,(r.y0+r.y1)/2);R=r.width/2
    t=' '.join(w[4] for w in words if math.hypot((w[0]+w[2])/2-c[0],(w[1]+w[3])/2-c[1])<R*0.8)
    if t and len(t)<=5: bub.append({'c':c,'t':t,'R':R})
segs=[]
for x in dr:
    for i in x['items']:
        if i[0]=='l':
            a,b=i[1],i[2];L=math.hypot(b.x-a.x,b.y-a.y)
            if L>0.5: segs.append((a.x,a.y,b.x,b.y,L))
def unit(s): return (s[2]-s[0])/s[4],(s[3]-s[1])/s[4]
def perp(px,py,cx,cy,ux,uy): return abs((px-cx)*uy-(py-cy)*ux)
def collect(cx,cy,ux,uy,tolang,told):
    pts=[]
    for q in segs:
        qx,qy=unit(q)
        if abs(qx*uy-qy*ux)<tolang and perp(q[0],q[1],cx,cy,ux,uy)<told and perp(q[2],q[3],cx,cy,ux,uy)<told:
            pts+=[(q[0],q[1]),(q[2],q[3])]
    return pts
def touching(pt,exclude):
    for q in segs:
        if q is exclude: continue
        for a,b in (((q[0],q[1]),(q[2],q[3])),((q[2],q[3]),(q[0],q[1]))):
            if math.dist(a,pt)<1.0: yield q,a,b
out=[]
for B in bub:
    cx,cy=B['c'];R=B['R'];best=None
    for s in segs:
        for e,o in ((((s[0],s[1])),(s[2],s[3])),((s[2],s[3]),(s[0],s[1]))):
            de=math.dist(e,(cx,cy));do=math.dist(o,(cx,cy))
            ux,uy=unit(s)
            if abs(de-R)<3 and do>de and perp(cx,cy,s[0],s[1],ux,uy)<1.5:
                if (o[0]-e[0])*ux+(o[1]-e[1])*uy<0: ux,uy=-ux,-uy
                # anchor point & direction; follow an elbow leader if present
                ax,ay,elbow=cx,cy,False
                if s[4]<60:
                    for q,a,b in touching(o,s):
                        qx,qy=unit(q)
                        if abs(qx*uy-qy*ux)>0.2:          # jog segment
                            for q2,a2,b2 in touching(b,q):
                                vx,vy=unit(q2)
                                if abs(vx*uy-vy*ux)<0.01:  # parallel again -> real grid
                                    ax,ay,elbow=a2[0],a2[1],True
                n=len(collect(ax,ay,ux,uy,0.01,2.5))
                if not best or n>best[0]: best=(n,ux,uy,ax,ay,elbow)
    if not best: out.append(dict(label=B['t'],ok=False));continue
    n,ux,uy,ax,ay,elbow=best
    for tol in ((0.01,2.5),(0.003,1.0)):
        pts=[q for q in collect(ax,ay,ux,uy,*tol) if (q[0]-ax)*ux+(q[1]-ay)*uy>-1]
        if len(pts)>=4:
            ts=sorted(((q[0]-ax)*ux+(q[1]-ay)*uy,q) for q in pts)
            end=ts[0]
            for t in ts:
                if t[0]-end[0]>GAP: break
                end=t
            far=end[1];L=math.dist(far,(ax,ay))
            if L>50: ux,uy=(far[0]-ax)/L,(far[1]-ay)/L
    ts=sorted((q[0]-ax)*ux+(q[1]-ay)*uy for q in pts)
    end=ts[0] if ts else 0
    for t in ts:
        if t-end>GAP: break
        end=max(end,t)
    start=R if not elbow else 0
    out.append(dict(label=B['t'],ok=True,a=(ax+ux*start,ay+uy*start),b=(ax+ux*end,ay+uy*end),elbow=elbow,nseg=len(pts)//2))
def ft(x,y):
    q=pymupdf.Point(x,y)*M; return (q.x/SCALE_PT_PER_FT,-q.y/SCALE_PT_PER_FT)
lines=collections.defaultdict(list)
for g in out:
    if g['ok']: lines[g['label']].append(g)
final=[]
for lab,gs in lines.items():
    A=[(ft(*g['a']),ft(*g['b']),g) for g in gs]
    def colin(l1,l2):
        (x1,y1),(x2,y2)=l1[0],l1[1];L=math.dist(l1[0],l1[1])
        return all(abs((x2-x1)*(y1-py)-(x1-px)*(y2-y1))/L<0.5 for px,py in l2[:2])
    if len(A)>1 and all(colin(A[0],l) for l in A[1:]):
        pts=[p for l in A for p in l[:2]];pa,pb=max(((p,q) for p in pts for q in pts),key=lambda z:math.dist(*z))
        A=[(pa,pb,dict(elbow=any(l[2]['elbow'] for l in A),nseg=sum(l[2]['nseg'] for l in A)))]
    for k,(pa,pb,g) in enumerate(A):
        final.append(dict(label=lab if k==0 else f"{lab} #{k+1}",start=pa,end=pb,elbow=g['elbow'],nseg=g['nseg'],flags=[]))
for f in final:
    dx,dy=f['end'][0]-f['start'][0],f['end'][1]-f['start'][1];f['angle']=math.degrees(math.atan2(dy,dx))%180
    if f['angle']>179.5: f['angle']-=180
# angle families: snap within 0.5 deg of the family median, flag outliers
fams=collections.defaultdict(list)
for f in final: fams[round(f['angle']/2.5)*2.5%180].append(f)
for k,fs in fams.items():
    med=sorted(f['angle'] for f in fs)[len(fs)//2]
    for f in fs:
        dev=abs(f['angle']-med)
        if dev>0.05:
            if dev>0.5: f['flags'].append(f'angle off family by {dev:.2f} deg')
            else:
                f['flags'].append(f'angle snapped {f["angle"]:.2f}->{med:.2f}')
                L=math.dist(f['start'],f['end']);th=math.radians(med)
                sx,sy=f['start'];s=1 if (f['end'][0]-sx)*math.cos(th)+(f['end'][1]-sy)*math.sin(th)>0 else -1
                f['end']=(sx+s*L*math.cos(th),sy+s*L*math.sin(th));f['angle']=med
    if len(fs)==1: f['flags'].append('only grid at this angle')
for f in final:
    if f['elbow']: f['flags'].append('bubble on elbow leader (placed at grid, not bubble)')
    if '#' in f['label']: f['flags'].append('duplicate label, not collinear with the other')
def inter(g1,g2):
    (x1,y1),(x2,y2)=g1['start'],g1['end'];(x3,y3),(x4,y4)=g2['start'],g2['end']
    D=(x1-x2)*(y3-y4)-(y1-y2)*(x3-x4);t=((x1-x3)*(y3-y4)-(y1-y3)*(x3-x4))/D
    return x1+t*(x2-x1),y1+t*(y2-y1)
G={f['label']:f for f in final};ox,oy=inter(G['1'],G['AA'])
for f in final:
    f['start']=[round(f['start'][0]-ox,4),round(f['start'][1]-oy,4)];f['end']=[round(f['end'][0]-ox,4),round(f['end'][1]-oy,4)]
    f['angle']=round(f['angle'],3)
json.dump(dict(source=PDF,scale='3/32"=1\'-0"',origin='Grid 1 / AA = (0,0)',origin_ft=[ox,oy],grids=sorted(final,key=lambda f:f['label'])),open('grids.json','w'),indent=1)
print(len(bub),'bubbles ->',len(final),'grids; no line:',[g['label'] for g in out if not g['ok']])
for f in final:
    if f['flags']: print(' ',f['label'],'|','; '.join(f['flags']))
