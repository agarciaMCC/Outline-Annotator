# -*- coding: utf-8 -*-
"""Shared view helpers: which floors a soffit view shows, their plan
extent, and the straight grids in the view."""
from mcc_compat import make_eid
import math
from pyrevit import DB


def soffit_floors(doc, view, level_only=True):
    """Floors visible in the view. Soffit views look up, so the slab shown
    is usually hosted a level above the view; take the level most floors
    sit on. Returns (floors, level or None)."""
    visible = list(DB.FilteredElementCollector(doc, view.Id)
                   .OfClass(DB.Floor))
    if not visible or not level_only:
        return visible, None
    by_level = {}
    for f in visible:
        by_level.setdefault(eid_int(f.LevelId), []).append(f)
    lid = max(by_level, key=lambda k: len(by_level[k]))
    return by_level[lid], doc.GetElement(make_eid(lid))


def plan_extent(elements, view=None):
    """(xmin, ymin, xmax, ymax) of the elements' bounding boxes."""
    xs, ys = [], []
    for e in elements:
        bb = e.get_BoundingBox(view)
        if bb is None:
            continue
        xs += [bb.Min.X, bb.Max.X]
        ys += [bb.Min.Y, bb.Max.Y]
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def straight_grids(doc, view):
    """[(grid, (x0, y0), u, n)] for straight grids visible in the view,
    using the view-specific curve when there is one."""
    out = []
    for g in DB.FilteredElementCollector(doc, view.Id).OfClass(DB.Grid):
        c = view_curve(g, view)
        if not isinstance(c, DB.Line):
            continue
        d = c.Direction
        m = math.hypot(d.X, d.Y)
        if m < 1e-9:
            continue
        ux, uy = d.X / m, d.Y / m
        p0 = c.GetEndPoint(0)
        out.append((g, (p0.X, p0.Y), (ux, uy), (-uy, ux)))
    return out


def view_curve(grid, view):
    try:
        curves = grid.GetCurvesInView(DB.DatumExtentType.ViewSpecific, view)
        if curves and curves.Count:
            return curves[0]
    except Exception:
        pass
    return grid.Curve


def grid_families(grids, parallel_deg=0.5):
    """Group grid indexes by direction."""
    sin_tol = math.sin(math.radians(parallel_deg))
    fams = []
    for gi, (g, g0, u, n) in enumerate(grids):
        for fam in fams:
            fu = grids[fam[0]][2]
            if abs(u[0] * fu[1] - u[1] * fu[0]) <= sin_tol:
                fam.append(gi)
                break
        else:
            fams.append([gi])
    return fams


def type_name(e):
    p = e.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    return p.AsString() if p else e.Name


# ---------------- crop / polygon helpers (Fit Grids) ----------------
def eid_int(eid):
    """ElementId as an int on any Revit version (IntegerValue went away
    in 2026)."""
    try:
        return int(eid.Value)
    except Exception:
        return eid.IntegerValue


def signed_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return a / 2.0


def crop_polygon(view):
    """The view's active crop boundary as [(x, y)] model feet - plain,
    rotated or sketched - or None when the crop is off."""
    try:
        if not view.CropBoxActive:
            return None
    except Exception:
        return None
    best = None
    try:
        for loop in view.GetCropRegionShapeManager().GetCropShape():
            lp = []
            for c in loop:
                if isinstance(c, DB.Line):
                    p = c.GetEndPoint(0)
                    lp.append((p.X, p.Y))
                else:
                    tp = list(c.Tessellate())
                    lp.extend((q.X, q.Y) for q in tp[:-1])
            if len(lp) >= 3 and (best is None or
                                 abs(signed_area(lp)) > abs(signed_area(best))):
                best = lp
    except Exception:
        best = None
    if best:
        return best
    cb = view.CropBox
    t = cb.Transform
    out = []
    for x, y in ((cb.Min.X, cb.Min.Y), (cb.Max.X, cb.Min.Y),
                 (cb.Max.X, cb.Max.Y), (cb.Min.X, cb.Max.Y)):
        p = t.OfPoint(DB.XYZ(x, y, cb.Min.Z))
        out.append((p.X, p.Y))
    return out


def offset_polygon(pts, d):
    """Polygon moved inward by d (mitred corners). None if it collapses."""
    ccw = signed_area(pts) > 0
    lines = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy)
        if m < 1e-6:
            continue
        ux, uy = dx / m, dy / m
        nx, ny = (-uy, ux) if ccw else (uy, -ux)      # inward normal
        lines.append(((a[0] + nx * d, a[1] + ny * d), (ux, uy)))
    out = []
    for i in range(len(lines)):
        (p1, u1), (p2, u2) = lines[i - 1], lines[i]
        cr = u1[0] * u2[1] - u1[1] * u2[0]
        if abs(cr) < 1e-9:
            out.append(p2)
            continue
        wx, wy = p2[0] - p1[0], p2[1] - p1[1]
        s = (wx * u2[1] - wy * u2[0]) / cr
        out.append((p1[0] + s * u1[0], p1[1] + s * u1[1]))
    if len(out) < 3 or signed_area(out) * signed_area(pts) <= 0 or \
            abs(signed_area(out)) > abs(signed_area(pts)):
        return None
    # every edge must keep its direction, else the inset turned inside out
    for i in range(len(out)):
        a, b = out[i], out[(i + 1) % len(out)]
        u = lines[i][1]
        if (b[0] - a[0]) * u[0] + (b[1] - a[1]) * u[1] < -1e-9:
            return None
    return out


def line_range_in_poly(p0, u, poly):
    """(t_first, t_last) where the infinite line p0 + t*u crosses the
    polygon boundary, or None when it misses."""
    ts = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        cr = u[0] * ey - u[1] * ex
        wx, wy = a[0] - p0[0], a[1] - p0[1]
        if abs(cr) < 1e-9 * max(1.0, math.hypot(ex, ey)):
            # edge parallel to the line: counts when it lies ON the line
            # (a grid drawn on a slab edge)
            if abs(wx * u[1] - wy * u[0]) < 1e-4:
                ts.append(wx * u[0] + wy * u[1])
                ts.append((b[0] - p0[0]) * u[0] + (b[1] - p0[1]) * u[1])
            continue
        t = (wx * ey - wy * ex) / cr
        s = (wx * u[1] - wy * u[0]) / cr
        if -1e-9 <= s <= 1.0 + 1e-9:
            ts.append(t)
    if len(ts) < 2:
        return None
    return min(ts), max(ts)


def clip_convex(subject, clipper):
    """Sutherland-Hodgman: subject polygon clipped by a convex polygon."""
    if signed_area(clipper) < 0:
        clipper = list(reversed(clipper))
    out = list(subject)
    for i in range(len(clipper)):
        if not out:
            break
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]

        def inside(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - \
                (b[1] - a[1]) * (p[0] - a[0]) >= -1e-9

        def cut(p, q):
            x1, y1, x2, y2 = p[0], p[1], q[0], q[1]
            x3, y3, x4, y4 = a[0], a[1], b[0], b[1]
            den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if abs(den) < 1e-12:
                return q
            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
            return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
        inp, out = out, []
        for j in range(len(inp)):
            p, q = inp[j - 1], inp[j]
            if inside(q):
                if not inside(p):
                    out.append(cut(p, q))
                out.append(q)
            elif inside(p):
                out.append(cut(p, q))
    return out
