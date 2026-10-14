# -*- coding: utf-8 -*-
"""Section marks in plans that follow whether their section is on a sheet.

The Hide Unplaced Sections button hides, in the open plan, the marks of
sections not on a sheet and records them on the plan. The updater registered
in startup.py shows those recorded marks again as soon as their section is
placed on a sheet. Marks someone hid by hand are never touched."""
import System
from Autodesk.Revit.DB import (BuiltInCategory, ElementClassFilter, ElementId,
                               FilteredElementCollector, View, ViewPlan,
                               ViewType, Viewport, Element, IUpdater,
                               UpdaterId, UpdaterRegistry, ChangePriority)
from Autodesk.Revit.DB.ExtensibleStorage import (Schema, SchemaBuilder,
                                                 Entity, AccessLevel)
from System import Guid
from System.Collections.Generic import List
from mcc_compat import eid_int, make_eid

UPDATER_GUID = Guid("6b1f6a52-3c0e-4f7e-9a3d-2f61c8d4a7e1")
SCHEMA_GUID = Guid("c4a1d3e8-5f27-4b90-8e6a-91d0b7f2a35c")
FIELD = "HiddenMarks"


# ---------------- what the button hid, stored on each plan ----------------
def _schema():
    s = Schema.Lookup(SCHEMA_GUID)
    if s is None:
        b = SchemaBuilder(SCHEMA_GUID)
        b.SetSchemaName("MCCHiddenSectionMarks")
        b.SetReadAccessLevel(AccessLevel.Public)
        b.SetWriteAccessLevel(AccessLevel.Public)
        b.AddSimpleField(FIELD, System.String)
        s = b.Finish()
    return s


def recorded(plan):
    """Ids (as ints) of marks the button hid in plan."""
    s = Schema.Lookup(SCHEMA_GUID)
    if s is None:
        return set()
    ent = plan.GetEntity(s)
    if not ent.IsValid():
        return set()
    txt = ent.Get[System.String](FIELD) or ""
    return set(int(x) for x in txt.split(",") if x)


def _record(plan, ids):
    ent = Entity(_schema())
    ent.Set[System.String](FIELD, ",".join(str(i) for i in sorted(ids)))
    plan.SetEntity(ent)


# ---------------- sections and their marks ----------------
def placed_view_ids(doc):
    """Ids (as ints) of every view placed on a sheet."""
    return set(eid_int(vp.ViewId) for vp in
               FilteredElementCollector(doc).OfClass(Viewport))


def section_views_by_name(doc):
    """{name: ViewSection} for building sections (not elevations, callouts,
    detail views or templates)."""
    out = {}
    for v in FilteredElementCollector(doc).OfClass(View):
        if v.ViewType == ViewType.Section and not v.IsTemplate:
            out[v.Name] = v
    return out


def section_marks(doc):
    """[(mark element, its section view)] for every section mark in the
    model. A mark carries the same name as the view it points at."""
    sections = section_views_by_name(doc)
    out = []
    for m in (FilteredElementCollector(doc)
              .OfCategory(BuiltInCategory.OST_Viewers)
              .WhereElementIsNotElementType()):
        v = sections.get(m.Name)
        if v is not None:
            out.append((m, v))
    return out


def _ids(int_ids):
    return List[ElementId]([make_eid(i) for i in int_ids])


def sync_plan(doc, plan):
    """Hide the marks of unplaced sections in plan; show the ones this
    button hid earlier whose section is now placed. Caller opens the
    transaction. -> (hidden count, shown count)."""
    placed = placed_view_ids(doc)
    mine = recorded(plan)
    visible = set(eid_int(i) for i in
                  FilteredElementCollector(doc, plan.Id)
                  .OfCategory(BuiltInCategory.OST_Viewers).ToElementIds())
    hide, show = set(), set()
    for m, v in section_marks(doc):
        mid = eid_int(m.Id)
        on_sheet = eid_int(v.Id) in placed
        if not on_sheet and mid in visible and m.CanBeHidden(plan):
            hide.add(mid)
        elif on_sheet and mid in mine and m.IsHidden(plan):
            show.add(mid)
    if hide:
        plan.HideElements(_ids(hide))
    if show:
        plan.UnhideElements(_ids(show))
    keep = set(i for i in mine if i not in show and doc.GetElement(make_eid(i)))
    if hide or keep != mine:
        _record(plan, keep | hide)
    return len(hide), len(show)


def show_marks_of(doc, view_ids):
    """In every plan the button ran in, show the recorded marks of the
    given section views."""
    wanted = set(eid_int(i) for i in view_ids)
    marks = set(eid_int(m.Id) for m, v in section_marks(doc)
                if eid_int(v.Id) in wanted)
    if not marks or Schema.Lookup(SCHEMA_GUID) is None:
        return
    for plan in FilteredElementCollector(doc).OfClass(ViewPlan):
        if plan.IsTemplate:
            continue
        mine = recorded(plan)
        back = mine & marks
        if back:
            plan.UnhideElements(_ids(back))
            _record(plan, mine - back)


# ---------------- automatic show on placement ----------------
class SectionPlacedUpdater(IUpdater):
    """Runs inside the transaction that puts a view on a sheet, so showing
    the marks again is part of the same undo step."""

    def __init__(self, addin_id):
        self._id = UpdaterId(addin_id, UPDATER_GUID)

    def Execute(self, data):
        try:
            doc = data.GetDocument()
            ids = []
            for i in data.GetAddedElementIds():
                vp = doc.GetElement(i)
                if isinstance(vp, Viewport):
                    v = doc.GetElement(vp.ViewId)
                    if v is not None and v.ViewType == ViewType.Section:
                        ids.append(v.Id)
            if ids:
                show_marks_of(doc, ids)
        except Exception:
            pass                        # never block placing a view

    def GetUpdaterId(self):
        return self._id

    def GetUpdaterName(self):
        return "MCC Show Placed Section Marks"

    def GetAdditionalInformation(self):
        return "Shows section marks in plans once the section is on a sheet."

    def GetChangePriority(self):
        return ChangePriority.Views


def register_updater(addin_id):
    """Register (or re-register after a pyRevit reload). Optional, so models
    opened without the MCC tab don't warn about a missing updater."""
    upd = SectionPlacedUpdater(addin_id)
    uid = upd.GetUpdaterId()
    if UpdaterRegistry.IsUpdaterRegistered(uid):
        UpdaterRegistry.UnregisterUpdater(uid)
    UpdaterRegistry.RegisterUpdater(upd, True)
    UpdaterRegistry.AddTrigger(uid, ElementClassFilter(Viewport),
                               Element.GetChangeTypeElementAddition())
    return upd
