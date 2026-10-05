# -*- coding: utf-8 -*-
"""Columns from PDF - Revit-independent helpers (IronPython 2.7 and CPython):
align the sheet to the grids already in the model, and work out each
column's model position, rotation and type size."""
import json
import math


def load(path):
    with open(path) as fh:
        return json.load(fh)


def _inter(p, u, q, v):
    d = u[0] * v[1] - u[1] * v[0]
    if abs(d) < 1e-9:
        return None
    t = ((q[0] - p[0]) * v[1] - (q[1] - p[1]) * v[0]) / d
    return (p[0] + t * u[0], p[1] + t * u[1])


def sheet_lines(res):
    """label -> (point, direction) of each grid in sheet feet."""
    out = {}
    for g in res['grids']:
        t, n = g['t'], g['n']
        a = g['along'][0]
        out[g['label']] = ((a * t[0] + g['pos'] * n[0], a * t[1] + g['pos'] * n[1]), (t[0], t[1]))
    return out


def fit(sheet, model, min_angle=20.0):
    """sheet/model: label -> (point, dir). Rigid 2D fit on the intersections of
    every non-parallel pair of grids both have. Returns (rot_rad, (tx, ty),
    rms_ft, n_points) or None."""
    common = sorted(k for k in sheet if k in model)
    S, M = [], []
    for i in range(len(common)):
        for j in range(i + 1, len(common)):
            a, b = common[i], common[j]
            (p1, u1), (p2, u2) = sheet[a], sheet[b]
            ang = math.degrees(math.acos(min(1.0, abs(u1[0] * u2[0] + u1[1] * u2[1]))))
            if ang < min_angle:
                continue
            s = _inter(p1, u1, p2, u2)
            m = _inter(model[a][0], model[a][1], model[b][0], model[b][1])
            if s and m:
                S.append(s)
                M.append(m)
    if len(S) < 2:
        return None
    cs = (sum(p[0] for p in S) / len(S), sum(p[1] for p in S) / len(S))
    cm = (sum(p[0] for p in M) / len(M), sum(p[1] for p in M) / len(M))
    num = den = 0.0
    for s, m in zip(S, M):
        sx, sy = s[0] - cs[0], s[1] - cs[1]
        mx, my = m[0] - cm[0], m[1] - cm[1]
        num += sx * my - sy * mx
        den += sx * mx + sy * my
    th = math.atan2(num, den)
    c, s_ = math.cos(th), math.sin(th)
    tx = cm[0] - (cs[0] * c - cs[1] * s_)
    ty = cm[1] - (cs[0] * s_ + cs[1] * c)
    err = 0.0
    for s, m in zip(S, M):
        x, y = s[0] * c - s[1] * s_ + tx, s[0] * s_ + s[1] * c + ty
        err += (x - m[0]) ** 2 + (y - m[1]) ** 2
    return th, (tx, ty), math.sqrt(err / len(S)), len(S)


def apply(T, p):
    th, (tx, ty) = T[0], T[1]
    c, s = math.cos(th), math.sin(th)
    return (p[0] * c - p[1] * s + tx, p[0] * s + p[1] * c + ty)


def rotate(T, v):
    c, s = math.cos(T[0]), math.sin(T[0])
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def placement(col, T):
    """Model point and rotation (radians, about Z) that put the family's
    Width (local X) along the drawn side matching the schedule W."""
    pt = apply(T, col['center'])
    u = rotate(T, col['u'])
    size = col.get('size') or []
    a, b = col['drawn']                    # inches along u, along n
    ang = math.atan2(u[1], u[0])
    if len(size) == 2:
        W = size[0]
        if abs(b - W) + 0.5 < abs(a - W):   # W runs along n
            ang += math.pi / 2
    # keep within (-90, 90] so text/labels read sensibly
    while ang > math.pi / 2:
        ang -= math.pi
    while ang <= -math.pi / 2:
        ang += math.pi
    return pt, ang


def type_name(family, size):
    if family == 'circular':
        return '%d DIA COL' % size[0]
    return '%dX%d COL' % (size[0], size[1])


def group_by_mark(res):
    """[dict(mark, size, detail, family, count, flags)] for the review list;
    each flag text lists the #numbers of the columns it applies to (the same
    numbers are circled on the check PDF)."""
    import re
    g = {}
    for c in res['columns']:
        k = c['mark']
        e = g.setdefault(k, dict(mark=k, size=c.get('size'), detail=c.get('detail'),
                                 family=c['family'], count=0, notes={}, order=[]))
        e['count'] += 1
        for f in c['flags']:
            if f not in e['notes']:
                e['notes'][f] = []
                e['order'].append(f)
            if c.get('ref'):
                e['notes'][f].append(c['ref'])
    for e in g.values():
        e['flags'] = ['%s (%s)' % (f, ', '.join('#%d' % r for r in sorted(e['notes'][f])))
                      if e['notes'][f] else f for f in e['order']]

    def key(m):
        mm = re.match(r'([A-Z]+)(\d+)', m)
        return (mm.group(1), int(mm.group(2))) if mm else (m, 0)
    return [g[k] for k in sorted(g, key=key)]


def center_dims(center, ang, half_x, half_y, grids, gap, max_dist=60.0):
    """Check dimensions from a column centre to the nearest grid in each of
    the column's two directions.
    center: (x, y); ang: column rotation (rad, family local X direction);
    half_x / half_y: half the column size along local X / Y (ft);
    grids: [(name, (px, py), (gx, gy))] model lines; gap: clearance (ft)
    between the column face and the dimension line.
    Returns [(grid name, 'LR' | 'FB', (x0, y0), (x1, y1))]:
      LR = column's Center (Left/Right) plane (normal = local X),
      FB = Center (Front/Back) plane (normal = local Y);
    the dimension line runs from the grid to the centre, beside the column."""
    X = (math.cos(ang), math.sin(ang))
    Y = (-X[1], X[0])
    tol = math.cos(math.radians(1.0))
    best = {}
    for name, p, g in grids:
        L = math.hypot(g[0], g[1])
        g = (g[0] / L, g[1] / L)
        if abs(g[0] * Y[0] + g[1] * Y[1]) > tol:      # grid runs along local Y
            which, along_half = 'LR', half_y
        elif abs(g[0] * X[0] + g[1] * X[1]) > tol:    # grid runs along local X
            which, along_half = 'FB', half_x
        else:
            continue
        m = (-g[1], g[0])
        d = (center[0] - p[0]) * m[0] + (center[1] - p[1]) * m[1]
        if abs(d) > max_dist:
            continue
        if which not in best or abs(d) < abs(best[which][0]):
            best[which] = (d, name, g, m, along_half)
    out = []
    for which, (d, name, g, m, along_half) in sorted(best.items()):
        if abs(d) < 1 / 64.0:          # centred on the grid - nothing to check
            continue
        o = along_half + gap
        foot = (center[0] - d * m[0], center[1] - d * m[1])
        a = (foot[0] + g[0] * o, foot[1] + g[1] * o)
        b = (center[0] + g[0] * o, center[1] + g[1] * o)
        out.append((name, which, a, b))
    return out


def snap_angle(center, ang, grids, tol_deg=3.0, max_dist=80.0):
    """Square a column to the grids around it: of the grids running within
    tol_deg of either column axis, take the one nearest the column and turn
    the column onto its direction (keeping which axis is which).
    grids: [(name, (px, py), (gx, gy))]. Returns (angle, grid name or None,
    change in degrees)."""
    best = None
    for name, p, g in grids:
        L = math.hypot(g[0], g[1])
        ga = math.atan2(g[1] / L, g[0] / L)
        # difference folded to (-45, 45] deg: parallel to either column axis
        d = (ang - ga) % (math.pi / 2)
        if d > math.pi / 4:
            d -= math.pi / 2
        if abs(math.degrees(d)) > tol_deg:
            continue
        m = (-g[1] / L, g[0] / L)
        dist = abs((center[0] - p[0]) * m[0] + (center[1] - p[1]) * m[1])
        if dist > max_dist:
            continue
        if best is None or dist < best[0]:
            best = (dist, name, d)
    if best is None:
        return ang, None, 0.0
    return ang - best[2], best[1], math.degrees(best[2])
