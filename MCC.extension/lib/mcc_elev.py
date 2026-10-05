# -*- coding: utf-8 -*-
"""MCC soffit tagging engine. Shared by Tag Soffit / Refresh Support Elev.

MCC's 3-Box tags read straight from the model: top and bottom come from
the element, and shoring height = element bottom - BOTTOM_REF_PARAM.
This module finds the concrete support below a point (slab, SOG, footing)
by shooting a ray down through the model, and writes that elevation to
BOTTOM_REF_PARAM so the tags can show the height.

Ray at plan XY:  T = first concrete hit, B = bottom of that (joined)
concrete, S = next concrete surface below = shore support.
"""
from mcc_compat import eid_int
from pyrevit import DB
from System.Collections.Generic import List

# =====================================================================
# CONFIG - Kalae / MCC R22-R23 template
# =====================================================================
BOTTOM_REF_PARAM = "Bottom Reference Elevation"   # on floors and beams
AREA_PARAM = "Sheet Area Name"

# category -> (tag family, tag type). Set a category to None to skip it.
TAGS = {
    "floor":  ("Tag - Floor - Box, Top Elev, Bot Elev (R22)",
               "3-Box (Type, Opaque, Left)"),
    "beam":   ("Tag - Beam - Box, Top Elev, Bott Elev, Clear Height (R22)",
               "3-Box (Type, Opaque, Left)"),
    "column": ("Tag - Column - Box, Soffit and Floor (R22)",
               "Soffit - (Type, Opaque, Left)"),
    "wall":   ("Tag - Wall - Box, Top Elev, Bot Elev, Height (R22)",
               "3-Box (All Info Calculated)"),
}
CATS = {
    "floor":  DB.BuiltInCategory.OST_Floors,
    "beam":   DB.BuiltInCategory.OST_StructuralFraming,
    "column": DB.BuiltInCategory.OST_StructuralColumns,
    "wall":   DB.BuiltInCategory.OST_Walls,
}
SUPPORT_CATS = ("floor", "beam")   # categories that get BOTTOM_REF_PARAM

RAY_START_ABOVE = 0.5      # ft above the element's top to start the ray
MAX_DROP = 80.0            # ft; ignore support farther down than this
JOIN_TOL = 1.0 / 96        # ft; faces this close = joined concrete
ROUND_TO = 8               # round reports to 1/8"
RAY_VIEW_NAME = "MCC_RAYCAST_3D"
CONCRETE_CATS = [
    DB.BuiltInCategory.OST_Floors,
    DB.BuiltInCategory.OST_StructuralFraming,
    DB.BuiltInCategory.OST_StructuralFoundation,
]
# =====================================================================


def type_name(e):
    p = e.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    return p.AsString() if p else e.Name


# ---------------- formatting ----------------
def fmt_ft_in(ft):
    neg = ft < 0
    total = round(abs(ft) * 12.0 * ROUND_TO) / ROUND_TO
    feet = int(total // 12)
    inches = total - feet * 12
    whole = int(inches)
    num, den = int(round((inches - whole) * ROUND_TO)), ROUND_TO
    while num and num % 2 == 0:
        num //= 2
        den //= 2
    frac = " {}/{}".format(num, den) if num else ""
    return "{}{}'-{}{}\"".format("-" if neg else "", feet, whole, frac)


# ---------------- model helpers ----------------
def get_tag_symbol(doc, key):
    fam, typ = TAGS.get(key) or (None, None)
    if not fam:
        return None
    for s in DB.FilteredElementCollector(doc).OfClass(DB.FamilySymbol):
        if s.FamilyName == fam and (typ is None or type_name(s) == typ):
            return s
    return None


def elements_in_view(doc, view, key):
    return list(DB.FilteredElementCollector(doc, view.Id)
                .OfCategory(CATS[key]).WhereElementIsNotElementType())


def tagged_ids(doc, view):
    ids = set()
    for t in DB.FilteredElementCollector(doc, view.Id) \
            .OfClass(DB.IndependentTag):
        try:
            for i in t.GetTaggedLocalElementIds():
                ids.add(eid_int(i))
        except AttributeError:            # pre-2022 API
            ids.add(eid_int(t.TaggedLocalElementId))
    return ids


def tag_point(doc, view, elem):
    """Bounding-box center in the view; good enough to drag from."""
    bb = elem.get_BoundingBox(view)
    if bb is None:
        return None
    return DB.XYZ((bb.Min.X + bb.Max.X) / 2, (bb.Min.Y + bb.Max.Y) / 2, 0)


def place_tag(doc, view, symbol, elem, pt):
    ref = DB.Reference(elem)
    return DB.IndependentTag.Create(doc, symbol.Id, view.Id, ref, False,
                                    DB.TagOrientation.Horizontal, pt)


def get_ray_view(doc):
    """Find or create a clean 3D view for raycasting (call in a txn)."""
    for v in DB.FilteredElementCollector(doc).OfClass(DB.View3D):
        if not v.IsTemplate and v.Name == RAY_VIEW_NAME:
            return v
    vft = next(t for t in DB.FilteredElementCollector(doc)
               .OfClass(DB.ViewFamilyType)
               if t.ViewFamily == DB.ViewFamily.ThreeDimensional)
    v = DB.View3D.CreateIsometric(doc, vft.Id)
    v.Name = RAY_VIEW_NAME
    return v


class Result(object):
    def __init__(self):
        self.top = self.bottom = self.support = None
        self.note = ""


def measure(doc, ray_view, x, y, level, top_z=None):
    """Top / bottom / support elevations at XY, on the level-head basis.
    top_z = internal Z to start just above (the element's top); defaults
    to the level."""
    level_z = level.ProjectElevation
    base = level_z - level.Elevation
    cat_ids = List[DB.BuiltInCategory](CONCRETE_CATS)
    ri = DB.ReferenceIntersector(DB.ElementMulticategoryFilter(cat_ids),
                                 DB.FindReferenceTarget.Face, ray_view)
    start = (top_z if top_z is not None else level_z) + RAY_START_ABOVE
    origin = DB.XYZ(x, y, start)
    raw = ri.Find(origin, DB.XYZ(0, 0, -1))

    hits, seen = [], set()
    for rwc in raw:
        z = origin.Z - rwc.Proximity
        eid = eid_int(rwc.GetReference().ElementId)
        key = (eid, round(z * 96))
        if key not in seen:
            seen.add(key)
            hits.append((z, eid))
    hits.sort(key=lambda h: -h[0])

    r = Result()
    if not hits:
        r.note = "no concrete at this point"
        return r
    r.top = hits[0][0]
    i = 1
    while i < len(hits):
        z, eid = hits[i]
        nxt = hits[i + 1] if i + 1 < len(hits) else None
        if nxt and abs(nxt[0] - z) < JOIN_TOL and nxt[1] != eid:
            i += 2                      # joined elements: still in concrete
            continue
        r.bottom = z
        if nxt and (z - nxt[0]) <= MAX_DROP:
            r.support = nxt[0]
        break
    if r.bottom is None:
        r.note = "bottom of concrete not found"
        return r
    if r.support is None:
        r.note = "no support below"
    r.top -= base
    r.bottom -= base
    if r.support is not None:
        r.support -= base
    return r


def support_point(doc, view, elem):
    """(x, y, top_z) to probe for an element's support: bbox center
    (floor) or curve midpoint (beam); top_z = element's top."""
    bb = elem.get_BoundingBox(None)
    if bb is None:
        return None
    loc = elem.Location
    if isinstance(loc, DB.LocationCurve):
        p = loc.Curve.Evaluate(0.5, True)
        return p.X, p.Y, bb.Max.Z
    return (bb.Min.X + bb.Max.X) / 2, (bb.Min.Y + bb.Max.Y) / 2, bb.Max.Z


def write_support(elem, r):
    """Write support elevation to BOTTOM_REF_PARAM. Returns
    (status, old_value, new_value) with status in ok/unchanged/missing."""
    p = elem.LookupParameter(BOTTOM_REF_PARAM)
    if p is None or p.IsReadOnly:
        return "missing", None, None
    if eid_int(elem.GroupId) != -1:     # member of a model group
        return "grouped", p.AsDouble(), r.support
    if r.support is None:
        return "nosupport", p.AsDouble(), None
    old = p.AsDouble()
    if abs(old - r.support) < 1.0 / 192:
        return "unchanged", old, r.support
    p.Set(r.support)
    return "ok", old, r.support
