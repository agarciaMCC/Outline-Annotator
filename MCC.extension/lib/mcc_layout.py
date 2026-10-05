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
    __slots__ = ("s", "fi", "st_f", "lo_f", "hi_f", "seg", "boxes", "cost", "cand", "rect", "tplan", "leaders")

    def __init__(self, s, fi, st_f, lo_f, hi_f, seg, boxes, cost, cand, tplan=None):
        self.s, self.fi, self.st_f, self.lo_f, self.hi_f = s, fi, st_f, lo_f, hi_f
        self.seg, self.boxes, self.cost, self.cand, self.tplan = seg, boxes, cost, cand, tplan
        self.leaders = [it[4] for it in (tplan or []) if it[4]]
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
        self.tsize = PL.text_size_ft(dim_type) * view.Scale     # ft on the plan
        self.notes = self._existing_annotations(view)            # text notes, tags, symbols already in the view
        self.placed = []
        self.review = []            # (string, reason)
        self.blocked = {}

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
            if o.eid in s.owners:
                continue
            if _rects_apart(myrect, o.rect, 0.0):
                continue
            line_hit = pi is not None and P.seg_hits_poly(pi, qi, o.poly)
            text_hit = any(_polys_overlap(bx, o.poly) for bx in boxes)
            if line_hit:
                if o.kind == "beam":
                    pen += c["W_BEAM"]
                else:
                    return None, "over a %s" % o.kind
            if text_hit:
                pen += c["W_TEXT_OBST"]         # text over a member/opening: avoid, don't forbid
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
        seen_st = set()
        for pl in self.placed:
            if pl.fi != s.fi:
                continue
            st = (pl.st_f - a0) * sgn
            key = round(st * 16)
            if key in seen_st or abs(st - prefer) > c["COLLINEAR_REACH"]:
                continue
            seen_st.add(key)
            outside = max(0.0, s_lo - st, st - s_hi)
            if home:
                side_pen = c["W_SIDE"] if (st - prefer) * home < -0.5 else 0.0
                slide = abs(st - prefer) * c["W_SLIDE"]
            else:
                side_pen = c["W_INSIDE"] if outside == 0.0 else 0.0
                slide = 0.0
            out.append((c["W_COLLINEAR"] + side_pen + slide + outside * c["W_OUTSIDE"], st, (0, "collinear", 0)))
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
        return pl, None

    # ---------------- driver ----------------
    def run(self):
        def _key(s):
            stk = getattr(s, "stack", None)
            return (0 if s.role == "locate" else 1,
                    PRIORITY.get(s.feature.kind, 9) if s.feature else 9,
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
        self.review = still
        for s, why in still:
            self.blocked[why] = self.blocked.get(why, 0) + 1
        return self.placed, self.review

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
