# -*- coding: utf-8 -*-
"""Reads the HAND-PLACED dimensions in one or more plan views and reports
how they were done: what each string references (grid, wall face, beam
face, slab edge, opening edge, column ...), in which grid direction, how
far the dim line sits from the things it locates, whether it sits inside
or outside the slab, and the reference pattern of each string
(e.g. grid > opening > opening). Read-only - changes nothing.

Use it on finished sheets (1.3.0 / 1.3.1 ...) to turn the detailers'
habits into numbers the auto-dim buttons can be tuned and scored against.
Writes a CSV (one row per reference) and prints summary tables."""
__title__ = "Audit\nDims"
__author__ = "MCC ENG"

from mcc_compat import eid_int
import io
import math
from collections import OrderedDict
from pyrevit import revit, DB, forms, script
import mcc_view as V
import mcc_plan as P
from mcc_dim import is_dim

doc = revit.doc
out = script.get_output()

# =====================================================================
# CONFIG
# =====================================================================
STATION_TOL = 0.15      # ft; a slab edge / face is "the one referenced"
                        # when it sits within this of the witness station
MIN_DIM_VALUE = 1.0 / 96
# =====================================================================


# ---------------- pick views ----------------
def plan_views_with_dims():
    vs = []
    for v in DB.FilteredElementCollector(doc).OfClass(DB.View):
        if v.IsTemplate or not isinstance(v, DB.ViewPlan):
            continue
        n = DB.FilteredElementCollector(doc, v.Id).OfClass(DB.Dimension) \
            .GetElementCount()
        if n:
            vs.append((v, n))
    return sorted(vs, key=lambda t: t[0].Name)


cands = plan_views_with_dims()
if not cands:
    forms.alert("No plan views with dimensions in this model.",
                exitscript=True)
active = doc.ActiveView
labels = OrderedDict()
for v, n in cands:
    sheet = ""
    try:
        sn = v.get_Parameter(DB.BuiltInParameter.VIEWPORT_SHEET_NUMBER)
        sheet = sn.AsString() if sn and sn.AsString() else ""
    except Exception:
        pass
    labels["{}{}  [{} dims]".format(
        v.Name, "  (sheet {})".format(sheet) if sheet else "", n)] = v
picked = forms.SelectFromList.show(
    list(labels.keys()), multiselect=True, title="Audit dimensions in ...",
    button_name="Audit") if len(labels) > 1 else list(labels.keys())
if not picked:
    script.exit()
views = [labels[k] for k in picked]

opts = DB.Options()
opts.ComputeReferences = True
opts.IncludeNonVisibleObjects = False


def cat_name(e):
    try:
        return e.Category.Name if e and e.Category else type(e).__name__
    except Exception:
        return "?"


def fam_label(grids, fam):
    names = sorted(grids[gi][0].Name for gi in fam)
    if len(names) <= 2:
        return "/".join(names)
    return "{}..{}".format(names[0], names[-1])


try:
    _text = unicode          # IronPython 2.7
except NameError:            # CPython 3 engine
    _text = str


def fmt(v):
    if v is None:
        return u""
    if isinstance(v, float):
        return u"{:.3f}".format(v)
    return _text(v)


def ftin(v):
    if v is None:
        return ""
    ft = int(v)
    inch = (v - ft) * 12.0
    return "{}'-{:.1f}\"".format(ft, inch)


rows = []
COLS = ["view", "dim_id", "dim_type", "segments", "zone", "pattern",
        "anchor", "ref_index", "ref_kind", "ref_element", "ref_id",
        "witness_station_ft", "standoff_ft", "dim_inside_slab",
        "dim_len_ft", "values", "overrides"]

summary = {}   # view name -> dict of counters


def bump(store, key, sub=None, val=1):
    if sub is None:
        store[key] = store.get(key, 0) + val
    else:
        store.setdefault(key, {})
        store[key][sub] = store[key].get(sub, 0) + val


def median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2.0


for view in views:
    grids = V.straight_grids(doc, view)
    fams = V.grid_families(grids)
    floors, level = V.soffit_floors(doc, view)
    # slab loops: (outer_poly, inner_polys, outer_edges, inner_edges, floor)
    loops = []
    for fl in floors:
        for outer, inners, oe, ie in P.soffit_loops(fl, opts):
            loops.append((outer, inners, oe, ie, eid_int(fl.Id)))
    outline_cache = {}

    def outline(e):
        k = eid_int(e.Id)
        if k not in outline_cache:
            outline_cache[k] = P.plan_poly(e, opts, view)
        return outline_cache[k]

    dims = [d for d in DB.FilteredElementCollector(doc, view.Id)
            .OfClass(DB.Dimension) if is_dim(d)]
    S = summary.setdefault(view.Name, {
        "dims": 0, "strings": 0, "singles": 0, "pattern": {}, "zone": {},
        "kind": {}, "anchor_by_kind": {}, "standoff": {}, "inside": 0,
        "outside": 0, "overrides": 0, "unresolved": 0})

    for dim in dims:
        crv = dim.Curve
        if not isinstance(crv, DB.Line):
            continue
        d = crv.Direction
        dm = math.hypot(d.X, d.Y)
        if dm < 1e-9:
            continue                          # vertical dim line (not plan)
        d = (d.X / dm, d.Y / dm)
        n = (-d[1], d[0])
        o = crv.Origin
        o = (o.X, o.Y)

        def along(p):
            return (p[0] - o[0]) * d[0] + (p[1] - o[1]) * d[1]

        def across(p):
            return (p[0] - o[0]) * n[0] + (p[1] - o[1]) * n[1]

        segs = list(dim.Segments) if dim.NumberOfSegments > 1 else [dim]
        S["dims"] += 1
        if len(segs) > 1:
            S["strings"] += 1
        else:
            S["singles"] += 1
        # witness stations along the line from segment origins + values
        stations = []
        values = []
        overrides = 0
        ok = True
        for sg in segs:
            try:
                v = sg.Value
                so = sg.Origin
            except Exception:
                ok = False
                break
            if v is None:
                ok = False
                break
            mid = along((so.X, so.Y))
            if not stations:
                stations.append(mid - v / 2.0)
            stations.append(mid + v / 2.0)
            try:
                values.append(sg.ValueString or "")
            except Exception:
                values.append("")
            try:
                if (sg.ValueOverride or sg.Prefix or sg.Suffix or sg.Above
                        or sg.Below):
                    overrides += 1
            except Exception:
                pass
        if overrides:
            S["overrides"] += 1
        refs = list(dim.References)
        if not ok or len(refs) != len(stations):
            # fall back: spread references evenly (still record them)
            stations = [None] * len(refs)
            S["unresolved"] += 1
        # dims measure ALONG d, i.e. across the grids whose direction is
        # perpendicular to d -> that family is the string's "zone"
        zone = ""
        for fam in fams:
            u = grids[fam[0]][2]
            if P.perpendicular(u, d):
                zone = fam_label(grids, fam)
                break
        if not zone:
            zone = "(no grid family)"
        bump(S, "zone", zone)
        # dim line inside the slab?
        # Dimension.Curve is an UNBOUND line: its extent comes from the
        # witness stations, not from end points
        known = [s for s in stations if s is not None]
        if known:
            s_lo, s_hi = min(known), max(known)
        else:
            s_lo, s_hi = 0.0, 0.0
        dim_len = s_hi - s_lo
        s_mid = (s_lo + s_hi) / 2.0
        mid_pt = (o[0] + d[0] * s_mid, o[1] + d[1] * s_mid)
        inside = False
        for outer, inners, oe, ie, fid in loops:
            if P.point_in_poly(mid_pt[0], mid_pt[1], outer) and not any(
                    P.point_in_poly(mid_pt[0], mid_pt[1], q) for q in inners):
                inside = True
                break
        S["inside" if inside else "outside"] += 1

        ref_rows = []
        for i, ref in enumerate(refs):
            st = stations[i]
            e = None
            try:
                e = doc.GetElement(ref.ElementId)
            except Exception:
                pass
            kind, label, standoff = "?", "", None
            if e is None:
                kind = "linked/unknown"
            elif isinstance(e, DB.Grid):
                kind, label = "grid", e.Name
            else:
                cn = cat_name(e)
                if isinstance(e, DB.Floor):
                    # which slab edge? one parallel to n at this station
                    best = None
                    for outer, inners, oe, ie, fid in loops:
                        if fid != eid_int(e.Id):
                            continue
                        for which, edges in (("slab edge", oe),) + tuple(
                                ("opening edge", x) for x in ie):
                            for p0, p1, ed, r, ln, curved in edges:
                                if curved or not P.parallel(ed, n):
                                    continue
                                s0 = along(p0)
                                if st is not None and abs(s0 - st) > STATION_TOL:
                                    continue
                                a0, a1 = across(p0), across(p1)
                                so_ = 0.0 if a0 * a1 <= 0 else min(abs(a0), abs(a1))
                                if best is None or so_ < best[1]:
                                    best = (which, so_)
                    if best:
                        kind, standoff = best
                    else:
                        kind = "slab (edge not matched)"
                    label = "floor {}".format(eid_int(e.Id))
                else:
                    if cn == "Walls":
                        kind = "wall face"
                    elif cn == "Structural Framing":
                        kind = "beam face"
                    elif cn in ("Structural Columns", "Columns"):
                        kind = "column face"
                    else:
                        kind = cn.lower()
                    try:
                        label = "{} : {}".format(
                            cn, V.type_name(doc.GetElement(e.GetTypeId())))
                    except Exception:
                        label = cn
                    poly = outline(e)
                    if poly:
                        near = [abs(across(p)) for p in poly
                                if st is None or abs(along(p) - st) < 0.5]
                        if not near:
                            near = [abs(across(p)) for p in poly]
                        standoff = min(near)
            bump(S, "kind", kind)
            if standoff is not None and kind != "grid":
                S["standoff"].setdefault(kind, []).append(standoff)
            ref_rows.append((i, kind, label, eid_int(e.Id) if e else "",
                             st, standoff))
        kinds = [r[1] for r in ref_rows]
        pattern = " > ".join(k.replace(" face", "").replace(" edge", "")
                             for k in kinds)
        bump(S, "pattern", pattern)
        grid_refs = [r[2] for r in ref_rows if r[1] == "grid"]
        if grid_refs:
            anchor = "grid " + "/".join(grid_refs)
            anchor_kind = "grid"
        else:
            anchor_kind = kinds[0] if kinds else "?"
            anchor = anchor_kind
        for k in set(kinds):
            if k != "grid":
                bump(S["anchor_by_kind"], k, anchor_kind)
        for i, kind, label, eid, st, standoff in ref_rows:
            rows.append([view.Name, eid_int(dim.Id),
                         V.type_name(doc.GetElement(dim.GetTypeId())),
                         len(segs), zone, pattern, anchor, i, kind, label,
                         eid, st, standoff, "yes" if inside else "no",
                         dim_len, " | ".join(values), overrides])

# ---------------- report ----------------
for vname, S in summary.items():
    out.print_md("## {}".format(vname))
    out.print_md("{} dimensions: {} strings, {} singles; {} with text "
                 "overrides/prefix/suffix; {} inside the slab, {} outside; "
                 "{} could not be matched to witness stations".format(
                     S["dims"], S["strings"], S["singles"], S["overrides"],
                     S["inside"], S["outside"], S["unresolved"]))
    out.print_table(sorted(S["zone"].items(), key=lambda t: -t[1]),
                    columns=["Grid direction (zone)", "dims"])
    out.print_table(sorted(S["kind"].items(), key=lambda t: -t[1]),
                    columns=["What is referenced", "witness lines"])
    tbl = []
    for kind, anchors in sorted(S["anchor_by_kind"].items()):
        total = sum(anchors.values())
        tbl.append([kind] + ["{} ({}%)".format(anchors.get(a, 0),
                                               100 * anchors.get(a, 0) // total)
                             for a in ("grid", "wall face", "beam face")]
                   + [total])
    if tbl:
        out.print_table(tbl, columns=["dims touching ...", "anchored to grid",
                                      "to wall face", "to beam face", "dims"])
    tbl = []
    for kind, xs in sorted(S["standoff"].items()):
        tbl.append([kind, len(xs), ftin(median(xs)), ftin(min(xs)),
                    ftin(sorted(xs)[int(len(xs) * 0.9)] if xs else None)])
    if tbl:
        out.print_table(tbl, columns=["referenced", "n", "standoff median",
                                      "min", "90th %"])
    out.print_table(sorted(S["pattern"].items(), key=lambda t: -t[1])[:25],
                    columns=["Reference pattern (along the string)", "dims"])

# ---------------- CSV ----------------
path = forms.save_file(file_ext="csv", default_name="dim_audit.csv",
                       title="Save the audit rows")
if path:
    def q(v):
        s = fmt(v)
        return '"' + s.replace('"', '""') + '"'
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(u",".join(COLS) + u"\n")
        for r in rows:
            fh.write(u",".join(q(v) for v in r) + u"\n")
    out.print_md("Saved **{}** rows to `{}`".format(len(rows), path))
