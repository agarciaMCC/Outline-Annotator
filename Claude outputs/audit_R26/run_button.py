# -*- coding: utf-8 -*-
"""Headless runner for MCC buttons (used via the Revit MCP code tool).
Globals in: SCRIPT (path), VIEW (a View used in place of doc.ActiveView),
PICKS (list, or list of lists for successive SelectFromList calls), YES (bool for yes/no alerts).
Out: BUTTON_REPORT (text)."""
import sys, io
EXT = r"C:\Users\agarcia\Desktop\Claude Projects\Outline Annotator\MCC.extension"
if EXT + r"\lib" not in sys.path:
    sys.path.insert(0, EXT + r"\lib")
for _m in [m for m in list(sys.modules) if m.startswith('mcc_')]:
    del sys.modules[_m]
from pyrevit import forms, script

class _Exit(Exception): pass
class _Out(object):
    def __init__(self): self.lines = []
    def print_md(self, s): self.lines.append(s)
    def print_table(self, rows, columns=None, **kw):
        self.lines.append("| " + " | ".join(str(c) for c in (columns or [])) + " |")
        for r in rows: self.lines.append("| " + " | ".join(str(c) for c in r) + " |")
    def linkify(self, x, *a, **k):
        try: return str(x.IntegerValue)
        except Exception:
            try: return str(x.Value)
            except Exception: return str(x)
    def __getattr__(self, n): return lambda *a, **k: None
class _PB(object):
    cancelled = False
    def __init__(self, *a, **k): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def update_progress(self, *a, **k): pass
class _Cfg(object):
    def __getattr__(self, n): return None

_out = _Out()
_picks = list(PICKS) if PICKS and isinstance(PICKS[0], list) else [PICKS]
def _pick(items, **kw):
    want = _picks.pop(0) if _picks else []
    names = [i if isinstance(i, (str, unicode)) else getattr(i, "name", str(i)) for i in items]
    return [i for i, n in zip(items, names) if n in want] if kw.get("multiselect") else next((i for i, n in zip(items, names) if n in want), None)
def _alert(msg, exitscript=False, yes=False, no=False, **kw):
    _out.lines.append("ALERT: " + msg)
    if exitscript: raise _Exit()
    return YES if (yes or no) else True
def _exit(*a, **k): raise _Exit()
saved = dict(sel=forms.SelectFromList.show, alert=forms.alert, pb=forms.ProgressBar,
             out=script.get_output, ex=script.exit, cfg=script.get_config, scfg=script.save_config)
forms.SelectFromList.show = staticmethod(_pick)
forms.alert = _alert
forms.ProgressBar = _PB
script.get_output = lambda: _out
script.exit = _exit
script.get_config = lambda *a, **k: _Cfg()
script.save_config = lambda *a, **k: None
try:
    src = io.open(SCRIPT, encoding="utf-8").read()
    src = src.replace("view = doc.ActiveView", "view = __VIEW__")
    g = {"__name__": "__main__", "__file__": SCRIPT, "__VIEW__": VIEW}
    try:
        exec(compile(src, SCRIPT, "exec"), g)
    except _Exit:
        pass
    except Exception:
        import traceback
        _out.lines.append("TRACEBACK:\n" + traceback.format_exc())
finally:
    forms.SelectFromList.show = saved["sel"]; forms.alert = saved["alert"]; forms.ProgressBar = saved["pb"]
    script.get_output = saved["out"]; script.exit = saved["ex"]; script.get_config = saved["cfg"]; script.save_config = saved["scfg"]
BUTTON_REPORT = "\n".join(_out.lines)
