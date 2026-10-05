# -*- coding: utf-8 -*-
"""Fit Grids decision logic - pure plan geometry, no Revit calls, so it
can be tested offline.

Rules (Adolfo, 2026-09-30):
1. Parallel grids stay aligned: one bubble line per family per side.
2. Where a grid leaves a VISIBLE hard slab edge, that side's line is set
   by the tightest bubble: the row sits where the bubble nearest the
   slab is exactly `margin` from it (true distance, so angled edges
   work). No bubble ever lands inside a visible slab.
3. Where the crop cuts the slab (no hard edge visible on that side) or
   the grid crosses no visible slab, the bubble sits `gap` just outside
   the crop edge.
4. Grids that don't cross the crop at all: bubbles hidden.
Everything is in plan feet."""
import math
import mcc_plan as P
import mcc_view as V

BIG = 1e9


def _dot(p, u):
    return p[0] * u[0] + p[1] * u[1]


def _slab_range(g0, u, polys):
    """Outermost crossings (t_lo, t_hi) of the grid line with the slab."""
    lo, hi = BIG, -BIG
    for poly in polys:
        r = V.line_range_in_poly(g0, u, poly)
        if r:
            lo, hi = min(lo, r[0]), max(hi, r[1])
    return (lo, hi) if lo < hi else None


def _clear(pt, vis, margin):
    """Bubble point is outside every visible slab and >= margin away."""
    for poly in vis:
        if P.point_in_poly(pt[0], pt[1], poly):
            return False
        if P.dist_point_poly_edges(pt, poly) < margin - 1e-6:
            return False
    return True


def fit(grids, slabs, crop, margin, gap, families):
    """grids: [(key, g0, u, end0, end1)] - u unit direction of the grid's
    view curve, end0/end1 its current ends (x, y).
    slabs: [poly] slab outer outlines. crop: poly or None.
    families: [[grid indexes]] of parallel grids.
    Returns {key: ("set", (x, y), (x, y)) | ("hide",)} - the two points in
    the grid's own End0 -> End1 order so bubbles stay on their ends."""
    out = {}
    if crop:
        hull = P.convex_hull(crop)
        vis = [c for c in (V.clip_convex(s, hull) for s in slabs)
               if len(c) >= 3 and abs(V.signed_area(c)) > 1e-3]
    else:
        vis = list(slabs)
    vis_pts = [p for poly in vis for p in poly]

    for fam in families:
        fu = grids[fam[0]][2]
        info = []                       # per grid in family
        for gi in fam:
            key, g0, u, e0, e1 = grids[gi]
            base = _dot(g0, fu)
            if crop:
                c = V.line_range_in_poly(g0, fu, crop)
                if c is None:
                    out[key] = ("hide",)
                    continue
                c = (base + c[0], base + c[1])
            else:
                c = (-BIG, BIG)
            sr = _slab_range(g0, fu, slabs)
            sr = (base + sr[0], base + sr[1]) if sr else None
            info.append((gi, base, c, sr))
        if not info:
            continue

        rows = {}
        for sg in (1, -1):              # +fu side, -fu side
            need_cut = -BIG             # rows in s' = sg * s
            hard = []                   # (gi, base, exit s')
            for gi, base, c, sr in info:
                c_side = max(sg * c[0], sg * c[1])
                c_in = min(sg * c[0], sg * c[1])
                if sr is None:
                    if crop:
                        need_cut = max(need_cut, c_side + gap)
                    continue
                s_out = max(sg * sr[0], sg * sr[1])
                s_in = min(sg * sr[0], sg * sr[1])
                visible = s_out > c_in and s_in < c_side
                if crop and (not visible or s_out >= c_side - 1e-6):
                    need_cut = max(need_cut, c_side + gap)   # crop cuts it
                else:
                    hard.append((gi, base, min(s_out, c_side)))
            R = need_cut
            if hard:
                lo = max(h[2] for h in hard)
                hi = max([sg * _dot(p, fu) for p in vis_pts] + [lo]) + margin

                def ok(r):
                    for gi, base, _ in hard:
                        g0 = grids[gi][1]
                        s = sg * r
                        pt = (g0[0] + fu[0] * (s - base),
                              g0[1] + fu[1] * (s - base))
                        if not _clear(pt, vis, margin):
                            return False
                    return True
                if not ok(hi):
                    hi += margin
                for _ in range(40):
                    mid = (lo + hi) / 2.0
                    if ok(mid):
                        hi = mid
                    else:
                        lo = mid
                R = max(R, hi)
            if R <= -BIG / 2:
                if vis_pts:
                    R = max(sg * _dot(p, fu) for p in vis_pts) + margin
                else:
                    R = None            # nothing to go on: keep this end
            rows[sg] = R

        for gi, base, c, sr in info:
            key, g0, u, e0, e1 = grids[gi]
            cur = sorted([_dot(e0, fu), _dot(e1, fu)])
            s_hi = rows[1] if rows[1] is not None else cur[1]
            s_lo = -rows[-1] if rows[-1] is not None else cur[0]
            if s_hi - s_lo < 0.5:
                continue
            a = (g0[0] + fu[0] * (s_lo - base), g0[1] + fu[1] * (s_lo - base))
            b = (g0[0] + fu[0] * (s_hi - base), g0[1] + fu[1] * (s_hi - base))
            out[key] = ("set", a, b) if _dot(u, fu) > 0 else ("set", b, a)
    return out
