# -*- coding: utf-8 -*-
"""Sheet-building helpers shared by the MCC sheet buttons.

What lives here:
- prototype sheet capture: what is on a finished sheet (plan viewport,
  legends, key plan, notes / symbols) so it can be reproduced
- model <-> sheet mapping so a grid intersection can be pinned to the
  same spot on every sheet of a zone
- scope-box zones: which scope boxes split which level, zone names,
  north-to-south ordering
- grid intersections, level tokens, sheet numbering

Nothing here starts a transaction; the calling script owns it."""
from mcc_compat import eid_int
import math
import re
from pyrevit import DB

PLAN_VIEW_TYPES = (DB.ViewType.FloorPlan, DB.ViewType.EngineeringPlan,
                   DB.ViewType.CeilingPlan)
KEY_PLAN_TOKEN = "KEY PLAN"          # legend / drafting views placed by zone


# ------------------------------------------------------------------ misc
def type_name(e):
    p = e.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    return p.AsString() if p else e.Name


def level_token(level_name, prefix="LEVEL"):
    """'LEVEL-B5' -> 'B5', 'Level 3' -> '3', 'ROOF' -> 'ROOF'."""
    tok = level_name.upper().replace(prefix.upper(), "", 1)
    return tok.strip(" -_").replace(" ", "")


def title_case(s):
    return " ".join(w.capitalize() for w in s.split())


# ------------------------------------------------------ level references
_LVL_RE = re.compile(r"(?<![A-Z0-9])(?:LEVEL|LVL|L)[\s\-_]*([A-Z]?\d+(?:\.\d+)?)"
                     r"(?![A-Z0-9])", re.I)
_NAME_RE = re.compile(r"(?<![A-Z0-9])(ROOF|MECH\s*ROOF|ELEV\s*MECH\s*RM)(?![A-Z0-9])",
                      re.I)


def _num(tok):
    m = re.match(r"^[A-Z]?(\d+(?:\.\d+)?)$", tok, re.I)
    return float(m.group(1)) if m else None


def level_refs(name):
    """Level tokens mentioned in a scope-box name, e.g.
    'L3 NORTH' -> ['3'], 'L6 to L40 Tower' -> ['6', '40']."""
    refs = [m.group(1).upper() for m in _LVL_RE.finditer(name)]
    refs += [m.group(1).upper().replace(" ", "")
             for m in _NAME_RE.finditer(name)]
    return refs


def refers_to_level(name, tok):
    """Does a scope-box name cover level token 'tok'? Handles single
    levels and 'L6 to L40' style ranges."""
    refs = level_refs(name)
    if not refs:
        return None                      # no opinion - caller falls back
    tok = tok.upper()
    if tok in refs:
        return True
    n = _num(tok)
    nums = [x for x in (_num(r) for r in refs) if x is not None]
    if n is not None and len(nums) >= 2 and \
            re.search(r"\b(TO|THRU|THROUGH)\b|-", name, re.I):
        return min(nums) <= n <= max(nums)
    return False


def rename_for_level(box_name, new_tok):
    """'L3 NORTH' -> 'L4 NORTH', 'LEVEL-3 SOUTH' -> 'LEVEL-4 SOUTH'
    (keeps the prefix style); a name with no level in it gets 'L4 '
    in front."""
    m = _LVL_RE.search(box_name)
    if m:
        head = m.group(0)[:m.start(1) - m.start(0)]
        return box_name[:m.start(0)] + head + new_tok + box_name[m.end(0):]
    m = _NAME_RE.search(box_name)
    if m:
        return box_name[:m.start(0)] + new_tok + box_name[m.end(0):]
    return "L{} {}".format(new_tok, box_name)


def zone_name(box_name):
    """Scope-box name minus its level references:
    'L3 NORTH' -> 'North', 'Level 3' -> '', 'L6 to L40 Tower Footprint'
    -> 'Tower Footprint'."""
    s = _LVL_RE.sub(" ", box_name)
    s = _NAME_RE.sub(" ", s)
    s = re.sub(r"\b(TO|THRU|THROUGH|LEVEL|LVL|PLAN|AREA)\b", " ", s, flags=re.I)
    s = re.sub(r"[\-_/,]+", " ", s)
    return title_case(" ".join(s.split()))


# ------------------------------------------------------------ scope boxes
def scope_boxes(doc):
    return sorted(DB.FilteredElementCollector(doc)
                  .OfCategory(DB.BuiltInCategory.OST_VolumeOfInterest)
                  .WhereElementIsNotElementType(), key=lambda b: b.Name)


def box_center(box):
    bb = box.get_BoundingBox(None)
    if bb is None:
        return (0.0, 0.0, 0.0, 0.0)
    return ((bb.Min.X + bb.Max.X) / 2.0, (bb.Min.Y + bb.Max.Y) / 2.0,
            bb.Min.Z, bb.Max.Z)


def boxes_for_level(boxes, level, tok):
    """Scope boxes that apply to a level: by name reference, or (when the
    name says nothing about levels) by the box's Z range. Ordered north
    to south, then west to east."""
    out = []
    for b in boxes:
        hit = refers_to_level(b.Name, tok)
        if hit is None:
            _, _, z0, z1 = box_center(b)
            hit = z0 - 0.5 <= level.Elevation <= z1 + 0.5
        if hit:
            out.append(b)
    out.sort(key=lambda b: (-round(box_center(b)[1], 1),
                            round(box_center(b)[0], 1)))
    return out


def same_plan_extent(a, b, tol=0.05):
    """Do two elements (scope boxes) cover the same plan rectangle?"""
    ba, bb = a.get_BoundingBox(None), b.get_BoundingBox(None)
    if ba is None or bb is None:
        return False
    return (abs(ba.Min.X - bb.Min.X) < tol and abs(ba.Min.Y - bb.Min.Y) < tol
            and abs(ba.Max.X - bb.Max.X) < tol
            and abs(ba.Max.Y - bb.Max.Y) < tol)


def same_crop(view, other, tol=0.05):
    """Same scope-box footprint, or (no boxes) same crop box in plan."""
    va, vb = view_scope_box_id(view), view_scope_box_id(other)
    if va != DB.ElementId.InvalidElementId and \
            vb != DB.ElementId.InvalidElementId:
        if va == vb:
            return True
        return same_plan_extent(view.Document.GetElement(va),
                                other.Document.GetElement(vb), tol)
    if va != vb and (va == DB.ElementId.InvalidElementId or
                     vb == DB.ElementId.InvalidElementId):
        return False
    ca, cb = view.CropBox, other.CropBox
    if not (view.CropBoxActive and other.CropBoxActive):
        return False
    pa = [ca.Transform.OfPoint(ca.Min), ca.Transform.OfPoint(ca.Max)]
    pb = [cb.Transform.OfPoint(cb.Min), cb.Transform.OfPoint(cb.Max)]
    return all(abs(pa[i].X - pb[i].X) < tol and abs(pa[i].Y - pb[i].Y) < tol
               for i in (0, 1))


def sketched_crop(view):
    """The view's sketched (non-rectangular) crop as a CurveLoop in model
    coordinates, or None when the crop is a plain rectangle or a scope
    box."""
    if view_scope_box_id(view) != DB.ElementId.InvalidElementId:
        return None
    try:
        if not view.CropBoxActive:
            return None
        m = view.GetCropRegionShapeManager()
        if not m.ShapeSet:
            return None
        loops = list(m.GetCropShape())
    except Exception:
        return None
    return loops[0] if loops else None


def apply_crop_shape(view, loop, dz=0.0):
    """Give 'view' the same sketched crop, moved up/down by dz to its own
    level. Clears the view's scope box first - Revit won't sketch a crop
    on a view that has one."""
    p = view.get_Parameter(DB.BuiltInParameter.VIEWER_VOLUME_OF_INTEREST_CROP)
    if p is not None and not p.IsReadOnly:
        p.Set(DB.ElementId.InvalidElementId)
    view.CropBoxActive = True
    if abs(dz) > 1e-9:
        loop = DB.CurveLoop.CreateViaTransform(
            loop, DB.Transform.CreateTranslation(DB.XYZ(0, 0, dz)))
    view.GetCropRegionShapeManager().SetCropShape(loop)


def copy_grid_display(doc, src_view, dst_view):
    """Match every grid in dst_view to how it's drawn in src_view:
    - hidden in view (Hide in View > Elements) -> hidden here too
    - 2D line extents, extent type (3D/2D) per end
    - bubble on/off per end
    - bubble elbows
    Grids span levels, so it's the same grid element in both views; the
    src view's curve is just moved to dst's height. Each piece is applied
    on its own, so one failure doesn't skip the rest of that grid.
    Returns (matched, hidden, [(grid name, reason)])."""
    ends = (DB.DatumEnds.End0, DB.DatumEnds.End1)
    vs, mdl = DB.DatumExtentType.ViewSpecific, DB.DatumExtentType.Model
    grids = list(DB.FilteredElementCollector(doc).OfClass(DB.Grid))
    failed = []

    # 1. grids hidden in the prototype view -> hide in the new view
    to_hide = []
    for g in grids:
        try:
            if g.IsHidden(src_view) and not g.IsHidden(dst_view) and \
                    g.CanBeHidden(dst_view):
                to_hide.append(g.Id)
        except Exception:
            pass
    if to_hide:
        from System.Collections.Generic import List
        try:
            dst_view.HideElements(List[DB.ElementId](to_hide))
        except Exception as ex:
            failed.append(("(hidden grids)", str(ex).split("\n")[0][:80]))
            to_hide = []
    hidden_ids = set(eid_int(i) for i in to_hide)

    # 2. visible grids: extents, bubbles, elbows
    src_ids = set(eid_int(g.Id) for g in
                  DB.FilteredElementCollector(doc, src_view.Id)
                  .OfClass(DB.Grid))
    matched = 0
    for g in DB.FilteredElementCollector(doc, dst_view.Id).OfClass(DB.Grid):
        gid = eid_int(g.Id)
        if gid not in src_ids or gid in hidden_ids:
            continue
        p = g.get_Parameter(DB.BuiltInParameter.DATUM_VOLUME_OF_INTEREST)
        if p is not None and p.AsElementId() != DB.ElementId.InvalidElementId:
            failed.append((g.Name, "grid has its own scope box"))
            continue
        ok = True
        move = DB.Transform.Identity
        # line ends: go 2D both ends, set the curve, then put back any end
        # that is 3D (model) on the prototype
        try:
            types = [g.GetDatumExtentTypeInView(e, src_view) for e in ends]
            sc = list(g.GetCurvesInView(vs, src_view))
            dc = list(g.GetCurvesInView(vs, dst_view))
            if sc and dc:
                dz = dc[0].GetEndPoint(0).Z - sc[0].GetEndPoint(0).Z
                move = DB.Transform.CreateTranslation(DB.XYZ(0, 0, dz))
                for e in ends:
                    g.SetDatumExtentType(e, dst_view, vs)
                g.SetCurveInView(vs, dst_view, sc[0].CreateTransformed(move))
                for e, t in zip(ends, types):
                    if t == mdl:
                        g.SetDatumExtentType(e, dst_view, mdl)
        except Exception as ex:
            ok = False
            failed.append((g.Name, "extents: " +
                           str(ex).split("\n")[0][:70]))
        # bubbles, each end on its own
        for e in ends:
            try:
                want = g.IsBubbleVisibleInView(e, src_view)
                if want != g.IsBubbleVisibleInView(e, dst_view):
                    if want:
                        g.ShowBubbleInView(e, dst_view)
                    else:
                        g.HideBubbleInView(e, dst_view)
            except Exception as ex:
                ok = False
                failed.append((g.Name, "bubble {}: ".format(e) +
                               str(ex).split("\n")[0][:60]))
        # elbows
        for e in ends:
            try:
                ld = g.GetLeader(e, src_view)
                if ld is None:
                    continue
                if g.GetLeader(e, dst_view) is None:
                    g.AddLeader(e, dst_view)
                nl = g.GetLeader(e, dst_view)
                nl.End = move.OfPoint(ld.End)
                nl.Elbow = move.OfPoint(ld.Elbow)
                g.SetLeader(e, dst_view, nl)
            except Exception as ex:
                ok = False
                failed.append((g.Name, "elbow: " +
                               str(ex).split("\n")[0][:70]))
        if ok:
            matched += 1
    return matched, len(hidden_ids), failed


def rect_crop(view):
    """The view's plain rectangular crop (a copy), or None when the crop
    is off, sketched, or set by a scope box."""
    if view_scope_box_id(view) != DB.ElementId.InvalidElementId:
        return None
    try:
        if not view.CropBoxActive:
            return None
        if view.GetCropRegionShapeManager().ShapeSet:
            return None
    except Exception:
        return None
    return view.CropBox


def apply_rect_crop(view, box, dz=0.0):
    """Give 'view' the same rectangular crop, moved to its level."""
    p = view.get_Parameter(DB.BuiltInParameter.VIEWER_VOLUME_OF_INTEREST_CROP)
    if p is not None and not p.IsReadOnly:
        p.Set(DB.ElementId.InvalidElementId)
    try:
        view.GetCropRegionShapeManager().RemoveCropRegionShape()
    except Exception:
        pass
    nb = DB.BoundingBoxXYZ()
    t = DB.Transform(box.Transform)
    t.Origin = t.Origin + DB.XYZ(0, 0, dz)
    nb.Transform = t
    nb.Min, nb.Max = box.Min, box.Max
    view.CropBoxActive = True
    view.CropBox = nb


def sheet_zone(sheet_name):
    """Zone from a sheet name: 'Level 3 - North Area (Soffit Plan)' ->
    'North Area'; '' when the name has no ' - ' part."""
    n = re.sub(r"\(.*?\)", "", sheet_name).strip()
    if " - " not in n:
        return ""
    return title_case(n.split(" - ", 1)[1].strip())


def view_scope_box_id(view):
    p = view.get_Parameter(DB.BuiltInParameter.VIEWER_VOLUME_OF_INTEREST_CROP)
    return p.AsElementId() if p else DB.ElementId.InvalidElementId


# ------------------------------------------------------------------ grids
def straight_grid_lines(doc):
    """{name: (p0, u)} for straight grids (plan xy, unit direction)."""
    out = {}
    for g in DB.FilteredElementCollector(doc).OfClass(DB.Grid):
        c = g.Curve
        if not isinstance(c, DB.Line):
            continue
        d = c.Direction
        m = math.hypot(d.X, d.Y)
        if m < 1e-9:
            continue
        p0 = c.GetEndPoint(0)
        out[g.Name] = ((p0.X, p0.Y), (d.X / m, d.Y / m))
    return out


def grid_intersections(grid_lines, min_angle_deg=20.0):
    """[(label, (x, y))] for every pair of non-parallel straight grids,
    label 'A / 1'."""
    names = sorted(grid_lines, key=_grid_sort_key)
    sin_min = math.sin(math.radians(min_angle_deg))
    out = []
    for i, a in enumerate(names):
        pa, ua = grid_lines[a]
        for b in names[i + 1:]:
            pb, ub = grid_lines[b]
            cross = ua[0] * ub[1] - ua[1] * ub[0]
            if abs(cross) < sin_min:
                continue
            # pa + t*ua = pb + s*ub
            dx, dy = pb[0] - pa[0], pb[1] - pa[1]
            t = (dx * ub[1] - dy * ub[0]) / cross
            pt = (pa[0] + t * ua[0], pa[1] + t * ua[1])
            # letters first in the label
            lab = "{} / {}".format(a, b) if _is_alpha(a) or not _is_alpha(b) \
                else "{} / {}".format(b, a)
            out.append((lab, pt))
    out.sort(key=lambda x: _grid_sort_key(x[0]))
    return out


def _is_alpha(n):
    return n[:1].isalpha()


def _grid_sort_key(n):
    parts = re.findall(r"\d+|[A-Za-z]+|[^A-Za-z\d\s/]+", n)
    key = []
    for p in parts:
        key.append((0, int(p)) if p.isdigit() else (1, p.upper()))
    return (1 if _is_alpha(n) else 0, key)


# ------------------------------------------------- model <-> sheet mapping
def model_to_sheet(view, viewport, x, y):
    """Where model plan point (x, y) lands on the sheet that carries
    'viewport' of 'view'. The view's Outline and the viewport's box
    outline are the same rectangle in paper vs sheet space, so map
    lower-left to lower-left; any constant offset (viewport label) is the
    same on every sheet and cancels out in place_aligned()."""
    # exact: the view's model->projection and the viewport's
    # projection->sheet transforms (Revit 2022+); independent of the
    # viewport box size (annotation crop, tags hanging outside...)
    try:
        z = view.GenLevel.ProjectElevation if view.GenLevel else 0.0
        mtp = list(view.GetModelToProjectionTransforms())[0] \
            .GetModelToProjectionTransform()
        p = viewport.GetProjectionToSheetTransform().OfPoint(
            mtp.OfPoint(DB.XYZ(x, y, z)))
        return (p.X, p.Y)
    except Exception:
        pass
    o = view.Origin
    r, u = view.RightDirection, view.UpDirection
    dx, dy = x - o.X, y - o.Y
    lx = dx * r.X + dy * r.Y
    ly = dx * u.X + dy * u.Y
    sc = float(view.Scale)
    ol = view.Outline
    bo = viewport.GetBoxOutline()
    return (bo.MinimumPoint.X + (lx / sc - ol.Min.U),
            bo.MinimumPoint.Y + (ly / sc - ol.Min.V))


def place_aligned(doc, sheet, view, anchor_xy, target_sheet_xy,
                  viewport_type_id=None):
    """Put 'view' on 'sheet' so model point anchor_xy sits at sheet point
    target_sheet_xy. Returns the viewport."""
    vp = DB.Viewport.Create(doc, sheet.Id, view.Id, DB.XYZ(1.5, 1.2, 0))
    if viewport_type_id is not None and \
            viewport_type_id != DB.ElementId.InvalidElementId:
        try:
            vp.ChangeTypeId(viewport_type_id)
        except Exception:
            pass
    doc.Regenerate()
    landed = model_to_sheet(view, vp, anchor_xy[0], anchor_xy[1])
    c = vp.GetBoxCenter()
    vp.SetBoxCenter(DB.XYZ(c.X + target_sheet_xy[0] - landed[0],
                           c.Y + target_sheet_xy[1] - landed[1], 0))
    return vp


def place_like(doc, sheet, view, src_vp, src_view):
    """Put 'view' on 'sheet' exactly where src_view sits on its sheet:
    the crop centre of src_view lands on the same sheet point, with the
    same viewport type, rotation and title position. Returns the viewport."""
    cb = src_view.CropBox
    c = cb.Transform.OfPoint((cb.Min + cb.Max) * 0.5)
    target = model_to_sheet(src_view, src_vp, c.X, c.Y)
    bc0 = src_vp.GetBoxCenter()
    vp = place_at(doc, sheet, view, (bc0.X, bc0.Y), src_vp.GetTypeId())
    try:
        if vp.Rotation != src_vp.Rotation:
            vp.Rotation = src_vp.Rotation
    except Exception:
        pass
    doc.Regenerate()
    landed = model_to_sheet(view, vp, c.X, c.Y)
    bc = vp.GetBoxCenter()
    vp.SetBoxCenter(DB.XYZ(bc.X + target[0] - landed[0],
                           bc.Y + target[1] - landed[1], 0))
    copy_label(vp, read_label(src_vp))
    return vp


def place_matching(doc, sheet, view, proto, viewport_type_id=None):
    """Put 'view' on 'sheet' so the prototype plan's crop centre lands
    exactly where it does on the prototype sheet. Copies the viewport
    rotation too. Returns the viewport."""
    pvp, pv = proto.plan_vp
    cb = pv.CropBox
    c = cb.Transform.OfPoint((cb.Min + cb.Max) * 0.5)
    target = model_to_sheet(pv, pvp, c.X, c.Y)
    vp = place_at(doc, sheet, view, proto.plan_center(), viewport_type_id)
    try:
        if vp.Rotation != pvp.Rotation:
            vp.Rotation = pvp.Rotation
    except Exception:
        pass
    doc.Regenerate()
    landed = model_to_sheet(view, vp, c.X, c.Y)
    bc = vp.GetBoxCenter()
    vp.SetBoxCenter(DB.XYZ(bc.X + target[0] - landed[0],
                           bc.Y + target[1] - landed[1], 0))
    return vp


def place_at(doc, sheet, view, center_xy, viewport_type_id=None):
    vp = DB.Viewport.Create(doc, sheet.Id, view.Id,
                            DB.XYZ(center_xy[0], center_xy[1], 0))
    if viewport_type_id is not None and \
            viewport_type_id != DB.ElementId.InvalidElementId:
        try:
            vp.ChangeTypeId(viewport_type_id)
            doc.Regenerate()
            vp.SetBoxCenter(DB.XYZ(center_xy[0], center_xy[1], 0))
        except Exception:
            pass
    return vp


def read_label(vp):
    """(LabelOffset, LabelLineLength) of a viewport title, or None."""
    try:
        return (vp.LabelOffset, vp.LabelLineLength)
    except Exception:
        return None


def copy_label(vp, label):
    """Put the viewport title where the prototype's is (same offset from
    the viewport, same title line length). True when applied."""
    if vp is None or label is None:
        return False
    try:
        vp.LabelOffset = label[0]
        vp.LabelLineLength = label[1]
        return True
    except Exception:
        return False


# --------------------------------------------------------- prototype sheet
class Prototype(object):
    """Everything the builder copies from a finished sheet."""

    def __init__(self, doc, sheet):
        self.doc = doc
        self.sheet = sheet
        self.plan_vp = None          # (viewport, view)
        self.legends = []            # [(view, center_xy, type_id)]
        self.key_plans = []          # [(view, center_xy, type_id)]
        self.other_vps = []          # [(view, center_xy, type_id)] sections etc.
        self.copy_ids = []           # text, symbols, lines, schedules...
        self.titleblock_type_id = None
        self._read()

    def _read(self):
        doc = self.doc
        self.labels = {}             # view id -> (label offset, line length)
        plans = []
        for vp in DB.FilteredElementCollector(doc, self.sheet.Id) \
                .OfClass(DB.Viewport):
            v = doc.GetElement(vp.ViewId)
            c = vp.GetBoxCenter()
            self.labels[eid_int(v.Id)] = read_label(vp)
            rec = (v, (c.X, c.Y), vp.GetTypeId())
            if v.ViewType in PLAN_VIEW_TYPES and \
                    KEY_PLAN_TOKEN not in v.Name.upper():
                plans.append((vp, v, rec))
            elif KEY_PLAN_TOKEN in v.Name.upper():
                self.key_plans.append(rec)
            elif v.ViewType == DB.ViewType.Legend:
                self.legends.append(rec)
            else:
                self.other_vps.append(rec)
        # the sheet's main plan is its biggest plan viewport; any other
        # plan views on it (partial plans...) are copied like other views
        if plans:
            def area(item):
                o = item[0].GetBoxOutline()
                d = o.MaximumPoint - o.MinimumPoint
                return d.X * d.Y
            plans.sort(key=area, reverse=True)
            self.plan_vp = (plans[0][0], plans[0][1])
            self.other_vps.extend(rec for _, _, rec in plans[1:])
        skip = (DB.Viewport, DB.ScheduleSheetInstance, DB.RevisionCloud)
        for e in DB.FilteredElementCollector(doc, self.sheet.Id) \
                .WhereElementIsNotElementType():
            if isinstance(e, skip):
                continue
            cat = e.Category
            if cat is None:
                continue
            bic = eid_int(cat.Id)
            if bic == int(DB.BuiltInCategory.OST_TitleBlocks):
                if self.titleblock_type_id is None:
                    self.titleblock_type_id = e.GetTypeId()
                continue
            if bic in (int(DB.BuiltInCategory.OST_Sheets),
                       int(DB.BuiltInCategory.OST_GuideGrid),
                       int(DB.BuiltInCategory.OST_Viewports),
                       int(DB.BuiltInCategory.OST_Cameras)):
                continue
            self.copy_ids.append(e.Id)
        self.schedules = [(s.ScheduleId, s.Point)
                          for s in DB.FilteredElementCollector(doc, self.sheet.Id)
                          .OfClass(DB.ScheduleSheetInstance)
                          if not s.IsTitleblockRevisionSchedule]

    @property
    def plan_view(self):
        return self.plan_vp[1] if self.plan_vp else None

    @property
    def plan_vp_type_id(self):
        return self.plan_vp[0].GetTypeId() if self.plan_vp else None

    def label_for(self, view):
        """Title position of 'view' on the prototype, or the plan's."""
        return self.labels.get(eid_int(view.Id))

    def plan_label(self):
        return self.labels.get(eid_int(self.plan_view.Id)) \
            if self.plan_vp else None

    def plan_center(self):
        c = self.plan_vp[0].GetBoxCenter()
        return (c.X, c.Y)

    def anchor_target(self, anchor_xy):
        """Sheet point where model anchor_xy sits on the prototype."""
        vp, v = self.plan_vp
        return model_to_sheet(v, vp, anchor_xy[0], anchor_xy[1])

    def copy_annotations(self, sheet, warnings):
        """Text, symbols, north arrow, detail lines, schedules -> sheet."""
        if self.copy_ids:
            from System.Collections.Generic import List
            lst = List[DB.ElementId](self.copy_ids)
            try:
                DB.ElementTransformUtils.CopyElements(
                    self.sheet, lst, sheet, DB.Transform.Identity,
                    DB.CopyPasteOptions())
            except Exception as ex:
                warnings.append("{}: could not copy sheet annotations "
                                "from {} ({})".format(sheet.SheetNumber,
                                                      self.sheet.SheetNumber,
                                                      ex))
        for sid, pt in self.schedules:
            try:
                DB.ScheduleSheetInstance.Create(self.doc, sheet.Id, sid, pt)
            except Exception as ex:
                warnings.append("{}: schedule not placed ({})".format(
                    sheet.SheetNumber, ex))

    def copy_sheet_params(self, sheet, warnings, skip=("Sheet Number",
                                                       "Sheet Name")):
        """User-defined (project / shared) sheet parameters, e.g. Issued
        For, Drawn By. Built-in ones are left to Revit."""
        for p in self.sheet.Parameters:
            d = p.Definition
            if p.IsReadOnly or d.Name in skip:
                continue
            if isinstance(d, DB.InternalDefinition) and \
                    d.BuiltInParameter != DB.BuiltInParameter.INVALID:
                continue
            q = sheet.LookupParameter(d.Name)
            if q is None or q.IsReadOnly or q.StorageType != p.StorageType:
                continue
            try:
                st = p.StorageType
                if st == DB.StorageType.String:
                    if p.AsString():
                        q.Set(p.AsString())
                elif st == DB.StorageType.Integer:
                    q.Set(p.AsInteger())
                elif st == DB.StorageType.Double:
                    q.Set(p.AsDouble())
                elif st == DB.StorageType.ElementId:
                    q.Set(p.AsElementId())
            except Exception as ex:
                warnings.append("{}: param '{}' not copied ({})".format(
                    sheet.SheetNumber, d.Name, ex))


def find_zone_view(doc, proto_view, zone, known_zones):
    """Key plan for 'zone': same name as the prototype's key plan with the
    zone word swapped, e.g. 'KEY PLAN - NORTH' -> 'KEY PLAN - SOUTH'.
    known_zones = every zone name in this run (to spot which one the
    prototype's name carries)."""
    if not zone:
        return proto_view
    want = proto_view.Name.upper()
    found = [z for z in known_zones if z and z.upper() in want]
    if found:
        old = max(found, key=len).upper()
        if old == zone.upper():
            return proto_view
        want = want.replace(old, zone.upper())
    else:
        want = "{} {}".format(want, zone.upper())
    for v in DB.FilteredElementCollector(doc).OfClass(DB.View):
        if not v.IsTemplate and v.Name.upper() == want:
            return v
    return None


def placed_view_ids(doc):
    return set(eid_int(vp.ViewId) for vp in
               DB.FilteredElementCollector(doc).OfClass(DB.Viewport))


def can_place(doc, sheet, view):
    try:
        return DB.Viewport.CanAddViewToSheet(doc, sheet.Id, view.Id)
    except Exception:
        return False
