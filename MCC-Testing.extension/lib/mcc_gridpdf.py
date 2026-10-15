# -*- coding: utf-8 -*-
"""Grids from PDF - Revit-independent helpers (IronPython 2.7 and CPython).

Reads the result written by pdfgrids/detect.py, applies the user's picks
for conflicts, and turns the grid chains into model-space lines."""
import json
import math


def load(path):
    with open(path) as fh:
        return json.load(fh)


def ftin(ft):
    s = '-' if ft < 0 else ''
    tot = round(abs(ft) * 96) / 8.0
    f = int(tot // 12)
    i = tot - 12 * f
    whole = int(i)
    frac = int(round((i - whole) * 8))
    fr = ''
    if frac:
        n, d = frac, 8
        while n % 2 == 0:
            n, d = n // 2, d // 2
        fr = ' %d/%d' % (n, d)
    return '%s%d\'-%d%s"' % (s, f, whole, fr)


def natural(lab):
    try:
        return (0, float(lab), '')
    except ValueError:
        return (1, len(lab), lab)


def conflicts(res):
    """[(key, description, [option labels])] - every item the user must pick."""
    out = []
    for fi, F in enumerate(res['families']):
        P = F['placement']
        if P['conflict']:
            out.append((('place', fi), 'Grids %s ... (%g deg) - position'
                        % (', '.join(g['label'] for g in F['grids'][:3]), F['angle']),
                        ['%s' % o['sheet'] for o in P['options']], P.get('note', '')))
        for gi, G in enumerate(F['gaps']):
            if G['conflict']:
                a, b = sorted([G['a'], G['b']], key=natural)
                out.append((('gap', fi, gi), 'Grid %s to %s' % (a, b),
                            ['%s: %s' % (o['sheet'], o['text']) for o in G['options']],
                            G.get('note', '')))
    return out


def build(res, picks):
    """picks: {key: option index} for every conflict. Returns grids:
    dict(label, angle, pos, along=[a0, a1], t, n, flags, sheets)."""
    grids = []
    for fi, F in enumerate(res['families']):
        P = F['placement']
        pi = picks.get(('place', fi), P['choice']) if P['conflict'] else None
        p0 = P['options'][pi]['p0'] if pi is not None else P['p0']
        pos = p0
        for k, g in enumerate(F['grids']):
            if k:
                G = F['gaps'][k - 1]
                ci = picks.get(('gap', fi, k - 1), G['choice']) if G['conflict'] else G['choice']
                if ci is None:
                    raise ValueError('no pick for gap %s-%s' % (G['a'], G['b']))
                pos += G['options'][ci]['value']
            grids.append(dict(label=g['label'], angle=F['angle'], pos=pos, along=g['along'],
                              t=F['t'], n=F['n'], flags=list(g['flags']), sheets=g['sheets']))
    return grids


def endpoints(g):
    t, n, p = g['t'], g['n'], g['pos']
    return [(a * t[0] + p * n[0], a * t[1] + p * n[1]) for a in g['along']]


def even_ends(grids):
    """Stretch every grid of a family to the family's overall extents."""
    lo, hi = {}, {}
    for g in grids:
        k = g['angle']
        lo[k] = min(lo.get(k, 1e9), g['along'][0])
        hi[k] = max(hi.get(k, -1e9), g['along'][1])
    for g in grids:
        g['along'] = [lo[g['angle']], hi[g['angle']]]


def intersection(g1, g2):
    """Sheet-space intersection of two grids (None if parallel)."""
    (x1, y1), (x2, y2) = endpoints(g1)
    (x3, y3), (x4, y4) = endpoints(g2)
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(d) < 1e-9:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / d
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def to_model(grids, ref, target, rot_deg):
    """Move sheet point `ref` to model point `target`, rotating rot_deg
    (counter-clockwise) about it. Returns [(grid, (x0,y0), (x1,y1))]."""
    th = math.radians(rot_deg)
    c, s = math.cos(th), math.sin(th)
    out = []
    for g in grids:
        pts = []
        for x, y in endpoints(g):
            dx, dy = x - ref[0], y - ref[1]
            pts.append((target[0] + dx * c - dy * s, target[1] + dx * s + dy * c))
        out.append((g, pts[0], pts[1]))
    return out


def default_origin(grids):
    """Pick the two grids for the placement point: the lowest numeric grid
    and the lowest lettered grid that cross (e.g. 1 / A or 1 / AA)."""
    def key(lab):
        try:
            return (0, float(lab))
        except ValueError:
            return (1, len(lab), lab)
    num = sorted((g for g in grids if key(g['label'])[0] == 0), key=lambda g: key(g['label']))
    let = sorted((g for g in grids if key(g['label'])[0] == 1), key=lambda g: key(g['label']))
    for a in num[:1]:
        def skew(b):
            return abs(90 - abs(((a['angle'] - b['angle'] + 90) % 180) - 90))
        cross = [b for b in let if skew(b) < 85]
        if cross:
            best = min(skew(b) for b in cross)
            b = [b for b in cross if skew(b) - best < 0.5][0]
            return a['label'], b['label']
    if len(grids) > 1:
        return grids[0]['label'], grids[-1]['label']
    return None, None


def spacing_rows(res, picks):
    """Rows for the spacing report: (from, to, value text, source)."""
    rows = []
    for fi, F in enumerate(res['families']):
        for gi, G in enumerate(F['gaps']):
            ci = picks.get(('gap', fi, gi), G['choice']) if G['conflict'] else G['choice']
            o = G['options'][ci] if ci is not None else None
            rows.append((G['a'], G['b'], o['text'] if o else '?', o['sheet'] if o else '',
                         G.get('note', '')))
    return rows


def dim_layout(lines, rot_deg, inset, min_span=0.5):
    """Dimension strings for created grids, one per grid family near EACH end,
    `inset` (model ft) in from the family's grid ends - just inside the bubbles.
    lines: [(grid dict, (x0,y0), (x1,y1), key)] in model XY.
    Returns [(keys in order, (x0,y0), (x1,y1))] - dim line endpoints."""
    th = math.radians(rot_deg)
    c, s = math.cos(th), math.sin(th)
    fams = {}
    for g, p0, p1, key in lines:
        fams.setdefault(g['angle'], []).append((g, p0, p1, key))
    jobs = []
    for ang, items in fams.items():
        if len(items) < 2:
            continue
        t = items[0][0]['t']
        u = (t[0] * c - t[1] * s, t[0] * s + t[1] * c)
        n = (-u[1], u[0])
        O = items[0][1]
        rows = []
        smin, smax = 1e18, -1e18
        for g, p0, p1, key in items:
            sa = (p0[0] - O[0]) * u[0] + (p0[1] - O[1]) * u[1]
            sb = (p1[0] - O[0]) * u[0] + (p1[1] - O[1]) * u[1]
            smin, smax = min(smin, sa, sb), max(smax, sa, sb)
            off = (p0[0] - O[0]) * n[0] + (p0[1] - O[1]) * n[1]
            rows.append((off, key))
        rows.sort()
        keep = []
        for off, key in rows:
            if keep and off - keep[-1][0] < min_span:
                continue
            keep.append((off, key))
        if len(keep) < 2 or smax - smin < 2 * inset:
            continue
        lo, hi = keep[0][0], keep[-1][0]
        for st in (smin + inset, smax - inset):
            px, py = O[0] + u[0] * st, O[1] + u[1] * st
            jobs.append(([k for o, k in keep], (px + n[0] * lo, py + n[1] * lo),
                         (px + n[0] * hi, py + n[1] * hi)))
    return jobs
