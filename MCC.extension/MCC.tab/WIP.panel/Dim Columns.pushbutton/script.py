# -*- coding: utf-8 -*-
"""Locates every column in the active plan from its nearest grid in each
direction. You choose per run: dimension to the column CENTERLINE or to
the near FACE (with the far face chained on so the size reads too).
A column centred on a grid in a direction gets no dimension in that
direction. Round columns are always located to centerline. Strings are placed
just outside the column, clear of other columns, walls, beams and
crossing gridlines, and short text is pulled out with a leader."""
__title__ = "Dim\nColumns"
__author__ = "MCC ENG"

from mcc_compat import eid_int
import math
from pyrevit import revit, DB, forms, script
import mcc_view as V

doc, uidoc = revit.doc, revit.uidoc
view = doc.ActiveView
output = script.get_output()

# =====================================================================
# CONFIG
# =====================================================================
AUTO_DIM_TYPE = None        # e.g. "MCC - AUTO COL DIM"; reruns replace
DEFAULT_MODE = None         # "Centerline" / "Face" / None = ask each run
FACE_ADD_FAR = True         # face mode: chain the far face (shows size)
COL_OFFSET = 1.0            # ft past the column to place the string
STATION_GAP = 1.75          # ft; spacing between strings on one grid
AVOID_PAD = 0.5             # ft clearance from other columns/walls/beams
GRID_CLEAR = 2.5            # ft clearance from crossing gridlines
AVOID_TRIES = 6
MAX_DIST = 40.0             # ft; skip columns farther than this from grid
ON_GRID_TOL = 1.0 / 96      # ft; a column centred on a grid (within 1/8")
                            # in that direction needs no dimension
PULL_TEXT = True
TEXT_PULL = 1.5             # text heights to pull short text outward
TEXT_FIT_MARGIN = 0.5       # text heights of room for ticks; lower = fewer
                            # values pulled out, higher = more
# =====================================================================

if not isinstance(view, DB.ViewPlan) or view.GenLevel is None:
    forms.alert("Open the soffit plan view first.", exitscript=True)

mode = DEFAULT_MODE or forms.CommandSwitchWindow.show(
    ["Centerline", "Face"], message="Dimension columns to:")
if not mode:
    script.exit()

grids = V.straight_grids(doc, view)
if not grids:
    forms.alert("No straight grids in this view.", exitscript=True)
fams = V.grid_families(grids)
sin_tol = math.sin(math.radians(0.5))
Z = view.GenLevel.ProjectElevation

dim_type = None
if AUTO_DIM_TYPE:
    dim_type = next((t for t in DB.FilteredElementCollector(doc)
                     .OfClass(DB.DimensionType)
                     if V.type_name(t) == AUTO_DIM_TYPE), None)
    if dim_type is None:
        forms.alert("Dimension type '{}' not found.".format(AUTO_DIM_TYPE),
                    exitscript=True)

# ---------- columns (selection first, else all in view) ----------
sel = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()]
cols = [e for e in sel if isinstance(e, DB.FamilyInstance) and e.Category
        and eid_int(e.Category.Id) in (
            int(DB.BuiltInCategory.OST_StructuralColumns),
            int(DB.BuiltInCategory.OST_Columns))]
if not cols:
    for bic in (DB.BuiltInCategory.OST_StructuralColumns,
                DB.BuiltInCategory.OST_Columns):
        cols += [e for e in DB.FilteredElementCollector(doc, view.Id)
                 .OfCategory(bic).WhereElementIsNotElementType()
                 if isinstance(e, DB.FamilyInstance)]
if not cols:
    forms.alert("No columns in this view.", exitscript=True)

# ---------- obstacles ----------
obstacles = {}
for bic in (DB.BuiltInCategory.OST_StructuralColumns, DB.BuiltInCategory.OST_Columns,
            DB.BuiltInCategory.OST_Walls, DB.BuiltInCategory.OST_StructuralFraming):
    for e in DB.FilteredElementCollector(doc, view.Id).OfCategory(bic) \
            .WhereElementIsNotElementType():
        bb = e.get_BoundingBox(view)
        if bb:
            obstacles[eid_int(e.Id)] = (bb.Min.X - AVOID_PAD, bb.Min.Y - AVOID_PAD,
                                            bb.Max.X + AVOID_PAD, bb.Max.Y + AVOID_PAD)


def seg_hits_rect(p, q, r):
    t0, t1 = 0.0, 1.0
    dx, dy = q[0] - p[0], q[1] - p[1]
    for pc, dc, lo, hi in ((p[0], dx, r[0], r[2]), (p[1], dy, r[1], r[3])):
        if abs(dc) < 1e-9:
            if pc < lo or pc > hi:
                return False
            continue
        ta, tb = (lo - pc) / dc, (hi - pc) / dc
        if ta > tb:
            ta, tb = tb, ta
        t0, t1 = max(t0, ta), min(t1, tb)
        if t0 > t1:
            return False
    return True


def blocker(gi, station, lo, hi, own_id):
    g, g0, u, n = grids[gi]
    for g2, g20, u2, n2 in grids:
        if abs(u2[0] * u[1] - u2[1] * u[0]) <= sin_tol:
            continue
        gs = (g20[0] - g0[0]) * u[0] + (g20[1] - g0[1]) * u[1]
        if abs(station - gs) < GRID_CLEAR:
            return ("grid", gs)
    for t in used.get(gi, []):
        if abs(station - t) < STATION_GAP:
            return ("used", t)
    px, py = g0[0] + u[0] * station, g0[1] + u[1] * station
    p = (px + n[0] * lo, py + n[1] * lo)
    q = (px + n[0] * hi, py + n[1] * hi)
    for eid, r in obstacles.items():
        if eid != own_id and seg_hits_rect(p, q, r):
            return ("rect", r)
    return None


def walk_lane(gi, start, sign, lo, hi, own_id):
    g, g0, u, n = grids[gi]
    st = start
    for _ in range(AVOID_TRIES):
        b = blocker(gi, st, lo, hi, own_id)
        if b is None:
            return st
        kind, val = b
        if kind == "rect":
            cs = [(val[0], val[1]), (val[2], val[1]), (val[2], val[3]),
                  (val[0], val[3])]
            sts = [(c[0] - g0[0]) * u[0] + (c[1] - g0[1]) * u[1] for c in cs]
            st = (max(sts) + COL_OFFSET) if sign > 0 else (min(sts) - COL_OFFSET)
        elif kind == "grid":
            st = val + sign * GRID_CLEAR
        else:
            st = val + sign * STATION_GAP
    return None


def line_clear(gi, station, lo, hi, own_id):
    g, g0, u, n = grids[gi]
    for g2, g20, u2, n2 in grids:
        if abs(u2[0] * u[1] - u2[1] * u[0]) <= sin_tol:
            continue
        gs = (g20[0] - g0[0]) * u[0] + (g20[1] - g0[1]) * u[1]
        if abs(station - gs) < GRID_CLEAR:
            return False
    px, py = g0[0] + u[0] * station, g0[1] + u[1] * station
    p = (px + n[0] * lo, py + n[1] * lo)
    q = (px + n[0] * hi, py + n[1] * hi)
    for eid, r in obstacles.items():
        if eid != own_id and seg_hits_rect(p, q, r):
            return False
    return True


used = {}


def free_station(gi, s, sign):
    taken = used.setdefault(gi, [])
    k = 0
    while any(abs(s - t) < STATION_GAP for t in taken) and k < 20:
        s += STATION_GAP * sign
        k += 1
    taken.append(s)
    return s


# ---------- column references ----------
def center_refs(col):
    """(ref_LR, ref_FB) center reference planes of the family instance."""
    out = []
    for rt in (DB.FamilyInstanceReferenceType.CenterLeftRight,
               DB.FamilyInstanceReferenceType.CenterFrontBack):
        try:
            refs = col.GetReferences(rt)
            out.append(refs[0] if refs and refs.Count else None)
        except Exception:
            out.append(None)
    return out


def face_refs(col, n):
    """Planar faces of the column whose normal is parallel to n:
    [(offset along n of the face, reference)]. Empty for round columns."""
    opts = DB.Options()
    opts.ComputeReferences = True
    opts.View = view
    found = []
    for geo in col.get_Geometry(opts):
        solids = []
        if isinstance(geo, DB.Solid):
            solids.append(geo)
        elif isinstance(geo, DB.GeometryInstance):
            for g2 in geo.GetInstanceGeometry():
                if isinstance(g2, DB.Solid):
                    solids.append(g2)
        for sol in solids:
            if sol.Volume <= 0:
                continue
            for face in sol.Faces:
                if not isinstance(face, DB.PlanarFace) or face.Reference is None:
                    continue
                fn = face.FaceNormal
                if abs(fn.Z) > 0.01:
                    continue
                if abs(fn.X * n[1] - fn.Y * n[0]) > sin_tol:
                    continue
                o = face.Origin
                found.append((o.X * n[0] + o.Y * n[1], face.Reference))
    return found


def ref_is_parallel(ref_plane_dir, n):
    return abs(ref_plane_dir[0] * n[1] - ref_plane_dir[1] * n[0]) <= sin_tol


jobs, notes = [], {"centerline": 0, "face": 0, "round -> centerline": 0,
                   "no reference": 0, "too far": 0, "over obstacle": 0,
                   "centred on grid (skipped)": 0}
for col in cols:
    bb = col.get_BoundingBox(view)
    if bb is None:
        continue
    cx, cy = (bb.Min.X + bb.Max.X) / 2, (bb.Min.Y + bb.Max.Y) / 2
    cid = eid_int(col.Id)
    lr, fb = center_refs(col)
    # instance axes: which center plane is parallel to which family?
    try:
        tf = col.GetTransform()
        ax_x = (tf.BasisX.X, tf.BasisX.Y)     # LR plane's normal direction
        ax_y = (tf.BasisY.X, tf.BasisY.Y)
    except Exception:
        ax_x, ax_y = (1, 0), (0, 1)
    for fam in fams:
        g_ref = fam[0]
        g, g0, u, n = grids[g_ref]
        # nearest grid in this family (offset measured along n)
        best = None
        for gi in fam:
            gg, gg0, gu, gn = grids[gi]
            off = (cx - gg0[0]) * gn[0] + (cy - gg0[1]) * gn[1]
            if best is None or abs(off) < abs(best[1]):
                best = (gi, off)
        gi, coff = best
        if abs(coff) < ON_GRID_TOL:
            notes["centred on grid (skipped)"] += 1
            continue
        if abs(coff) > MAX_DIST:
            notes["too far"] += 1
            continue
        gg, gg0, gu, gn = grids[gi]
        refs = []
        use_face = (mode == "Face")
        if use_face:
            faces = face_refs(col, gn)
            if not faces:
                use_face = False
                notes["round -> centerline"] += 1
            else:
                # offsets relative to this grid
                fo = sorted(((f[0] - (gg0[0] * gn[0] + gg0[1] * gn[1])), f[1])
                            for f in faces)
                near = min(fo, key=lambda t: abs(t[0]))
                refs = [near]
                if FACE_ADD_FAR:
                    far = max(fo, key=lambda t: abs(t[0]))
                    if abs(far[0] - near[0]) > 1.0 / 96:
                        refs.append(far)
                notes["face"] += 1
        if not use_face:
            # center plane whose normal is parallel to gn
            cref = None
            if lr is not None and ref_is_parallel(ax_x, gn):
                cref = lr
            elif fb is not None and ref_is_parallel(ax_y, gn):
                cref = fb
            if cref is None:
                notes["no reference"] += 1
                continue
            refs = [(coff, cref)]
            notes["centerline"] += 1
        refs.sort(key=lambda t: t[0])
        lo, hi = min(0.0, refs[0][0]), max(0.0, refs[-1][0])
        # station range of the column along gu
        corners = [(bb.Min.X, bb.Min.Y), (bb.Max.X, bb.Min.Y),
                   (bb.Max.X, bb.Max.Y), (bb.Min.X, bb.Max.Y)]
        sts = [(c[0] - gg0[0]) * gu[0] + (c[1] - gg0[1]) * gu[1] for c in corners]
        up = walk_lane(gi, max(sts) + COL_OFFSET, 1, lo, hi, cid)
        dn = walk_lane(gi, min(sts) - COL_OFFSET, -1, lo, hi, cid)
        opts_ = [(abs(st - (max(sts) if sg_ > 0 else min(sts))), st, sg_)
                 for st, sg_ in ((up, 1), (dn, -1)) if st is not None]
        if opts_:
            _, st, sg_ = min(opts_)
        else:
            st, sg_ = max(sts) + COL_OFFSET, 1
            notes["over obstacle"] += 1
        used.setdefault(gi, []).append(st)
        jobs.append((gi, st, refs, sg_))

if not jobs:
    forms.alert("Nothing to dimension.", exitscript=True)


# ---------- text pull ----------
def text_size_ft(dtype):
    p = dtype.get_Parameter(DB.BuiltInParameter.TEXT_SIZE) if dtype else None
    return p.AsDouble() if p else 3.0 / 32 / 12


pull_failed = [0]
pull_errors = []
metrics = [0.0]


# Arial Narrow advance widths (fraction of text size); anything else ~digit
_CW = {"'": 0.16, '"': 0.29, "-": 0.27, "/": 0.23, " ": 0.23, ".": 0.23,
       "1": 0.46}


TEXT_EM = 1.40              # Revit text size ~ cap height; the font's em
                            # (what glyph widths are measured in) is ~1.4x
_width_factor = [1.0]


def text_width(txt, tsize):
    em = tsize * TEXT_EM * _width_factor[0]
    if not txt:
        return 4 * 0.46 * em
    return sum(_CW.get(ch, 0.46) for ch in txt) * em


def fits(val, width, tsize):
    return val >= width + TEXT_FIT_MARGIN * tsize


def pull_short_text(dim, outward, dline):
    """Move text of segments narrower than the text out past the end of
    the segment with a leader, the way it's done by hand. Revit only
    honours a leader once the text is already displaced, so: nudge the
    text along the line, switch the leader on, then move it to its final
    spot (past the witness line and off the line). Neighbouring short
    texts alternate sides / stack rows so they never overlap or cross."""
    dtype_ = doc.GetElement(dim.GetTypeId())
    tsize = text_size_ft(dtype_) * view.Scale
    metrics[0] = tsize
    try:
        wf = dtype_.get_Parameter(DB.BuiltInParameter.TEXT_WIDTH_SCALE)
        _width_factor[0] = wf.AsDouble() if wf and wf.AsDouble() > 0 else 1.0
    except Exception:
        _width_factor[0] = 1.0
    segs = list(dim.Segments) if dim.NumberOfSegments > 1 else [dim]
    items = []
    for sg in segs:
        try:
            val = sg.Value
        except Exception as ex:
            pull_errors.append("Value: {}".format(ex))
            continue
        if val is None:
            continue
        try:
            txt = sg.ValueString or ""
        except Exception:
            txt = ""
        try:
            pos = sg.TextPosition
        except Exception as ex:
            pull_errors.append("TextPosition: {}".format(ex))
            continue
        width = text_width(txt, tsize)
        along = pos.X * dline.X + pos.Y * dline.Y
        items.append((along, sg, val, width, pos))
    items.sort(key=lambda t: t[0])
    short = [it for it in items if not fits(it[2], it[3], tsize)]
    if not short:
        return 0
    # occupied intervals along the line, per row outward (row 0 = on line)
    occupied = {0: [(a - w / 2.0, a + w / 2.0) for a, sg, v, w, p in items
                    if fits(v, w, tsize)]}
    pulled = 0
    row_h = 1.4 * tsize
    # middle of the whole string: texts go toward the end they're nearest
    # to (away from the middle) so their leaders diverge, never cross
    s_lo = items[0][0] - items[0][2] / 2.0
    s_hi = items[-1][0] + items[-1][2] / 2.0
    s_mid = (s_lo + s_hi) / 2.0
    for i, (along, sg, val, width, pos) in enumerate(short):
        # step 1: nudge along the line (always accepted)
        try:
            sg.TextPosition = DB.XYZ(pos.X + dline.X * 0.05, pos.Y + dline.Y * 0.05, pos.Z)
        except Exception as ex:
            pull_failed[0] += 1
            pull_errors.append("nudge: {}".format(ex))
            continue
        # step 2: leader on (only valid once displaced)
        try:
            if not dim.HasLeader:
                dim.HasLeader = True
        except Exception as ex:
            pull_errors.append("HasLeader: {}".format(ex))
        # step 3: final spot - past the segment end, off the line; pick the
        # side/row where it doesn't overlap anything already placed
        pref = 1 if along >= s_mid else -1
        # push past the END of the string on the preferred side, not just
        # past this segment, so stacked texts line up beyond the string
        end = s_hi if pref > 0 else s_lo
        cand = []
        for side in (pref, -pref):
            e = s_hi if side > 0 else s_lo
            centre = e + side * (width / 2.0 + 0.5 * tsize)
            cand.append((side, centre))
        placed = False
        for side, centre in cand:
            for k in range(4):
                lo, hi = centre - width / 2.0, centre + width / 2.0
                if any(not (hi < a or lo > b) for a, b in occupied.get(k + 1, [])):
                    continue
                d = TEXT_PULL * tsize + k * row_h
                try:
                    sg.TextPosition = DB.XYZ(
                        pos.X + dline.X * (centre - along) + outward.X * d,
                        pos.Y + dline.Y * (centre - along) + outward.Y * d,
                        pos.Z)
                except Exception as ex:
                    pull_failed[0] += 1
                    pull_errors.append("set: {}".format(ex))
                    placed = True
                    break
                occupied.setdefault(k + 1, []).append((lo, hi))
                pulled += 1
                placed = True
                # verify Revit kept the perpendicular offset
                try:
                    chk = sg.TextPosition
                    got = (chk.X - pos.X) * outward.X + (chk.Y - pos.Y) * outward.Y
                    if abs(got) < 0.5 * d:
                        snapped[0] += 1
                except Exception:
                    pass
                break
            if placed:
                break
    return pulled


snapped = [0]


def width_ok(width):
    return width * 1.15


pull_failed = [0]
pull_errors = []


def pull_short_text(dim, outward, dline):
    tsize = text_size_ft(doc.GetElement(dim.GetTypeId())) * view.Scale
    segs = list(dim.Segments) if dim.NumberOfSegments > 1 else [dim]
    items = []
    for sg in segs:
        try:
            val = sg.Value
        except Exception as ex:
            pull_errors.append("Value: {}".format(ex))
            continue
        if val is None:
            continue
        try:
            txt = sg.ValueString or ""
        except Exception:
            txt = ""
        org = None
        try:
            org = sg.Origin
        except Exception:
            pass
        if org is None:
            try:
                org = sg.TextPosition
            except Exception as ex:
                pull_errors.append("TextPosition: {}".format(ex))
                continue
        width = text_width(txt, tsize)
        items.append((org.X * dline.X + org.Y * dline.Y, sg, val, width))
    items.sort(key=lambda t: t[0])
    if any(val < width * 1.15 for along, sg, val, width in items):
        try:
            dim.HasLeader = True       # must be on BEFORE moving text
            doc.Regenerate()
        except Exception as ex:
            pull_errors.append("HasLeader: {}".format(ex))
    cursor, pulled, gap = None, 0, 0.6 * tsize
    for along, sg, val, width in items:
        if val >= width * 1.15:
            cursor = along + width / 2.0
            continue
        pos = along if cursor is None else max(along, cursor + gap + width / 2.0)
        shift = pos - along
        old = sg.TextPosition
        try:
            sg.TextPosition = DB.XYZ(
                old.X + outward.X * TEXT_PULL * tsize + dline.X * shift,
                old.Y + outward.Y * TEXT_PULL * tsize + dline.Y * shift, old.Z)
            pulled += 1
            cursor = pos + width / 2.0
        except Exception as ex:
            pull_failed[0] += 1
            pull_errors.append("set: {}".format(ex))
    if pulled:
        try:
            dim.HasLeader = True
        except Exception:
            pass
    return pulled


# ---------- create ----------
old = []
if dim_type:
    old = [d for d in DB.FilteredElementCollector(doc, view.Id)
           .OfClass(DB.Dimension) if d.GetTypeId() == dim_type.Id]
made, failed, pulled = 0, 0, 0
with revit.Transaction("MCC: Dimension columns ({})".format(mode)):
    for d in old:
        doc.Delete(d.Id)
    for gi, st, refs, sign in jobs:
        g, g0, u, n = grids[gi]
        ra = DB.ReferenceArray()
        ra.Append(DB.Reference(g))
        for o, r in refs:
            ra.Append(r)
        lo, hi = min(0.0, refs[0][0]), max(0.0, refs[-1][0])
        if hi - lo < 1.0 / 192:
            continue
        px, py = g0[0] + u[0] * st, g0[1] + u[1] * st
        line = DB.Line.CreateBound(DB.XYZ(px + n[0] * lo, py + n[1] * lo, Z),
                                   DB.XYZ(px + n[0] * hi, py + n[1] * hi, Z))
        try:
            dim = (doc.Create.NewDimension(view, line, ra, dim_type) if dim_type
                   else doc.Create.NewDimension(view, line, ra))
            made += 1
            if PULL_TEXT and dim is not None:
                doc.Regenerate()
                pulled += pull_short_text(dim, DB.XYZ(u[0] * sign, u[1] * sign, 0),
                                          DB.XYZ(n[0], n[1], 0))
        except Exception:
            failed += 1

output.print_md("## Column dimensions ({}): {}".format(mode, view.Name))
if pull_errors:
    output.print_md("**Text pull errors:** " + " | ".join(
        sorted(set(pull_errors))[:4]))
output.print_table([["strings", made], ["failed", failed],
                    ["text pulled out", pulled],
                    ["text pull failed", pull_failed[0]],
                    ["text snapped back by Revit", snapped[0]]] +
                   [[k, v] for k, v in notes.items() if v],
                   columns=["Result", "Count"])
