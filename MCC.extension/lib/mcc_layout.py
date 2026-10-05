# -*- coding: utf-8 -*-
"""Dim Soffit v2, stage 3 - LAYOUT.

Places every planned String of a view together, text-aware, then creates
the dimensions in one transaction and reads back what Revit made.

A candidate position for a string = (side, lane, slide): which side of the
object its home station is on, how many lanes out (LANE_STEP apart, max
MAX_LANE), and a slide along the object. Each candidate is scored; hard
constraints reject it outright:
  - outside the view's annotation crop
  - dim line over a parallel grid line (GRID_CLEAR)
  - dim line crossing a column / wall / opening (beams and CJs: soft)
  - same-direction placed string too close and overlapping
  - crossing a placed string of another direction
  - estimated TEXT BOX overlapping any placed text box or dim line
Text boxes come from the segment values (known from the witness offsets),
the dimension type's text size and the view scale; a segment too short for
its text gets its box pulled out past the nearer end of the string, as the
real text will be.

Strings with no feasible candidate are not forced in: they go to the
review list with the constraint that blocked them most often."""
import math
from pyrevit import DB
import mcc_plan as P
import mcc_place as PL
from mcc_strings import ftin

CFG = {
    # spacing is set on PAPER (measured on Kalae + Alia hand dims, 2026-10-05:
    # rows 3/16" apart at every scale, first row ~1/4" off the object);
    # Layout converts these to plan feet with the view scale
    "LANE_STEP_IN": 0.1875,  # paper inches between stacked dim lines
    "FIRST_GAP_IN": 0.25,    # paper inches from the object to the first row
    "STATION_GAP_IN": 0.16,  # paper inches; parallel strings closer than this must not overlap
    "W_STACK": -1.0,         # base cost of the next row of a stack, one lane out from the last
    "W_ORDER": 3.0,          # a row nearer the element than a shorter neighbour (or further than a longer one)
    "W_IN_SHAFT": 8.0,       # a shaft's own overall-size dim inside the shaft: last resort only
    "EDGE_CLEAR_IN": 0.0625, # paper inches; a dim line keeps this clear of an edge running the same way
    "W_JOIN": -1.5,          # bonus for lining up end-to-end with a dim sharing a witness line (joined after)
    "W_COLLINEAR": -0.75,    # bonus for a dim line on the same line as a placed parallel dim (Adolfo: align)
    "COLLINEAR_REACH": 4.0,  # ft from the preferred station a string may move to line up
    "MAX_LANE": 2,          # lanes 0..2 (Adolfo: 2 to 3 rows), 3 = last resort
    "LAST_RESORT_LANE": 3,
    "SLIDE_STEP": 1.0,      # ft
    "SLIDE_MAX": 4.0,       # ft either way along the object
    "GRID_CLEAR": 1.5,      # ft; no dim line this close to a parallel grid
    "CROP_MARGIN": 1.0,
    "TEXT_PAD": 0.25,
    "TEXT_LIFT": 0.2,       # x text size: gap between dim line and the text (Revit default, measured)
    "TEXT_FIT_MARGIN": 0.5, # x text size: a segment narrower than text + this gets its text pulled out       # ft around text boxes
    "W_LANE": 2.0, "W_SIDE": 4.0, "W_SLIDE": 0.5, "W_BEAM": 1.0, "W_CJ": 1.0,
    "W_CROSS": 2.5,         # per dim line crossed - two crossings cost more than the other side (W_SIDE)
    "W_CROSS_LEADER": 3.0,  # a dim line or leader crossing another string's leader
    "W_ALIGN": 0.5,         # base cost of a candidate that lines pulled text up with a neighbour's
    "MARGIN_IN": 2.5,       # ft past the end of an edge for the first lane in open margin
    "MARGIN_MAX": 12.0,     # ft: how far into the margin a string may go to line up with another
    "W_MARGIN": -0.5,       # base cost of a margin lane: preferred over a lane inside the slab
    "W_INSIDE": 3.5,
    "UNBLOCK_COST": None,   # move neighbours for a placement costing more than this (None: off -
                            # moving placed strings cost more real overlaps than it saved on L3N)
    "UNBLOCK_PAIRS": False, # also try lifting two neighbours at once (slow: 20 s -> 60 s on L3N)        # a no-home-side string laid through its own span (across a shaft)
    "W_OUTSIDE": 2.0,       # per ft the station sits past the string's home span
    "W_TEXT_CROP": 3.0,     # text box clipped by the crop
    "W_TEXT_OBST": 2.0,     # text box over a wall/column/opening/beam
    "END_TRIM": 0.6,        # ft; dim-line ends may touch an obstacle (anchors)
    "IMPROVE_PASSES": 2,
}

PRIORITY = {"run": 0, "corner": 0, "bump": 1, "notch": 1, "step": 1,
            "opening": 2, "beam": 3, "cj": 4}


class Placed(object):
    __slots__ = ("s", "fi", "st_f", "lo_f", "hi_f", "seg", "boxes", "cost", "cand", "rect", "tplan", "leaders", "side")

    def __init__(self, s, fi, st_f, lo_f, hi_f, seg, boxes, cost, cand, tplan=None):
        self.s, self.fi, self.st_f, self.lo_f, self.hi_f = s, fi, st_f, lo_f, hi_f
        self.seg, self.boxes, self.cost, self.cand, self.tplan = seg, boxes, cost, cand, tplan
        self.leaders = [it[4] for it in (tplan or []) if it[4]]
        self.side = None            # set by Layout: +1/-1 element toward higher/lower family stations, 0 inside span
        pts = list(seg) + [pt for b in boxes for pt in b] + [pt for l in self.leaders for pt in l]
        self.rect = (min(p[0] for p in pts), min(p[1] for p in pts),
                     max(p[0] for p in pts), max(p[1] for p in pts))


def _rects_apart(a, b, gap):
    return a[2] + gap < b[0] or b[2] + gap < a[0] or a[3] + gap < b[1] or b[3] + gap < a[1]


def _rect_poly(c, u, n, half_u, half_n):
    """World polygon of a rectangle centred at c, half-extents along u / n."""
    return [(c[0] + u[0] * a + n[0] * b, c[1] + u[1] * a + n[1] * b)
            for a, b in ((-half_u, -half_n), (half_u, -half_n), (half_u, half_n), (-half_u, half_n))]


def _polys_overlap(A, B):
    if P.point_in_poly(sum(p[0] for p in A) / 4.0, sum(p[1] for p in A) / 4.0, B):
        return True
    if P.point_in_poly(sum(p[0] for p in B) / 4.0, sum(p[1] for p in B) / 4.0, A):
        return True
    for i in range(4):
        if P.seg_hits_poly(A[i], A[(i + 1) % 4], B):
            return True
    return False


def _box_poly_overlap(box, poly):
    """A 4-corner text box against a polygon with any number of vertices
    (_polys_overlap assumes both have 4)."""
    if any(P.point_in_poly(x, y, poly) for x, y in box):
        return True
    if P.point_in_poly(poly[0][0], poly[0][1], box):
        return True
    return any(P.seg_hits_poly(box[i], box[(i + 1) % 4], poly) for i in range(4))


class Layout(object):
    def __init__(self, model, strings, view, dim_type, crop, cfg=None):
        self.m = model
        self.strings = strings
        self.view = view
        self.crop = crop
        self.c = dict(CFG)
        if cfg:
            self.c.update(cfg)
        k = float(view.Scale or 96) / 12.0          # paper inches -> plan feet
        self.c.setdefault("LANE_STEP", self.c["LANE_STEP_IN"] * k)
        self.c.setdefault("FIRST_GAP", self.c["FIRST_GAP_IN"] * k)
        self.c.setdefault("STATION_GAP", self.c["STATION_GAP_IN"] * k)
        self.c.setdefault("EDGE_CLEAR", self.c["EDGE_CLEAR_IN"] * k)
        self.par_edges = self._parallel_edges(model)
        self.tsize = PL.text_size_ft(dim_type) * view.Scale     # ft on the plan
        self.notes = self._existing_annotations(view)            # text notes, tags, symbols already in the view
        self.placed = []
        self.review = []            # (string, reason)
        self.blocked = {}

    def _parallel_edges(self, model):
        """Per grid family: soffit edges running the way that family's dim
        lines run (across the grids) -> [(family station, off lo, off hi)]."""
        faces = []
        for sl in model.slabs:
            faces += list(sl.edges)
            for loop in sl.open_edges:
                faces += list(loop)
        for bm in model.beams:
            faces += list(getattr(bm, "sides", None) or getattr(bm, "faces", None) or [])
        out = {}
        for fi, fam in enumerate(model.families):
            g, g0, u, n = model.grids[fam[0]]
            rows = []
            for f in faces:
                if not P.parallel(f.d, n):
                    continue
                st = model.station(f.p0, fam[0])
                o0, o1 = model.offset(f.p0, fam[0]), model.offset(f.p1, fam[0])
                rows.append((st, min(o0, o1), max(o0, o1)))
            out[fi] = rows
        return out

    def _existing_annotations(self, view):
        """Rectangles (world) of annotation already in the view that dims
        must keep clear of: text notes, tags, generic annotations, keynotes,
        view references. Grids, dims, detail lines are handled elsewhere."""
        doc = view.Document
        cats = set()
        for name in ("OST_TextNotes", "OST_GenericAnnotation", "OST_KeynoteTags", "OST_ReferenceViewer",
                     "OST_SpotElevations", "OST_SpotCoordinates", "OST_MultiCategoryTags", "OST_MaterialTags",
                     "OST_StructuralFramingTags", "OST_StructuralColumnTags", "OST_FloorTags", "OST_WallTags",
                     "OST_StructuralFoundationTags", "OST_GenericModelTags", "OST_DetailComponentTags"):
            try:
                cats.add(int(getattr(DB.BuiltInCategory, name)))
            except Exception:
                pass
        out = []
        try:
            col = DB.FilteredElementCollector(doc, view.Id).WhereElementIsNotElementType()
            for e in col:
                try:
                    if e.Category is None or int(e.Category.Id.Value if hasattr(e.Category.Id, "Value") else e.Category.Id.IntegerValue) not in cats:
                        continue
                    bb = e.get_BoundingBox(view)
                    if bb is None:
                        continue
                    if (bb.Max.X - bb.Min.X) > 60 or (bb.Max.Y - bb.Min.Y) > 60:
                        continue                     # leaders across the sheet etc.
                    out.append([(bb.Min.X, bb.Min.Y), (bb.Max.X, bb.Min.Y), (bb.Max.X, bb.Max.Y), (bb.Min.X, bb.Max.Y)])
                except Exception:
                    continue
        except Exception:
            pass
        return out

    # ---------------- frames ----------------
    def frame(self, gi):
        return self.m.grids[gi]

    def world(self, gi, st, off):
        g, g0, u, n = self.m.grids[gi]
        return (g0[0] + u[0] * st + n[0] * off, g0[1] + u[1] * st + n[1] * off)

    def fam_sign(self, gi):
        """+1 when stations in frame gi run the same way as the family frame."""
        g, g0, u, n = self.m.grids[gi]
        g2, g20, u2, n2 = self.m.grids[self.m.families[self.m.fam_of[gi]][0]]
        return 1 if (u[0] * u2[0] + u[1] * u2[1]) > 0 else -1

    def spans_meet(self, s1, s2, slack=1.0):
        """Do two strings of one family measure elements at the same place
        along the grids (their spans overlap, in family stations)?"""
        a = sorted(self.to_fam(s1.gi, x, 0.0)[0] for x in s1.span)
        b = sorted(self.to_fam(s2.gi, x, 0.0)[0] for x in s2.span)
        return a[0] - slack <= b[1] and b[0] - slack <= a[1]

    def elem_side(self, s, sf):
        """Where string s's element lies from a dim line at family station sf:
        +1 toward higher stations, -1 lower, 0 when the line is inside the span."""
        a = self.to_fam(s.gi, s.span[0], 0.0)[0]
        b = self.to_fam(s.gi, s.span[1], 0.0)[0]
        if sf < min(a, b) - 0.05:
            return 1
        if sf > max(a, b) + 0.05:
            return -1
        return 0

    def to_fam(self, gi, st, off):
        p = self.world(gi, st, off)
        gr = self.m.families[self.m.fam_of[gi]][0]
        return self.m.station(p, gr), self.m.offset(p, gr)

    # ---------------- text model ----------------
    def text_side(self, gi):
        """Which way (+1/-1 along the frame's u) Revit puts dimension text:
        above the line in reading orientation, i.e. the left-hand side of the
        dim direction once that direction is turned to read right/up."""
        g, g0, u, n = self.frame(gi)
        nn = n
        if nn[0] < -1e-6 or (abs(nn[0]) < 1e-6 and nn[1] < 0):
            nn = (-nn[0], -nn[1])
        side = (-nn[1], nn[0])
        return 1 if (side[0] * u[0] + side[1] * u[1]) > 0 else -1

    def text_plan(self, s, st):
        """Where each segment's text goes for string s at station st - the
        one rule used both to judge a candidate and to set TextPosition.
        -> [(value, width, centre_world, pulled)]"""
        offs = [r[0] for r in s.refs]
        ts = self.tsize
        h = ts * 1.4
        side = self.text_side(s.gi)
        fit = self.c["TEXT_FIT_MARGIN"] * ts
        row0 = st + side * (self.c["TEXT_LIFT"] * ts + 0.5 * ts)   # centre of text sitting on the line
        # pulled-out text goes on the far side of the dim line from the
        # element being dimensioned (Adolfo) - never in the gap between them;
        # a line running through its own span keeps Revit's text side
        s_lo, s_hi = s.span
        mid = (s_lo + s_hi) / 2.0
        pull_side = side if s_lo - 0.1 <= st <= s_hi + 0.1 else (1 if st > mid else -1)
        row0_pull = st + pull_side * (self.c["TEXT_LIFT"] * ts + 0.5 * ts)
        plan = []
        rows = {}                                   # end -> number of pulled texts stacked there
        for a, b in zip(offs, offs[1:]):
            v = b - a
            w = PL.text_width(ftin(v), ts)
            if v >= w + fit:
                plan.append((v, w, self.world(s.gi, row0, (a + b) / 2.0), False, None))
                continue
            # pulled past the nearer end with a leader; later ones stack outward,
            # all starting at the same inner edge so the column reads aligned
            end = 0 if abs(a - offs[0]) <= abs(b - offs[-1]) else 1
            e = offs[0] if end == 0 else offs[-1]
            sgn = -1 if end == 0 else 1
            centre_off = e + sgn * (0.5 * ts + w / 2.0)
            k = rows.get(end, 0)
            rows[end] = k + 1
            c = self.world(s.gi, row0_pull + pull_side * k * h, centre_off)
            leader = (self.world(s.gi, st, (a + b) / 2.0), c)
            plan.append((v, w, c, True, leader))
        return plan

    def text_boxes(self, s, st, plan=None):
        """Estimated text boxes (world polygons) for string s at station st."""
        g, g0, u, n = self.frame(s.gi)
        h = self.tsize * 1.4
        pad = self.c["TEXT_PAD"]
        return [_rect_poly(it[2], n, u, it[1] / 2.0 + pad, h / 2.0 + pad)
                for it in (plan or self.text_plan(s, st))]

    # ---------------- constraints ----------------
    def in_crop(self, pts):
        if not self.crop:
            return True
        m = self.c["CROP_MARGIN"]
        for x, y in pts:
            for dx, dy in ((0, 0), (m, 0), (-m, 0), (0, m), (0, -m)):
                if not P.point_in_poly(x + dx, y + dy, self.crop):
                    return False
        return True

    def evaluate(self, s, st):
        """-> (cost, boxes) or (None, reason)."""
        c = self.c
        offs = [r[0] for r in s.refs]
        lo, hi = min(offs), max(offs)
        p = self.world(s.gi, st, lo)
        q = self.world(s.gi, st, hi)
        plan = self.text_plan(s, st)
        boxes = self.text_boxes(s, st, plan)
        leaders = [it[4] for it in plan if it[4]]
        allpts = [p, q] + [pt for b in boxes for pt in b] + [pt for l in leaders for pt in l]
        if not self.in_crop([p, q]):
            return None, "outside crop"
        pen = 0.0
        if not self.in_crop([pt for b in boxes for pt in b]):
            pen += c["W_TEXT_CROP"]            # text clipped at the crop edge
        # the dim line may END at an obstacle (wall-face anchor, edge on a
        # wall): only its interior counts for crossings
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        if L > 2 * c["END_TRIM"]:
            k = c["END_TRIM"] / L
            pi = (p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k)
            qi = (q[0] - (q[0] - p[0]) * k, q[1] - (q[1] - p[1]) * k)
        else:
            pi, qi = None, None
        g, g0, u, n = self.frame(s.gi)
        mid = self.world(s.gi, st, (lo + hi) / 2.0)
        for gj, (g2, g20, u2, n2) in enumerate(self.m.grids):
            if self.m.fam_of[gj] == s.fi or not P.parallel(u2, n, 0.35):
                continue
            if abs((mid[0] - g20[0]) * n2[0] + (mid[1] - g20[1]) * n2[1]) < c["GRID_CLEAR"]:
                return None, "on a grid line"
        sf, a = self.to_fam(s.gi, st, lo)
        _, b = self.to_fam(s.gi, st, hi)
        a, b = min(a, b), max(a, b)
        xs = [pt[0] for pt in allpts]; ys = [pt[1] for pt in allpts]
        myrect = (min(xs), min(ys), max(xs), max(ys))
        # stacked rows: shortest nearest the element, longest furthest (Adolfo);
        # equal lengths: the chain inside, the single overall dim outside
        my_side = self.elem_side(s, sf)
        if my_side:
            my_key = (round((b - a) * 48), -len(s.refs))
            reach = 1.6 * c["LANE_STEP"]
            for pl in self.placed:
                # rows of the SAME element keep the order however far apart
                # they ended up (the 2'-0" / 3'-0 1/8" pair sat a wall apart)
                same = s.feature is not None and pl.s.feature is s.feature
                if pl.fi != s.fi or pl.side != my_side or (abs(pl.st_f - sf) > reach and not same):
                    continue
                if min(b, pl.hi_f) - max(a, pl.lo_f) <= 0.1:
                    continue
                pk = (round((pl.hi_f - pl.lo_f) * 48), -len(pl.s.refs))
                if pk == my_key:
                    continue
                nearer = my_side * (sf - pl.st_f) > 0
                if (my_key > pk) == nearer:
                    pen += c["W_ORDER"]
        for pl in self.placed:
            if _rects_apart(myrect, pl.rect, c["STATION_GAP"]):
                continue
            if pl.fi == s.fi:
                if abs(pl.st_f - sf) < c["STATION_GAP"] and not (b <= pl.lo_f + 0.1 or a >= pl.hi_f - 0.1):
                    return None, "too close to a parallel string"
            else:
                if P.seg_intersect(p, q, pl.seg[0], pl.seg[1]):
                    pen += c["W_CROSS"]
            for bx in pl.boxes:
                if P.seg_hits_poly(p, q, bx):
                    return None, "line through another text"
                for mine in boxes:
                    if _polys_overlap(mine, bx):
                        return None, "text overlaps another text"
                for ml in leaders:
                    if P.seg_hits_poly(ml[0], ml[1], bx):
                        return None, "leader through another text"
            for mine in boxes:
                if P.seg_hits_poly(pl.seg[0], pl.seg[1], mine):
                    return None, "text over another line"
                for lb in pl.leaders:
                    if P.seg_hits_poly(lb[0], lb[1], mine):
                        return None, "text over another leader"
            for lb in pl.leaders:
                if P.seg_intersect(p, q, lb[0], lb[1]):
                    pen += c["W_CROSS_LEADER"]
                for ml in leaders:
                    if P.seg_intersect(ml[0], ml[1], lb[0], lb[1]):
                        pen += c["W_CROSS_LEADER"]
            for ml in leaders:
                if P.seg_intersect(ml[0], ml[1], pl.seg[0], pl.seg[1]):
                    pen += c["W_CROSS_LEADER"]
        for poly in self.notes:
            r = (min(p[0] for p in poly), min(p[1] for p in poly), max(p[0] for p in poly), max(p[1] for p in poly))
            if _rects_apart(myrect, r, 0.0):
                continue
            if any(_polys_overlap(bx, poly) for bx in boxes):
                return None, "text over a note/tag"
            if P.seg_hits_poly(p, q, poly) or any(P.seg_hits_poly(ml[0], ml[1], poly) for ml in leaders):
                return None, "line through a note/tag"
        for o in self.m.obstacles:
            # openings are no-go zones for every dim - including the ones that
            # measure that opening (their obstacle carries the slab's id, which
            # used to let the slab's own strings run straight through)
            if o.eid in s.owners and o.kind != "opening":
                continue
            if _rects_apart(myrect, o.rect, 0.0):
                continue
            line_hit = pi is not None and P.seg_hits_poly(pi, qi, o.poly)
            text_hit = any(_polys_overlap(bx, o.poly) for bx in boxes)
            if o.kind == "opening":
                # the true outline, not the convex hull (an L-shaped opening's
                # hull covers solid slab beside it)
                poly = o.raw or o.poly
                a_, b_ = (pi, qi) if pi is not None else (p, q)
                line_in = P.seg_hits_poly(a_, b_, poly)
                text_in = any(_box_poly_overlap(bx, poly) for bx in boxes) or \
                    any(P.seg_hits_poly(ml[0], ml[1], poly) for ml in leaders)
                if not (line_in or text_in):
                    continue
                # Adolfo: a shaft may carry dims inside "if absolutely necessary",
                # and only its OVERALL SIZE (edge to edge of that shaft) - never a
                # dim locating an edge off a grid. Allowed at a high cost.
                f = s.feature
                own_shaft = f is not None and f.kind == "opening" and getattr(f, "sub", None) in ("shaft", "core") \
                    and "centroid" in getattr(f, "meta", {}) and P.point_in_poly(f.meta["centroid"][0], f.meta["centroid"][1], poly)
                size_only = all(r[2] == "opening edge" for r in s.refs)
                if own_shaft and size_only:
                    pen += c["W_IN_SHAFT"]
                    continue
                return None, ("inside an opening" if line_in else "text inside an opening")
            if line_hit:
                if o.kind == "beam":
                    pen += c["W_BEAM"]
                else:
                    return None, "over a %s" % o.kind
            if text_hit:
                pen += c["W_TEXT_OBST"]         # text over a member/beam: avoid, don't forbid
        # a dim line must not lie on (or hug) an edge running the same way
        for e_st, e_lo, e_hi in self.par_edges.get(s.fi, ()):
            if abs(e_st - sf) < c["EDGE_CLEAR"] and min(b, e_hi) - max(a, e_lo) > c["END_TRIM"]:
                return None, "on an edge"
        return pen, boxes

    # ---------------- candidates ----------------
    def candidates(self, s, allow_last_resort=False):
        c = self.c
        s_lo, s_hi = s.span
        prefer = s.prefer if s.prefer is not None else (s_lo + s_hi) / 2.0
        home = s.outward if s.outward is not None else 0
        out = []
        max_lane = c["LAST_RESORT_LANE"] if allow_last_resort else c["MAX_LANE"]
        sides = [home, -home] if home else [1, -1]
        n_slide = int(c["SLIDE_MAX"] / c["SLIDE_STEP"])
        # the next row of a stack goes one lane further out from the row before
        # it (shortest dim nearest the object, as on the hand sheets)
        stk = getattr(s, "stack", None)
        if stk and stk[1] > 0:
            prev = [pl for pl in self.placed if getattr(pl.s, "stack", None)
                    and pl.s.stack[0] == stk[0] and pl.s.stack[1] < stk[1]]
            if prev:
                last = max(prev, key=lambda pl: pl.s.stack[1])
                st0 = last.cand[0]
                away = home or (1 if st0 >= (s_lo + s_hi) / 2.0 else -1)
                for j in (1, 2):
                    out.append((c["W_STACK"] + (j - 1) * c["W_LANE"], st0 + away * j * c["LANE_STEP"],
                                (away, "stack", j)))
        if home == 0:
            # through the span itself (a shaft width is read across the shaft)
            for k in range(-n_slide, n_slide + 1):
                st = prefer + k * c["SLIDE_STEP"]
                if s_lo + 0.5 <= st <= s_hi - 0.5:
                    out.append((c["W_INSIDE"] + abs(k) * c["W_SLIDE"], st, (0, 0, k)))
        for side_i, side in enumerate(sides):
            for lane in range(max_lane + 1):
                for k in range(-n_slide, n_slide + 1):
                    if home == 0:
                        # no home side: lanes start just outside the span on each side
                        edge = s_hi if side > 0 else s_lo
                        st = edge + side * (c["FIRST_GAP"] + lane * c["LANE_STEP"]) + k * c["SLIDE_STEP"]
                    else:
                        st = prefer + side * lane * c["LANE_STEP"] + k * c["SLIDE_STEP"]
                    outside = max(0.0, s_lo - st, st - s_hi)
                    base = lane * c["W_LANE"] + (c["W_SIDE"] if (home and side != home) else 0) \
                        + abs(k) * c["W_SLIDE"] + outside * c["W_OUTSIDE"]
                    out.append((base, st, (side, lane, k)))
        # a run whose edge ends at open margin: lanes in that margin, past the
        # end, with no "outside the span" cost - and lined up with any string
        # of the same family already standing in that margin
        if getattr(s, "free", False) and home:
            end = s_lo if home < 0 else s_hi
            for lane in range(max_lane + 1):
                for k in range(-n_slide, n_slide + 1):
                    st = end + home * (c["MARGIN_IN"] + lane * c["LANE_STEP"]) + k * c["SLIDE_STEP"]
                    out.append((c["W_MARGIN"] + lane * c["W_LANE"] + abs(k) * c["W_SLIDE"], st, (home, "margin", k)))
            sf0, _ = self.to_fam(s.gi, end, 0.0)
            for pl in self.placed:
                if pl.fi != s.fi:
                    continue
                dst = (pl.st_f - sf0)
                if 0.5 < dst * home * self.fam_sign(s.gi) < c["MARGIN_MAX"]:
                    st = end + abs(dst) * home
                    out.append((c["W_ALIGN"], st, (home, "margin-align", 0)))
        # dim lines in a row: the same line as a placed parallel dim of this
        # family (not overlapping it - evaluate() rejects that), within reach
        a0, _ = self.to_fam(s.gi, 0.0, 0.0)
        sgn = self.fam_sign(s.gi)
        my_offs = [self.to_fam(s.gi, 0.0, r[0])[1] for r in s.refs]
        my_lo, my_hi = min(my_offs), max(my_offs)
        seen_st = set()
        for pl in self.placed:
            if pl.fi != s.fi:
                continue
            st = (pl.st_f - a0) * sgn
            key = round(st * 16)
            # end to end with a dim sharing a witness line: they get joined into
            # one string afterwards (9'-3 7/8" | 8'-4 1/8" through the grid)
            joins = (abs(my_lo - pl.hi_f) < 1.0 / 96 or abs(my_hi - pl.lo_f) < 1.0 / 96) \
                and s.feature is not None and pl.s.feature is s.feature
            if key in seen_st or abs(st - prefer) > c["COLLINEAR_REACH"] * (2 if joins else 1):
                continue
            seen_st.add(key)
            bonus = c["W_JOIN"] if joins else c["W_COLLINEAR"]
            outside = max(0.0, s_lo - st, st - s_hi)
            if home:
                side_pen = c["W_SIDE"] if (st - prefer) * home < -0.5 else 0.0
                slide = abs(st - prefer) * c["W_SLIDE"]
            else:
                side_pen = c["W_INSIDE"] if outside == 0.0 else 0.0
                slide = 0.0
            out.append((bonus + side_pen + slide + outside * c["W_OUTSIDE"], st, (0, "collinear", 0)))
        # pulled text lines up with a neighbour's pulled text (same family, nearby)
        probe = self.text_plan(s, prefer)
        if any(it[3] for it in probe):
            ts = self.tsize
            lift = (self.c["TEXT_LIFT"] + 0.5) * ts
            reach = max_lane * c["LANE_STEP"] + c["SLIDE_MAX"]
            seen = set()
            for pl in self.placed:
                if pl.fi != s.fi or not pl.leaders:
                    continue
                for it in pl.tplan:
                    if not it[3]:
                        continue
                    row = self.m.station(it[2], s.gi)
                    for side in (1, -1):
                        st = row - side * lift
                        key = round(st * 8)
                        if key in seen or abs(st - prefer) > reach:
                            continue
                        mine = self.text_plan(s, st)
                        pulled = [m for m in mine if m[3]]
                        if not pulled or abs(self.m.station(pulled[0][2], s.gi) - row) > 0.05:
                            continue                # its pull side puts the row elsewhere
                        if abs(self.m.offset(pulled[0][2], s.gi) - self.m.offset(it[2], s.gi)) > 30:
                            continue                # too far along to read as one column
                        seen.add(key)
                        outside = max(0.0, s_lo - st, st - s_hi)
                        out.append((c["W_ALIGN"] + outside * c["W_OUTSIDE"], st, (side, "align", 0)))
        out.sort(key=lambda t: t[0])
        return out

    def place_one(self, s, allow_last_resort=False):
        best = None
        reasons = {}
        for base, st, cand in self.candidates(s, allow_last_resort):
            if best is not None and base >= best[0]:
                break                       # candidates are sorted by base cost
            pen, boxes = self.evaluate(s, st)
            if pen is None:
                reasons[boxes] = reasons.get(boxes, 0) + 1
                continue
            cost = base + pen
            if best is None or cost < best[0]:
                best = (cost, st, boxes, cand)
        if best is None:
            return None, (max(reasons.items(), key=lambda kv: kv[1])[0] if reasons else "no candidates")
        cost, st, boxes, cand = best
        offs = [r[0] for r in s.refs]
        lo, hi = min(offs), max(offs)
        sf, a = self.to_fam(s.gi, st, lo)
        _, b = self.to_fam(s.gi, st, hi)
        pl = Placed(s, s.fi, sf, min(a, b), max(a, b),
                    (self.world(s.gi, st, lo), self.world(s.gi, st, hi)), boxes, cost, (st, cand),
                    self.text_plan(s, st))
        pl.side = self.elem_side(s, sf)
        return pl, None

    # ---------------- driver ----------------
    def run(self):
        def _key(s):
            stk = getattr(s, "stack", None)
            # a small void's edge dims go after the real openings' strings, so
            # they don't take the spot beside an opening its own dims need
            void = 1 if s.feature is not None and getattr(s.feature, "sub", None) == "void" else 0
            return (0 if s.role == "locate" else 1,
                    PRIORITY.get(s.feature.kind, 9) if s.feature else 9, void,
                    stk[0] if stk else 0, stk[1] if stk else 0)
        order = sorted(self.strings, key=_key)
        pending = []
        for s in order:
            pl, why = self.place_one(s)
            if pl is None:
                pending.append((s, why))
            else:
                self.placed.append(pl)
        # last resort: lane 3 for what didn't fit
        still = []
        for s, why in pending:
            pl, why2 = self.place_one(s, allow_last_resort=True)
            if pl is None:
                still.append((s, why2))
            else:
                self.placed.append(pl)
        # improvement passes: re-place the worst-scoring strings
        for _ in range(self.c["IMPROVE_PASSES"]):
            worst = sorted(self.placed, key=lambda pl: -pl.cost)[:max(1, len(self.placed) // 5)]
            for pl in worst:
                self.placed.remove(pl)
                pl2, why = self.place_one(pl.s, allow_last_resort=True)
                self.placed.append(pl2 if pl2 is not None else pl)
        # unblock pass: a string that still has no place may be blocked by one
        # neighbour that can move - lift the neighbour, place ours, re-place it
        still = self._unblock(still)
        # ...and a string that only found a poor spot (far outside its span)
        # gets the same treatment, keeping the poor spot if nothing better
        poor = [pl for pl in self.placed if pl.cost > self.c["UNBLOCK_COST"]] if self.c["UNBLOCK_COST"] else []
        for pl in poor:
            if pl not in self.placed:
                continue                        # already moved as someone's neighbour
            self.placed.remove(pl)
            left = self._unblock([(pl.s, "poor")], max_total=pl.cost - 1.0)
            if left:
                self.placed.append(pl)
        self._join_collinear()
        self._order_stacks()
        self.review = still
        for s, why in still:
            self.blocked[why] = self.blocked.get(why, 0) + 1
        return self.placed, self.review

    def _join_collinear(self):
        """Two placed dims on the same line, end to end on a shared witness
        line, become ONE string (Adolfo 2026-10-05: 9'-3 7/8" | 8'-4 1/8"
        through the grid, 8'-3" | 11'-9" to the grid). Kept apart if the
        joined string breaks a hard rule."""
        import copy
        self.notes_join = 0
        tol = 1.0 / 96
        changed = True
        while changed:
            changed = False
            for p in list(self.placed):
                for q in list(self.placed):
                    if q is p or q.fi != p.fi or abs(q.st_f - p.st_f) > 0.05 or abs(p.hi_f - q.lo_f) > tol:
                        continue
                    if p.s.feature is None or q.s.feature is not p.s.feature:
                        continue                    # one element only: don't pull a dim off its own element
                    s1, s2 = p.s, q.s
                    refs = list(s1.refs)
                    names = list(getattr(s1, "names", [r[2] for r in s1.refs]))
                    for r, nm in zip(s2.refs, getattr(s2, "names", [r[2] for r in s2.refs])):
                        off = self.m.offset(self.world(s2.gi, 0.0, r[0]), s1.gi)
                        if any(abs(off - x[0]) < tol for x in refs):
                            continue                # the shared witness line
                        refs.append((off, r[1], r[2]))
                        names.append(nm)
                    order = sorted(range(len(refs)), key=lambda k: refs[k][0])
                    sp2 = [self.m.station(self.world(s2.gi, x, 0.0), s1.gi) for x in s2.span]
                    ns = copy.copy(s1)
                    ns.refs = [refs[k] for k in order]
                    ns.names = [names[k] for k in order]
                    ns.span = (min(s1.span[0], min(sp2)), max(s1.span[1], max(sp2)))
                    ns.role = "locate" if "locate" in (s1.role, s2.role) else "check"
                    ns.label = s1.label + " + " + s2.label
                    ns.owners = set(s1.owners) | set(s2.owners)
                    ns.stack = None
                    st = p.cand[0]
                    self.placed.remove(p)
                    self.placed.remove(q)
                    pen, boxes = self.evaluate(ns, st)
                    if pen is None:
                        self.placed.extend([p, q])
                        continue
                    offs = [r[0] for r in ns.refs]
                    lo_o, hi_o = min(offs), max(offs)
                    sf, aa = self.to_fam(ns.gi, st, lo_o)
                    _, bb = self.to_fam(ns.gi, st, hi_o)
                    pj = Placed(ns, ns.fi, sf, min(aa, bb), max(aa, bb),
                                (self.world(ns.gi, st, lo_o), self.world(ns.gi, st, hi_o)), boxes,
                                min(p.cost, q.cost), (st, (0, "joined", 0)), self.text_plan(ns, st))
                    pj.side = self.elem_side(ns, sf)
                    self.placed.append(pj)
                    self.notes_join += 1
                    changed = True
                    break
                if changed:
                    break

    def _order_stacks(self):
        """Stacked rows read shortest nearest the element, longest furthest
        (Adolfo 2026-10-05) - for ANY rows standing side by side, whatever
        string they came from. Rows of one family whose measured ranges
        overlap, lying outside their spans on the same side and spaced no more
        than ~1.5 lanes apart, form a stack; their stations are handed out
        again by length. A stack whose new order breaks a hard rule keeps
        its old order."""
        c = self.c
        self.notes_order = 0
        info = []
        for pl in self.placed:
            s = pl.s
            a, b = self.to_fam(s.gi, s.span[0], 0.0)[0], self.to_fam(s.gi, s.span[1], 0.0)[0]
            lo, hi = min(a, b), max(a, b)
            if lo - 0.05 <= pl.st_f <= hi + 0.05:
                continue                        # inside its own span: no "nearest the element"
            side = 1 if pl.st_f < lo else -1    # +1: element lies toward higher stations
            info.append((pl, side, abs(pl.hi_f - pl.lo_f)))
        used = set()
        gap = 1.5 * c["LANE_STEP"]
        for pl, side, ln in info:
            if id(pl) in used:
                continue
            grp = [(pl, side, ln)]
            used.add(id(pl))
            grew = True
            while grew:
                grew = False
                for q in info:
                    if id(q[0]) in used or q[0].fi != pl.fi or q[1] != side:
                        continue
                    for m in grp:
                        same = q[0].s.feature is not None and q[0].s.feature is m[0].s.feature
                        if (abs(q[0].st_f - m[0].st_f) <= gap or (same and abs(q[0].st_f - m[0].st_f) <= 4 * gap)) and \
                                min(q[0].hi_f, m[0].hi_f) - max(q[0].lo_f, m[0].lo_f) > 0.1:
                            grp.append(q); used.add(id(q[0])); grew = True
                            break
            if len(grp) < 2:
                continue
            # stations nearest the element first (element toward +side)
            stations = sorted([m[0].st_f for m in grp], key=lambda st: -side * st)
            # shortest first; equal length (a chain and its overall): the
            # chain inside, the single overall dim outside
            by_len = sorted(grp, key=lambda m: (round(m[2] * 48), -len(m[0].s.refs)))
            if [id(m[0]) for m in by_len] == [id(m[0]) for m in sorted(grp, key=lambda m: -side * m[0].st_f)]:
                continue                        # already shortest-nearest
            olds = [m[0] for m in grp]
            for o in olds:
                self.placed.remove(o)
            new = []
            ok = True
            for (m, st_f) in zip(by_len, stations):
                s = m[0].s
                a0, _ = self.to_fam(s.gi, 0.0, 0.0)
                st = (st_f - a0) * self.fam_sign(s.gi)
                pen, boxes = self.evaluate(s, st)
                if pen is None:
                    ok = False
                    break
                offs = [r[0] for r in s.refs]
                lo_o, hi_o = min(offs), max(offs)
                sf, aa = self.to_fam(s.gi, st, lo_o)
                _, bb = self.to_fam(s.gi, st, hi_o)
                p2 = Placed(s, s.fi, sf, min(aa, bb), max(aa, bb),
                            (self.world(s.gi, st, lo_o), self.world(s.gi, st, hi_o)), boxes,
                            m[0].cost, (st, (0, "reordered", 0)), self.text_plan(s, st))
                p2.side = self.elem_side(s, sf)
                new.append(p2)
                self.placed.append(p2)          # later rows are checked against it
            if not ok:
                for p2 in new:
                    self.placed.remove(p2)
                # second try: keep the shortest row where it is and push each
                # longer row out past the one before it (one or two lanes)
                new = []
                ok = True
                prev_sf = None
                for m in by_len:
                    s = m[0].s
                    tries = [m[0].st_f] if prev_sf is None else \
                        ([m[0].st_f] if -side * (m[0].st_f - prev_sf) >= 0.9 * c["LANE_STEP"] else []) + \
                        [prev_sf - side * k * c["LANE_STEP"] for k in (1, 2)]
                    got = None
                    for st_f in tries:
                        a0, _ = self.to_fam(s.gi, 0.0, 0.0)
                        st = (st_f - a0) * self.fam_sign(s.gi)
                        pen, boxes = self.evaluate(s, st)
                        if pen is not None:
                            got = (st_f, st, boxes)
                            break
                    if got is None:
                        ok = False
                        break
                    st_f, st, boxes = got
                    offs = [r[0] for r in s.refs]
                    lo_o, hi_o = min(offs), max(offs)
                    sf, aa = self.to_fam(s.gi, st, lo_o)
                    _, bb = self.to_fam(s.gi, st, hi_o)
                    p2 = Placed(s, s.fi, sf, min(aa, bb), max(aa, bb),
                                (self.world(s.gi, st, lo_o), self.world(s.gi, st, hi_o)), boxes,
                                m[0].cost, (st, (0, "pushed out", 0)), self.text_plan(s, st))
                    p2.side = self.elem_side(s, sf)
                    new.append(p2)
                    self.placed.append(p2)
                    prev_sf = sf
                if not ok:
                    for p2 in new:
                        self.placed.remove(p2)
                    self.placed.extend(olds)
                    continue
            self.notes_order += 1

    def _unblock(self, still, max_total=None):
        out = []
        for s, why in still:
            offs = [r[0] for r in s.refs]
            lo, hi = min(offs), max(offs)
            s_lo, s_hi = s.span
            a = self.world(s.gi, s_lo - 6, lo); b = self.world(s.gi, s_hi + 6, hi)
            c_ = self.world(s.gi, s_lo - 6, hi); d = self.world(s.gi, s_hi + 6, lo)
            xs = [q[0] for q in (a, b, c_, d)]; ys = [q[1] for q in (a, b, c_, d)]
            rect = (min(xs), min(ys), max(xs), max(ys))
            near = [pl for pl in self.placed if not _rects_apart(rect, pl.rect, 0.0)]
            near = sorted(near, key=lambda pl: -pl.cost)[:8]
            groups = [(pl,) for pl in near]
            if self.c["UNBLOCK_PAIRS"]:
                groups += [(near[i], near[j]) for i in range(min(6, len(near))) for j in range(i + 1, min(6, len(near)))]
            best = None
            for grp in groups:
                if best is not None and len(grp) > 1 and best[0] < 2.0:
                    break                       # a cheap single lift already found
                for pl in grp:
                    self.placed.remove(pl)
                mine, _ = self.place_one(s, allow_last_resort=True)
                if mine is not None:
                    self.placed.append(mine)
                    theirs = []
                    for pl in grp:
                        t2, _ = self.place_one(pl.s, allow_last_resort=True)
                        if t2 is None:
                            break
                        theirs.append(t2)
                        self.placed.append(t2)
                    for t2 in theirs:
                        self.placed.remove(t2)
                    self.placed.remove(mine)
                    if len(theirs) == len(grp):
                        total = mine.cost + sum(t2.cost for t2 in theirs) - sum(pl.cost for pl in grp)
                        if (max_total is None or total <= max_total) and (best is None or total < best[0]):
                            best = (total, grp, mine, theirs)
                for pl in grp:
                    self.placed.append(pl)
            if best is None:
                out.append((s, why))
            else:
                _, grp, mine, theirs = best
                for pl in grp:
                    self.placed.remove(pl)
                self.placed.append(mine)
                self.placed.extend(theirs)
        return out

    # ---------------- create ----------------
    def create(self, doc, dim_type, z, pull_text=True):
        """Create the placed dims (caller owns the transaction). Returns
        (created dims, failures)."""
        made, failed = [], []
        for pl in self.placed:
            s = pl.s
            line = DB.Line.CreateBound(DB.XYZ(pl.seg[0][0], pl.seg[0][1], z),
                                       DB.XYZ(pl.seg[1][0], pl.seg[1][1], z))
            ra = DB.ReferenceArray()
            for off, ref, kind in sorted(s.refs, key=lambda r: r[0]):
                ra.Append(ref)
            try:
                d = doc.Create.NewDimension(self.view, line, ra, dim_type) if dim_type \
                    else doc.Create.NewDimension(self.view, line, ra)
            except Exception as ex:
                failed.append((s, str(ex))); continue
            if d is None:
                failed.append((s, "null")); continue
            made.append((d, pl))
        if pull_text:
            doc.Regenerate()
            self.text_errors = []
            for d, pl in made:
                try:
                    self.apply_text_plan(d, pl, z)
                except Exception as ex:
                    self.text_errors.append(str(ex))
        return [d for d, pl in made], failed

    def apply_text_plan(self, d, pl, z):
        """Put pulled-out text exactly where the layout assumed it."""
        if not pl.tplan or not any(it[3] for it in pl.tplan):
            return
        g, g0, u, n = self.frame(pl.s.gi)
        side = self.text_side(pl.s.gi)
        back = 0.5 * self.tsize                     # TextPosition is the text's base, not its centre
        segs = list(d.Segments) if d.NumberOfSegments > 1 else [d]
        used = set()
        for v, w, c, pulled, leader in pl.tplan:
            if not pulled:
                continue
            sg = None
            for i, cand in enumerate(segs):
                if i in used:
                    continue
                try:
                    if cand.Value is not None and abs(cand.Value - v) < 1.0 / 96:
                        sg = cand; used.add(i); break
                except Exception:
                    continue
            if sg is None:
                continue
            pos = sg.TextPosition
            target = DB.XYZ(c[0] - side * u[0] * back, c[1] - side * u[1] * back, pos.Z)
            # Revit only honours a leader once the text has been displaced: nudge, leader on, final spot
            sg.TextPosition = DB.XYZ(pos.X + n[0] * 0.05, pos.Y + n[1] * 0.05, pos.Z)
            try:
                if not d.HasLeader:
                    d.HasLeader = True
            except Exception:
                pass
            sg.TextPosition = target


def actual_overlaps(doc, view, dims, tsize_ft_plan):
    """Count pairs of created dims whose text boxes (from TextPosition and
    the estimated text size) overlap - the 'mess' metric."""
    boxes = []
    h = tsize_ft_plan * 1.4
    for d in dims:
        try:
            segs = list(d.Segments) if d.NumberOfSegments > 1 else [d]
            dirv = d.Curve.Direction
            u = (dirv.X, dirv.Y); n = (-u[1], u[0])
            nn = u if not (u[0] < -1e-6 or (abs(u[0]) < 1e-6 and u[1] < 0)) else (-u[0], -u[1])
            side = (-nn[1], nn[0])                  # text sits above the line, TextPosition at its base
            for sg in segs:
                tp = sg.TextPosition
                w = PL.text_width(sg.ValueString or "", tsize_ft_plan)
                c = (tp.X + side[0] * 0.5 * tsize_ft_plan, tp.Y + side[1] * 0.5 * tsize_ft_plan)
                boxes.append((d.Id, _rect_poly(c, u, n, w / 2.0, h / 2.0)))
        except Exception:
            continue
    count = 0
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if boxes[i][0] == boxes[j][0]:
                continue
            if _polys_overlap(boxes[i][1], boxes[j][1]):
                count += 1
    return count, len(boxes)
