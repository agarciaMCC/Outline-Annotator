# -*- coding: utf-8 -*-
"""Sheet Builder - clone finished sheets of any type (soffit, embed,
vertical plans...) to other levels.

The prototype sheets are the whole spec. For every target level, each
prototype sheet gets a copy with the level swapped in its number and
name, and every level-based plan view on it gets a counterpart view:
- same view type, template, and every setting the template doesn't
  control (scale, phase, detail level, underlay...), level references
  shifted to the target level
- view range copied relative to the level (Associated +4' stays so)
- dependents recreated under the matching parent on the target level
- crop (scope box / sketched shape / crop box), crop + annotation crop
  visibility, grid ends / bubbles / elbows
- placed on the sheet exactly where the prototype's is, same viewport
  type, rotation and title position
Legends, schedules, text, symbols and sheet parameters are copied too.

Second mode, "Split a view into zone sheets", sets up the first level of
a new sheet type: dependents of one plan view + a sheet for each."""
__title__ = "Sheet\nBuilder"
__author__ = "MCC ENG"

from mcc_compat import eid_int
from System.Collections.Generic import List
from pyrevit import revit, DB, forms, script
import mcc_sheet as ms

doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()

# =====================================================================
LEVEL_PREFIX = "LEVEL"          # "LEVEL-3" -> level token "3"
COPY_GRIDS = True               # grid ends / bubbles / elbows per view
# =====================================================================

CLONE = "Clone sheets to other levels"
SPLIT = "Split a view into zone sheets (set up a first level)"
INV = DB.ElementId.InvalidElementId
BIP = DB.BuiltInParameter

levels = sorted(DB.FilteredElementCollector(doc).OfClass(DB.Level),
                key=lambda l: l.ProjectElevation)
lvl_index = dict((eid_int(l.Id), i) for i, l in enumerate(levels))
all_views = [v for v in DB.FilteredElementCollector(doc).OfClass(DB.View)
             if not v.IsTemplate]
existing_view_names = set(v.Name for v in all_views)
existing_numbers = set(s.SheetNumber for s in
                       DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet))
placed = ms.placed_view_ids(doc)
PLAN_TYPES = (DB.ViewType.FloorPlan, DB.ViewType.EngineeringPlan,
              DB.ViewType.CeilingPlan)
warnings = []


def pick(items, title, multiselect=False, **kw):
    res = forms.SelectFromList.show(items, title=title,
                                    multiselect=multiselect, **kw)
    if res is None:
        script.exit()
    return res


def tok(level):
    return ms.level_token(level.Name, LEVEL_PREFIX)


def unique_name(base):
    name, n = base, 2
    while name in existing_view_names:
        name = "{} ({})".format(base, n)
        n += 1
    existing_view_names.add(name)
    return name


def is_plan(v):
    return isinstance(v, DB.ViewPlan) and not v.IsTemplate and \
        v.ViewType in PLAN_TYPES and v.GenLevel is not None


def is_dependent(v):
    return v.GetPrimaryViewId() != INV


def swap_level_text(text, new_tok):
    """'LEVEL 3 - NORTH (EMBED PLAN)' -> 'LEVEL 5 - NORTH (EMBED PLAN)'.
    None when the text names no level."""
    if not text or not ms.level_refs(text):
        return None
    return ms.rename_for_level(text, new_tok)


def swap_sheet_number(number, old_tok, new_tok):
    """'6.3.0' -> '6.5.0' (series.level.index). None if the level token
    isn't one of the dotted parts."""
    parts = number.split(".")
    for i, p in enumerate(parts):
        if i > 0 and p.upper() == old_tok.upper():
            parts[i] = new_tok
            return ".".join(parts)
    return None


def shift_level(level, diff):
    i = lvl_index.get(eid_int(level.Id))
    if i is None or not 0 <= i + diff < len(levels):
        return None
    return levels[i + diff]


def view_name_for(src, target_level):
    n = swap_level_text(src.Name, tok(target_level))
    return n or "{} - L{}".format(src.Name, tok(target_level))


# ---------------------------------------------------------- copy settings
SKIP_BIPS = set(int(b) for b in (
    BIP.VIEW_NAME, BIP.PLAN_VIEW_LEVEL, BIP.VIEW_DEPENDENCY,
    BIP.VIEW_TEMPLATE, BIP.VIEWER_VOLUME_OF_INTEREST_CROP,
    BIP.VIEWER_CROP_REGION, BIP.VIEWER_CROP_REGION_VISIBLE,
    BIP.VIEWER_ANNOTATION_CROP_ACTIVE, BIP.VIEW_DESCRIPTION,
    BIP.VIEWER_SHEET_NUMBER, BIP.VIEWER_DETAIL_NUMBER,
    BIP.ELEM_TYPE_PARAM, BIP.ELEM_FAMILY_AND_TYPE_PARAM,
    BIP.ELEM_FAMILY_PARAM))


def controlled_ids(view):
    t = doc.GetElement(view.ViewTemplateId)
    if t is None:
        return set()
    allp = set(eid_int(i) for i in t.GetTemplateParameterIds())
    non = set(eid_int(i) for i in t.GetNonControlledTemplateParameterIds())
    return allp - non


def copy_view_settings(src, dst, diff):
    """Every writable setting of src that dst's template doesn't control.
    Level references (underlay...) move by 'diff' levels. View name and
    level are left alone; Title on Sheet gets its level swapped."""
    ctrl = controlled_ids(dst)
    for p in src.Parameters:
        try:
            if p.IsReadOnly or eid_int(p.Id) in SKIP_BIPS or \
                    eid_int(p.Id) in ctrl:
                continue
            d = p.Definition
            if p.IsShared:
                q = dst.get_Parameter(p.GUID)
            elif isinstance(d, DB.InternalDefinition) and \
                    d.BuiltInParameter != BIP.INVALID:
                q = dst.get_Parameter(d.BuiltInParameter)
            else:
                q = dst.LookupParameter(d.Name)
            if q is None or q.IsReadOnly or q.StorageType != p.StorageType:
                continue
            st = p.StorageType
            if st == DB.StorageType.String:
                if p.AsString() is not None and q.AsString() != p.AsString():
                    q.Set(p.AsString())
            elif st == DB.StorageType.Integer:
                if q.AsInteger() != p.AsInteger():
                    q.Set(p.AsInteger())
            elif st == DB.StorageType.Double:
                if abs(q.AsDouble() - p.AsDouble()) > 1e-9:
                    q.Set(p.AsDouble())
            elif st == DB.StorageType.ElementId:
                eid = p.AsElementId()
                e = doc.GetElement(eid)
                if isinstance(e, DB.Level):
                    lv = shift_level(e, diff)
                    eid = lv.Id if lv is not None else eid
                if q.AsElementId() != eid:
                    q.Set(eid)
        except Exception:
            pass
    # Title on Sheet, level swapped
    try:
        t = src.get_Parameter(BIP.VIEW_DESCRIPTION).AsString()
        if t:
            nt = swap_level_text(t, tok(dst.GenLevel)) or t
            dst.get_Parameter(BIP.VIEW_DESCRIPTION).Set(nt)
    except Exception:
        pass


def copy_view_range(src, dst, diff):
    """Same planes and offsets; explicit level ids move by 'diff'."""
    if int(BIP.PLAN_VIEW_RANGE) in controlled_ids(dst):
        return
    try:
        svr = src.GetViewRange()
        dvr = dst.GetViewRange()
        for pl in (DB.PlanViewPlane.TopClipPlane, DB.PlanViewPlane.CutPlane,
                   DB.PlanViewPlane.BottomClipPlane,
                   DB.PlanViewPlane.ViewDepthPlane):
            lid = svr.GetLevelId(pl)
            e = doc.GetElement(lid)
            if isinstance(e, DB.Level):
                lv = shift_level(e, diff)
                lid = lv.Id if lv is not None else lid
            dvr.SetLevelId(pl, lid)
            dvr.SetOffset(pl, svr.GetOffset(pl))
        dst.SetViewRange(dvr)
    except Exception as ex:
        warnings.append("{}: view range not copied ({})".format(dst.Name, ex))


def copy_crop(src, dst, dz, target_level):
    """Scope box / sketched shape / crop box, plus crop visibility and
    annotation crop, from src to dst."""
    try:
        box = doc.GetElement(ms.view_scope_box_id(src))
        shape = ms.sketched_crop(src)
        rect = ms.rect_crop(src)
        if box is not None:
            # same box if it spans the target level, else its level twin
            use = box
            _, _, z0, z1 = ms.box_center(box)
            if not (z0 - 0.5 <= target_level.ProjectElevation <= z1 + 0.5):
                twin = swap_level_text(box.Name, tok(target_level))
                use = next((b for b in ms.scope_boxes(doc)
                            if twin and b.Name == twin), None)
            if use is not None:
                dst.get_Parameter(BIP.VIEWER_VOLUME_OF_INTEREST_CROP) \
                    .Set(use.Id)
            else:
                ms.apply_rect_crop(dst, src.CropBox, dz)
                warnings.append("{}: no scope box for this level - crop box "
                                "copied instead".format(dst.Name))
        elif shape is not None:
            ms.apply_crop_shape(dst, shape, dz)
        elif rect is not None:
            ms.apply_rect_crop(dst, rect, dz)
        else:
            dst.CropBoxActive = src.CropBoxActive
        dst.CropBoxVisible = src.CropBoxVisible
        a = src.get_Parameter(BIP.VIEWER_ANNOTATION_CROP_ACTIVE)
        b = dst.get_Parameter(BIP.VIEWER_ANNOTATION_CROP_ACTIVE)
        if a is not None and b is not None and not b.IsReadOnly:
            b.Set(a.AsInteger())
    except Exception as ex:
        warnings.append("{}: crop not fully copied ({})".format(dst.Name, ex))


def create_like(src, target_level, diff, name):
    v = DB.ViewPlan.Create(doc, src.GetTypeId(), target_level.Id)
    v.Name = unique_name(name)
    if src.ViewTemplateId != INV:
        v.ViewTemplateId = src.ViewTemplateId
    copy_view_settings(src, v, diff)
    copy_view_range(src, v, diff)
    return v


# ---------------------------------------------------------- find / reuse
plans = [v for v in all_views if is_plan(v)]
parent_cache = {}           # (src parent id, level id) -> view
taken = set()


def find_parent(src_parent, target_level):
    """Existing whole-level twin of src_parent on target_level: same name
    with the level swapped, else the one view with the same template and
    type there (asks when several)."""
    want = view_name_for(src_parent, target_level).upper()
    cands = [v for v in plans if v.GenLevel.Id == target_level.Id and
             not is_dependent(v) and v.Id != src_parent.Id]
    hit = next((v for v in cands if v.Name.upper() == want), None)
    if hit is None:
        same = [v for v in cands if v.GetTypeId() == src_parent.GetTypeId()
                and v.ViewTemplateId == src_parent.ViewTemplateId and
                src_parent.ViewTemplateId != INV]
        if len(same) == 1:
            hit = same[0]
        elif len(same) > 1:
            new_opt = "(make a new one: {})".format(
                view_name_for(src_parent, target_level))
            by = dict((v.Name, v) for v in same)
            p = pick(sorted(by) + [new_opt],
                     "{} - which view matches '{}'?".format(
                         target_level.Name, src_parent.Name))
            hit = by.get(p)
    return hit


class Job(object):
    """One view to make on one target level."""

    def __init__(self, src_vp, src_view, target_level, diff):
        self.src_vp, self.src, self.level, self.diff = \
            src_vp, src_view, target_level, diff
        self.name = view_name_for(src_view, target_level)
        self.dz = target_level.ProjectElevation - \
            src_view.GenLevel.ProjectElevation
        self.existing = None
        self.parent_src = doc.GetElement(src_view.GetPrimaryViewId()) \
            if is_dependent(src_view) else None
        self.parent = None          # existing target parent
        if self.parent_src is not None:
            key = (eid_int(self.parent_src.Id), eid_int(target_level.Id))
            if key not in parent_cache:
                parent_cache[key] = find_parent(self.parent_src, target_level)
            self.parent = parent_cache[key]
            if self.parent is not None:
                self.existing = next(
                    (v for v in plans if v.GetPrimaryViewId() == self.parent.Id
                     and v.Name.upper() == self.name.upper()
                     and eid_int(v.Id) not in placed
                     and eid_int(v.Id) not in taken), None)
        else:
            self.existing = next(
                (v for v in plans if v.GenLevel.Id == target_level.Id and
                 not is_dependent(v) and v.Name.upper() == self.name.upper()
                 and eid_int(v.Id) not in placed
                 and eid_int(v.Id) not in taken), None)
        if self.existing is not None:
            taken.add(eid_int(self.existing.Id))

    def label(self):
        if self.existing is not None:
            return "reuse {}".format(self.existing.Name)
        if self.parent_src is not None:
            return "new {} (of {})".format(
                self.name, self.parent.Name if self.parent is not None
                else "NEW " + view_name_for(self.parent_src, self.level))
        return "new {}".format(self.name)


made_parents = {}


def build_view(job):
    if job.existing is not None:
        v = job.existing
    elif job.parent_src is None:
        v = create_like(job.src, job.level, job.diff, job.name)
    else:
        key = (eid_int(job.parent_src.Id), eid_int(job.level.Id))
        par = job.parent or made_parents.get(key)
        if par is None:
            par = create_like(job.parent_src, job.level, job.diff,
                              view_name_for(job.parent_src, job.level))
            copy_crop(job.parent_src, par, job.dz, job.level)
            made_parents[key] = par
        v = doc.GetElement(par.Duplicate(DB.ViewDuplicateOption.AsDependent))
        v.Name = unique_name(job.name)
        copy_view_settings(job.src, v, job.diff)
    if job.existing is None or job.parent_src is not None:
        copy_crop(job.src, v, job.dz, job.level)
    return v


# =====================================================================
mode = forms.CommandSwitchWindow.show([CLONE, SPLIT], message="Sheet Builder")
if not mode:
    script.exit()

# ---------------------------------------------------------------- SPLIT
if mode == SPLIT:
    av = doc.ActiveView
    cands = sorted([v for v in plans if not is_dependent(v)],
                   key=lambda v: (v.GenLevel.ProjectElevation, v.Name))
    lab = dict(("{}   [{}]".format(v.Name, v.GenLevel.Name), v) for v in cands)
    first = [k for k, v in lab.items() if v.Id == av.Id]
    parent = lab[pick(first + sorted(k for k in lab if k not in first),
                      "1/4  Plan view to split into zones")]
    boxes = ms.scope_boxes(doc)
    bl = dict((b.Name, b) for b in boxes)
    TYPED = "(type zone names - I'll sketch each crop with Edit Crop)"
    ch = pick([TYPED] + sorted(bl), "2/4  Zones: scope boxes and/or typed names",
              multiselect=True)
    zones = [(ms.zone_name(bl[n].Name) or bl[n].Name, bl[n])
             for n in ch if n in bl]
    if TYPED in ch:
        s = forms.ask_for_string(default="NORTH, SOUTH", title="Zones",
                                 prompt="Zone names, comma separated, in "
                                        "sheet order")
        zones += [(z.strip().upper(), None) for z in (s or "").split(",")
                  if z.strip()]
    if not zones:
        script.exit()
    tbs = list(DB.FilteredElementCollector(doc)
               .OfCategory(DB.BuiltInCategory.OST_TitleBlocks)
               .WhereElementIsElementType())
    tbl = dict(("{} : {}".format(t.FamilyName, ms.type_name(t)), t)
               for t in tbs)
    tb = tbl[pick(sorted(tbl), "3/4  Title block")]
    t0 = tok(parent.GenLevel)
    num_fmt = forms.ask_for_string(
        default="1.{}.{{idx}}".format(t0), title="Sheet Builder",
        prompt="4/4  Sheet number - {idx} = 0, 1, 2... per zone")
    name_fmt = forms.ask_for_string(
        default="LEVEL {} - {{zone}} (SOFFIT PLAN)".format(t0),
        title="Sheet Builder", prompt="Sheet name - {zone} = zone name")
    if not num_fmt or not name_fmt:
        script.exit()
    rows = []
    with revit.Transaction("MCC: Sheet Builder - split"):
        for i, (zone, box) in enumerate(zones):
            no = num_fmt.format(idx=i)
            if no in existing_numbers:
                rows.append([no, zone, "-", "SKIP: sheet exists"])
                continue
            v = doc.GetElement(parent.Duplicate(
                DB.ViewDuplicateOption.AsDependent))
            v.Name = unique_name("{} - {}".format(parent.Name, zone.upper()))
            v.CropBoxActive = True
            if box is not None:
                v.get_Parameter(BIP.VIEWER_VOLUME_OF_INTEREST_CROP).Set(box.Id)
            p = v.get_Parameter(BIP.VIEWER_ANNOTATION_CROP_ACTIVE)
            if p is not None and not p.IsReadOnly:
                p.Set(1)
            sh = DB.ViewSheet.Create(doc, tb.Id)
            sh.SheetNumber = no
            sh.Name = name_fmt.format(zone=zone).upper()
            existing_numbers.add(no)
            doc.Regenerate()
            tbi = next(iter(DB.FilteredElementCollector(doc, sh.Id)
                            .OfCategory(DB.BuiltInCategory.OST_TitleBlocks)),
                       None)
            c = DB.XYZ(1.5, 1.2, 0)
            if tbi is not None:
                bb = tbi.get_BoundingBox(sh)
                if bb is not None:
                    c = (bb.Min + bb.Max) * 0.5
            DB.Viewport.Create(doc, sh.Id, v.Id, DB.XYZ(c.X, c.Y, 0))
            rows.append([no, sh.Name, v.Name,
                         "box {}".format(box.Name) if box else
                         "sketch the crop (Edit Crop)"])
    output.print_md("## Sheet Builder - zone sheets from {}".format(
        parent.Name))
    output.print_table(rows, columns=["Sheet", "Name", "View", "Crop"])
    output.print_md("**Next:** sketch any crops, place legends / notes / "
                    "titles on these sheets, set grids - then use *Clone "
                    "sheets to other levels* with these as the prototype.")
    script.exit()

# ---------------------------------------------------------------- CLONE
sheets = sorted(DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet),
                key=lambda s: s.SheetNumber)
pre_sel = set(eid_int(i) for i in uidoc.Selection.GetElementIds())
slab = dict(("{}  {}".format(s.SheetNumber, s.Name), s) for s in sheets)
# sheets selected in the Project Browser are used directly
pre = [k for k, s in slab.items() if eid_int(s.Id) in pre_sel]
chosen_sheets = pre or pick(sorted(slab), "1/3  Prototype sheets to clone "
                            "(tip: select them in the Project Browser first)",
                            multiselect=True)
if not chosen_sheets:
    script.exit()


class Proto(object):
    def __init__(self, sheet):
        self.sheet = sheet
        self.p = ms.Prototype(doc, sheet)
        vps = list(DB.FilteredElementCollector(doc, sheet.Id)
                   .OfClass(DB.Viewport))
        self.level_vps = [(vp, doc.GetElement(vp.ViewId)) for vp in vps
                          if is_plan(doc.GetElement(vp.ViewId))]
        self.other_vps = [(vp, doc.GetElement(vp.ViewId)) for vp in vps
                          if not is_plan(doc.GetElement(vp.ViewId))]
        self.level = None
        if self.level_vps:
            def area(item):
                o = item[0].GetBoxOutline()
                d = o.MaximumPoint - o.MinimumPoint
                return d.X * d.Y
            self.level = max(self.level_vps, key=area)[1].GenLevel


protos = []
for k in chosen_sheets:
    pr = Proto(slab[k])
    if pr.level is None:
        warnings.append("{}: no level-based plan view on it - skipped"
                        .format(pr.sheet.SheetNumber))
    else:
        protos.append(pr)
if not protos:
    forms.alert("None of those sheets has a plan view on it.",
                exitscript=True)

src_levels = set(eid_int(pr.level.Id) for pr in protos)
targets = pick([l for l in levels if eid_int(l.Id) not in src_levels]
               if len(src_levels) == 1 else levels,
               "2/3  Levels to clone to", name_attr="Name", multiselect=True)
if not targets:
    script.exit()


class Row(object):
    def __init__(self, pr, target):
        self.pr, self.level = pr, target
        self.diff = lvl_index[eid_int(target.Id)] - \
            lvl_index[eid_int(pr.level.Id)]
        self.number = swap_sheet_number(pr.sheet.SheetNumber, tok(pr.level),
                                        tok(target))
        self.name = swap_level_text(pr.sheet.Name, tok(target)) or \
            pr.sheet.Name
        self.jobs, self.status = [], ""
        if target.Id == pr.level.Id:
            self.status = "SKIP: same level as the prototype"
        elif self.number is None:
            self.status = "SKIP: can't find level '{}' in sheet number {}" \
                .format(tok(pr.level), pr.sheet.SheetNumber)
        elif self.number in existing_numbers:
            self.status = "SKIP: sheet {} exists".format(self.number)
        if self.status:
            return
        for vp, v in pr.level_vps:
            tl = shift_level(v.GenLevel, self.diff)
            if tl is None:
                self.status = "SKIP: no level {} levels from {}".format(
                    self.diff, v.GenLevel.Name)
                return
            self.jobs.append(Job(vp, v, tl, self.diff))

    def label(self):
        s = "  <- " + self.status if self.status else ""
        views = "; ".join(j.label() for j in self.jobs)
        return "{:<10} {:<40} from {}  [{}]{}".format(
            self.number or "?", self.name, self.pr.sheet.SheetNumber,
            views, s)


rows = [Row(pr, t) for t in targets for pr in protos]
ok = [r for r in rows if not r.status]
bad = [r for r in rows if r.status]
if not ok:
    forms.alert("Nothing to build:\n" + "\n".join(r.label() for r in bad),
                exitscript=True)
lab = dict((r.label(), r) for r in ok)
todo = [lab[k] for k in pick(sorted(lab, key=lambda k: lab[k].number),
                             "3/3  Sheets to create (untick any you don't "
                             "want)" + ("  -  {} skipped".format(len(bad))
                                        if bad else ""),
                             multiselect=True, checked_by_default=True)]
if not todo:
    script.exit()

results = []
with revit.Transaction("MCC: Sheet Builder"):
    for r in todo:
        pr = r.pr
        tb_id = pr.p.titleblock_type_id
        if tb_id is None:
            tb_id = next(iter(DB.FilteredElementCollector(doc)
                              .OfCategory(DB.BuiltInCategory.OST_TitleBlocks)
                              .WhereElementIsElementType())).Id
        sheet = DB.ViewSheet.Create(doc, tb_id)
        sheet.SheetNumber = r.number
        sheet.Name = r.name
        existing_numbers.add(r.number)
        pr.p.copy_sheet_params(sheet, warnings)
        made = []
        for job in r.jobs:
            try:
                v = build_view(job)
                doc.Regenerate()
                if COPY_GRIDS:
                    n, nh, gbad = ms.copy_grid_display(doc, job.src, v)
                    for gname, why in gbad:
                        warnings.append("{}: grid {} ({})".format(
                            v.Name, gname, why))
                ms.place_like(doc, sheet, v, job.src_vp, job.src)
                if v.Scale != job.src.Scale:
                    warnings.append("{}: scale 1:{} vs prototype 1:{} - won't "
                                    "line up".format(v.Name, v.Scale,
                                                     job.src.Scale))
                made.append(v.Name)
            except Exception as ex:
                warnings.append("{}: {} not built ({})".format(
                    r.number, job.name, ex))
        for vp, v in pr.other_vps:
            if ms.can_place(doc, sheet, v):
                c = vp.GetBoxCenter()
                nvp = ms.place_at(doc, sheet, v, (c.X, c.Y), vp.GetTypeId())
                ms.copy_label(nvp, ms.read_label(vp))
            else:
                warnings.append("{}: '{}' can only be on one sheet ({}) - "
                                "not copied".format(r.number, v.Name,
                                                    v.ViewType))
        pr.p.copy_annotations(sheet, warnings)
        results.append([r.number, r.name, pr.sheet.SheetNumber,
                        "<br>".join(made)])

output.print_md("## Sheet Builder")
output.print_table(results, columns=["Sheet", "Name", "From", "Views"])
if bad:
    output.print_md("**Skipped**")
    for r in bad:
        output.print_md("- {} from {} - {}".format(
            r.number or "?", r.pr.sheet.SheetNumber, r.status))
if warnings:
    output.print_md("**Warnings**")
    for w in warnings:
        output.print_md("- " + w)
