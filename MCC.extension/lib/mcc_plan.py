# -*- coding: utf-8 -*-
"""Plan-geometry helpers shared by the MCC dimension buttons.

Everything here works in plan (x, y) feet. The point of this module is
that every button sees the model the same way: an element's TRUE plan
outline (not its axis-aligned bounding box, which is useless on a rotated
wing), slab loops split into perimeter / openings, and simple, tested
polygon tests. Read-only: nothing here touches the document."""
import math
from pyrevit import DB


# ---------------- basic polygon ops ----------------
def poly_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2.0


def point_in_poly(x, y, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y):
            xx = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < xx:
                inside = not inside
        j = i
    return inside


def centroid(pts):
    return (sum(p[0] for p in pts) / len(pts),
            sum(p[1] for p in pts) / len(pts))


def convex_hull(pts):
    pts = sorted(set((round(p[0], 4), round(p[1], 4)) for p in pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def inflate(poly, pad):
    """Hull grown by 'pad' on every side (Minkowski sum with a square)."""
    if pad <= 0:
        return poly
    pts = []
    for x, y in poly:
        pts.extend([(x - pad, y - pad), (x + pad, y - pad),
                    (x + pad, y + pad), (x - pad, y + pad)])
    return convex_hull(pts)


def seg_intersect(a, b, c, d):
    """Do segments ab and cd intersect (touching counts)?"""
    def cr(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])

    def on_seg(o, p, q):
        return min(o[0], q[0]) - 1e-9 <= p[0] <= max(o[0], q[0]) + 1e-9 and \
            min(o[1], q[1]) - 1e-9 <= p[1] <= max(o[1], q[1]) + 1e-9
    d1, d2 = cr(c, d, a), cr(c, d, b)
    d3, d4 = cr(a, b, c), cr(a, b, d)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and \
            d1 != 0 and d2 != 0 and d3 != 0 and d4 != 0:
        return True
    if abs(d1) < 1e-9 and on_seg(c, a, d):
        return True
    if abs(d2) < 1e-9 and on_seg(c, b, d):
        return True
    if abs(d3) < 1e-9 and on_seg(a, c, b):
        return True
    if abs(d4) < 1e-9 and on_seg(a, d, b):
        return True
    return False


def seg_hits_poly(p, q, poly):
    if point_in_poly(p[0], p[1], poly) or point_in_poly(q[0], q[1], poly):
        return True
    m = len(poly)
    for i in range(m):
        if seg_intersect(p, q, poly[i], poly[(i + 1) % m]):
            return True
    return False


def dist_point_seg(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 < 1e-12:
        return math.hypot(p[0] - ax, p[1] - ay)
    t = ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2
    t = max(0.0, min(1.0, t))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def dist_point_poly_edges(p, poly):
    m = len(poly)
    return min(dist_point_seg(p, poly[i], poly[(i + 1) % m]) for i in range(m))


# ---------------- element outlines ----------------
def solids_of(e, opts):
    out = []
    try:
        for geo in e.get_Geometry(opts):
            if isinstance(geo, DB.Solid):
                if geo.Volume > 0:
                    out.append(geo)
            elif isinstance(geo, DB.GeometryInstance):
                for g2 in geo.GetInstanceGeometry():
                    if isinstance(g2, DB.Solid) and g2.Volume > 0:
                        out.append(g2)
    except Exception:
        pass
    return out


def plan_poly(e, opts, view=None):
    """Convex plan outline of an element, or None."""
    pts = []
    for s in solids_of(e, opts):
        for ed in s.Edges:
            try:
                for p in ed.Tessellate():
                    pts.append((p.X, p.Y))
            except Exception:
                pass
    if len(pts) < 3:
        bb = e.get_BoundingBox(view)
        if not bb:
            return None
        pts = [(bb.Min.X, bb.Min.Y), (bb.Max.X, bb.Min.Y),
               (bb.Max.X, bb.Max.Y), (bb.Min.X, bb.Max.Y)]
    hull = convex_hull(pts)
    return hull if len(hull) >= 3 else None


def vertical_faces(e, opts):
    """[(PlanarFace, (nx, ny), origin_xy)] vertical faces of an element,
    with references when the geometry carries them."""
    out = []
    for s in solids_of(e, opts):
        for face in s.Faces:
            if not isinstance(face, DB.PlanarFace):
                continue
            fn = face.FaceNormal
            if abs(fn.Z) > 0.01:
                continue
            o = face.Origin
            out.append((face, (fn.X, fn.Y), (o.X, o.Y)))
    return out


# ---------------- slabs ----------------
def soffit_loops(floor, opts):
    """For each downward face of a floor: (outer_poly, [inner_polys],
    outer_edges, inner_edges) where an edge is
    (p0, p1, dir, reference, length, curved)."""
    result = []
    for s in solids_of(floor, opts):
        for face in s.Faces:
            if not isinstance(face, DB.PlanarFace) or face.FaceNormal.Z > -0.99:
                continue
            loops = []
            for loop in face.EdgeLoops:
                eds = []
                pts = []
                for edge in loop:
                    crv = edge.AsCurve()
                    p0, p1 = crv.GetEndPoint(0), crv.GetEndPoint(1)
                    curved = not isinstance(crv, DB.Line)
                    dx, dy = p1.X - p0.X, p1.Y - p0.Y
                    m = math.hypot(dx, dy)
                    d = (dx / m, dy / m) if m > 1e-9 else (0.0, 0.0)
                    eds.append(((p0.X, p0.Y), (p1.X, p1.Y), d,
                                edge.Reference, crv.Length, curved))
                    if curved:
                        for tp in crv.Tessellate():
                            pts.append((tp.X, tp.Y))
                    else:
                        pts.append((p0.X, p0.Y))
                if len(pts) >= 3:
                    loops.append((poly_area(pts), pts, eds))
            if not loops:
                continue
            loops.sort(key=lambda l: -l[0])
            outer = loops[0]
            result.append((outer[1], [l[1] for l in loops[1:]],
                           outer[2], [l[2] for l in loops[1:]]))
    return result


def frame_of(u):
    """(u, n) unit vectors from a direction."""
    m = math.hypot(u[0], u[1])
    ux, uy = u[0] / m, u[1] / m
    return (ux, uy), (-uy, ux)


def parallel(d1, d2, sin_tol=0.0087):
    return abs(d1[0] * d2[1] - d1[1] * d2[0]) <= sin_tol


def perpendicular(d1, d2, tol=0.0087):
    return abs(d1[0] * d2[0] + d1[1] * d2[1]) <= tol
