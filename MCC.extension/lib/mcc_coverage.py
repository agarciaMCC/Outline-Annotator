# -*- coding: utf-8 -*-
"""Grid-location coverage: can every edge in a soffit plan be located off a
gridline from the dimensions in a view?  (Adolfo's rule: locate every edge
from a grid; edge-to-edge strings are only a double check.)

Targets come from mcc_model.PlanModel: slab perimeter edges (incl. soffit
steps), opening edges, beam side/end faces, wall faces, CJ lines. Coincident
targets (same plane, overlapping) are merged. For each target and view:
  DIRECT   a dim has a grid witness line right next to the target's witness
           line (grid -> edge, or face | grid | face)
  CHAINED  only reachable along a string that starts at a grid
  CHECK    only in dims with no grid (edge-to-edge)
  NONE     no dim touches it
  ON GRID  the target lies on a gridline (located by the grid itself)
  ANGLED   no grid family runs along it (can't be located square to a grid)
Read-only."""
import math
from pyrevit import DB
import mcc_score as SC

TOL = 1.0 / 24        # ft, witness line on the target plane
SPAN_SLACK = 8.0      # ft, dim line may sit this far past the target's ends
MIN_LEN = 0.5         # ft, ignore shorter targets
ON_GRID = 1.0 / 96


class Target(object):
    def __init__(self, kind, p0, p1, owner, fi):
        self.kind, self.p0, self.p1, self.owner, self.fi = kind, p0, p1, owner, fi
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy)
        self.length = L
        self.t = (dx / L, dy / L)
        self.n = (-self.t[1], self.t[0])
        self.kinds = set([kind])

    def mid(self):
        return ((self.p0[0] + self.p1[0]) / 2.0, (self.p0[1] + self.p1[1]) / 2.0)

    def span(self):
        if getattr(self, "_span", None):
            return self._span
        a = self.t[0] * self.p0[0] + self.t[1] * self.p0[1]
        b = self.t[0] * self.p1[0] + self.t[1] * self.p1[1]
        return min(a, b), max(a, b)

    def absorb(self, other):
        """Merge a coincident target: union of kinds and extent."""
        self.kinds |= other.kinds
        pts = [self.t[0] * p[0] + self.t[1] * p[1]
               for p in (self.p0, self.p1, other.p0, other.p1)]
        self._span = (min(pts), max(pts))
        self.on_wall = getattr(self, "on_wall", False) or getattr(other, "on_wall", False)


def _framed(model, f):
    """Beam end face that runs into a column or wall (probe both sides)."""
    m = f.mid()
    n = (-f.d[1], f.d[0])
    for sgn in (1, -1):
        x, y = m[0] + sgn * 0.25 * n[0], m[1] + sgn * 0.25 * n[1]
        hit = model.member_at(x, y)
        if hit is not None and hit.eid != getattr(f, "owner", None):
            return True
    return False


def _on_wall(model, f, tol=1.0 / 24):
    """Edge lying on a wall face (flush, overlapping): located by the wall,
    which has its own sheets."""
    m = f.mid()
    for w in model.walls:
        for wf in w.sides:
            if abs(abs(wf.d[0] * f.d[0] + wf.d[1] * f.d[1]) - 1) > 1e-4:
                continue
            n = (-wf.d[1], wf.d[0])
            if abs((m[0] - wf.p0[0]) * n[0] + (m[1] - wf.p0[1]) * n[1]) > tol:
                continue
            a = [wf.p0[0] * wf.d[0] + wf.p0[1] * wf.d[1], wf.p1[0] * wf.d[0] + wf.p1[1] * wf.d[1]]
            b = [f.p0[0] * wf.d[0] + f.p0[1] * wf.d[1], f.p1[0] * wf.d[0] + f.p1[1] * wf.d[1]]
            if min(b) < max(a) - 0.1 and min(a) < max(b) - 0.1:
                return True
    return False


def targets(model):
    raw = []
    for s in model.slabs:
        raw += [("slab edge", f) for f in s.edges]
        for loop in s.open_edges:
            raw += [("opening edge", f) for f in loop]
    for m in model.beams:
        raw += [("beam side", f) for f in m.sides] + [("beam end", f) for f in m.ends]
    for m in model.walls:
        raw += [("wall face", f) for f in m.sides]
    for c in model.cjs:
        raw.append(("cj", c))
    out, angled, ongrid = [], [], []
    for kind, f in raw:
        if kind in SKIP_KINDS:
            continue
        if kind == "beam end" and _framed(model, f):
            continue                    # stops at a column/wall: located by it
        p0, p1 = tuple(f.p0[:2]), tuple(f.p1[:2])
        if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) < MIN_LEN:
            continue
        fi = model.family_parallel(f.d)
        t = Target(kind, p0, p1, getattr(f, "owner", getattr(f, "eid", None)), fi)
        t.on_wall = kind in ("slab edge", "opening edge") and _on_wall(model, f)
        if fi is None:
            angled.append(t)
            continue
        gi, off = model.nearest_grid(t.mid(), fi)
        if abs(off) <= ON_GRID:
            ongrid.append(t)
            continue
        out.append(t)
    # merge coincident targets (same family, same plane, overlapping)
    merged = []
    for t in out:
        c = t.n[0] * t.p0[0] + t.n[1] * t.p0[1]
        a0, a1 = t.span()
        hit = None
        for m in merged:
            if m.fi != t.fi:
                continue
            if abs(abs(m.n[0] * t.n[0] + m.n[1] * t.n[1]) - 1) > 1e-6:
                continue
            cm = m.n[0] * m.p0[0] + m.n[1] * m.p0[1]
            sgn = 1 if (m.n[0] * t.n[0] + m.n[1] * t.n[1]) > 0 else -1
            if abs(cm - sgn * c) > TOL:
                continue
            b0, b1 = m.span()
            if a0 <= b1 + 0.1 and b0 <= a1 + 0.1:
                hit = m
                break
        if hit:
            hit.absorb(t)
        else:
            merged.append(t)
    return merged, angled, ongrid


def _dim_point(dim):
    """A point on the dimension line. Dimension.Origin throws for
    multi-segment dims, so use the curve (or the first segment's origin)."""
    try:
        if dim.NumberOfSegments <= 1:
            o = dim.Origin
            return (o.X, o.Y)
    except Exception:
        pass
    try:
        c = dim.Curve
        p = c.Evaluate(0.5, True) if c.IsBound else c.Origin
        return (p.X, p.Y)
    except Exception:
        pass
    try:
        o = list(dim.Segments)[0].Origin
        return (o.X, o.Y)
    except Exception:
        return None


def _dim_rows(doc, view, is_dim):
    rows = []
    for dim in DB.FilteredElementCollector(doc, view.Id).OfClass(DB.Dimension):
        if is_dim and not is_dim(dim):
            continue
        s = SC.signature(doc, dim)
        if not s:
            continue
        d = SC._dir(dim)
        o = _dim_point(dim)
        if o is None:
            continue
        rows.append((s, (d.X, d.Y), o))
    return rows


RANK = {"DIRECT": 0, "WALL": 1, "CHAINED": 2, "CHECK": 3, "NONE": 4}
LOCATED = ("DIRECT", "WALL")    # WALL: located off a wall face (elevator /
                                # shaft openings in line with a wall keep the
                                # rough opening constant up the building)
SKIP_KINDS = ("wall face",)     # walls are located on their own sheets


def grade(target, dim_rows):
    if getattr(target, "on_wall", False):
        return "WALL"
    best = "NONE"
    for s, d, o in dim_rows:
        if abs(abs(d[0] * target.n[0] + d[1] * target.n[1]) - 1) > 1e-3:
            continue                                   # not measuring across it
        lo, hi = target.span()
        along = target.t[0] * o[0] + target.t[1] * o[1]
        if along < lo - SPAN_SLACK or along > hi + SPAN_SLACK:
            continue                                   # dim is elsewhere
        st = target_station = d[0] * target.p0[0] + d[1] * target.p0[1]
        sts = s["stations"]
        idx = [i for i, (v, k) in enumerate(sts) if abs(v - st) <= TOL]
        if not idx:
            continue
        i = idx[0]
        grids = [j for j, (v, k) in enumerate(sts) if k == "grid"]
        walls = [j for j, (v, k) in enumerate(sts) if k == "wall"]
        if any(abs(j - i) == 1 for j in grids):
            g = "DIRECT"
        elif any(abs(j - i) == 1 for j in walls):
            g = "WALL"
        elif grids:
            g = "CHAINED"
        else:
            g = "CHECK"
        if RANK[g] < RANK[best]:
            best = g
            if g == "DIRECT":
                break
    return best


def annotation_crop_poly(view):
    """Plan polygon of the view's ANNOTATION crop - what decides whether a
    dimension shows (it is usually wider than the model crop, leaving a
    margin beside the slab for dims). Falls back to the model crop."""
    try:
        if view.CropBoxActive and view.get_Parameter(DB.BuiltInParameter.VIEWER_ANNOTATION_CROP_ACTIVE).AsInteger():
            loop = view.GetCropRegionShapeManager().GetAnnotationCropShape()
            pts = [(c.GetEndPoint(0).X, c.GetEndPoint(0).Y) for c in loop]
            if len(pts) >= 3:
                return pts
    except Exception:
        pass
    return crop_poly(view)


def crop_poly(view):
    """Plan polygon of the view's crop (shape if set, else box), or None."""
    try:
        if not view.CropBoxActive:
            return None
        sm = view.GetCropRegionShapeManager()
        if sm.ShapeSet:
            loop = sm.GetCropShape()[0]
            return [(c.GetEndPoint(0).X, c.GetEndPoint(0).Y) for c in loop]
        bb = view.CropBox
        tr = bb.Transform
        pts = [tr.OfPoint(DB.XYZ(x, y, 0)) for x, y in
               ((bb.Min.X, bb.Min.Y), (bb.Max.X, bb.Min.Y), (bb.Max.X, bb.Max.Y), (bb.Min.X, bb.Max.Y))]
        return [(p.X, p.Y) for p in pts]
    except Exception:
        return None


def _inside(pt, poly):
    x, y = pt
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            c = not c
        j = i
    return c


def coverage(doc, model, views, is_dim=None, crop_view=None):
    """-> (targets, angled, ongrid, {view name: [grade per target]})
    crop_view: only targets whose midpoint is inside this view's crop."""
    T, angled, ongrid = targets(model)
    poly = crop_poly(crop_view) if crop_view is not None else None
    if poly:
        keep = lambda t: _inside(t.mid(), poly)
        T, angled, ongrid = [t for t in T if keep(t)], [t for t in angled if keep(t)], [t for t in ongrid if keep(t)]
    res = {}
    for v in views:
        rows = _wall_stations(model, _dim_rows(doc, v, is_dim))
        res[v.Name] = [grade(t, rows) for t in T]
    return T, angled, ongrid, res


def _wall_stations(model, rows):
    """A witness line standing on a wall face plane locates like the wall
    does, whatever element it references (an elevator opening edge in line
    with the shaft wall is dimensioned off that face). Re-tag such stations
    as 'wall'."""
    faces = []
    for w in model.walls:
        for wf in (w.sides or []):
            n = (-wf.d[1], wf.d[0])
            faces.append((n, n[0] * wf.p0[0] + n[1] * wf.p0[1], wf))
    out = []
    for s, d, o in rows:
        sts = []
        for v, k in s["stations"]:
            if k not in ("grid", "wall"):
                for n, c, wf in faces:
                    dot = n[0] * d[0] + n[1] * d[1]
                    if abs(abs(dot) - 1) > 1e-3:
                        continue
                    if abs(v - c * dot) > TOL:
                        continue
                    a = [wf.p0[0] * wf.d[0] + wf.p0[1] * wf.d[1], wf.p1[0] * wf.d[0] + wf.p1[1] * wf.d[1]]
                    along = o[0] * wf.d[0] + o[1] * wf.d[1]
                    if min(a) - 3.0 <= along <= max(a) + 3.0:
                        k = "wall"
                        break
            sts.append((v, k))
        s2 = dict(s); s2["stations"] = sts
        out.append((s2, d, o))
    return out
