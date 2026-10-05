# Fit Grids — behaviour rules (agreed 2026-09-30)

Button: MCC tab > Soffit Plans > Fit Grids. Logic in `lib/mcc_gridfit.py` (pure geometry, testable offline); Revit wiring in the button's `script.py` + `ui.xaml`.

1. **Aligned bubbles** — each family of parallel grids gets one bubble line per side.
2. **Clearance set by the tightest bubble** — where grids leave a visible hard slab edge, the row moves out until the bubble nearest the slab is exactly the clearance (default 16 ft) from it, measured as true distance so angled edges work. Grids drawn on a slab edge count as touching it.
3. **Never inside a visible hard slab edge.**
4. **Crop cuts the slab / no slab on the grid** — bubble sits just outside the crop edge (default 1/8" paper gap).
5. **Grid doesn't cross the crop** — its bubbles are hidden.
6. Bubble visibility otherwise left alone (line direction preserved).
7. View picker: plan views with zone dependents listed under parents; filter box; run from a sheet to pre-tick its placed views ("This sheet" button). "Set as default" remembers clearance + gap. No end-of-run report — alert only on problems.
8. Views are processed dependents first, parents last; afterwards the button checks whether another view overwrote a view's grid ends (possible shared extents between parent and dependents) and flags it.

Open questions to confirm in Revit: whether grid ends outside the model crop display (and whether annotation crop clips them); whether dependent views share grid extents with their parent.
