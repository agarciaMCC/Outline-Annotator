# -*- coding: utf-8 -*-
"""Places structural columns from a PDF level plan + the column schedule.
Column positions and outlines come from the plan, sizes and detail types
from the schedule at that level; everything is lined up on the grids
already in the model (make them first with Grids from PDF). One story per
column: base at the level (0'-0"), top at the level above, attached to the
slab above. Family by detail type (T9 bullnose, T10/T11 round, else
rectangular) - change any mark's family in the list. Bullnose columns are
lined up with their outline; flip the rounded end by hand if needed.
'Create all types from schedule' makes every size in the schedule as a
column type up front."""
__title__ = "Columns\nfrom PDF"
__author__ = "MCC ENG"

from mcc_compat import eid_int
import math
import os
import re
import tempfile

from pyrevit import revit, DB, forms, script
from System.Windows import Controls, Thickness, GridLength, GridUnitType, FontWeights, \
    TextWrapping, VerticalAlignment
from System.Windows.Media import Brushes
from System.Windows.Threading import DispatcherPriority
from System import Action
from System.Collections.Generic import List
import mcc_pyrun as PR
import mcc_colpdf as CP

doc = revit.doc
uidoc = revit.uidoc
cfg = script.get_config()
HERE = os.path.dirname(__file__)
ENGINE = os.path.join(HERE, "pdfcols", "columns.py")
WORK = os.path.join(tempfile.gettempdir(), "MCC_ColumnsFromPDF")
if not os.path.isdir(WORK):
    os.makedirs(WORK)

NONE_FAM = "(none - skip these)"
FAMILIES = {"rectangular": None, "circular": None, "bullnose": None}   # chosen in the window
FAM_CFG = {"rectangular": "fam_rect", "circular": "fam_round", "bullnose": "fam_bull"}
FAM_WORDS = {"rectangular": ("rectangular", "rect", "square"), "circular": ("circular", "round", "circle"),
             "bullnose": ("bullnose", "bull")}


def column_families():
    """Every loaded family in the Structural Columns category, by name."""
    cid = eid_int(DB.ElementId(DB.BuiltInCategory.OST_StructuralColumns))
    out = {}
    for f in DB.FilteredElementCollector(doc).OfClass(DB.Family):
        try:
            if f.FamilyCategory and eid_int(f.FamilyCategory.Id) == cid:
                out[f.Name] = f
        except Exception:
            pass
    return out


COL_FAMS = column_families()


def guess_family(key):
    """Saved choice if still loaded, else the best name match (concrete + shape word)."""
    saved = cfg.get_option(FAM_CFG[key], "")
    if saved in COL_FAMS:
        return saved
    best, score = None, 0
    for n in COL_FAMS:
        low = n.lower()
        sc = sum(3 for w in FAM_WORDS[key] if w in low)
        if sc:
            sc += 2 if "concrete" in low else 0
            sc -= 0.001 * len(n)
            if sc > score:
                best, score = n, sc
    return best


FAM_LABELS = [("rectangular", "Rectangular"), ("circular", "Circular"), ("bullnose", "Bullnose")]
SCALES = [("Auto - from grid dimensions", "auto"), ('1/16" = 1\'-0"', 1 / 16.0),
          ('3/32" = 1\'-0"', 3 / 32.0), ('1/8" = 1\'-0"', 1 / 8.0), ('3/16" = 1\'-0"', 3 / 16.0),
          ('1/4" = 1\'-0"', 1 / 4.0)]

WIDTH_NAMES = ("column width", "b", "width", "w", "col width")
DEPTH_NAMES = ("column length", "h", "depth", "d", "column depth", "col depth", "length")
DIA_NAMES = ("column diameter", "diameter", "dia", "col diameter", "d")
RAD_NAMES = ("column radius", "radius", "r")
NOSE_NAMES = ("column nose radius", "nose radius")     # bullnose: set to W / 2


# ---------------------------------------------------------------------------
# model helpers
# ---------------------------------------------------------------------------
def ename(e):
    p = e.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    if p and p.AsString():
        return p.AsString()
    try:
        return DB.Element.Name.__get__(e)
    except Exception:
        return str(eid_int(e.Id))


DIM_DEFAULT = "(project default)"
DIM_TYPES = {}
for _t in DB.FilteredElementCollector(doc).OfClass(DB.DimensionType):
    try:
        if _t.StyleType == DB.DimensionStyleType.Linear:
            DIM_TYPES[ename(_t)] = _t
    except Exception:
        pass
LEVELS = sorted(DB.FilteredElementCollector(doc).OfClass(DB.Level), key=lambda l: l.ProjectElevation)
LEVEL_BY_NAME = dict((l.Name, l) for l in LEVELS)


def info_only(flags):
    """Notes that need no action beyond a glance: bullnose flip reminders and
    columns extended into a wall (blue on the check PDF too)."""
    return bool(flags) and all(f.startswith(("bullnose", "in a wall")) for f in flags)


def schedule_level(name):
    """Revit level name -> schedule level key: 'Level 1' -> '1', 'LEVEL B7' -> 'B7',
    'L02 - Podium' -> '2', 'Roof' -> 'ROOF'. The engine normalises it again."""
    n = (name or "").upper()
    for w in ("MACHINE ROOM", "ROOF", "PENTHOUSE", "MEZZ"):
        if w in n:
            return w
    m = (re.search(r"\b(?:LEVEL|LVL|LEV|FLOOR|FLR)[\s_-]*([A-Z]{0,2}\d{1,3}[A-Z]?)\b", n)
         or re.search(r"\bL(\d{1,3}[A-Z]?)\b", n)
         or re.search(r"\b([A-Z]{0,2}\d{1,3}[A-Z]?)\b", n))
    if not m:
        return ""
    return re.sub(r"^([A-Z]*)0+(\d)", r"\1\2", m.group(1))


def level_above(lv):
    up = [l for l in LEVELS if l.ProjectElevation > lv.ProjectElevation + 0.01]
    return up[0] if up else None


def family(key):
    return COL_FAMS.get(FAMILIES.get(key) or "")


def is_length(p):
    try:
        return p.Definition.GetDataType() == DB.SpecTypeId.Length
    except Exception:
        try:
            return p.Definition.ParameterType == DB.ParameterType.Length
        except Exception:
            return False


def length_params(sym):
    out = {}
    for p in sym.Parameters:
        if p.StorageType == DB.StorageType.Double and not p.IsReadOnly and is_length(p):
            out[p.Definition.Name.strip().lower()] = p
    return out


def pick(params, names):
    for n in names:
        if n in params:
            return params[n]
    return None


_TYPES = {}


def type_for(key, size, create=True):
    """(symbol, note). size in inches: [W, D] or [dia]."""
    ck = (key, tuple(size))
    if ck in _TYPES:
        return _TYPES[ck]
    fam = family(key)
    if fam is None:
        r = (None, "no %s column family picked" % key)
        _TYPES[ck] = r
        return r
    syms = [doc.GetElement(i) for i in fam.GetFamilySymbolIds()]
    want = [v / 12.0 for v in size]

    def dims(s):
        ps = length_params(s)
        if key == "circular":
            d = pick(ps, DIA_NAMES)
            if d:
                return [d.AsDouble()], d, None
            r = pick(ps, RAD_NAMES)
            return ([r.AsDouble() * 2], r, "radius") if r else (None, None, None)
        w, d = pick(ps, WIDTH_NAMES), pick(ps, DEPTH_NAMES)
        return ([w.AsDouble(), d.AsDouble()], w, d) if w and d else (None, None, None)
    for s in syms:
        v = dims(s)[0]
        if v and len(v) == len(want) and all(abs(a - b) < 1 / 192.0 for a, b in zip(v, want)):
            _TYPES[ck] = (s, "")
            return _TYPES[ck]
    name = CP.type_name(key, size)
    for s in syms:
        if ename(s).strip().upper() == name.upper():
            _TYPES[ck] = (s, "type '%s' exists but its size parameters differ" % name)
            return _TYPES[ck]
    if not create or not syms:
        r = (None, "no %s type %s" % (key, name))
        _TYPES[ck] = r
        return r
    base = syms[0]
    v, p1, p2 = dims(base)
    if v is None:
        names = ", ".join(sorted(length_params(base))) or "none"
        r = (None, "can't find the size parameters on '%s' (length parameters: %s)"
             % (FAMILIES[key] or key, names))
        _TYPES[ck] = r
        return r
    new = base.Duplicate(name)
    ps = length_params(new)
    if key == "circular":
        if p2 == "radius":
            pick(ps, RAD_NAMES).Set(want[0] / 2)
        else:
            pick(ps, DIA_NAMES).Set(want[0])
    else:
        pick(ps, WIDTH_NAMES).Set(want[0])
        pick(ps, DEPTH_NAMES).Set(want[1])
        if key == "bullnose":
            nose = pick(ps, NOSE_NAMES)
            if nose:
                nose.Set(want[0] / 2.0)
    _TYPES[ck] = (new, "new type")
    return _TYPES[ck]


def model_grids():
    out = {}
    for g in DB.FilteredElementCollector(doc).OfClass(DB.Grid):
        c = g.Curve
        if not isinstance(c, DB.Line):
            continue
        a, b = c.GetEndPoint(0), c.GetEndPoint(1)
        L = math.hypot(b.X - a.X, b.Y - a.Y)
        if L > 0.1:
            out[g.Name] = ((a.X, a.Y), ((b.X - a.X) / L, (b.Y - a.Y) / L))
    return out


def existing_columns(level):
    out = []
    for c in DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_StructuralColumns) \
            .WhereElementIsNotElementType():
        try:
            p = c.get_Parameter(DB.BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)
            if p and p.AsElementId() == level.Id and c.Location:
                pt = c.Location.Point
                m = c.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
                out.append(((pt.X, pt.Y), m.AsString() if m else ""))
        except Exception:
            pass
    return out


def run_engine(args):
    exe, pre = PR.ensure_python(cfg, "Columns from PDF")
    if not exe:
        return None, "Python 3 with PyMuPDF is needed for the PDF step."
    out = os.path.join(WORK, "result.json")
    if os.path.exists(out):
        os.remove(out)
    code, so, se = PR.run(exe, pre + [PR.q(ENGINE), "--out", PR.q(out)] + args)
    if code != 0 or not os.path.exists(out):
        return None, "Couldn't read the PDF: " + (se or so or "no output").strip()[-600:]
    return CP.load(out), None


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


def size_text(size, key):
    if not size:
        return "?"
    return ('%d" DIA' % size[0]) if len(size) == 1 else "%dx%d" % tuple(size)


class ColumnsWindow(forms.WPFWindow):
    def __init__(self):
        forms.WPFWindow.__init__(self, script.get_bundle_file("ui.xaml"))
        self.result = None
        self.res = None
        self.T = None
        self.rows = []
        self.txt_plan.Text = cfg.get_option("plan", "")
        self.txt_sched.Text = cfg.get_option("schedule", "")
        self.cmb_scale.ItemsSource = [s[0] for s in SCALES]
        self.cmb_scale.SelectedIndex = min(int(cfg.get_option("scale", 0)), len(SCALES) - 1)
        self.cmb_level.ItemsSource = [l.Name for l in LEVELS]
        av = doc.ActiveView
        gl = getattr(av, "GenLevel", None)
        self.cmb_level.SelectedItem = gl.Name if gl else (LEVELS[0].Name if LEVELS else None)
        self.chk_attach.IsChecked = cfg.get_option("attach", True)
        self.chk_cdims.IsChecked = cfg.get_option("cdims", True)
        dn = [DIM_DEFAULT] + sorted(DIM_TYPES)
        self.cmb_dimtype.ItemsSource = dn
        ds = cfg.get_option("dim_type", DIM_DEFAULT)
        self.cmb_dimtype.SelectedItem = ds if ds in dn else DIM_DEFAULT
        self.level_changed(None, None)
        names = [NONE_FAM] + sorted(COL_FAMS)
        for key, cb in (("rectangular", self.cmb_fam_rect), ("circular", self.cmb_fam_round),
                        ("bullnose", self.cmb_fam_bull)):
            cb.ItemsSource = names
            g = guess_family(key)
            cb.SelectedItem = g if g else NONE_FAM
        self.fam_changed(None, None)
        if not COL_FAMS:
            self.status("No Structural Columns families are loaded in this model - load the "
                        "concrete column families first.", True)

    def status(self, text, err=False):
        self.lbl_status.Text = text
        self.lbl_status.Foreground = Brushes.Firebrick if err else Brushes.DimGray
        self.Dispatcher.Invoke(Action(lambda: None), DispatcherPriority.Background)

    def _browse(self, box):
        start = os.path.dirname(box.Text) if box.Text else ""
        f = forms.pick_file(file_ext="pdf", init_dir=start if os.path.isdir(start) else "")
        if f:
            box.Text = f

    def browse_plan(self, s, a):
        self._browse(self.txt_plan)

    def browse_sched(self, s, a):
        self._browse(self.txt_sched)

    def level_changed(self, s, a):
        n = self.cmb_level.SelectedItem
        self.txt_slevel.Text = schedule_level(n)

    def fam_changed(self, s, a):
        for key, cb in (("rectangular", getattr(self, "cmb_fam_rect", None)),
                        ("circular", getattr(self, "cmb_fam_round", None)),
                        ("bullnose", getattr(self, "cmb_fam_bull", None))):
            if cb is None:
                continue
            v = cb.SelectedItem
            FAMILIES[key] = None if v in (None, NONE_FAM) else v
        _TYPES.clear()

    def save_families(self):
        for key in FAMILIES:
            setattr(cfg, FAM_CFG[key], FAMILIES[key] or "")
        script.save_config()

    def _sched(self):
        f = self.txt_sched.Text.strip().strip('"')
        if not os.path.isfile(f):
            self.status("Pick the column schedule PDF.", True)
            return None
        return f

    # --- create all types -------------------------------------------------
    def types_click(self, s, a):
        f = self._sched()
        if not f:
            return
        self.status("Reading the schedule...")
        res, err = run_engine(["--schedule", PR.q(f), "--types-only"])
        if err:
            self.status(err, True)
            return
        self.save_families()
        made, have, bad = 0, 0, {}
        with revit.Transaction("MCC: Column types from schedule"):
            for t in res["types"]:
                sym, note = type_for(t["family"], t["size"])
                if sym is None:
                    bad[note] = bad.get(note, 0) + 1
                elif note == "new type":
                    made += 1
                else:
                    have += 1
        msg = "Schedule has %d column sizes: %d new types created, %d already in the model." % (
            len(res["types"]), made, have)
        if res.get("schedule_summary"):
            msg += "\nRead: " + "; ".join(res["schedule_summary"])
        for note, n in bad.items():
            msg += "\n! %d not made - %s" % (n, note)
        self.status(msg, bool(bad))

    # --- read ---------------------------------------------------------------
    def read_click(self, s, a):
        plan = self.txt_plan.Text.strip().strip('"')
        sched = self._sched()
        if not sched:
            return
        if not os.path.isfile(plan):
            self.status("Pick the level plan PDF.", True)
            return
        try:
            page = int(self.txt_page.Text.strip() or "1")
        except ValueError:
            self.status("Page must be a number.", True)
            return
        slevel = self.txt_slevel.Text.strip()
        if not slevel:
            self.status("Type the schedule level (e.g. 1, B7, ROOF).", True)
            return
        scale = SCALES[self.cmb_scale.SelectedIndex][1]
        self.status("Reading the plan and schedule (about 10 seconds)...")
        res, err = run_engine(["--plan", PR.q("%s:%d" % (plan, page)), "--schedule", PR.q(sched),
                               "--level", PR.q(slevel), "--check-dir", PR.q(WORK),
                               "--scale", "auto" if scale == "auto" else "%.6f" % scale])
        if err:
            self.status(err, True)
            return
        self.res = res
        T = CP.fit(CP.sheet_lines(res), model_grids())
        self.T = T
        info = ["%s p%d: %s (%s). %d columns with marks, %d gray shapes without a mark (not placed)%s."
                % (os.path.basename(plan), page, res["scale"], res["scale_source"],
                   len(res["columns"]), res["unmarked_shapes"],
                   ", %d legend sample(s) skipped" % res["legend_skipped"] if res.get("legend_skipped") else "")]
        if res.get("schedule_summary"):
            info.append("Schedule level %s. Read: %s." % (res.get("level"), "; ".join(res["schedule_summary"])))
        nf = sum(1 for c in res["columns"] if c.get("ref"))
        if nf:
            info.append("%d column(s) flagged - the #numbers in the notes are circled on the check PDF "
                        "(red = check it, blue = bullnose, flip if needed)." % nf)
        info += ["! " + w for w in res["warnings"]]
        if T is None:
            info.append("! Fewer than two crossing grids in the model match this sheet's grid "
                        "names - create the grids first (Grids from PDF).")
            self.lbl_align.Text = ""
        else:
            self.lbl_align.Text = ("Lined up on %d grid intersections in the model: rotation %.3f deg, "
                                   "fit within %.2f in." % (T[3], math.degrees(T[0]), T[2] * 12))
            self.lbl_align.Foreground = Brushes.Firebrick if T[2] > 0.25 else Brushes.DimGray
        self.status("\n".join(info), T is None)
        self.fill()
        self.btn_check.IsEnabled = bool(res.get("check_pdf"))
        self.btn_ok.IsEnabled = T is not None

    def fill(self):
        T = self.tbl
        T.Children.Clear()
        T.RowDefinitions.Clear()
        T.ColumnDefinitions.Clear()
        for w in (28, 60, 70, 50, 44, 120, 0):
            cd = Controls.ColumnDefinition()
            cd.Width = GridLength(w) if w else GridLength(1, GridUnitType.Star)
            T.ColumnDefinitions.Add(cd)
        self._row([tb(h, bold=True) for h in ("", "Mark", "Size", "Type", "Qty", "Family", "Notes")])
        self.rows = []
        for g in CP.group_by_mark(self.res):
            chk = Controls.CheckBox()
            chk.VerticalAlignment = VerticalAlignment.Center
            chk.IsChecked = bool(g["size"])
            chk.IsEnabled = bool(g["size"])
            chk.Checked += self.count
            chk.Unchecked += self.count
            cb = Controls.ComboBox()
            cb.Height = 22
            cb.ItemsSource = [l for k, l in FAM_LABELS]
            keys = [k for k, l in FAM_LABELS]
            cb.SelectedIndex = keys.index(g["family"]) if g["family"] in keys else 0
            if g["size"] and len(g["size"]) == 1:
                cb.SelectedIndex = keys.index("circular")
            notes = "; ".join(g["flags"])
            self._row([chk, tb(g["mark"], bold=True), tb(size_text(g["size"], g["family"])),
                       tb(g["detail"] or ""), tb(str(g["count"])), cb,
                       tb(notes, color=(Brushes.SteelBlue if info_only(g["flags"]) else Brushes.DarkOrange)
                          if notes else None, wrap=True)])
            self.rows.append((chk, cb, g))
        self.count(None, None)

    def _row(self, cells):
        T = self.tbl
        rd = Controls.RowDefinition()
        rd.Height = GridLength.Auto
        T.RowDefinitions.Add(rd)
        r = T.RowDefinitions.Count - 1
        for c, el in enumerate(cells):
            Controls.Grid.SetRow(el, r)
            Controls.Grid.SetColumn(el, c)
            T.Children.Add(el)

    def count(self, s, a):
        n = sum(g["count"] for c, cb, g in self.rows if c.IsChecked)
        tot = sum(g["count"] for c, cb, g in self.rows)
        self.lbl_count.Text = "%d of %d columns will be placed" % (n, tot)

    def all_click(self, s, a):
        for c, cb, g in self.rows:
            if c.IsEnabled:
                c.IsChecked = True

    def none_click(self, s, a):
        for c, cb, g in self.rows:
            c.IsChecked = False

    def check_click(self, s, a):
        f = self.res.get("check_pdf") if self.res else None
        if f and os.path.exists(f):
            os.startfile(f)

    # --- place --------------------------------------------------------------
    def ok_click(self, s, a):
        lv = LEVEL_BY_NAME.get(self.cmb_level.SelectedItem)
        if lv is None:
            forms.alert("Pick the level.")
            return
        top = level_above(lv)
        if top is None:
            forms.alert("There's no level above %s for the column tops." % lv.Name)
            return
        keys = [k for k, l in FAM_LABELS]
        fam = dict((g["mark"], keys[cb.SelectedIndex]) for c, cb, g in self.rows if c.IsChecked)
        if not fam:
            forms.alert("No marks ticked.")
            return
        if self.chk_default.IsChecked:
            cfg.plan = self.txt_plan.Text.strip()
            cfg.schedule = self.txt_sched.Text.strip()
            cfg.scale = self.cmb_scale.SelectedIndex
            cfg.attach = bool(self.chk_attach.IsChecked)
            cfg.cdims = bool(self.chk_cdims.IsChecked)
            cfg.dim_type = self.cmb_dimtype.SelectedItem or DIM_DEFAULT
            script.save_config()
        self.save_families()
        self.result = dict(level=lv, top=top, fam=fam, attach=bool(self.chk_attach.IsChecked),
                           skip=bool(self.chk_skip.IsChecked),
                           cdims=bool(self.chk_cdims.IsChecked),
                           dim_type=DIM_TYPES.get(self.cmb_dimtype.SelectedItem))
        self.Close()

    def cancel_click(self, s, a):
        self.Close()


win = ColumnsWindow()
win.ShowDialog()
R = win.result
if not R:
    script.exit()
res, T = win.res, win.T
lv, top = R["level"], R["top"]
base_z = lv.ProjectElevation

floors = []
if R["attach"]:
    for f in DB.FilteredElementCollector(doc).OfClass(DB.Floor):
        try:
            bb = f.get_BoundingBox(None)
            if bb and bb.Min.Z - 0.1 <= top.ProjectElevation <= bb.Max.Z + 3.0:
                floors.append((f, bb))
        except Exception:
            pass

have = existing_columns(lv) if R["skip"] else []
SNAP_GRIDS = [(n, p, d) for n, (p, d) in model_grids().items()]
made, failed, skipped, unattached = [], [], 0, 0
col_info = {}
dims_made, dims_bad, dims_note = 0, 0, ""
with revit.Transaction("MCC: Columns from PDF"):
    for c in res["columns"]:
        key = R["fam"].get(c["mark"])
        if not key or not c.get("size"):
            continue
        size = c["size"]
        if key == "circular" and len(size) == 2:
            size = [min(size)]
        if key != "circular" and len(size) == 1:
            size = [size[0], size[0]]
        pt, ang = CP.placement(dict(c, size=size), T)
        if key != "circular":
            ang, _g, _d = CP.snap_angle(pt, ang, SNAP_GRIDS)   # square to the nearest grid
        if any(math.hypot(p[0] - pt[0], p[1] - pt[1]) < 0.5 and m == c["mark"] for p, m in have):
            skipped += 1
            continue
        sym, note = type_for(key, size)
        if sym is None:
            failed.append("%s: %s" % (c["mark"], note))
            continue
        try:
            if not sym.IsActive:
                sym.Activate()
                doc.Regenerate()
            loc = DB.XYZ(pt[0], pt[1], base_z)
            col = doc.Create.NewFamilyInstance(loc, sym, lv, DB.Structure.StructuralType.Column)
            for bip, val in ((DB.BuiltInParameter.FAMILY_BASE_LEVEL_PARAM, lv.Id),
                             (DB.BuiltInParameter.FAMILY_TOP_LEVEL_PARAM, top.Id)):
                p = col.get_Parameter(bip)
                if p and not p.IsReadOnly:
                    p.Set(val)
            for bip in (DB.BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM,
                        DB.BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM):
                p = col.get_Parameter(bip)
                if p and not p.IsReadOnly:
                    p.Set(0.0)
            m = col.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
            if m:
                m.Set(c["mark"])
            if key != "circular" and abs(ang) > 1e-6:
                axis = DB.Line.CreateBound(loc, loc + DB.XYZ.BasisZ)
                DB.ElementTransformUtils.RotateElement(doc, col.Id, axis, ang)
            made.append((col, pt))
            col_info[eid_int(col.Id)] = (ang, size, key)
        except Exception as ex:
            failed.append("%s: %s" % (c["mark"], str(ex).splitlines()[0][:100]))
    if R["attach"] and made:
        doc.Regenerate()
        for col, pt in made:
            hit = None
            for f, bb in floors:
                if bb.Min.X <= pt[0] <= bb.Max.X and bb.Min.Y <= pt[1] <= bb.Max.Y:
                    hit = f
                    break
            ok = False
            if hit:
                try:
                    DB.Structure.ColumnAttachment.AddColumnAttachment(
                        doc, col, hit, 1, getattr(DB.Structure.ColumnAttachmentCutStyle, "None"),
                        DB.Structure.ColumnAttachmentJustification.Minimum, 0.0)
                    ok = True
                except Exception:
                    ok = False
            if not ok:
                unattached += 1

    # --- check dimensions: column centre to the nearest grid each way ---------
    av = doc.ActiveView
    if R["cdims"] and made:
        if not isinstance(av, DB.ViewPlan) or av.GenLevel is None:
            dims_note = "Column check dimensions skipped - run from a plan view to get them."
        else:
            doc.Regenerate()
            gap = 0.375 * av.Scale / 12.0          # 3/8" on paper past the column face
            glines = [(n, p, d) for n, (p, d) in model_grids().items()]
            gobj = dict((g.Name, g) for g in DB.FilteredElementCollector(doc).OfClass(DB.Grid))
            Z = av.GenLevel.ProjectElevation
            for col, pt in made:
                ang, size, key = col_info[eid_int(col.Id)]
                if key == "circular":
                    hx = hy = size[0] / 24.0
                else:
                    hx, hy = size[0] / 24.0, size[1] / 24.0
                for gname, which, a, b in CP.center_dims(pt, ang, hx, hy, glines, gap):
                    try:
                        kind = DB.FamilyInstanceReferenceType.CenterLeftRight if which == "LR" \
                            else DB.FamilyInstanceReferenceType.CenterFrontBack
                        refs = list(col.GetReferences(kind))
                        if not refs:
                            dims_bad += 1
                            continue
                        ra = DB.ReferenceArray()
                        ra.Append(DB.Reference(gobj[gname]))
                        ra.Append(refs[0])
                        ln = DB.Line.CreateBound(DB.XYZ(a[0], a[1], Z), DB.XYZ(b[0], b[1], Z))
                        if R["dim_type"]:
                            doc.Create.NewDimension(av, ln, ra, R["dim_type"])
                        else:
                            doc.Create.NewDimension(av, ln, ra)
                        dims_made += 1
                    except Exception:
                        dims_bad += 1

if made:
    uidoc.Selection.SetElementIds(List[DB.ElementId]([c.Id for c, p in made]))
msg = []
if failed:
    msg.append("%d column(s) not placed:\n%s" % (len(failed), "\n".join(sorted(set(failed))[:25])))
if unattached:
    msg.append("%d column(s) have their top at %s - no slab found above them to attach to."
               % (unattached, top.Name))
if skipped:
    msg.append("%d already placed - skipped." % skipped)
if dims_note:
    msg.append(dims_note)
if dims_bad:
    msg.append("%d check dimension(s) couldn't be made (column family has no center reference "
               "planes, or the column isn't square to the grid)." % dims_bad)
if msg:
    forms.alert("%d columns placed on %s.\n\n%s" % (len(made), lv.Name, "\n\n".join(msg)),
                title="Columns from PDF")
