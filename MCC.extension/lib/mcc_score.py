# -*- coding: utf-8 -*-
"""Geometric dimension signatures for scoring auto-dims against hand dims.

A linear dimension is reduced to its direction (angle mod 180) and the
positions of its witness lines along that direction ("stations"), each
tagged with the kind of thing it touches (grid, slab, beam, ...). Two dims
match when they are parallel and their stations coincide - regardless of
whether Revit stores the reference as a face or an edge, or which element
copy it points at. Read-only."""
import math
from pyrevit import DB
from mcc_compat import eid_int

ANG_TOL = 0.5           # degrees
STA_TOL = 1.0 / 24      # ft (1/2")


def kind_of(e):
    if e is None:
        return "?"
    if isinstance(e, DB.Grid):
        return "grid"
    if isinstance(e, DB.Floor):
        return "slab"
    try:
        cn = e.Category.Name
    except Exception:
        return "?"
    if cn == "Detail Items":
        try:
            fam = e.Symbol.Family.Name
            if "CJ" in fam.upper() or fam == "Large Scale":
                return "cj"
        except Exception:
            pass
        return "detail"
    return {"Walls": "wall", "Structural Framing": "beam",
            "Structural Columns": "column", "Columns": "column",
            "Shaft Openings": "opening", "Generic Models": "generic",
            "Lines": "line"}.get(cn, cn.lower())


def _dir(dim):
    try:
        c = dim.Curve
        d = c.Direction
    except Exception:
        return None
    d = DB.XYZ(d.X, d.Y, 0)
    if d.GetLength() < 1e-9:
        return None
    d = d.Normalize()
    if d.Y < -1e-9 or (abs(d.Y) <= 1e-9 and d.X < 0):
        d = d.Negate()
    return d


def _dim_stations(dim, d):
    out = []
    try:
        segs = list(dim.Segments) if dim.NumberOfSegments > 1 else [dim]
        for sg in segs:
            v = sg.Value
            if v is None:
                continue
            s = d.DotProduct(sg.Origin)
            out += [s - v / 2.0, s + v / 2.0]
    except Exception:
        return []
    out.sort()
    ded = []
    for s in out:
        if not ded or abs(s - ded[-1]) > STA_TOL:
            ded.append(s)
    return ded


def _ref_station(doc, ref, e, d):
    """Station of one reference, from its geometry; None if unknown."""
    try:
        if isinstance(e, DB.Grid):
            return d.DotProduct(e.Curve.GetEndPoint(0))
        g = e.GetGeometryObjectFromReference(ref)
        if isinstance(g, DB.PlanarFace):
            return d.DotProduct(g.Origin)
        if isinstance(g, DB.Edge):
            return d.DotProduct(g.AsCurve().GetEndPoint(0))
        if isinstance(g, DB.Curve):
            return d.DotProduct(g.GetEndPoint(0))
    except Exception:
        pass
    try:
        loc = e.Location
        if isinstance(loc, DB.LocationCurve):
            return d.DotProduct(loc.Curve.GetEndPoint(0))
    except Exception:
        pass
    return None


def signature(doc, dim):
    """dict(id, ang, stations=[(s, kind)], cat, kinds, vals) or None."""
    d = _dir(dim)
    if d is None:
        return None
    sts = _dim_stations(dim, d)
    if len(sts) < 2:
        return None
    refs = []
    for r in dim.References:
        e = doc.GetElement(r.ElementId)
        refs.append((kind_of(e), _ref_station(doc, r, e, d)))
    kinds = [None] * len(sts)
    left = []
    for k, s in refs:                      # snap located refs to stations
        if s is None:
            left.append(k)
            continue
        i = min(range(len(sts)), key=lambda j: abs(sts[j] - s))
        if abs(sts[i] - s) < 0.5 and kinds[i] is None:
            kinds[i] = k
        else:
            left.append(k)
    for i in range(len(sts)):              # the rest in order
        if kinds[i] is None:
            kinds[i] = left.pop(0) if left else "?"
    ang = math.degrees(math.atan2(d.Y, d.X)) % 180.0
    try:
        vals = " | ".join((sg.ValueString or "") for sg in
                          (list(dim.Segments) if dim.NumberOfSegments > 1 else [dim]))
    except Exception:
        vals = ""
    ks = set(kinds)
    cat = next((c for c in ("beam", "opening", "slab", "wall", "column", "cj",
                            "detail", "generic") if c in ks),
               "grid" if ks == {"grid"} else "other")
    return {"id": eid_int(dim.Id), "ang": ang, "stations": list(zip(sts, kinds)),
            "cat": cat, "kinds": " > ".join(kinds), "vals": vals}


def view_signatures(doc, view, is_dim=None):
    out = []
    for dim in DB.FilteredElementCollector(doc, view.Id).OfClass(DB.Dimension):
        if is_dim and not is_dim(dim):
            continue
        s = signature(doc, dim)
        if s:
            out.append(s)
    return out


def _parallel(a, b):
    x = abs(a["ang"] - b["ang"]) % 180.0
    return min(x, 180.0 - x) <= ANG_TOL


def _has(stations, s):
    return any(abs(t - s) <= STA_TOL for t, _ in stations)


def exact(a, b):
    return _parallel(a, b) and len(a["stations"]) == len(b["stations"]) and \
        all(_has(b["stations"], s) for s, _ in a["stations"])


def object_hit(a, b):
    """b measures a's object stations (non-grid), anchor may differ."""
    if not _parallel(a, b):
        return False
    obj = [s for s, k in a["stations"] if k != "grid"] or [s for s, _ in a["stations"]]
    return all(_has(b["stations"], s) for s in obj)


def score(ref_sigs, test_sigs):
    """-> rows per category, missed (ref with no counterpart), extra."""
    def best(a, pool):
        if any(exact(a, b) for b in pool):
            return "exact"
        if any(object_hit(a, b) or object_hit(b, a) for b in pool):
            return "object"
        return None
    rm = [(s, best(s, test_sigs)) for s in ref_sigs]
    tm = [(s, best(s, ref_sigs)) for s in test_sigs]
    cats = sorted(set(s["cat"] for s in ref_sigs + test_sigs))
    rows = []
    for c in cats:
        r = [m for s, m in rm if s["cat"] == c]
        t = [m for s, m in tm if s["cat"] == c]
        pct = lambda xs, ok: "{}%".format(100 * sum(1 for m in xs if m in ok) // len(xs)) if xs else "-"
        rows.append([c, len(r), len(t), pct(r, ("exact",)), pct(r, ("exact", "object")),
                     pct(t, ("exact",)), pct(t, ("exact", "object"))])
    tot_r = [m for _, m in rm]; tot_t = [m for _, m in tm]
    pct = lambda xs, ok: "{}%".format(100 * sum(1 for m in xs if m in ok) // len(xs)) if xs else "-"
    rows.append(["ALL", len(tot_r), len(tot_t), pct(tot_r, ("exact",)), pct(tot_r, ("exact", "object")),
                 pct(tot_t, ("exact",)), pct(tot_t, ("exact", "object"))])
    missed = [s for s, m in rm if m is None]
    extra = [s for s, m in tm if m is None]
    return rows, missed, extra
