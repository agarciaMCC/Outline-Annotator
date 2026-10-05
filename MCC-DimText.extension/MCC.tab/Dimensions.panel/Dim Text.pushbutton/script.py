# -*- coding: utf-8 -*-
"""Batch edit of dimension text, laid out like Revit's Dimension Text
dialog but applied to everything selected at once:
- Dimension Value: leave as is / use actual value (clears overrides) /
  replace with text (default ?'-?" for unknown dimensions)
- Above / Prefix / Suffix / Below fields (e.g. suffix "R.O."), with the
  space between prefix/suffix and the value added for you
- optional switch to another dimension style
Select dimensions first, or run with nothing selected and pick them on
screen. Strings show a tick list of their segments (the one you clicked
is pre-ticked). Blank text fields are left alone unless you tick
"Clear fields left blank". "Set as default" remembers the whole form."""
__title__ = "Dim\nText"
__author__ = "MCC ENG"

from pyrevit import revit, forms, script
import mcc_dim as MD
from System.Windows import Visibility

doc = revit.doc
cfg = script.get_config()
FACTORY_OVERRIDE = "?'-?\""
FIELDS = ("above", "prefix", "suffix", "below")
MODES = ("leave", "actual", "replace")


class DimTextWindow(forms.WPFWindow):
    def __init__(self, targets, styles):
        forms.WPFWindow.__init__(self, script.get_bundle_file("ui.xaml"))
        self.result = None
        self.styles = styles
        self.targets = targets
        self._init_segs(targets)
        # dimension value
        mode = cfg.get_option("mode", "leave")
        getattr(self, "rb_" + (mode if mode in MODES else "leave")) \
            .IsChecked = True
        self.txt_override.Text = cfg.get_option("override", FACTORY_OVERRIDE)
        # text fields
        for f in FIELDS:
            getattr(self, "txt_" + f).Text = cfg.get_option(f, "")
        self.chk_space.IsChecked = cfg.get_option("space", True)
        # style
        names = [MD.KEEP_STYLE] + sorted(styles)
        self.cmb.ItemsSource = names
        saved = cfg.get_option("style", MD.KEEP_STYLE)
        self.cmb.SelectedItem = saved if saved in names else MD.KEEP_STYLE
        self.txt_suffix.Focus()

    # --- segment picker ---------------------------------------------
    def _init_segs(self, targets):
        if MD.has_strings(targets):
            self.picker = MD.SegmentPicker(self.pnl_segs, targets,
                                           self.seg_changed)
        else:
            self.picker = None
            self.grp_segs.Visibility = Visibility.Collapsed
        self.update_count()

    def update_count(self):
        if self.picker:
            self.picker.read()
        self.lbl_count.Text = "{} segment(s) on {} dimension(s)".format(
            MD.count_items(self.targets), len(self.targets))

    def seg_changed(self, sender, args):
        self.update_count()

    def segs_all(self, sender, args):
        if self.picker:
            self.picker.set_all(True)

    def segs_none(self, sender, args):
        if self.picker:
            self.picker.set_all(False)

    # --- dimension value ---------------------------------------------
    def mode(self):
        for m in MODES:
            if getattr(self, "rb_" + m).IsChecked:
                return m
        return "leave"

    def value_mode_changed(self, sender, args):
        replace = bool(self.rb_replace.IsChecked)
        self.txt_override.IsEnabled = replace
        if replace:
            self.txt_override.Focus()
            self.txt_override.SelectAll()

    def override_focus(self, sender, args):
        self.rb_replace.IsChecked = True

    # --- buttons ------------------------------------------------------
    def ok_click(self, sender, args):
        if self.picker:
            self.picker.read()
            if not MD.count_items(self.targets):
                forms.alert("No segments ticked.")
                return
        mode = self.mode()
        override = self.txt_override.Text.strip()
        if mode == "replace" and not override:
            forms.alert("Replacement text can't be blank.")
            return
        raw = dict((f, getattr(self, "txt_" + f).Text) for f in FIELDS)
        space = bool(self.chk_space.IsChecked)
        clear = bool(self.chk_clear.IsChecked)
        name = self.cmb.SelectedItem
        if mode == "leave" and not clear and name == MD.KEEP_STYLE \
                and not any(v.strip() for v in raw.values()):
            forms.alert("Nothing to apply: choose a dimension value option, "
                        "fill in a field, pick a style, or tick "
                        "'Clear fields left blank'.")
            return
        if self.chk_default.IsChecked:
            cfg.mode = mode
            cfg.override = override or FACTORY_OVERRIDE
            for f in FIELDS:
                setattr(cfg, f, raw[f])
            cfg.space = space
            cfg.style = name
            script.save_config()
        self.result = (mode, override, raw, space, clear,
                       self.styles.get(name))
        self.Close()

    def cancel_click(self, sender, args):
        self.Close()


def spaced(field, value, space):
    """Trim what the user typed, then add the one space Revit needs."""
    v = value.strip()
    if not v or not space:
        return v
    if field == "prefix":
        return v + " "
    if field == "suffix":
        return " " + v
    return v


targets = MD.get_targets("Select dimensions to edit")
if not targets:
    script.exit()

win = DimTextWindow(targets, MD.styles_for(doc, targets))
win.ShowDialog()
if not win.result:
    script.exit()
mode, override, raw, space, clear, dtype = win.result

values = {}
for f in FIELDS:
    v = spaced(f, raw[f], space)
    if v or clear:
        values[f] = v          # blank + clear -> "" wipes the field

with revit.Transaction("Dim Text"):
    for t in targets:
        if mode == "replace":
            MD.set_override(t, override)
        elif mode == "actual":
            MD.clear_override(t)
        if values:
            MD.set_fields(t, values)
        MD.apply_style(t, dtype)
