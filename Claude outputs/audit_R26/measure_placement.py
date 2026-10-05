# -*- coding: utf-8 -*-
"""Read-only: measure where hand-placed dims sit on soffit plans (paper inches).
Call from execute_revit_code:  OUT = r"...\placement_<tag>"; execfile(this)
Writes OUT + ".csv" (one row per dim) and OUT + ".md" (summary). Changes nothing."""
import io, math
from Autodesk.Revit import DB

NAME_HAS = globals().get("NAME_HAS", "SOFFIT")


def views():
    out = []
    for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan):
        if v.IsTemplate:
            continue
        if v.Name.upper().startswith("ZZ"):   # Claude test views hold auto dims, not hand dims
            continue
        if NAME_HAS.upper() in v.Name.upper():
            out.append(v)
    return out


def bip(el, name):
    try:
        p = el.get_Parameter(getattr(DB.BuiltInParameter, name))
        return p.AsDouble() if p else None
    except Exception:
        return None


def ref_points(ref, d, n):
    """Return (kind, list of XY points) for the referenced geometry, or None."""
    el = doc.GetElement(ref)
    if el is None:
        return None
    if isinstance(el, DB.Grid):
        return ("grid", [])
    kind = el.Category.Name if el.Category else "?"
    pts = []
    try:
        g = el.GetGeometryObjectFromReference(ref)
    except Exception:
        g = None
    try:
        if isinstance(g, DB.Edge):
            c = g.AsCurve(); pts = [c.GetEndPoint(0), c.GetEndPoint(1), c.Evaluate(0.5, True)]
        elif isinstance(g, DB.Face):
            bb = g.GetBoundingBox()
            for u in (bb.Min.U, (bb.Min.U + bb.Max.U) / 2, bb.Max.U):
                for v in (bb.Min.V, (bb.Min.V + bb.Max.V) / 2, bb.Max.V):
                    pts.append(g.Evaluate(DB.UV(u, v)))
        elif isinstance(g, DB.Curve):
            pts = [g.GetEndPoint(0), g.GetEndPoint(1), g.Evaluate(0.5, True)]
        elif isinstance(g, DB.Point):
            pts = [g.Coord]
    except Exception:
        pts = []
    if not pts:
        try:
            loc = el.Location
            if isinstance(loc, DB.LocationCurve):
                c = loc.Curve; pts = [c.GetEndPoint(0), c.GetEndPoint(1), c.Evaluate(0.5, True)]
            elif isinstance(loc, DB.LocationPoint):
                pts = [loc.Point]
            elif isinstance(el, DB.CurveElement):
                c = el.GeometryCurve; pts = [c.GetEndPoint(0), c.GetEndPoint(1), c.Evaluate(0.5, True)]
        except Exception:
            pts = []   # unbound curves (reference planes, grids-like): no object gap
    return (kind, pts)


def dot(p, v):
    return p.X * v.X + p.Y * v.Y


rows = []
seen = set()
for v in views():
    sc = float(v.Scale) or 96.0
    k = 12.0 / sc  # model ft -> paper inches
    for dim in DB.FilteredElementCollector(doc, v.Id).OfClass(DB.Dimension):
        did = str(dim.Id)
        if did in seen or dim.OwnerViewId != v.Id:
            continue
        seen.add(did)
        try:
            if dim.DimensionShape != DB.DimensionShape.Linear:
                continue
            ln = dim.Curve
            d = ln.Direction
        except Exception:
            continue
        if abs(d.Z) > 0.01:
            continue
        d = DB.XYZ(d.X, d.Y, 0).Normalize()
        n = DB.XYZ(-d.Y, d.X, 0)
        o = ln.Origin
        s_line = dot(o, n)
        # witness stations along d
        segs = list(dim.Segments) if dim.NumberOfSegments > 1 else [dim]
        st = []
        texts = []
        for sg in segs:
            val = sg.Value or 0.0
            c = dot(sg.Origin, d)
            st += [c - val / 2, c + val / 2]
            try:
                tp = sg.TextPosition
                texts.append((dot(tp, d) - c, dot(tp, n) - s_line, val, getattr(sg, "IsTextPositionAdjustable", lambda: True)()))
            except Exception:
                pass
        st = sorted(set(round(x, 4) for x in st))
        lo, hi = st[0], st[-1]
        # distance from dim line to referenced objects (non-grid), signed along n
        kinds = []
        gaps = []
        grids = 0
        for r in dim.References:
            rp = ref_points(r, d, n)
            if rp is None:
                continue
            kind, pts = rp
            kinds.append(kind)
            if kind == "grid":
                grids += 1
                continue
            # nearest point of that geometry to the dim line, measured along n
            best = None
            for p in pts:
                g = dot(p, n) - s_line
                if best is None or abs(g) < abs(best):
                    best = g
            if best is not None:
                gaps.append(best)
        gap = min(gaps, key=abs) if gaps else None
        far = max(gaps, key=abs) if gaps else None
        # text moved off the line? (along-line offset beyond the segment)
        moved = 0
        for (along, off, val, adj) in texts:
            if abs(along) > max(val / 2.0, 0.01) + 0.05:
                moved += 1
        dt = doc.GetElement(dim.GetTypeId())
        rows.append({
            "view": v.Name, "scale": sc, "id": did, "type": dt.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString() if dt else "",
            "ang": round(math.degrees(math.atan2(d.Y, d.X)) % 180.0, 1), "s_line": s_line, "lo": lo, "hi": hi,
            "nseg": len(segs), "nref": dim.References.Size, "grids": grids, "kinds": "/".join(sorted(set(kinds))),
            "stations": st, "gap_in": gap * k if gap is not None else None, "far_in": far * k if far is not None else None,
            "text_off_in": [round(t[1] * k, 3) for t in texts], "moved": moved, "k": k,
            "has_leader": int(bool(getattr(dim, "HasLeader", False))),
            "txt": (dim.Prefix or "") + "|" + (dim.Suffix or "") + "|" + (dim.Below or "") + "|" + (dim.ValueOverride or "") if dim.NumberOfSegments <= 1 else "",
        })

# --- neighbours: parallel dims whose spans overlap ---
by_ang = {}
for r in rows:
    by_ang.setdefault((r["view"], round(r["ang"] * 2) / 2.0), []).append(r)
for key, grp in by_ang.items():
    for r in grp:
        best = None
        base = 0
        for q in grp:
            if q is r:
                continue
            ov = min(r["hi"], q["hi"]) - max(r["lo"], q["lo"])
            if ov <= 0.01:
                continue
            sp = abs(q["s_line"] - r["s_line"]) * r["k"]
            if sp < 0.005:
                continue
            if best is None or sp < best:
                best = sp
            # stacked from a shared baseline: same end station, different other end
            if (abs(q["lo"] - r["lo"]) < 0.01 and abs(q["hi"] - r["hi"]) > 0.05) or \
               (abs(q["hi"] - r["hi"]) < 0.01 and abs(q["lo"] - r["lo"]) > 0.05):
                base += 1
        r["nn_in"] = best
        r["baseline_mates"] = base

# --- write ---
cols = ["view", "scale", "id", "type", "ang", "nseg", "nref", "grids", "kinds", "gap_in", "far_in", "nn_in",
        "baseline_mates", "moved", "has_leader", "text_off_in", "txt"]
with io.open(OUT + ".csv", "w", encoding="utf-8") as f:
    f.write(u",".join(cols) + u"\n")
    for r in rows:
        f.write(u",".join(u'"%s"' % unicode(r.get(c, "")).replace('"', "'") for c in cols) + u"\n")


def q(xs, p):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    i = (len(xs) - 1) * p
    a = int(math.floor(i)); b = min(a + 1, len(xs) - 1)
    return xs[a] + (xs[b] - xs[a]) * (i - a)


def hist(xs, edges):
    xs = [x for x in xs if x is not None]
    out = []
    for i in range(len(edges) - 1):
        out.append("%s-%s\": %d" % (edges[i], edges[i + 1], len([x for x in xs if edges[i] <= x < edges[i + 1]])))
    out.append(">%s\": %d" % (edges[-1], len([x for x in xs if x >= edges[-1]])))
    return " · ".join(out)


L = []
L.append("# Dim placement — %s" % doc.Title)
L.append("Views: %d soffit plans; dims measured: %d" % (len(set(r["view"] for r in rows)), len(rows)))
obj = [r for r in rows if r["gap_in"] is not None]
L.append("\n## Distance from dim line to the nearest dimensioned object (paper inches, non-grid refs)")
ag = [abs(r["gap_in"]) for r in obj]
L.append("n=%d · p10 %.3f · p25 %.3f · median %.3f · p75 %.3f · p90 %.3f" % (len(ag), q(ag, .1), q(ag, .25), q(ag, .5), q(ag, .75), q(ag, .9)) if ag else "none")
L.append(hist(ag, [0, 0.0625, 0.125, 0.25, 0.375, 0.5, 0.75, 1.0, 1.5, 2.0]))
L.append("\n## Spacing to the nearest parallel, overlapping dim (paper inches)")
nn = [r["nn_in"] for r in rows if r.get("nn_in")]
L.append("n=%d · p10 %.3f · p25 %.3f · median %.3f · p75 %.3f · p90 %.3f" % (len(nn), q(nn, .1), q(nn, .25), q(nn, .5), q(nn, .75), q(nn, .9)) if nn else "none")
L.append(hist(nn, [0, 0.0625, 0.125, 0.1875, 0.25, 0.3125, 0.375, 0.5, 0.75, 1.0]))
L.append("\n## Strings")
L.append("single-segment %d · chains (2+ segs) %d · median segs in chains %s · grid-only %d · dims with a grid ref %d" % (
    len([r for r in rows if r["nseg"] == 1]), len([r for r in rows if r["nseg"] > 1]),
    q([r["nseg"] for r in rows if r["nseg"] > 1], .5), len([r for r in rows if r["grids"] == r["nref"]]),
    len([r for r in rows if r["grids"] > 0])))
L.append("dims sharing an end with a parallel dim (stacked from one baseline): %d of %d" % (
    len([r for r in rows if r.get("baseline_mates")]), len(rows)))
L.append("\n## Text")
moved = [r for r in rows if r["moved"]]
L.append("dims with text pulled along the line: %d · with leader: %d" % (len(moved), len([r for r in rows if r["has_leader"]])))
offs = [abs(o) for r in rows for o in r["text_off_in"]]
L.append("text distance from dim line: median %.3f · p90 %.3f" % (q(offs, .5), q(offs, .9)) if offs else "")
sx = {}
for r in rows:
    for part in r["txt"].split("|"):
        if part.strip():
            sx[part.strip()] = sx.get(part.strip(), 0) + 1
L.append("prefix/suffix/below/override text: " + " · ".join("%s ×%d" % (k2, v2) for k2, v2 in sorted(sx.items(), key=lambda x: -x[1])[:25]))
L.append("\n## Dim types")
tc = {}
for r in rows:
    tc[r["type"]] = tc.get(r["type"], 0) + 1
for t, c in sorted(tc.items(), key=lambda x: -x[1])[:8]:
    dt = [e for e in DB.FilteredElementCollector(doc).OfClass(DB.DimensionType) if e.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == t]
    e = dt[0] if dt else None
    def pv(name):
        x = bip(e, name) if e else None
        return "%.4f\"" % (x * 12) if x is not None else "-"
    L.append("- %s ×%d · text size %s · witness gap %s · witness ext %s · dim line ext %s · text offset %s" % (
        t, c, pv("TEXT_SIZE"), pv("WITNS_LINE_GAP_TO_ELMT"), pv("WITNS_LINE_EXTENSION"), pv("DIM_LINE_EXTENSION"), pv("TEXT_DIST_TO_LINE")))
L.append("\n## Per view")
for vn in sorted(set(r["view"] for r in rows)):
    vr = [r for r in rows if r["view"] == vn]
    g = [abs(r["gap_in"]) for r in vr if r["gap_in"] is not None]
    s = [r["nn_in"] for r in vr if r.get("nn_in")]
    L.append("- %s (1/%d): %d dims · gap median %s · spacing median %s · chains %d · baseline-stacked %d" % (
        vn, vr[0]["scale"], len(vr), "%.3f" % q(g, .5) if g else "-", "%.3f" % q(s, .5) if s else "-",
        len([r for r in vr if r["nseg"] > 1]), len([r for r in vr if r.get("baseline_mates")])))
PLACEMENT_REPORT = "\n".join(L)
with io.open(OUT + ".md", "w", encoding="utf-8") as f:
    f.write(PLACEMENT_REPORT)
