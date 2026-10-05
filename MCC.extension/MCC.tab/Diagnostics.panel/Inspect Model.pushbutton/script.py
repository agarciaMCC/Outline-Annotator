# -*- coding: utf-8 -*-
"""Lists the names the other MCC buttons need to match: view templates,
title blocks, legends, scope boxes, dimension types, sheet parameters,
and any family that looks like an elevation box (with its parameters).
Read-only - changes nothing. Paste the output when tuning the CONFIG blocks."""
__title__ = "Inspect\nModel"
__author__ = "MCC ENG"

from mcc_compat import eid_int
from pyrevit import revit, DB, script

doc = revit.doc
out = script.get_output()
BOX_HINTS = ("ELEV", "BOX", "TOP", "DEPTH", "SUPPORT")



def type_name(e):
    """Type name that works in IronPython (Element.Name is hidden on types)."""
    p = e.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    return p.AsString() if p else e.Name

def names(elems, getter=lambda e: e.Name):
    return sorted(set(getter(e) for e in elems))


def section(title, items):
    out.print_md("### {} ({})".format(title, len(items)))
    for i in items:
        out.print_md("- `{}`".format(i))


views = list(DB.FilteredElementCollector(doc).OfClass(DB.View))
out.print_md("# Model inspection: {}".format(doc.Title))

section("Plan view templates (type: view type it applies to)",
        names((v for v in views if v.IsTemplate
               and v.ViewType in (DB.ViewType.FloorPlan,
                                  DB.ViewType.EngineeringPlan,
                                  DB.ViewType.CeilingPlan)),
              lambda v: "{}  ({})".format(v.Name, str(v.ViewType)
                                          .replace("EngineeringPlan",
                                                   "StructuralPlan"))))
section("Legend views",
        names(v for v in views if not v.IsTemplate
              and v.ViewType == DB.ViewType.Legend))
section("Scope boxes",
        names(DB.FilteredElementCollector(doc)
              .OfCategory(DB.BuiltInCategory.OST_VolumeOfInterest)
              .WhereElementIsNotElementType()))
section("Levels (name -> token the sheet builder would use)",
        ["{}  ->  {}".format(l.Name, l.Name.upper().replace("LEVEL", "", 1)
                             .strip(" -_").replace(" ", ""))
         for l in sorted(DB.FilteredElementCollector(doc).OfClass(DB.Level),
                         key=lambda l: l.Elevation)])

tbs = list(DB.FilteredElementCollector(doc)
           .OfCategory(DB.BuiltInCategory.OST_TitleBlocks)
           .WhereElementIsElementType())
section("Title block family : type",
        names(tbs, lambda t: "{} : {}".format(
            t.FamilyName, type_name(t))))

section("Dimension types",
        names(DB.FilteredElementCollector(doc).OfClass(DB.DimensionType),
              lambda t: type_name(t)))

sheets = list(DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet))
if sheets:
    s = sheets[0]
    section("Sheet instance parameters (writable, from sheet {})".format(
        s.SheetNumber),
        sorted(p.Definition.Name for p in s.Parameters if not p.IsReadOnly))
    section("Existing sheet numbers", sorted(x.SheetNumber for x in sheets))
else:
    out.print_md("### Sheets\nNone in model - sheet parameters unknown.")

# Tag / annotation families: every family in a *Tags category, plus
# generic annotations and detail items whose name hints at elevations
out.print_md("### Tag and annotation families (instance parameters)")
found = False
fams = sorted(DB.FilteredElementCollector(doc).OfClass(DB.Family),
              key=lambda f: (f.FamilyCategory.Name if f.FamilyCategory
                             else "", f.Name))
for fam in fams:
    cat = fam.FamilyCategory
    if cat is None:
        continue
    is_tag = "Tag" in cat.Name or "Symbol" in cat.Name
    hinted = any(h in fam.Name.upper() for h in BOX_HINTS) and \
        eid_int(cat.Id) in (int(DB.BuiltInCategory.OST_GenericAnnotation),
                                int(DB.BuiltInCategory.OST_DetailComponents))
    if not (is_tag or hinted):
        continue
    found = True
    sym_ids = list(fam.GetFamilySymbolIds())
    types = [type_name(doc.GetElement(i)) for i in sym_ids]
    out.print_md("**`{}`** - {} - types: {}".format(
        fam.Name, cat.Name, ", ".join("`{}`".format(t) for t in types)))
    inst = None
    for i in sym_ids:
        inst = next((x for x in DB.FilteredElementCollector(doc)
                     .OfClass(DB.FamilyInstance)
                     if x.Symbol.Id == i), None)
        if inst is None:
            inst = next((x for x in DB.FilteredElementCollector(doc)
                         .OfClass(DB.IndependentTag)
                         if x.GetTypeId() == i), None)
        if inst:
            break
    if inst:
        pnames = [p.Definition.Name for p in inst.Parameters
                  if not p.IsReadOnly and p.StorageType in (
                      DB.StorageType.String, DB.StorageType.Double)]
        out.print_md("  params: " + (", ".join(
            "`{}`".format(n) for n in sorted(set(pnames))) or "(none writable)"))
    else:
        out.print_md("  (no instances placed)")
if not found:
    out.print_md("No tag families found.")

# View parameters (browser organisation etc.) from an existing plan view
vp = next((v for v in views if not v.IsTemplate
           and v.ViewType == DB.ViewType.EngineeringPlan), None) or \
     next((v for v in views if not v.IsTemplate
           and v.ViewType == DB.ViewType.FloorPlan), None)
if vp:
    section("Writable view parameters (from '{}')".format(vp.Name),
            ["{} = {}".format(p.Definition.Name, p.AsString() or
                              p.AsValueString() or "")
             for p in sorted(vp.Parameters, key=lambda p: p.Definition.Name)
             if not p.IsReadOnly and p.StorageType == DB.StorageType.String])

# Writable instance parameters on the members the box tags read from
out.print_md("### Writable instance parameters on model elements")
for label, bic in (("Floor", DB.BuiltInCategory.OST_Floors),
                   ("Beam", DB.BuiltInCategory.OST_StructuralFraming),
                   ("Column", DB.BuiltInCategory.OST_StructuralColumns),
                   ("Wall", DB.BuiltInCategory.OST_Walls)):
    e = DB.FilteredElementCollector(doc).OfCategory(bic) \
        .WhereElementIsNotElementType().FirstElement()
    if e is None:
        out.print_md("**{}**: none in model".format(label))
        continue
    pn = sorted(set(p.Definition.Name for p in e.Parameters
                    if not p.IsReadOnly and p.StorageType in (
                        DB.StorageType.String, DB.StorageType.Double)))
    out.print_md("**{}** (id {}): ".format(label, eid_int(e.Id)) +
                 ", ".join("`{}`".format(n) for n in pn))

out.print_md("---\nCopy this output back to set the CONFIG blocks in "
             "Sheet Builder, Dim Soffit and lib/mcc_elev.py.")
