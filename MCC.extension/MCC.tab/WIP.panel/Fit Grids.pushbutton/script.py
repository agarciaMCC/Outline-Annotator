# -*- coding: utf-8 -*-
"""Trims grids IN THE CHOSEN VIEWS ONLY (view-specific / 2D extents).
- Parallel grids stay aligned: one bubble line per side.
- Where a grid leaves a visible slab edge, the row is set by the bubble
  nearest the slab: it sits exactly the clearance away (true distance,
  so angled edges work). No bubble lands inside a visible slab.
- Where the crop cuts the slab (no hard edge visible), bubbles sit just
  outside the crop edge.
- Grids that don't cross the crop get their bubbles hidden.
Run from a sheet to pre-tick the plan views placed on it. "Set as
default" remembers the form. Rules live in lib/mcc_gridfit.py."""
__title__ = "Fit\nGrids"
__author__ = "MCC ENG"

from pyrevit import revit, DB, forms, script
from System.Windows import Visibility, Thickness
from System.Windows.Controls import CheckBox
import mcc_view as V
import mcc_plan as P
import mcc_gridfit as F

import os
doc = revit.doc
active = doc.ActiveView

# crash-safe step log (flushed every line) - if Revit dies, the last line
# of Outline Annotator/fitgrids_debug.log says which grid / call it was on
import io
try:
    _here = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _here = os.path.dirname(script.get_bundle_file("script.py"))
LOG = os.path.join(_here, "..", "..", "..", "..", "fitgrids_debug.log")
_logf = []


def log(msg):
    try:
        if not _logf:
            _logf.append(io.open(LOG, "w", encoding="utf-8"))
        f = _logf[0]
        f.write(u"{}\n".format(msg))
        f.flush()
        os.fsync(f.fileno())
    except Exception:
        pass


cfg = script.get_config()

# =====================================================================
# FACTORY DEFAULTS
# =====================================================================
MARGIN_FT = 16.0      # bubble clearance from slab edge: edge dims ~4-7
                      # ft, grid dims ~10-13 ft, then the bubble
GAP_IN = 0.125        # paper inches outside the crop edge
PLAN_TYPES = (DB.ViewType.FloorPlan, DB.ViewType.CeilingPlan,
              DB.ViewType.EngineeringPlan, DB.ViewType.AreaPlan)
# =====================================================================


def candidate_views():
    """[(view, is_dependent)]: parents by name, each followed by its
    dependents."""
    vs = [v for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan)
          if not v.IsTemplate and v.ViewType in PLAN_TYPES]
    ids = set(V.eid_int(v.Id) for v in vs)
    parents, kids = [], {}
    for v in vs:
        pid = v.GetPrimaryViewId()
        if pid != DB.ElementId.InvalidElementId and V.eid_int(pid) in ids:
            kids.setdefault(V.eid_int(pid), []).append(v)
        else:
            parents.append(v)
    rows = []
    for p in sorted(parents, key=lambda x: x.Name):
        rows.append((p, False))
        for k in sorted(kids.get(V.eid_int(p.Id), []), key=lambda x: x.Name):
            rows.append((k, True))
    return rows


def sheet_view_ids():
    if isinstance(active, DB.ViewSheet):
        return set(V.eid_int(i) for i in active.GetAllPlacedViews())
    return set()


class FitGridsWindow(forms.WPFWindow):
    def __init__(self, rows, on_sheet):
        forms.WPFWindow.__init__(self, script.get_bundle_file("ui.xaml"))
        self.result = None
        self.boxes = []
        self.on_sheet = on_sheet
        pre = on_sheet or set([V.eid_int(active.Id)])
        for v, dep in rows:
            cb = CheckBox()
            name = v.Name + (u"   [on sheet]" if V.eid_int(v.Id) in on_sheet
                             else u"")
            cb.Content = (u"└ " if dep else u"") + name
            cb.Margin = Thickness(18 if dep else 0, 1, 0, 1)
            cb.IsChecked = V.eid_int(v.Id) in pre
            cb.Checked += self.count_changed
            cb.Unchecked += self.count_changed
            self.pnl_views.Children.Add(cb)
            self.boxes.append((cb, v))
        if not on_sheet:
            self.btn_sheet.IsEnabled = False
            self.btn_sheet.ToolTip = "Open a sheet first to use this"
        self.txt_margin.Text = str(cfg.get_option("margin", MARGIN_FT))
        self.txt_gap.Text = str(cfg.get_option("gap", GAP_IN))
        self.count_changed(None, None)

    def picked(self):
        return [v for cb, v in self.boxes if cb.IsChecked]

    def count_changed(self, sender, args):
        self.lbl_count.Text = "Views ({} ticked)".format(len(self.picked()))

    def filter_changed(self, sender, args):
        f = self.txt_filter.Text.strip().lower()
        for cb, v in self.boxes:
            cb.Visibility = Visibility.Visible \
                if (not f or f in v.Name.lower()) else Visibility.Collapsed

    def _set_visible(self, state):
        for cb, v in self.boxes:
            if cb.Visibility == Visibility.Visible:
                cb.IsChecked = state

    def views_all(self, sender, args):
        self._set_visible(True)

    def views_none(self, sender, args):
        self._set_visible(False)

    def views_sheet(self, sender, args):
        for cb, v in self.boxes:
            cb.IsChecked = V.eid_int(v.Id) in self.on_sheet

    def ok_click(self, sender, args):
        views = self.picked()
        if not views:
            forms.alert("No views ticked.")
            return
        try:
            margin = float(self.txt_margin.Text)
            gap = float(self.txt_gap.Text)
        except ValueError:
            forms.alert("Clearance and gap must be numbers.")
            return
        if self.chk_default.IsChecked:
            cfg.margin, cfg.gap = margin, gap
            script.save_config()
        self.result = (views, margin, gap)
        self.Close()

    def cancel_click(self, sender, args):
        self.Close()


# ---------------------------------------------------------------------
OPTS = DB.Options()


def view_grids(view):
    """[(grid, g0, u, end0, end1)] straight grids that exist in the view
    (including ones outside the crop, so their bubbles can be hidden)."""
    try:
        if view.GetCategoryHidden(DB.ElementId(DB.BuiltInCategory.OST_Grids)):
            return []
    except Exception:
        pass
    out = []
    for g in DB.FilteredElementCollector(doc).OfClass(DB.Grid):
        try:
            # Revit 2023 can crash when asked about a datum that can't
            # show in the view - always ask this first
            if not g.CanBeVisibleInView(view):
                continue
            if g.IsHidden(view):
                continue
            log(u"  read {} ({})".format(g.Name, V.eid_int(g.Id)))
            cs = g.GetCurvesInView(DB.DatumExtentType.ViewSpecific, view)
            if not cs or not cs.Count:
                continue
            c = cs[0]
        except Exception:
            continue                    # grid doesn't reach this view
        if not isinstance(c, DB.Line):
            continue
        d = c.Direction
        m = (d.X ** 2 + d.Y ** 2) ** 0.5
        if m < 1e-9:
            continue
        p0, p1 = c.GetEndPoint(0), c.GetEndPoint(1)
        out.append((g, (p0.X, p0.Y), (d.X / m, d.Y / m),
                    (p0.X, p0.Y), (p1.X, p1.Y), p0.Z))
    return out


def slab_outlines(view):
    floors, _ = V.soffit_floors(doc, view)
    polys = []
    for f in floors:
        try:
            for outer, inners, oe, ie in P.soffit_loops(f, OPTS):
                polys.append(outer)
        except Exception:
            h = P.plan_poly(f, OPTS, view)
            if h:
                polys.append(h)
    return polys


def apply_line(g, view, line):
    for end in (DB.DatumEnds.End0, DB.DatumEnds.End1):
        try:
            if g.GetDatumExtentTypeInView(end, view) != \
                    DB.DatumExtentType.ViewSpecific:
                g.SetDatumExtentType(end, view,
                                     DB.DatumExtentType.ViewSpecific)
        except Exception:
            pass
    g.SetCurveInView(DB.DatumExtentType.ViewSpecific, view, line)


def matches(g, view, line, tol=0.02):
    c = V.view_curve(g, view)
    p, q = c.GetEndPoint(0), c.GetEndPoint(1)
    a, b = line.GetEndPoint(0), line.GetEndPoint(1)
    d = lambda m, k: abs(m.X - k.X) + abs(m.Y - k.Y)
    return (d(p, a) < tol and d(q, b) < tol) or \
        (d(p, b) < tol and d(q, a) < tol)


def fit_view(view, margin, gap_in):
    """Returns (applied [(grid, line)], hidden count, problem or None)."""
    log(u"view {} ({})".format(view.Name, V.eid_int(view.Id)))
    raw = view_grids(view)
    log(u"  {} grids".format(len(raw)))
    if not raw:
        return [], 0, "no straight grids"
    crop = V.crop_polygon(view)
    slabs = slab_outlines(view)
    log(u"  crop {} pts, {} slab outlines".format(
        len(crop) if crop else 0, len(slabs)))
    if not crop and not slabs:
        return [], 0, "no crop and no slab visible to fit to"
    grids = [(i, r[1], r[2], r[3], r[4]) for i, r in enumerate(raw)]
    fams = V.grid_families([(i, g0, u, (-u[1], u[0]))
                            for i, g0, u, a, b in grids])
    plan = F.fit(grids, slabs, crop, margin, gap_in * view.Scale / 12.0,
                 fams)
    log(u"  plan: {} actions".format(len(plan)))
    applied, hidden, fails = [], 0, 0
    for i, act in plan.items():
        g, z = raw[i][0], raw[i][5]
        log(u"  {} {} ({})".format(act[0], g.Name, V.eid_int(g.Id)))
        try:
            if act[0] == "hide":
                for end in (DB.DatumEnds.End0, DB.DatumEnds.End1):
                    if g.IsBubbleVisibleInView(end, view):
                        g.HideBubbleInView(end, view)
                hidden += 1
            else:
                a, b = act[1], act[2]
                line = DB.Line.CreateBound(DB.XYZ(a[0], a[1], z),
                                           DB.XYZ(b[0], b[1], z))
                apply_line(g, view, line)
                applied.append((g, line))
        except Exception:
            fails += 1
    prob = "{} grid(s) Revit refused".format(fails) if fails else None
    return applied, hidden, prob


# ---------------------------------------------------------------------
rows = candidate_views()
if not rows:
    forms.alert("No plan views in this model.", exitscript=True)
win = FitGridsWindow(rows, sheet_view_ids())
win.ShowDialog()
if not win.result:
    script.exit()
views, margin, gap = win.result

# dependents first, parents last: if Revit shares grid ends between a
# parent and its zones, the parent's fit is the one kept (and flagged)
views.sort(key=lambda v: 0 if v.GetPrimaryViewId() !=
           DB.ElementId.InvalidElementId else 1)

problems, done = [], []
with revit.Transaction("MCC: Fit grids"):
    for view in views:
        try:
            applied, hidden, prob = fit_view(view, margin, gap)
        except Exception as ex:
            problems.append(u"{}: {}".format(view.Name, ex))
            continue
        if prob:
            problems.append(u"{}: {}".format(view.Name, prob))
        done.extend((g, view, line) for g, line in applied)
    log("regenerate")
    doc.Regenerate()
    log("verify")
    moved = {}
    for g, view, line in done:
        if not matches(g, view, line):
            moved[view.Name] = moved.get(view.Name, 0) + 1
    for name, k in sorted(moved.items()):
        problems.append(u"{}: {} grid(s) were changed again by another "
                        u"view (parent/zone views share grid ends)"
                        .format(name, k))

log("done")
if problems:
    forms.alert("Fit Grids finished with notes:\n\n" +
                "\n".join(problems[:25]), title="Fit Grids")
