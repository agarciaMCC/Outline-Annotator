# -*- coding: utf-8 -*-
"""RECOGNIZE: read a soffit plan view into a plain plan model.

PlanModel holds, in plan feet:
  grids     [(grid, origin, u, n)]     families: [[grid index]]
  slabs     [Slab]   perimeter edges + opening loops, each edge with its
                     Revit reference
  beams     [Member] structural framing: direction, side faces, end faces
  walls     [Member] walls: direction, side faces
  columns   [Member] structural columns: faces
  cjs       [CJLine] construction-joint detail components (CJ_FAMILY)
  obstacles [Obst]   true plan outlines of everything above (for routing)

Every face/edge carries (offset-able) geometry + a DB.Reference so the
DECIDE stage can say "locate this face from that grid" without touching
Revit again. Nothing here writes to the document."""
from mcc_compat import eid_int
import math
from pyrevit import DB
import mcc_view as V
import mcc_plan as P

CJ_FAMILY = "Large Scale"      # detail item family used for CJ lines
SIN_TOL = math.sin(math.radians(0.5))


class Face(object):
    """A vertical face (or slab edge) in plan: a segment with a reference."""
    __slots__ = ("p0", "p1", "d", "ref", "length", "owner", "kind")

    def __init__(self, p0, p1, ref, owner, kind):
        self.p0, self.p1 = p0, p1
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        self.length = math.hypot(dx, dy)
        self.d = (dx / self.length, dy / self.length) if self.length > 1e-9 \
            else (0.0, 0.0)
        self.ref = ref
        self.owner = owner          # element id (int)
        self.kind = kind            # "slab edge" / "opening edge" / "beam
                                    # side" / "beam end" / "wall face" /
                                    # "column face" / "cj"

    def mid(self):
        return ((self.p0[0] + self.p1[0]) / 2.0, (self.p0[1] + self.p1[1]) / 2.0)


class Slab(object):
    __slots__ = ("eid", "outer", "openings", "edges", "open_edges", "floor")

    def __init__(self, floor, outer, openings, edges, open_edges):
        self.floor = floor
        self.eid = eid_int(floor.Id)
        self.outer = outer            # polygon
        self.openings = openings      # [polygon]
        self.edges = edges            # [Face] perimeter (straight only)
        self.open_edges = open_edges  # [[Face]] per opening


class Member(object):
    """Beam / wall / column with its plan outline and faces."""
    __slots__ = ("e", "eid", "cat", "poly", "d", "p0", "p1", "sides", "ends",
                 "faces", "width")

    def __init__(self, e, cat, poly):
        self.e = e
        self.eid = eid_int(e.Id)
        self.cat = cat
        self.poly = poly
        self.d = None
        self.p0 = self.p1 = None
        self.sides, self.ends, self.faces = [], [], []
        self.width = None


class CJLine(object):
    __slots__ = ("e", "eid", "p0", "p1", "d", "ref", "length")

    def __init__(self, e, p0, p1, ref):
        self.e = e
        self.eid = eid_int(e.Id)
        self.p0, self.p1, self.ref = p0, p1, ref
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        self.length = math.hypot(dx, dy)
        self.d = (dx / self.length, dy / self.length) if self.length > 1e-9 \
            else (0.0, 0.0)


class Obst(object):
    __slots__ = ("poly", "rect", "eid", "kind", "raw")

    def __init__(self, poly, eid, kind, raw=None):
        self.poly = poly
        self.raw = raw              # openings: the true outline (poly is its inflated convex hull)
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        self.rect = (min(xs), min(ys), max(xs), max(ys))
        self.eid = eid
        self.kind = kind


class PlanModel(object):
    def __init__(self, doc, view, floors=None, level_only=True, pad=0.5):
        self.doc, self.view = doc, view
        self.opts = DB.Options()          # view geometry: slabs, detail items
        self.opts.ComputeReferences = True
        self.opts.View = view
        self.opts_fine = DB.Options()     # model geometry: beams, walls, cols
        self.opts_fine.ComputeReferences = True
        self.opts_fine.DetailLevel = DB.ViewDetailLevel.Fine
        self.grids = V.straight_grids(doc, view)
        self.families = V.grid_families(self.grids)
        self.fam_of = {}
        for fi, fam in enumerate(self.families):
            for gi in fam:
                self.fam_of[gi] = fi
        if floors is None:
            floors, self.level = V.soffit_floors(doc, view, level_only)
        else:
            self.level = None
        self.floors = floors
        self.slabs = self._read_slabs()
        # the slabs' VERTICAL corner edges: a plan dimension reads one as a
        # point, which is how Adolfo locates a corner where the perimeter
        # turns at a non-90 degree angle (2026-10-06, refs 25562 / 25933 on L3N)
        self.corner_refs = self._read_corner_refs()
        self.beams = self._read_members(DB.BuiltInCategory.OST_StructuralFraming,
                                        "beam")
        # curbs and CMU walls aren't "walls" for any wall rule (Adolfo
        # 2026-10-05: Kalae curbs are walls "8.5 x 4 CURB"); they neither
        # block dims nor anchor them
        walls = self._read_members(DB.BuiltInCategory.OST_Walls, "wall")
        self.soft_walls = [w for w in walls if any(k in (w.e.Name or "").upper() for k in ("CURB", "CMU"))]
        self.walls = [w for w in walls if w not in self.soft_walls]
        self.columns = self._read_members(
            DB.BuiltInCategory.OST_StructuralColumns, "column") + \
            self._read_members(DB.BuiltInCategory.OST_Columns, "column")
        self.cjs = self._read_cjs()
        self.join_cuts = self._drop_join_cuts()
        self.filled_holes = self._drop_filled_holes()
        self.pad = pad
        self.obstacles = self._build_obstacles(pad)

    # ---------------- grids ----------------
    def grid(self, gi):
        return self.grids[gi]

    def offset(self, pt, gi):
        g, g0, u, n = self.grids[gi]
        return (pt[0] - g0[0]) * n[0] + (pt[1] - g0[1]) * n[1]

    def station(self, pt, gi):
        g, g0, u, n = self.grids[gi]
        return (pt[0] - g0[0]) * u[0] + (pt[1] - g0[1]) * u[1]

    def family_parallel(self, d):
        """Index of the grid family whose grids run along d, or None."""
        for fi, fam in enumerate(self.families):
            if P.parallel(d, self.grids[fam[0]][2], SIN_TOL):
                return fi
        return None

    def nearest_grid(self, pt, fi, max_dist=None):
        """(gi, offset) of the family-fi grid nearest to pt."""
        best = None
        for gi in self.families[fi]:
            off = self.offset(pt, gi)
            if best is None or abs(off) < abs(best[1]):
                best = (gi, off)
        if best and max_dist is not None and abs(best[1]) > max_dist:
            return None
        return best

    def grid_between(self, pt_a, pt_b, fi, tol=1.0 / 96):
        """A family-fi grid lying between two points (offset signs differ),
        e.g. a beam centred on a grid. Returns gi or None."""
        for gi in self.families[fi]:
            a, b = self.offset(pt_a, gi), self.offset(pt_b, gi)
            if (a < -tol and b > tol) or (a > tol and b < -tol):
                return gi
        return None

    # ---------------- slabs ----------------
    def _read_corner_refs(self):
        """{(round(x*96), round(y*96)): Reference} of every vertical edge of the
        soffit floors' solids (the slab's thickness at an outline vertex)."""
        out = {}
        for fl in self.floors:
            try:
                geo = fl.get_Geometry(self.opts)
            except Exception:
                continue
            for g in geo:
                if not isinstance(g, DB.Solid):
                    continue
                for ed in g.Edges:
                    try:
                        r = ed.Reference
                        if r is None:
                            continue
                        c = ed.AsCurve()
                        a, b = c.GetEndPoint(0), c.GetEndPoint(1)
                    except Exception:
                        continue
                    if abs(a.Z - b.Z) > 0.3 and abs(a.X - b.X) < 1.0 / 96 and abs(a.Y - b.Y) < 1.0 / 96:
                        out.setdefault((int(round(a.X * 96)), int(round(a.Y * 96))), r)
        return out

    def corner_ref(self, pt, tol=1):
        """Reference of the vertical slab edge at a plan point (within tol/96 ft)."""
        kx, ky = int(round(pt[0] * 96)), int(round(pt[1] * 96))
        for dx in range(-tol, tol + 1):
            for dy in range(-tol, tol + 1):
                r = self.corner_refs.get((kx + dx, ky + dy))
                if r is not None:
                    return r
        return None

    def _read_slabs(self):
        slabs = []
        self.cut_edges = 0
        def real(fl, r):
            # an edge made by the view's cut plane slicing a floor (a ramp
            # dropping below it) references the cut FACE, not a model edge -
            # it isn't a soffit edge (Adolfo: "a line produced by a cut in
            # the view range")
            try:
                g = fl.GetGeometryObjectFromReference(r)
            except Exception:
                return True
            if isinstance(g, DB.Face):
                self.cut_edges += 1
                return False
            return True
        for fl in self.floors:
            for outer, inners, oe, ie in P.soffit_loops(fl, self.opts):
                edges = [Face(p0, p1, r, eid_int(fl.Id), "slab edge")
                         for p0, p1, d, r, ln, curved in oe
                         if not curved and r is not None and real(fl, r)]
                open_edges = []
                for loop in ie:
                    open_edges.append([Face(p0, p1, r, eid_int(fl.Id),
                                            "opening edge")
                                       for p0, p1, d, r, ln, curved in loop
                                       if not curved and r is not None and real(fl, r)])
                slabs.append(Slab(fl, outer, inners, edges, open_edges))
        # a slab whose outline sits inside another's is an island: keep it
        # (its perimeter is still a soffit edge) but mark it via kind
        return slabs

    def _drop_join_cuts(self):
        """Inner loops of a slab's soffit face that are just a joined
        column / wall / beam cutting through (not a modeled opening) -
        e.g. an 18x18 column on the rotated wing reads as a 2'x2' hole.
        A loop is a join cut when every vertex, nudged 1/2" toward the
        loop centre, lies inside one member's outline. Returns the count."""
        members = self.columns + self.walls + self.beams
        dropped = 0
        for sl in self.slabs:
            keep_o, keep_e = [], []
            for poly, edges in zip(sl.openings, sl.open_edges):
                pts = [p[:2] for p in poly] if poly else [f.p0[:2] for f in edges]
                if not pts:
                    keep_o.append(poly); keep_e.append(edges)
                    continue
                cx = sum(p[0] for p in pts) / len(pts)
                cy = sum(p[1] for p in pts) / len(pts)
                nudged = []
                for x, y in pts:
                    dx, dy = cx - x, cy - y
                    L = math.hypot(dx, dy) or 1.0
                    k = min(1.0 / 24, L / 2.0) / L
                    nudged.append((x + dx * k, y + dy * k))
                cut = any(m.poly and all(P.point_in_poly(x, y, m.poly)
                                         for x, y in nudged)
                          for m in members)
                if cut:
                    dropped += 1
                else:
                    keep_o.append(poly); keep_e.append(edges)
            sl.openings, sl.open_edges = keep_o, keep_e
        return dropped

    def _drop_filled_holes(self):
        """A hole in one floor that other floors fill (Kalae L3: the PT
        slab's 33 x 113 ft hole holding the 9" MS ramp slabs) is not an
        opening: drop it when 80% of a sample grid inside it is covered by
        another floor shown in the view (any level - the L4 ramp piece counts),
        a wall or a beam. Returns the count."""
        dropped = 0
        covers = []
        try:
            col = DB.FilteredElementCollector(self.doc, self.view.Id) \
                .OfCategory(DB.BuiltInCategory.OST_Floors).WhereElementIsNotElementType()
            for fl in col:
                bb = fl.get_BoundingBox(None)
                pp = P.plan_poly(fl, self.opts, self.view)
                if pp and bb is not None:
                    covers.append((eid_int(fl.Id), [q[:2] for q in pp], bb.Min.Z, bb.Max.Z))
        except Exception:
            pass
        covers += [(m.eid, m.poly, None, None) for m in self.walls + getattr(self, "soft_walls", []) + self.beams if m.poly]
        self.filled_hole_boxes = []
        for sl in self.slabs:
            sbb = sl.floor.get_BoundingBox(None)
            z0, z1 = (sbb.Min.Z - 1.0, sbb.Max.Z + 1.0) if sbb is not None else (-1e9, 1e9)
            # only floors at this slab's height fill its holes (a floor on the
            # level above seen through a real opening must not)
            cov = [(e, cp) for e, cp, a, b in covers
                   if e != sl.eid and (a is None or (a <= z1 and b >= z0))]
            keep_o, keep_e = [], []
            for poly, edges in zip(sl.openings, sl.open_edges):
                pts = [p[:2] for p in poly] if poly else []
                if len(pts) < 3:
                    keep_o.append(poly); keep_e.append(edges)
                    continue
                xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                step = max(2.0, max(max(xs) - min(xs), max(ys) - min(ys)) / 40.0)
                n_in = n_fill = 0
                x = min(xs) + step / 2.0
                while x < max(xs):
                    y = min(ys) + step / 2.0
                    while y < max(ys):
                        if P.point_in_poly(x, y, pts):
                            n_in += 1
                            if any(P.point_in_poly(x, y, cp) for eid, cp in cov):
                                n_fill += 1
                        y += step
                    x += step
                if n_in and n_fill >= 0.8 * n_in:
                    dropped += 1
                    self.filled_hole_boxes.append((sl.eid, min(xs), max(xs), min(ys), max(ys), n_fill * 1.0 / n_in))
                else:
                    keep_o.append(poly); keep_e.append(edges)
            sl.openings, sl.open_edges = keep_o, keep_e
        return dropped

    def slab_polys(self):
        return [s.outer for s in self.slabs]

    def in_slab(self, x, y):
        for s in self.slabs:
            if P.point_in_poly(x, y, s.outer) and not any(
                    P.point_in_poly(x, y, o) for o in s.openings):
                return True
        return False

    # ---------------- members ----------------
    def _read_members(self, bic, cat):
        out = []
        col = DB.FilteredElementCollector(self.doc, self.view.Id) \
            .OfCategory(bic).WhereElementIsNotElementType()
        for e in col:
            poly = P.plan_poly(e, self.opts_fine, self.view)
            if not poly:
                continue
            m = Member(e, cat, poly)
            # direction from the location curve when it is a line
            loc = e.Location
            crv = loc.Curve if isinstance(loc, DB.LocationCurve) else None
            if isinstance(crv, DB.Line):
                d = crv.Direction
                mm = math.hypot(d.X, d.Y)
                if mm > 1e-9:
                    m.d = (d.X / mm, d.Y / mm)
                    a, b = crv.GetEndPoint(0), crv.GetEndPoint(1)
                    m.p0, m.p1 = (a.X, a.Y), (b.X, b.Y)
            # faces: vertical planar faces with references
            for face, fn, o in P.vertical_faces(e, self.opts_fine):
                ref = face.Reference
                if ref is None:
                    continue
                seg = self._face_segment(face)
                if seg is None:
                    continue
                f = Face(seg[0], seg[1], ref, m.eid, cat + " face")
                m.faces.append(f)
                if m.d is not None:
                    if P.perpendicular(fn, m.d):
                        f.kind = cat + " side"
                        m.sides.append(f)
                    elif P.parallel(fn, m.d):
                        f.kind = cat + " end"
                        m.ends.append(f)
            # width = distance between the two outermost side faces
            if m.d is not None and len(m.sides) >= 2:
                n = (-m.d[1], m.d[0])
                offs = [(p[0] - m.p0[0]) * n[0] + (p[1] - m.p0[1]) * n[1]
                        for f in m.sides for p in (f.p0, f.p1)]
                m.width = max(offs) - min(offs)
            out.append(m)
        return out

    def _face_segment(self, face):
        """Plan segment of a vertical planar face: the extent of its outer
        loop projected onto the plan."""
        pts = []
        try:
            for loop in face.EdgeLoops:
                for ed in loop:
                    for p in ed.Tessellate():
                        pts.append((p.X, p.Y))
        except Exception:
            return None
        if len(pts) < 2:
            return None
        fn = face.FaceNormal
        d = (-fn.Y, fn.X)
        base = pts[0]
        ts = [((p[0] - base[0]) * d[0] + (p[1] - base[1]) * d[1]) for p in pts]
        lo, hi = min(ts), max(ts)
        if hi - lo < 1e-6:
            return None
        return ((base[0] + d[0] * lo, base[1] + d[1] * lo),
                (base[0] + d[0] * hi, base[1] + d[1] * hi))

    # ---------------- CJ lines ----------------
    def _read_cjs(self):
        out = []
        col = DB.FilteredElementCollector(self.doc, self.view.Id) \
            .OfCategory(DB.BuiltInCategory.OST_DetailComponents) \
            .WhereElementIsNotElementType()
        for e in col:
            try:
                fam = e.Symbol.Family.Name
                typ = e.Name
            except Exception:
                continue
            # older models: family "Large Scale"; Kalae R26: family
            # "Annotation - Line - CJ Form Line", type "Large Scale"
            if fam != CJ_FAMILY and not ("CJ" in fam.upper() and typ == CJ_FAMILY):
                continue
            best = None
            try:
                for geo in e.get_Geometry(self.opts):
                    items = [geo]
                    if isinstance(geo, DB.GeometryInstance):
                        items = list(geo.GetInstanceGeometry())
                    for it in items:
                        if isinstance(it, DB.Line) and it.IsBound:
                            if best is None or it.Length > best.Length:
                                best = it
            except Exception:
                best = None
            # reference: the family's centre (front/back) plane - what the
            # detailers dimension to. Instance-geometry line refs are
            # symbol-level and Revit drops dims built on them at commit
            # ("references no longer parallel").
            ref = None
            try:
                rs = e.GetReferences(DB.FamilyInstanceReferenceType.CenterFrontBack)
                if rs and rs.Count:
                    ref = rs[0]
            except Exception:
                ref = None
            seg = None
            try:
                loc = e.Location
                if isinstance(loc, DB.LocationCurve) and isinstance(loc.Curve, DB.Line):
                    seg = loc.Curve
            except Exception:
                seg = None
            if seg is None:
                seg = best
            if ref is None and best is not None:
                ref = self._instance_line_ref(e, best)
            if seg is None or ref is None:
                continue
            a, b = seg.GetEndPoint(0), seg.GetEndPoint(1)
            out.append(CJLine(e, (a.X, a.Y), (b.X, b.Y), ref))
        return out

    def _instance_line_ref(self, e, line):
        """Same line from the symbol geometry - its reference carries the
        instance prefix, so it is valid for a dimension."""
        try:
            for geo in e.get_Geometry(self.opts):
                if isinstance(geo, DB.GeometryInstance):
                    for it in geo.GetSymbolGeometry():
                        if isinstance(it, DB.Line) and it.Reference is not None \
                                and abs(it.Length - line.Length) < 1e-6:
                            return it.Reference
        except Exception:
            pass
        return None

    # ---------------- obstacles ----------------
    def _build_obstacles(self, pad):
        obs = []
        for m in self.beams + self.walls + self.columns:
            obs.append(Obst(P.inflate(m.poly, pad), m.eid, m.cat))
        for s in self.slabs:
            for o in s.openings:
                hull = P.convex_hull(o)
                if len(hull) >= 3:
                    obs.append(Obst(P.inflate(hull, 0.25), s.eid, "opening", raw=[p[:2] for p in o]))
        return obs

    def member_at(self, x, y, cats=("column", "wall")):
        """Member of one of the categories whose outline contains (x, y)."""
        for m in self.columns + self.walls + self.beams:
            if m.cat in cats and P.point_in_poly(x, y, m.poly):
                return m
        return None
