# -*- coding: utf-8 -*-
"""Headless runner for the Audit Dims button (read-only).
Call from execute_revit_code:  TARGETS=[view names]; OUTCSV=path; execfile(this)"""
import sys, io
EXT = r"C:\Users\agarcia\Desktop\Claude Projects\Outline Annotator\MCC.extension"
LIB = EXT + r"\lib"
if LIB not in sys.path:
    sys.path.insert(0, LIB)
SCRIPT = EXT + r"\MCC.tab\Diagnostics.panel\Audit Dims.pushbutton\script.py"
from pyrevit import forms, script
for _m in [m for m in list(sys.modules) if m.startswith('mcc_')]:
    del sys.modules[_m]   # always load the current lib code

class _Exit(Exception):
    pass

class _Out(object):
    def __init__(self): self.lines = []
    def print_md(self, s): self.lines.append(s)
    def print_table(self, rows, columns=None, **kw):
        self.lines.append("| " + " | ".join(columns or []) + " |")
        for r in rows: self.lines.append("| " + " | ".join(str(c) for c in r) + " |")
    def __getattr__(self, name): return lambda *a, **k: None

_out = _Out()
_saved = (forms.SelectFromList.show, forms.save_file, forms.alert, script.get_output, script.exit)
def _pick(items, **kw):
    return [k for k in items if any(k.startswith(t + "  ") or k == t for t in TARGETS)]
def _alert(msg, exitscript=False, **kw):
    _out.lines.append("ALERT: " + msg)
    if exitscript: raise _Exit()
def _exit(*a, **k): raise _Exit()
forms.SelectFromList.show = staticmethod(_pick)
forms.save_file = lambda **kw: OUTCSV
forms.alert = _alert
script.get_output = lambda: _out
script.exit = _exit
try:
    src = io.open(SCRIPT, encoding="utf-8").read()
    g = {"__name__": "__main__", "__file__": SCRIPT}
    try:
        exec(compile(src, SCRIPT, "exec"), g)
    except _Exit:
        pass
finally:
    (forms.SelectFromList.show, forms.save_file, forms.alert, script.get_output, script.exit) = _saved
AUDIT_REPORT = "\n".join(_out.lines)
