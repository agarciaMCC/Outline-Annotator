# -*- coding: utf-8 -*-
"""Run the PDF engines under the PC's own Python 3 (+ PyMuPDF) from pyRevit.
Shared by Grids from PDF / Columns from PDF."""
import glob
import os

from pyrevit import forms, script
from System.Diagnostics import Process, ProcessStartInfo


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


def _candidates(cfg):
    saved = cfg.get_option("python", "")
    if saved:
        yield saved, []
    yield "py", ["-3"]
    yield "python", []
    yield "python3", []
    roots = [os.environ.get("LOCALAPPDATA", ""), os.environ.get("ProgramFiles", ""),
             os.environ.get("ProgramFiles(x86)", ""), "C:\\"]
    for r in roots:
        if not r:
            continue
        for pat in (os.path.join(r, "Programs", "Python", "Python3*", "python.exe"),
                    os.path.join(r, "Python3*", "python.exe")):
            for exe in sorted(glob.glob(pat), reverse=True):
                yield exe, []


def _is_py3(exe, pre):
    code, out, err = run(exe, pre + ["-c", q("import sys;print(sys.version_info[0])")], 20000)
    return code == 0 and out.strip() == "3"


def ensure_python(cfg, title="MCC"):
    exe = pre = None
    for e, p in _candidates(cfg):
        if _is_py3(e, p):
            exe, pre = e, p
            break
    if not exe:
        ok = forms.alert(
            "Python 3 isn't installed on this PC (or isn't on the PATH). The PDF step "
            "needs it.\n\nInstall it from python.org (tick 'Add python.exe to PATH'), "
            "then run the button again - or browse to python.exe now.",
            title=title, options=["Browse to python.exe", "Cancel"])
        if ok != "Browse to python.exe":
            return None, None
        exe, pre = forms.pick_file(file_ext="exe"), []
        if not exe or not _is_py3(exe, pre):
            forms.alert("That isn't a Python 3 executable.")
            return None, None
    code, out, err = run(exe, pre + ["-c", q("import pymupdf")], 30000)
    if code != 0:
        if not forms.alert("The PDF reader (PyMuPDF) isn't installed for this Python yet.\n\n"
                           "Install it now? (pip install --user pymupdf - needs internet, "
                           "about a minute)", title=title, yes=True, no=True):
            return None, None
        code, out, err = run(exe, pre + ["-m", "pip", "install", "--user", "pymupdf"], 600000)
        if run(exe, pre + ["-c", q("import pymupdf")], 30000)[0] != 0:
            forms.alert("PyMuPDF install failed:\n\n" + (err or out)[-1500:])
            return None, None
    if not pre and cfg.get_option("python", "") != exe:
        cfg.python = exe
        script.save_config()
    return exe, pre
