# -*- coding: utf-8 -*-
"""Creates Revit grids from PDF plan sheets (structural and/or
architectural). Reads the grid bubbles and lines out of the vector PDF,
sets the spacing from the called-out grid dimensions, and lines the two
sheets up on their common grids. Where the sheets call out different
dimensions you pick which one to use. Then pick where one grid
intersection goes in the model and the named grids are created.

Needs Python 3 with PyMuPDF on this PC for the PDF step (the button finds
Python and offers to install PyMuPDF the first time). Scanned PDFs can't
be read - the sheet must be a vector PDF exported from Revit/CAD."""
__title__ = "Grids\nfrom PDF"
__author__ = "MCC ENG"

from mcc_compat import eid_int
import glob
import os
import tempfile

from pyrevit import revit, DB, forms, script
from System.Diagnostics import Process, ProcessStartInfo
from System.Windows import Controls, Thickness, Visibility, GridLength, \
    GridUnitType, FontWeights, TextWrapping, VerticalAlignment
from System.Windows.Media import Brushes
from System.Windows.Threading import DispatcherPriority
from System import Action
import mcc_gridpdf as GP

doc = revit.doc
uidoc = revit.uidoc
cfg = script.get_config()
HERE = os.path.dirname(__file__)
DETECT = os.path.join(HERE, "pdfgrids", "detect.py")
WORK = os.path.join(tempfile.gettempdir(), "MCC_GridsFromPDF")
if not os.path.isdir(WORK):
    os.makedirs(WORK)

SCALES = [("Auto - read from grid dimensions", "auto"),
          ('1/32" = 1\'-0"', 1 / 32.0), ('1/16" = 1\'-0"', 1 / 16.0),
          ('3/32" = 1\'-0"', 3 / 32.0), ('1/8" = 1\'-0"', 1 / 8.0),
          ('3/16" = 1\'-0"', 3 / 16.0), ('1/4" = 1\'-0"', 1 / 4.0),
          ('3/8" = 1\'-0"', 3 / 8.0), ('1/2" = 1\'-0"', 1 / 2.0),
          ('1" = 10\'', 1 / 10.0), ('1" = 20\'', 1 / 20.0),
          ('1" = 30\'', 1 / 30.0), ('1" = 40\'', 1 / 40.0)]


# ---------------------------------------------------------------------------
# Python 3 + PyMuPDF on this PC
# ---------------------------------------------------------------------------
def run(exe, args, timeout_ms=300000):
    psi = ProcessStartInfo(exe, " ".join(args))
    psi.UseShellExecute = False
    psi.CreateNoWindow = True
    psi.RedirectStandardOutput = True
    psi.RedirectStandardError = True
    try:
        p = Process.Start(psi)
    except Exception as ex:
        return None, "", str(ex)
    out = p.StandardOutput.ReadToEndAsync()
    err = p.StandardError.ReadToEndAsync()
    if not p.WaitForExit(timeout_ms):
        p.Kill()
        return None, "", "timed out"
    return p.ExitCode, out.Result, err.Result


def q(s):
    return '"%s"' % s


def python_candidates():
    saved = cfg.get_option("python", "")
    if saved:
        yield saved, []
    yield "py", ["-3"]
    yield "python", []
    yield "python3", []
    roots = [os.environ.get("LOCALAPPDATA", ""), os.environ.get("ProgramFiles", ""),
             os.environ.get("ProgramFiles(x86)", ""), "C:\\"]
    pats = []
    for r in roots:
        if r:
            pats += [os.path.join(r, "Programs", "Python", "Python3*", "python.exe"),
                     os.path.join(r, "Python3*", "python.exe")]
    for pat in pats:
        for exe in sorted(glob.glob(pat), reverse=True):
            yield exe, []


def is_py3(exe, pre):
    code, out, err = run(exe, pre + ["-c", q("import sys;print(sys.version_info[0])")], 20000)
    return code == 0 and out.strip() == "3"


def find_python():
    for exe, pre in python_candidates():
        if is_py3(exe, pre):
            return exe, pre
    return None, None


def ensure_python():
    exe, pre = find_python()
    if not exe:
        ok = forms.alert(
            "Python 3 isn't installed on this PC (or isn't on the PATH). The PDF step "
            "needs it.\n\nInstall it from python.org (tick 'Add python.exe to PATH'), "
            "then run the button again - or browse to python.exe now.",
            title="Grids from PDF", options=["Browse to python.exe", "Cancel"])
        if ok != "Browse to python.exe":
            return None, None
        exe = forms.pick_file(file_ext="exe")
        pre = []
        if not exe or not is_py3(exe, pre):
            forms.alert("That isn't a Python 3 executable.")
            return None, None
    code, out, err = run(exe, pre + ["-c", q("import pymupdf")], 30000)
    if code != 0:
        ok = forms.alert(
            "The PDF reader (PyMuPDF) isn't installed for this Python yet.\n\n"
            "Install it now? (runs: pip install --user pymupdf - needs internet, "
            "about a minute)", title="Grids from PDF", yes=True, no=True)
        if not ok:
            return None, None
        code, out, err = run(exe, pre + ["-m", "pip", "install", "--user", "pymupdf"], 600000)
        code2, o2, e2 = run(exe, pre + ["-c", q("import pymupdf")], 30000)
        if code2 != 0:
            forms.alert("PyMuPDF install failed:\n\n" + (err or out)[-1500:])
            return None, None
    if cfg.get_option("python", "") != exe and not pre:
        cfg.python = exe
        script.save_config()
    return exe, pre


# ---------------------------------------------------------------------------
# model
# ---------------------------------------------------------------------------
def type_name(t):
    p = t.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    return p.AsString() if p else str(eid_int(t.Id))


GRID_TYPES = dict((type_name(t), t.Id) for t in
                  DB.FilteredElementCollector(doc).OfClass(DB.GridType))
DEFAULT_TYPE = doc.GetDefaultElementTypeId(DB.ElementTypeGroup.GridType)
EXISTING = set(g.Name for g in DB.FilteredElementCollector(doc).OfClass(DB.Grid))
DIM_DEFAULT = "(project default)"
DIM_TYPES = {}
for _t in DB.FilteredElementCollector(doc).OfClass(DB.DimensionType):
    try:
        if _t.StyleType == DB.DimensionStyleType.Linear:
            DIM_TYPES[type_name(_t)] = _t
    except Exception:
        pass


def paper_in(txt):
    """'3/8', '0.375', '1 1/4' -> inches."""
    tot = 0.0
    for part in txt.replace('"', '').split():
        if "/" in part:
            a, b = part.split("/")
            tot += float(a) / float(b)
        else:
            tot += float(part)
    return tot


# ---------------------------------------------------------------------------
# window
# ---------------------------------------------------------------------------
def tb(text, bold=False, color=None, wrap=False):
    t = Controls.TextBlock()
    t.Text = text
    t.VerticalAlignment = VerticalAlignment.Center
    t.Margin = Thickness(0, 2, 10, 2)
    if bold:
        t.FontWeight = FontWeights.SemiBold
    if color:
        t.Foreground = color
    if wrap:
        t.TextWrapping = TextWrapping.Wrap
    return t


class GridsWindow(forms.WPFWindow):
    def __init__(self):
        forms.WPFWindow.__init__(self, script.get_bundle_file("ui.xaml"))
        self.result = None
        self.res = None
        self.rows = []          # (checkbox, grid label)
        self.picks = []         # (key, combobox)
        self.cmb_scale.ItemsSource = [s[0] for s in SCALES]
        self.cmb_scale.SelectedIndex = min(int(cfg.get_option("scale", 0)), len(SCALES) - 1)
        names = sorted(GRID_TYPES)
        self.cmb_type.ItemsSource = names
        saved = cfg.get_option("grid_type", "")
        dflt = [n for n in names if GRID_TYPES[n] == DEFAULT_TYPE]
        self.cmb_type.SelectedItem = saved if saved in names else (dflt[0] if dflt else None)
        self.txt_rot.Text = str(cfg.get_option("rotation", "0"))
        self.chk_even.IsChecked = cfg.get_option("even", False)
        self.chk_dims.IsChecked = cfg.get_option("dims", True)
        self.txt_inset.Text = cfg.get_option("inset", "3/8")
        dnames = [DIM_DEFAULT] + sorted(DIM_TYPES)
        self.cmb_dimtype.ItemsSource = dnames
        dsaved = cfg.get_option("dim_type", DIM_DEFAULT)
        self.cmb_dimtype.SelectedItem = dsaved if dsaved in dnames else DIM_DEFAULT
        if cfg.get_option("place", "pick") == "origin":
            self.rb_origin.IsChecked = True

    # --- sheets --------------------------------------------------------
    def _browse(self, box):
        start = os.path.dirname(box.Text) if box.Text else cfg.get_option("folder", "")
        f = forms.pick_file(file_ext="pdf", init_dir=start if os.path.isdir(start) else "")
        if f:
            box.Text = f
            cfg.folder = os.path.dirname(f)
            script.save_config()

    def browse1(self, sender, args):
        self._browse(self.txt_pdf1)

    def browse2(self, sender, args):
        self._browse(self.txt_pdf2)

    def status(self, text, err=False):
        self.lbl_status.Text = text
        self.lbl_status.Foreground = Brushes.Firebrick if err else Brushes.DimGray
        # let WPF repaint before a blocking step
        self.Dispatcher.Invoke(Action(lambda: None), DispatcherPriority.Background)

    def detect_click(self, sender, args):
        sheets = []
        for box, page in ((self.txt_pdf1, self.txt_page1), (self.txt_pdf2, self.txt_page2)):
            f = box.Text.strip().strip('"')
            if not f:
                continue
            if not os.path.isfile(f):
                self.status("File not found: " + f, True)
                return
            try:
                pg = int(page.Text.strip() or "1")
            except ValueError:
                self.status("Page must be a number.", True)
                return
            sheets.append("%s:%d" % (f, pg))
        if not sheets:
            self.status("Pick at least one PDF sheet.", True)
            return
        self.status("Finding Python...")
        exe, pre = ensure_python()
        if not exe:
            self.status("Python 3 with PyMuPDF is needed for the PDF step.", True)
            return
        scale = SCALES[self.cmb_scale.SelectedIndex][1]
        out = os.path.join(WORK, "result.json")
        if os.path.exists(out):
            os.remove(out)
        args = pre + [q(DETECT), "--out", q(out), "--check-dir", q(WORK),
                      "--scale", "auto" if scale == "auto" else "%.6f" % scale] + \
            [q(s) for s in sheets]
        self.status("Reading grids from %d sheet(s)..." % len(sheets))
        code, so, se = run(exe, args)
        if code != 0 or not os.path.exists(out):
            self.status("Couldn't read the sheet(s): " + (se or so or "no output").strip()[-600:], True)
            return
        self.res = GP.load(out)
        self.fill()

    # --- review --------------------------------------------------------
    def fill(self):
        res = self.res
        info = []
        for s in res["sheets"]:
            line = "%s p%d: %s (%s), %d bubbles" % (s["name"], s["page"], s["scale"],
                                                   s["scale_source"], s["bubbles"])
            if s.get("registration"):
                line += ", aligned to %s on %d grids" % (res["sheets"][0]["name"],
                                                        s["registration"]["common"])
            info.append(line)
            info += ["   ! " + w for w in s["warnings"]]
            info += ["   ! %s %s excluded - %s" % (s["name"], e["label"], "; ".join(e["flags"]))
                     for e in s["excluded"]]
        info += ["! " + n for n in res["notes"]]
        self.status("\n".join(info))
        # conflicts
        self.pnl_conflicts.Children.Clear()
        self.picks = []
        for key, desc, opts, note in GP.conflicts(res):
            row = Controls.DockPanel()
            row.Margin = Thickness(0, 2, 0, 2)
            cb = Controls.ComboBox()
            cb.Width = 300
            cb.ItemsSource = ["- pick -"] + opts
            cb.SelectedIndex = 0
            Controls.DockPanel.SetDock(cb, Controls.Dock.Right)
            row.Children.Add(cb)
            row.Children.Add(tb("%s   (%s)" % (desc, note), wrap=True))
            self.pnl_conflicts.Children.Add(row)
            self.picks.append((key, cb))
        self.grp_conflicts.Visibility = Visibility.Visible if self.picks else Visibility.Collapsed
        # grid table
        T = self.tbl_grids
        T.Children.Clear()
        T.RowDefinitions.Clear()
        T.ColumnDefinitions.Clear()
        for w in (30, 70, 70, 0):
            cd = Controls.ColumnDefinition()
            cd.Width = GridLength(w) if w else GridLength(1, GridUnitType.Star)
            T.ColumnDefinitions.Add(cd)
        self.rows = []
        grids = [g for F in res["families"] for g in F["grids"]]
        heads = ["", "Grid", "Angle", "Notes"]
        self._add_row([tb(h, bold=True) for h in heads])
        for F in res["families"]:
            for g in F["grids"]:
                chk = Controls.CheckBox()
                chk.VerticalAlignment = VerticalAlignment.Center
                notes = list(g["flags"])
                exists = g["label"] in EXISTING
                if exists:
                    notes.insert(0, "already in the model")
                chk.IsChecked = not exists or bool(self.chk_replace.IsChecked)
                chk.IsEnabled = not exists or bool(self.chk_replace.IsChecked)
                chk.Checked += self.count
                chk.Unchecked += self.count
                color = Brushes.DarkOrange if notes else None
                self._add_row([chk, tb(g["label"], bold=True), tb(u"%g\u00b0" % F["angle"]),
                               tb("; ".join(notes), color=color, wrap=True)])
                self.rows.append((chk, g["label"]))
        self.btn_find.IsEnabled = any(l in EXISTING for c, l in self.rows)
        # origin combos
        labels = sorted([g["label"] for g in grids], key=GP.natural)
        self.cmb_ox.ItemsSource = labels
        self.cmb_oy.ItemsSource = labels
        built = GP.build(res, dict((k, 0) for k, c in self.picks))
        a, b = GP.default_origin(built)
        self.cmb_ox.SelectedItem = a
        self.cmb_oy.SelectedItem = b
        self.btn_check.IsEnabled = any(s.get("check_pdf") for s in res["sheets"])
        self.btn_ok.IsEnabled = True
        self.count(None, None)

    def _add_row(self, cells):
        T = self.tbl_grids
        rd = Controls.RowDefinition()
        rd.Height = GridLength.Auto
        T.RowDefinitions.Add(rd)
        r = T.RowDefinitions.Count - 1
        for c, el in enumerate(cells):
            Controls.Grid.SetRow(el, r)
            Controls.Grid.SetColumn(el, c)
            T.Children.Add(el)

    def count(self, sender, args):
        n = sum(1 for c, l in self.rows if c.IsChecked)
        self.lbl_count.Text = "%d of %d grids will be created" % (n, len(self.rows))

    def all_click(self, sender, args):
        for c, l in self.rows:
            if c.IsEnabled:
                c.IsChecked = True

    def none_click(self, sender, args):
        for c, l in self.rows:
            c.IsChecked = False

    def replace_changed(self, sender, args):
        on = bool(self.chk_replace.IsChecked)
        for c, l in self.rows:
            if l in EXISTING:
                c.IsEnabled = on
                c.IsChecked = on
        self.count(None, None)

    def find_click(self, sender, args):
        self.result = dict(find=[l for c, l in self.rows if l in EXISTING])
        self.Close()

    def check_click(self, sender, args):
        for s in self.res["sheets"]:
            if s.get("check_pdf") and os.path.exists(s["check_pdf"]):
                os.startfile(s["check_pdf"])

    # --- create --------------------------------------------------------
    def ok_click(self, sender, args):
        picks = {}
        for key, cb in self.picks:
            if cb.SelectedIndex < 1:
                forms.alert("Pick a value for every line in 'Sheets disagree' first.")
                return
            picks[key] = cb.SelectedIndex - 1
        keep = set(l for c, l in self.rows if c.IsChecked)
        if not keep:
            forms.alert("No grids ticked.")
            return
        ox, oy = self.cmb_ox.SelectedItem, self.cmb_oy.SelectedItem
        try:
            rot = float(self.txt_rot.Text.strip() or "0")
        except ValueError:
            forms.alert("Rotation must be a number (degrees).")
            return
        grids = GP.build(self.res, picks)
        byl = dict((g["label"], g) for g in grids)
        ref = GP.intersection(byl[ox], byl[oy]) if ox in byl and oy in byl and ox != oy else None
        if ref is None:
            forms.alert("Pick two grids that cross for the placement point.")
            return
        if self.chk_even.IsChecked:
            GP.even_ends(grids)
        place = "origin" if self.rb_origin.IsChecked else "pick"
        tname = self.cmb_type.SelectedItem
        dims = bool(self.chk_dims.IsChecked)
        try:
            inset = paper_in(self.txt_inset.Text)
        except (ValueError, ZeroDivisionError):
            forms.alert("Set-in distance must be inches, e.g. 3/8 or 0.5")
            return
        dname = self.cmb_dimtype.SelectedItem
        if self.chk_default.IsChecked:
            cfg.scale = self.cmb_scale.SelectedIndex
            cfg.grid_type = tname or ""
            cfg.rotation = self.txt_rot.Text.strip() or "0"
            cfg.even = bool(self.chk_even.IsChecked)
            cfg.place = place
            cfg.dims = dims
            cfg.inset = self.txt_inset.Text.strip()
            cfg.dim_type = dname or DIM_DEFAULT
            script.save_config()
        replace = [l for l in keep if l in EXISTING]
        if replace and not forms.alert(
                "%d grid(s) already in the model will be DELETED and recreated: %s\n\n"
                "Dimensions and tags attached to them will be deleted too. Continue?"
                % (len(replace), ", ".join(sorted(replace, key=GP.natural))),
                title="Grids from PDF", yes=True, no=True):
            return
        self.result = dict(grids=[g for g in grids if g["label"] in keep], ref=ref,
                           replace=replace,
                           ox=ox, oy=oy, rot=rot, place=place,
                           type_id=GRID_TYPES.get(tname, DEFAULT_TYPE),
                           dims=dims, inset=inset, dim_type=DIM_TYPES.get(dname))
        self.Close()

    def cancel_click(self, sender, args):
        self.Close()


win = GridsWindow()
win.ShowDialog()
R = win.result
if not R:
    script.exit()

def level_span():
    lv = list(DB.FilteredElementCollector(doc).OfClass(DB.Level))
    if not lv:
        return -10.0, 100.0, []
    return (min(l.ProjectElevation for l in lv) - 10.0, max(l.ProjectElevation for l in lv) + 10.0,
            sorted(lv, key=lambda l: l.ProjectElevation))


if "find" in R:
    from System.Collections.Generic import List
    view = doc.ActiveView
    names = set(R["find"])
    found = sorted([g for g in DB.FilteredElementCollector(doc).OfClass(DB.Grid)
                    if g.Name in names], key=lambda g: GP.natural(g.Name))
    zlo, zhi, levels = level_span()
    ft = lambda z: GP.ftin(z)

    def height(g):
        try:
            ext = g.GetExtents()
            return ext.MinimumPoint.Z, ext.MaximumPoint.Z
        except Exception:
            z = g.Curve.GetEndPoint(0).Z
            return z, z

    def missed(g):
        z0, z1 = height(g)
        return [l.Name for l in levels if not (z0 - 0.01 <= l.ProjectElevation <= z1 + 0.01)]

    # 1. fix first (the prompt would otherwise cover the table)
    short = [g for g in found if missed(g)]
    fixed = 0
    if short and forms.alert(
            "%d of the %d grids with these names don't reach every level, so plan views "
            "can't show them.\n\nStretch them through all levels (%s to %s)? Only their "
            "height changes." % (len(short), len(found), ft(zlo), ft(zhi)),
            title="Grids from PDF", yes=True, no=True):
        bad = []
        with revit.Transaction("MCC: Stretch grids through all levels"):
            for g in short:
                try:
                    g.SetVerticalExtents(zlo, zhi)
                    fixed += 1
                except Exception as ex:
                    bad.append("%s: %s" % (g.Name, ex))
        if bad:
            forms.alert("Couldn't stretch:\n" + "\n".join(bad))

    # 2. then report, with the heights as they are now
    shown = set(eid_int(e.Id) for e in
                DB.FilteredElementCollector(doc, view.Id).OfClass(DB.Grid))
    out = script.get_output()
    rows = []
    for g in found:
        a, b = g.Curve.GetEndPoint(0), g.Curve.GetEndPoint(1)
        z0, z1 = height(g)
        m = missed(g)
        ws = ""
        if doc.IsWorkshared:
            w = doc.GetWorksetTable().GetWorkset(g.WorksetId)
            ws = w.Name + ("" if w.IsOpen else " (CLOSED)")
        rows.append([g.Name, out.linkify(g.Id),
                     "(%.1f, %.1f) to (%.1f, %.1f)" % (a.X, a.Y, b.X, b.Y),
                     "%s to %s" % (ft(z0), ft(z1)),
                     ("misses %d of %d" % (len(m), len(levels))) if m else "all",
                     "yes" if eid_int(g.Id) in shown else "NO",
                     "yes" if g.IsHidden(view) else "", ws])
    out.print_md("### Grids already in the model with these names")
    if fixed:
        out.print_md("**Stretched %d grid(s) through all levels.**" % fixed)
    out.print_md("Active view: **%s**. Levels run %s to %s. Coordinates in feet from the "
                 "internal origin. Click an id to zoom to that grid."
                 % (view.Name, ft(zlo + 10), ft(zhi - 10)))
    out.print_table(rows, columns=["Grid", "Id", "Line (ft)", "Height", "Reaches levels",
                                   "Shown in this view", "Hidden in view", "Workset"])
    # why might this view hide them?
    checks = []
    cat = DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Grids)
    tid = view.ViewTemplateId
    tmpl = doc.GetElement(tid) if tid != DB.ElementId.InvalidElementId else None
    try:
        if view.GetCategoryHidden(cat.Id):
            checks.append("**Grids are turned OFF** in this view's Visibility/Graphics"
                          + (" - set by view template **%s** (edit the template, or "
                             "remove it from the view)" % tmpl.Name if tmpl else
                             " (VG > Annotation Categories > Grids)"))
    except Exception:
        pass
    if tmpl:
        checks.append("View template: **%s**" % tmpl.Name)
    for v, who in ((view, "this view"), (tmpl, "view template '%s'" % (tmpl.Name if tmpl else ""))):
        if v is None:
            continue
        try:
            if v is tmpl and v.GetCategoryHidden(cat.Id):
                checks.append("**Grids are turned OFF in %s** (VG > Annotation Categories)" % who)
        except Exception:
            pass
        try:
            if v.AreAnnotationCategoriesHidden:
                checks.append("**'Show annotation categories in this view' is OFF in %s** - "
                              "that hides all grids (VG > Annotation Categories, top tick box)"
                              % who)
        except Exception:
            pass
    try:
        if view.IsTemporaryViewPropertiesModeEnabled():
            checks.append("**Temporary View Properties is on** - it can override VG")
    except Exception:
        pass
    try:
        sub = [c for c in cat.SubCategories]
        for c in sub:
            if view.GetCategoryHidden(c.Id):
                checks.append("Grid subcategory '%s' is off in this view" % c.Name)
    except Exception:
        pass
    try:
        dv = view.get_Parameter(DB.BuiltInParameter.VIEW_DISCIPLINE)
        checks.append("Discipline: %s, detail level: %s" % (dv.AsValueString() if dv else "?",
                                                             view.DetailLevel))
    except Exception:
        pass
    try:
        if view.AreGraphicsOverridesAllowed():
            for fid in view.GetFilters():
                if view.GetFilterVisibility(fid):
                    continue
                f = doc.GetElement(fid)
                hits = 0
                try:
                    enabled = view.GetIsFilterEnabled(fid)
                except Exception:
                    enabled = True
                if enabled and found:
                    cats = set(eid_int(c) for c in f.GetCategories())
                    if eid_int(cat.Id) in cats:
                        ef = f.GetElementFilter() if hasattr(f, "GetElementFilter") else None
                        hits = sum(1 for g in found if ef is None or ef.PassesFilter(doc, g.Id))
                if hits:
                    checks.append("**Filter '%s' HIDES %d of these grids** - it includes the "
                                  "Grids category. Fix: VV > Filters, or edit the filter's "
                                  "rule/categories" % (f.Name, hits))
                else:
                    checks.append("Filter '%s' hides elements in this view (not these grids)"
                                  % f.Name)
    except Exception:
        pass
    if view.CropBoxActive:
        bb = view.CropBox
        tr = bb.Transform
        lo, hi = tr.OfPoint(bb.Min), tr.OfPoint(bb.Max)
        checks.append("Crop region is on: about (%.0f, %.0f) to (%.0f, %.0f) ft - compare "
                      "with the grid lines above" % (min(lo.X, hi.X), min(lo.Y, hi.Y),
                                                     max(lo.X, hi.X), max(lo.Y, hi.Y)))
    try:
        if view.IsTemporaryHideIsolateActive():
            checks.append("Temporary Hide/Isolate is on in this view")
    except Exception:
        pass
    if hasattr(view, "GetViewRange"):
        vr = view.GetViewRange()
        lvl = doc.GetElement(vr.GetLevelId(DB.PlanViewPlane.CutPlane))
        if lvl:
            cut = lvl.ProjectElevation + vr.GetOffset(DB.PlanViewPlane.CutPlane)
            checks.append("Cut plane at %s (grids must span it)" % ft(cut))
    out.print_md("#### This view")
    for c in checks or ["No view setting found that hides grids."]:
        out.print_md("- " + c)
    if found:
        uidoc.Selection.SetElementIds(List[DB.ElementId]([g.Id for g in found]))
        vis = List[DB.ElementId]([g.Id for g in found if eid_int(g.Id) in shown])
        if vis.Count:
            uidoc.ShowElements(vis)
        else:
            out.print_md("**None of them show in this view.** Check the columns above: "
                         "workset (closed?), hidden in view, or Visibility/Graphics > Grids.")
    script.exit()

if R["place"] == "pick":
    from Autodesk.Revit.Exceptions import OperationCanceledException
    try:
        pt = uidoc.Selection.PickPoint("Click where grid %s / %s goes" % (R["ox"], R["oy"]))
    except OperationCanceledException:
        script.exit()
    except Exception:
        forms.alert("Can't pick a point in this view. Open a floor plan view and run "
                    "again, or choose 'the internal origin'.", exitscript=True)
    target = (pt.X, pt.Y)
else:
    target = (0.0, 0.0)

lines = GP.to_model(R["grids"], R["ref"], target, R["rot"])
zlo, zhi, _lv = level_span()
z0 = zlo + 10.0
made, failed, created = [], [], []
dim_note = ""
with revit.Transaction("MCC: Grids from PDF"):
    if R.get("replace"):
        old = [g.Id for g in DB.FilteredElementCollector(doc).OfClass(DB.Grid)
               if g.Name in set(R["replace"])]
        from System.Collections.Generic import List as _L
        doc.Delete(_L[DB.ElementId](old))
    for g, p0, p1 in lines:
        if abs(p1[0] - p0[0]) + abs(p1[1] - p0[1]) < 0.5:
            failed.append("%s: too short" % g["label"])
            continue
        try:
            ln = DB.Line.CreateBound(DB.XYZ(p0[0], p0[1], z0), DB.XYZ(p1[0], p1[1], z0))
            gr = DB.Grid.Create(doc, ln)
            gr.Name = g["label"]
            if R["type_id"] and gr.GetTypeId() != R["type_id"]:
                gr.ChangeTypeId(R["type_id"])
            try:
                gr.SetVerticalExtents(zlo, zhi)     # run through every level
            except Exception:
                pass
            made.append(gr.Id)
            created.append((g, p0, p1, gr))
        except Exception as ex:
            failed.append("%s: %s" % (g["label"], ex))

    # --- grid dimensions: one string per family just inside each end -------
    av = doc.ActiveView
    if R["dims"] and created:
        if not isinstance(av, DB.ViewPlan) or av.GenLevel is None:
            dim_note = "Grid dimensions skipped - run from a plan view to get them."
        else:
            doc.Regenerate()
            inset_ft = R["inset"] * av.Scale / 12.0
            byid = dict((eid_int(gr.Id), gr) for g, p0, p1, gr in created)
            jobs = GP.dim_layout([(g, p0, p1, eid_int(gr.Id))
                                  for g, p0, p1, gr in created], R["rot"], inset_ft)
            Z = av.GenLevel.ProjectElevation
            nd, bad = 0, 0
            for keys, a, b in jobs:
                ra = DB.ReferenceArray()
                for k in keys:
                    ra.Append(DB.Reference(byid[k]))
                ln = DB.Line.CreateBound(DB.XYZ(a[0], a[1], Z), DB.XYZ(b[0], b[1], Z))
                try:
                    if R["dim_type"]:
                        doc.Create.NewDimension(av, ln, ra, R["dim_type"])
                    else:
                        doc.Create.NewDimension(av, ln, ra)
                    nd += 1
                except Exception as ex:
                    bad += 1
                    failed.append("dimension string (%s...): %s" % (
                        byid[keys[0]].Name, str(ex).splitlines()[0][:80]))

# --- are they visible here? ---------------------------------------------
view = doc.ActiveView
why = []
if made:
    from System.Collections.Generic import List
    ids = List[DB.ElementId](made)
    uidoc.Selection.SetElementIds(ids)
    cat = DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Grids)
    try:
        if view.GetCategoryHidden(cat.Id):
            src = doc.GetElement(view.ViewTemplateId) if view.ViewTemplateId != DB.ElementId.InvalidElementId else None
            why.append("Grids are turned off in this view's Visibility/Graphics"
                       + (" (controlled by view template '%s')" % src.Name if src else ""))
    except Exception:
        pass
    seen = set(eid_int(e.Id) for e in
               DB.FilteredElementCollector(doc, view.Id).OfClass(DB.Grid))
    n_in = sum(1 for i in made if eid_int(i) in seen)
    if n_in < len(made) and not why:
        if view.CropBoxActive:
            why.append("%d of %d new grids fall outside this view's crop region"
                       % (len(made) - n_in, len(made)))
        else:
            why.append("%d of %d new grids aren't shown in this view (check the view "
                       "range / filters / hidden elements)" % (len(made) - n_in, len(made)))
    vis = List[DB.ElementId]([i for i in made if eid_int(i) in seen])
    if vis.Count:
        uidoc.ShowElements(vis)                  # zoom to them

msg = []
if dim_note:
    msg.append(dim_note)
if failed:
    msg.append("These failed:\n" + "\n".join(failed))
if why:
    msg.append("%d grids were created and are selected, but you may not see them in "
               "'%s':\n- %s\n\nTry a 3D view or a plan with no view template to "
               "check them." % (len(made), view.Name, "\n- ".join(why)))
if msg:
    forms.alert("\n\n".join(msg), title="Grids from PDF")
