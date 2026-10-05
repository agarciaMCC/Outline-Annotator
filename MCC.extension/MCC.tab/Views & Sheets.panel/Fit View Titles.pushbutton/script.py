# -*- coding: utf-8 -*-
"""Fit viewport title lines to their titles: line = title width plus a
couple of characters.

Revit can't report how wide a title draws, so the width is estimated
from the character count, calibrated once per viewport type from titles
fitted by hand (line length = lead + per-character width x characters).
If a type isn't calibrated yet, the command asks you to click 2+ titles
of that type you've already fitted by hand, then carries on - one run.
Calibrations are saved in title_fit.json next to this script, so everyone
using the extension shares them."""
__title__ = "Fit View\nTitles"
__author__ = "MCC ENG"

import os
import json
from pyrevit import revit, DB, UI, forms, script
import mcc_sheet as ms

doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()

# =====================================================================
PAD_CHARS = 2.0            # extra characters of line past the title
# =====================================================================

CAL_FILE = os.path.join(os.path.dirname(__file__), "title_fit.json")

FIT_SHEET = "Fit titles on this sheet"
FIT_SEL = "Fit selected viewports"
FIT_PICK = "Fit titles on sheets..."
RECAL = "Recalibrate from selected viewports (fitted by hand)"


# ---------------------------------------------------------- calibrations
def load_cal():
    try:
        with open(CAL_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_cal(cal):
    try:
        with open(CAL_FILE, "w") as f:
            json.dump(cal, f, indent=1, sort_keys=True)
        return True
    except Exception:
        return False


cal = load_cal()


def title_text(vp):
    """What the title shows: Title on Sheet if set, else the view name."""
    v = doc.GetElement(vp.ViewId)
    p = v.get_Parameter(DB.BuiltInParameter.VIEW_DESCRIPTION)
    t = p.AsString() if p is not None else None
    return (t or v.Name).strip()


def vp_type_name(vp):
    return ms.type_name(doc.GetElement(vp.GetTypeId()))


def fit_line(pts):
    """Least squares length = a + b * chars. None if not solvable."""
    if len(set(n for n, _ in pts)) < 2:
        return None
    k = float(len(pts))
    sx = sum(n for n, _ in pts)
    sy = sum(l for _, l in pts)
    sxx = sum(n * n for n, _ in pts)
    sxy = sum(n * l for n, l in pts)
    b = (k * sxy - sx * sy) / (k * sxx - sx * sx)
    a = (sy - b * sx) / k
    return a, b


def calibrate(tname, vps, rows):
    pts = []
    for vp in vps:
        try:
            pts.append((len(title_text(vp)), vp.LabelLineLength))
        except Exception:
            pass
    ab = fit_line(pts)
    if ab is None:
        rows.append([tname, len(pts), "-", "-",
                     "need 2+ titles of different lengths"])
        return False
    a, b = ab
    worst = max(abs(a + b * n - l) for n, l in pts)
    cal[tname] = [a, b]
    rows.append([tname, len(pts), "{:.3f}\"".format(a * 12),
                 "{:.4f}\"".format(b * 12),
                 "saved (worst miss {:.3f}\")".format(worst * 12)])
    return True


class TypeFilter(UI.Selection.ISelectionFilter):
    def __init__(self, tname):
        self.tname = tname

    def AllowElement(self, e):
        return isinstance(e, DB.Viewport) and vp_type_name(e) == self.tname

    def AllowReference(self, ref, pt):
        return False


def pick_calibration(tname):
    """Ask for hand-fitted titles of 'tname' on the open sheet."""
    if not isinstance(doc.ActiveView, DB.ViewSheet):
        return []
    ok = forms.alert(
        "Viewport type '{}' isn't calibrated yet.\n\n"
        "Click 2 or more titles of this type on this sheet whose lines "
        "you've already set by hand (different lengths), then Finish."
        .format(tname), title="Fit View Titles", ok=False, yes=True,
        no=True)
    if not ok:
        return []
    try:
        refs = uidoc.Selection.PickObjects(
            UI.Selection.ObjectType.Element, TypeFilter(tname),
            "Pick hand-fitted '{}' titles, then Finish".format(tname))
    except Exception:
        return []
    return [doc.GetElement(r) for r in refs]


# ---------------------------------------------------------------- mode
sel = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()]
sel = [e for e in sel if isinstance(e, DB.Viewport)]
on_sheet = isinstance(doc.ActiveView, DB.ViewSheet)
opts = ([FIT_SEL] if sel else []) + ([FIT_SHEET] if on_sheet else []) + \
    [FIT_PICK] + ([RECAL] if sel else [])
mode = forms.CommandSwitchWindow.show(opts, message="Fit View Titles")
if not mode:
    script.exit()

cal_rows = []
if mode == RECAL:
    by_type = {}
    for vp in sel:
        by_type.setdefault(vp_type_name(vp), []).append(vp)
    for tname in sorted(by_type):
        calibrate(tname, by_type[tname], cal_rows)
    saved = save_cal(cal)
    output.print_md("## Title fit calibration")
    output.print_table(cal_rows, columns=["Viewport type", "Titles", "Lead",
                                          "Per character", "Result"])
    if not saved:
        output.print_md("Couldn't write {} - calibration not saved."
                        .format(CAL_FILE))
    script.exit()

# ---------------------------------------------------------------- targets
if mode == FIT_SEL:
    vps = sel
elif mode == FIT_SHEET:
    vps = list(DB.FilteredElementCollector(doc, doc.ActiveView.Id)
               .OfClass(DB.Viewport))
else:
    sheets = sorted(DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet),
                    key=lambda s: s.SheetNumber)
    lab = dict(("{}  {}".format(s.SheetNumber, s.Name), s) for s in sheets)
    picked = forms.SelectFromList.show(sorted(lab), title="Sheets",
                                       multiselect=True)
    if not picked:
        script.exit()
    vps = [vp for n in picked for vp in
           DB.FilteredElementCollector(doc, lab[n].Id).OfClass(DB.Viewport)]

# ---------------------------------------------------------------- calibrate
# any type we're about to fit that has no calibration -> ask now
needed = sorted(set(vp_type_name(vp) for vp in vps))
for tname in [t for t in needed if t not in cal]:
    # hand-fitted examples already selected count first
    pre = [vp for vp in sel if vp_type_name(vp) == tname]
    picks = pre if len(pre) >= 2 else pick_calibration(tname)
    if picks:
        calibrate(tname, picks, cal_rows)
if cal_rows:
    save_cal(cal)

# ---------------------------------------------------------------- fit
rows, missing = [], set()
with revit.Transaction("MCC: Fit View Titles"):
    for vp in vps:
        tname = vp_type_name(vp)
        if tname not in cal:
            missing.add(tname)
            continue
        a, b = cal[tname]
        text = title_text(vp)
        new = a + b * (len(text) + PAD_CHARS)
        try:
            old = vp.LabelLineLength
            vp.LabelLineLength = new
            rows.append([doc.GetElement(vp.SheetId).SheetNumber, text,
                         "{:.2f}\"".format(old * 12),
                         "{:.2f}\"".format(new * 12)])
        except Exception as ex:
            rows.append(["?", text, "-", "failed: {}".format(ex)])

output.print_md("## Fit View Titles")
if cal_rows:
    output.print_md("**Calibrated this run**")
    output.print_table(cal_rows, columns=["Viewport type", "Titles", "Lead",
                                          "Per character", "Result"])
if rows:
    output.print_table(rows, columns=["Sheet", "Title", "Was", "Now"])
if missing:
    output.print_md("**Skipped - not calibrated:** {}".format(
        ", ".join(sorted(missing))))
    output.print_md("Open a sheet with 2+ hand-fitted titles of that type "
                    "and run again - it will ask you to click them.")
