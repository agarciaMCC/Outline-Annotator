# -*- coding: utf-8 -*-
"""Dim Soffit v2, stage 1 - FEATURES.

Groups the raw edges of a PlanModel into the things a detailer would name
and dimension as a unit (design: claude/dim-soffit-v2-design.md):

  run        a straight perimeter slab edge between two turns
  bump       perimeter chain out-and-back (pilaster): leg | top | leg
  notch      same, going into the slab
  step       one short perpendicular leg between two parallel runs (jog)
  corner     two runs meeting
  opening    kind: core / shaft / penetration / void / plain
  beam       sides + free ends (ends framed into a member are 'located')
  cj         construction-joint line

Every slab edge (>= MIN_EDGE, with a reference) belongs to exactly one
feature. Nothing here touches the document."""
import math
import mcc_plan as P

MIN_EDGE = 0.5          # ft; shorter edges are stubs (ignored, counted)
BUMP_MAX_TOP = 8.0      # ft; a bump/notch top no longer than this
BUMP_MAX_LEG = 6.0      # ft; bump/notch legs (= v1 JOG_MAX)
STEP_MAX = 6.0          # ft; a step leg no longer than this
PENETRATION = 2.0       # ft; openings this small
VOID = 20.0             # ft; openings this big (or stepped)
CORE_REACH = 25.0       # ft; a core opening has a wall facing every side within this
TOL = 1.0 / 48          # ft; same-offset tolerance (1/4")


class Feature(object):
    __slots__ = ("kind", "sub", "edges", "owners", "refs", "fams", "extent",
                 "in_crop", "members", "loop_id", "index", "meta")

    def __init__(self, kind, edges, owners=(), sub=None):
        self.kind = kind            # run / bump / notch / step / corner /
                                    # opening / beam / cj
        self.sub = sub              # opening kind, step direction, ...
        self.edges = list(edges)    # Face / CJLine objects, in order
        self.owners = set(owners)
        self.refs = []
        self.fams = {}              # family index -> [edges parallel to it]
        self.extent = None          # (xmin, ymin, xmax, ymax)
        self.in_crop = True
        self.members = []           # members (walls/columns) touching it
        self.loop_id = None
        self.index = None
        self.meta = {}

    def mid(self):
        xs = [p[0] for e in self.edges for p in (e.p0, e.p1)]
        ys = [p[1] for e in self.edges for p in (e.p0, e.p1)]
        return (sum(xs) / len(xs), sum(ys) / len(ys)) if xs else (0.0, 0.0)

    def label(self):
        n = self.kind if self.sub is None else "%s/%s" % (self.kind, self.sub)
        return "%s#%d" % (n, self.index if self.index is not None else -1)


def _same(a, b, tol=1e-6):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def _chains(edges):
    """Split a loop's edge list into connected chains (gaps where curved /
    reference-less edges were dropped)."""
    chains, cur = [], []
    for e in edges:
        if cur and not _same(cur[-1].p1, e.p0, 1e-4):
            chains.append(cur); cur = []
        cur.append(e)
    if cur:
        chains.append(cur)
    if len(chains) > 1 and _same(chains[-1][-1].p1, chains[0][0].p0, 1e-4):
        chains[0] = chains.pop() + chains[0]     # loop wraps
    return chains


def _offset_from(e, ref_edge):
    """Signed distance of edge e (its midpoint) from ref_edge's line, along
    ref_edge's left normal."""
    n = (-ref_edge.d[1], ref_edge.d[0])
    m = e.mid()
    return (m[0] - ref_edge.p0[0]) * n[0] + (m[1] - ref_edge.p0[1]) * n[1]


def _left_normal(e):
    return (-e.d[1], e.d[0])


def _signed_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return a / 2.0


class FeatureSet(object):
    def __init__(self, model, crop=None):
        self.m = model
        self.crop = crop            # plan polygon or None
        self.features = []
        self.stubs = 0
        self.unassigned = []
        self._build()

    # ---------------- helpers ----------------
    def _inside(self, pt):
        return self.crop is None or P.point_in_poly(pt[0], pt[1], self.crop)

    def _add(self, f, loop_id=None):
        f.index = len(self.features)
        f.loop_id = loop_id
        for e in f.edges:
            fi = self.m.family_parallel(e.d)
            f.fams.setdefault(fi, []).append(e)
            r = getattr(e, "ref", None)
            if r is not None:
                f.refs.append(r)
        xs = [p[0] for e in f.edges for p in (e.p0, e.p1)]
        ys = [p[1] for e in f.edges for p in (e.p0, e.p1)]
        if xs:
            f.extent = (min(xs), min(ys), max(xs), max(ys))
        f.in_crop = self._inside(f.mid())
        self.features.append(f)
        return f

    # ---------------- perimeter ----------------
    def _perimeter(self, slab, loop_id):
        edges = [e for e in slab.edges if e.length >= MIN_EDGE]
        self.stubs += len(slab.edges) - len(edges)
        poly = slab.outer
        inward_sign = 1.0 if _signed_area(poly) > 0 else -1.0  # CCW: left = inside
        for chain in _chains(edges):
            n = len(chain)
            used = [False] * n
            closed = n > 2 and _same(chain[-1].p1, chain[0].p0, 1e-4)
            idx = lambda k: k % n if closed else k
            valid = lambda k: closed or 0 <= k < n
            # 1) bumps / notches: a | b | c with a ⟂ b, c ⟂ b, a anti-parallel c
            for i in range(n):
                if used[i] or not valid(i + 2):
                    continue
                a, b, c = chain[idx(i)], chain[idx(i + 1)], chain[idx(i + 2)]
                if used[idx(i + 1)] or used[idx(i + 2)]:
                    continue
                if not (P.perpendicular(a.d, b.d, 0.05) and P.perpendicular(c.d, b.d, 0.05)):
                    continue
                if a.d[0] * c.d[0] + a.d[1] * c.d[1] > -0.99:   # must come back
                    continue
                if a.length > BUMP_MAX_LEG or c.length > BUMP_MAX_LEG or b.length > BUMP_MAX_TOP:
                    continue
                # the neighbours before a and after c must be parallel to b
                prev_, next_ = (chain[idx(i - 1)] if valid(i - 1) else None,
                                chain[idx(i + 3)] if valid(i + 3) else None)
                if prev_ is None or next_ is None:
                    continue
                if not (P.parallel(prev_.d, b.d) and P.parallel(next_.d, b.d)):
                    continue
                # outward (bump) or inward (notch)? leg a turns left = inside
                cross = a.d[0] * b.d[1] - a.d[1] * b.d[0]
                # from prev_ to a: turning toward inside means notch
                turn = prev_.d[0] * a.d[1] - prev_.d[1] * a.d[0]
                kind = "notch" if turn * inward_sign > 0 else "bump"
                f = Feature(kind, [a, b, c], owners=(slab.eid,))
                f.meta = {"legs": (a.length, c.length), "top": b.length,
                          "run_before": prev_, "run_after": next_}
                self._add(f, loop_id)
                for k in (i, i + 1, i + 2):
                    used[idx(k)] = True
            # 2) steps: one short leg between two parallel edges
            for i in range(n):
                if used[i] or not valid(i - 1) or not valid(i + 1):
                    continue
                a, s, b = chain[idx(i - 1)], chain[i], chain[idx(i + 1)]
                if used[idx(i - 1)] or used[idx(i + 1)]:
                    continue
                if s.length > STEP_MAX:
                    continue
                if not (P.perpendicular(s.d, a.d, 0.05) and P.parallel(a.d, b.d)):
                    continue
                if a.d[0] * b.d[0] + a.d[1] * b.d[1] < 0.99:      # same way on
                    continue
                f = Feature("step", [s], owners=(slab.eid,))
                f.meta = {"run_before": a, "run_after": b, "height": s.length}
                self._add(f, loop_id)
                used[i] = True
            # 3) runs: everything left
            for i in range(n):
                if used[i]:
                    continue
                f = Feature("run", [chain[i]], owners=(slab.eid,))
                f.meta = {"prev": chain[idx(i - 1)] if valid(i - 1) else None,
                          "next": chain[idx(i + 1)] if valid(i + 1) else None}
                self._add(f, loop_id)
                used[i] = True
            # 4) corners: consecutive non-parallel edges that are both runs
            runs = dict((id(f.edges[0]), f) for f in self.features
                        if f.kind == "run" and f.loop_id == loop_id)
            for i in range(n):
                if not valid(i + 1):
                    continue
                a, b = chain[i], chain[idx(i + 1)]
                if P.parallel(a.d, b.d):
                    continue
                fa, fb = runs.get(id(a)), runs.get(id(b))
                if fa is None or fb is None:
                    continue
                f = Feature("corner", [a, b], owners=(slab.eid,))
                f.meta = {"runs": (fa, fb), "point": a.p1}
                self._add(f, loop_id)

    # ---------------- openings ----------------
    def _opening_kind(self, loop, poly, cx, cy):
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if max(w, h) <= PENETRATION:
            kind = "penetration"
        else:
            # distinct offsets per family (stepped?)
            stepped = False
            for fi in range(len(self.m.families)):
                par = [e for e in loop if self.m.family_parallel(e.d) == fi]
                if len(par) < 2:
                    continue
                gi = self.m.families[fi][0]
                offs = sorted(set(round(self.m.offset(e.mid(), gi) * 96) for e in par))
                if len(offs) > 2:
                    stepped = True
            # stepped small openings (the 3'x3'-8" pilaster hole) still get
            # one string per direction with every step in it; only big
            # ones are dimensioned edge by edge
            kind = "void" if max(w, h) > VOID else "plain"
            self._last_stepped = stepped
        # core: every straight face has a facing parallel wall face nearby
        if kind in ("plain", "penetration"):
            faced = 0; total = 0
            for e in loop:
                if e.length < MIN_EDGE:
                    continue
                total += 1
                # outward = away from the opening's centroid
                n = _left_normal(e)
                m_ = e.mid()
                if (cx - m_[0]) * n[0] + (cy - m_[1]) * n[1] > 0:
                    n = (-n[0], -n[1])
                hit = False
                for w_ in self.m.walls:
                    for wf in w_.sides:
                        if not P.parallel(wf.d, e.d):
                            continue
                        gap = _offset_from(wf, e)
                        # must lie on the outward side, within reach
                        if gap * (n[0] * _left_normal(e)[0] + n[1] * _left_normal(e)[1]) < -TOL or abs(gap) > CORE_REACH:
                            continue
                        # overlap along the edge - against the whole wall
                        # outline (side faces come back chopped at joins)
                        t = e.d
                        a0, a1 = sorted([t[0]*e.p0[0]+t[1]*e.p0[1], t[0]*e.p1[0]+t[1]*e.p1[1]])
                        pr = [t[0]*q[0]+t[1]*q[1] for q in (w_.poly or [wf.p0, wf.p1])]
                        b0, b1 = min(pr), max(pr)
                        if a0 < b1 - 0.1 and b0 < a1 - 0.1:
                            hit = True; break
                    if hit:
                        break
                faced += hit
            # a core opening has walls on (nearly) all sides; one side may
            # open to a corridor / the next shaft
            # walls on (nearly) every side; one side may open to a corridor
            if total >= 3 and faced >= total - 1:
                kind = "core"
            self._last_faced = (faced, total)
        return kind, (w, h)

    def _openings(self, slab, loop_id):
        shaft_boxes = []
        try:
            from pyrevit import DB
            for s in DB.FilteredElementCollector(self.m.doc).OfCategory(
                    DB.BuiltInCategory.OST_ShaftOpening).WhereElementIsNotElementType():
                bb = s.get_BoundingBox(None)
                if bb:
                    shaft_boxes.append((bb.Min.X, bb.Min.Y, bb.Max.X, bb.Max.Y))
        except Exception:
            pass
        for k, (loop, poly) in enumerate(zip(slab.open_edges, slab.openings)):
            edges = [e for e in loop if e.length >= MIN_EDGE]
            self.stubs += len(loop) - len(edges)
            if not edges:
                continue
            cx, cy = P.centroid(poly)
            kind, size = self._opening_kind(edges, poly, cx, cy)
            # a Shaft Opening element about the size of this hole
            if kind in ("plain", "penetration"):
                area = max(size[0] * size[1], 0.01)
                for x0, y0, x1, y1 in shaft_boxes:
                    if x0 - 0.1 <= cx <= x1 + 0.1 and y0 - 0.1 <= cy <= y1 + 0.1 \
                            and (x1 - x0) * (y1 - y0) <= 2.5 * area:
                        kind = "shaft"
                        break
            f = Feature("opening", edges, owners=(slab.eid,), sub=kind)
            f.meta = {"poly": poly, "size": size, "centroid": (cx, cy),
                      "faced": getattr(self, "_last_faced", None),
                      "stepped": getattr(self, "_last_stepped", False)}
            self._last_faced = None; self._last_stepped = False
            self._add(f, "%s/o%d" % (loop_id, k))

    # ---------------- members ----------------
    def _beams(self):
        for b in self.m.beams:
            if b.d is None or len(b.sides) < 2:
                continue
            free, framed = [], []
            for end in b.ends:
                em = end.mid()
                hit = None
                for sgn in (1, -1):
                    x, y = em[0] + sgn * 0.25 * b.d[0], em[1] + sgn * 0.25 * b.d[1]
                    h = self.m.member_at(x, y)
                    if h is not None and h.eid != b.eid:
                        hit = h; break
                (framed if hit else free).append(end)
            f = Feature("beam", list(b.sides) + free, owners=(b.eid,))
            f.meta = {"member": b, "sides": list(b.sides), "free_ends": free,
                      "framed_ends": framed, "width": b.width}
            self._add(f)

    def _cjs(self):
        for cj in self.m.cjs:
            f = Feature("cj", [cj], owners=(cj.eid,))
            self._add(f)

    # ---------------- build ----------------
    def _build(self):
        for si, slab in enumerate(self.m.slabs):
            self._perimeter(slab, "s%d" % si)
            self._openings(slab, "s%d" % si)
        self._beams()
        self._cjs()

    # ---------------- reporting ----------------
    def summary(self, crop_only=True):
        from collections import Counter
        c = Counter()
        for f in self.features:
            if crop_only and not f.in_crop:
                continue
            c[f.kind if f.sub is None else "%s/%s" % (f.kind, f.sub)] += 1
        return dict(c)

    def near(self, x0, y0, x1, y1):
        return [f for f in self.features if f.extent and
                f.extent[2] >= x0 and f.extent[0] <= x1 and
                f.extent[3] >= y0 and f.extent[1] <= y1]
