# -*- coding: utf-8 -*-
"""Shared helpers for the MCC dimension buttons.

Revit rules that drive all of this:
- A dimension with ONE segment takes its text (override / prefix / ...)
  on the Dimension itself; a multi-segment string ignores that and each
  piece must be set through dim.Segments.
- Revit can only *select* a whole dimension, never one segment of a
  string. When picked on screen, the click point tells us which segment
  was meant and the window lists every segment of each string with a
  tick box (clicked one pre-ticked) so any mix can be chosen.
  Pre-selected dimensions start with every segment ticked.
"""
from pyrevit import revit, DB, forms
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType
from Autodesk.Revit.Exceptions import OperationCanceledException

KEEP_STYLE = "(keep current style)"

FIELD_PROPS = {"above": "Above", "prefix": "Prefix",
               "suffix": "Suffix", "below": "Below"}


class DimFilter(ISelectionFilter):
    """Only lets the user pick real dimensions (not spot elevations)."""
    def AllowElement(self, e):
        return is_dim(e)

    def AllowReference(self, ref, point):
        return False


class Target(object):
    """One dimension plus the pieces of it we're editing.
    For a string: segs = its segments in order along the string,
    chosen = indices to edit (starts as the clicked one, or all)."""
    def __init__(self, dim, clicked=None):
        self.dim = dim
        self.segs = list(dim.Segments) if dim.NumberOfSegments > 1 else []
        self.multi = len(self.segs) > 1
        self.clicked = clicked           # index or None
        if self.multi:
            self.chosen = set([clicked]) if clicked is not None \
                else set(range(len(self.segs)))
        else:
            self.chosen = set()

    @property
    def items(self):
        """Objects that carry the text properties: the Dimension itself
        for a single dimension, the chosen DimensionSegments for a string."""
        if not self.multi:
            return [self.dim]
        return [self.segs[i] for i in sorted(self.chosen)]

    def seg_label(self, i):
        seg = self.segs[i]
        try:
            val = seg.ValueString
        except Exception:
            val = "?"
        tag = "   (clicked)" if i == self.clicked else ""
        return "{}:  {}{}".format(i + 1, val, tag)


def is_dim(e):
    return isinstance(e, DB.Dimension) and not isinstance(e, DB.SpotDimension)


def nearest_segment(dim, point, view):
    """Index of the segment whose midpoint is closest to a click point,
    measured in the plane of the view. None for single dimensions."""
    if dim.NumberOfSegments <= 1 or point is None:
        return None
    n = view.ViewDirection
    best, best_d = None, None
    for i, seg in enumerate(dim.Segments):
        d = point - seg.Origin
        d = d - n.Multiply(d.DotProduct(n))
        if best is None or d.GetLength() < best_d:
            best, best_d = i, d.GetLength()
    return best


def get_targets(prompt="Select dimensions"):
    """Pre-selected dimensions (whole strings), or Revit's normal pick
    (click dimensions, then Finish). For each picked string the clicked
    segment is remembered as the starting choice; the window's segment
    list lets the user tick any others."""
    doc, uidoc = revit.doc, revit.uidoc
    pre = [e for e in revit.get_selection().elements if is_dim(e)]
    if pre:
        return [Target(d) for d in pre]
    try:
        refs = uidoc.Selection.PickObjects(ObjectType.Element, DimFilter(),
                                           prompt + " - then Finish")
    except OperationCanceledException:
        return []
    except Exception:
        return []
    view = doc.ActiveView
    out = []
    for ref in refs:
        dim = doc.GetElement(ref)
        try:
            pt = ref.GlobalPoint
        except Exception:
            pt = None
        out.append(Target(dim, nearest_segment(dim, pt, view)))
    return out


def has_strings(targets):
    return any(t.multi for t in targets)


class SegmentPicker(object):
    """Fills a WPF StackPanel with one check box per segment of every
    string in targets, grouped by dimension. Call read() before applying
    to push the ticks back into target.chosen."""
    def __init__(self, panel, targets, on_change=None):
        from System.Windows.Controls import CheckBox, TextBlock
        from System.Windows import Thickness
        self.boxes = []                  # (target, index, CheckBox)
        panel.Children.Clear()
        n = 0
        for t in targets:
            if not t.multi:
                continue
            n += 1
            head = TextBlock()
            head.Text = "String {}  -  {} segments".format(n, len(t.segs))
            head.FontWeight = __import__("System").Windows.FontWeights.SemiBold
            head.Margin = Thickness(0, 4 if n > 1 else 0, 0, 2)
            panel.Children.Add(head)
            for i in range(len(t.segs)):
                cb = CheckBox()
                cb.Content = t.seg_label(i)
                cb.IsChecked = i in t.chosen
                cb.Margin = Thickness(12, 1, 0, 1)
                if on_change:
                    cb.Checked += on_change
                    cb.Unchecked += on_change
                panel.Children.Add(cb)
                self.boxes.append((t, i, cb))

    def read(self):
        for t, i, cb in self.boxes:
            if cb.IsChecked:
                t.chosen.add(i)
            else:
                t.chosen.discard(i)

    def set_all(self, value):
        for t, i, cb in self.boxes:
            cb.IsChecked = value


def count_items(targets):
    return sum(len(t.items) for t in targets)


def type_name(t):
    p = t.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    return p.AsString() if p else t.Name


def set_override(target, text):
    for item in target.items:
        item.ValueOverride = text


def clear_override(target):
    set_override(target, "")


def set_fields(target, values):
    """values: {'prefix': 'R.O. ', ...}; keys not present are untouched."""
    for item in target.items:
        for key, text in values.items():
            setattr(item, FIELD_PROPS[key], text)


def styles_for(doc, targets):
    """name -> DimensionType for every style matching the kinds selected.
    A mixed linear/angular/radial selection lists every matching style;
    apply_style() skips the ones that don't fit a given dimension."""
    kinds = set(t.dim.DimensionType.StyleType for t in targets)
    types = [t for t in DB.FilteredElementCollector(doc)
             .OfClass(DB.DimensionType)
             if t.StyleType in kinds and type_name(t)]
    return dict((type_name(t), t) for t in types)


def pick_style(doc, targets, title, allow_keep=True):
    """Ask for a dimension style valid for the selected dimensions.
    Returns a DimensionType, None for 'keep current', or False on cancel."""
    by_name = styles_for(doc, targets)
    names = sorted(by_name)
    if allow_keep:
        names.insert(0, KEEP_STYLE)
    choice = forms.SelectFromList.show(names, title=title,
                                       button_name="Apply", width=450)
    if not choice:
        return False
    if choice == KEEP_STYLE:
        return None
    return by_name[choice]


def apply_style(target, dtype):
    """Change the whole dimension's type (a style is per dimension, not
    per segment) only if Revit allows it. Returns bool."""
    dim = target.dim
    if dtype is None:
        return False
    if dim.GetTypeId() == dtype.Id:
        return False
    if dtype.Id not in dim.GetValidTypes():
        return False
    dim.ChangeTypeId(dtype.Id)
    return True
