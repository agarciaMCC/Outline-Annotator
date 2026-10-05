# -*- coding: utf-8 -*-
"""Revit version shims shared by the MCC buttons."""


def eid_int(eid):
    """ElementId as an int on any Revit version.
    ElementId.Value exists in 2024+; IntegerValue was removed in 2026."""
    try:
        return int(eid.Value)
    except AttributeError:
        return eid.IntegerValue


def make_eid(i):
    """ElementId from an int on any Revit version. 2026 adds enum/Int64
    overloads, so a bare Python int is ambiguous there; 2023 only has Int32."""
    from System import Int64
    from Autodesk.Revit.DB import ElementId
    try:
        return ElementId(Int64(int(i)))
    except TypeError:
        return ElementId(int(i))
