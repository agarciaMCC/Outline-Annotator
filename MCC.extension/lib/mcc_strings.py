# -*- coding: utf-8 -*-
"""Dim Soffit v2, stage 2 - STRING PLAN.

Turns Features into Strings (one String = one Revit dimension to be):
ordered witness references measured across one grid family, an extent
along the string, a preferred station and side, a role ('locate' or
'check'), and the feature it belongs to. Rules: claude/dimensioning-rules.md.

Nothing is drawn here. plan_view() returns the strings plus a coverage
report graded the same way mcc_coverage grades real dims, so the plan can
be checked against the hand sheets before any layout code runs."""
import math
from pyrevit import DB
import mcc_plan as P
import mcc_features as F
from mcc_place import Intent, dedupe

CFG = {
    "LOC_MAX": 30.0,        # ft; field tape length (Adolfo 2026-10-05, was 20) - anchors farther are a last resort
    "MAX_DIST": 30.0,       # ft; nothing beyond the tape (was 40)
    "ON_GRID_TOL": 1.0 / 192,
    "FLUSH_TOL": 1.0 / 48,
    "SAME_OFF_TOL": 1.0 / 96,
    "CORNER_IN": 2.0,       # ft; run dims sit this far in from the corner
    "TURN_BOTH": 40.0,      # ft; slab edges / CJs longer than this get a dim at each end (Adolfo 2026-10-05:
                            # at 20 ft the two end dims sat 8-18 ft apart and read as doubles; was 20)
    "BEAM_BOTH": 20.0,      # ft; beams longer than this get a width dim at each end - when both ends are in the
                            # view's crop (Adolfo 2026-10-06); no halfway dim any more (not seen on any past sheet)
    "OPEN_OFFSET_IN": 0.25, # paper inches; opening strings sit this far outside (3/16" tried in runs 85-86, net worse)
    "BEAM_END_GAP_IN": 0.25, # paper inches past a beam end for its width dim (Adolfo pulled them in to ~1/4")
    "CLUTTER_R_IN": 0.75,   # paper inches; a small opening/notch with 2+ other small ones this close -> enlarged plan
                            # (8 ft at 1:128, 6 ft at 1:96 - "hard to tell what dimension goes where", Adolfo L7 round 1)
    "RUN_BOTH": 6.0,        # ft; a slab edge longer than this is located at both its corners
    "RUN_BOTH_ALWAYS": 30.0, # ft; ... and past the tape, at both corners even where a corner has no open margin
                            # (Adolfo 2026-10-07, L7: "a dim at each end" of the 39 ft edge above AA; was TURN_BOTH 40)
    "SLOT_MAX": 1.0,        # ft; an opening narrower than this is a slot: clutter with just 1 neighbour, core/shaft or not
    "LANE_STEP_IN": 0.1875, # paper inches between stacked rows (hand sheets: 3/16" at every scale)
    "CONSISTENCY": 1.0,     # switch to the neighbours' grid only if no farther (Adolfo
                            # 2026-10-05: always dimension from the closest gridline; was 1.25)
    "FAR_EDGE_MIN": 6.0,    # ft; one-sided openings wider than this also get
                            # anchor -> far edge (smaller: the size dim is enough)
    # stacked dims (Adolfo 2026-10-05): every edge of a chained string also gets
    # its own dim from the chain's anchor; the chain stays as a check
    # soffit elements only (Adolfo 2026-10-05): dims go TO slab edges, beams,
    # openings, CJs - never to walls / curbs / columns (other plans show
    # those). A wall face may be the anchor only when no grid is within LOC_MAX.
    "WALL_ANCHOR_IF_NO_GRID": True,
    # a shaft the slab outline wraps around (not a hole in the slab): a slab
    # edge facing a wall face across open space gets an overall-size dim
    "SMALL_OPEN": 4.0,      # ft; a smaller opening gets only its near edge off the grid, plus its size
    "MINOR_EDGE": 0.0,      # ft; an opening edge shorter than this, off the opening's own grid set, is a chamfer/jog -
                            # OFF (0): Adolfo added the 1'-4" jog's 3'-11 1/8" off B three rounds running (2026-10-06)
    "CORE_WALL_NEAR": 1.0,  # ft; a core/shaft opening with a core wall face this close is dimensioned off that wall
    "CJ_MID_TOL": 1.5,      # ft; a CJ whose distances to the two grids differ by less is dimensioned from both
    "CJ_PAIR": 4.0,         # ft; parallel CJs this close get dims at one shared end + a spacing dim
    "FRAMED_CROSS": 6.0,    # ft; a framed beam end's width crosses the other beam only if open slab is this near
    "CORNER_MIN_EDGE": 5.0, # ft; a non-90 corner is located along its straight edge only when that edge is this long
    "SHAFT_MAX": 15.0,      # ft; widest such pocket
    "SHAFT_MIN_EDGE": 2.0,  # ft; shorter slab edges are jogs, not shaft sides
    "STACK": True,
    # "R.O." on the overall size of a shaft / core opening only - never on dims off a grid (Adolfo 2026-10-06;
    # past sheets: ~310 "(R.O.)" on 2022-26 soffit plans). Off -> no suffix.
    "RO_SUFFIX": "R.O.",
    "RO_MIN": 4.0,          # ft; R.O. only on openings at least this big BOTH ways (Adolfo 2026-10-06: stair /
                            # elevator openings; the 3'-4" / 8" ones he had marked were an oversight)
    "STACK_KINDS": ("opening", "bump", "notch"),   # beams: width + one anchor (Adolfo 2026-10-05)
}


class String(Intent):
    """An Intent (so mcc_place.dedupe and the layout can consume it) plus
    plan metadata."""
    def __init__(self, fi, gi, refs, span, label, feature, role="locate",
                 names=None, **kw):
        Intent.__init__(self, fi, gi, refs, span, label,
                        owners=tuple(feature.owners) if feature else (), **kw)
        self.feature = feature
        self.role = role
        self.names = names or [k for _, _, k in refs]   # human labels per ref
        self.alt = None
        self.stack = None       # (group key, rank, size) for stacked dims, rank 0 = shortest

    def values(self):
        offs = [r[0] for r in self.refs]
        return [b - a for a, b in zip(offs, offs[1:])]


def ftin(v):
    if v is None:
        return "?"
    neg = v < 0
    v = abs(v)
    ft = int(v + 1e-9)
    inch = (v - ft) * 12.0
    whole = int(inch + 1e-9)
    frac = inch - whole
    sixteenths = int(round(frac * 16))
    if sixteenths == 16:
        whole += 1; sixteenths = 0
    if whole == 12:
        ft += 1; whole = 0
    s = "%d'-%d" % (ft, whole)
    if sixteenths:
        g = 16
        n = sixteenths
        while n % 2 == 0:
            n //= 2; g //= 2
        s += " %d/%d" % (n, g)
    return ("-" if neg else "") + s + '"'


class Planner(object):
    def __init__(self, model, features, cfg=None):
        self.m = model
        self.fs = features
        self.c = dict(CFG)
        if cfg:
            self.c.update(cfg)
        # paper inches -> plan feet at this view's scale
        sc = float(getattr(getattr(model, "view", None), "Scale", 96) or 96)
        self.c.setdefault("OPEN_OFFSET", self.c["OPEN_OFFSET_IN"] * sc / 12.0)
        self.c.setdefault("CLUTTER_R", self.c["CLUTTER_R_IN"] * sc / 12.0)
        self.c.setdefault("BEAM_END_GAP", self.c["BEAM_END_GAP_IN"] * sc / 12.0)
        self.c.setdefault("LANE_STEP", self.c["LANE_STEP_IN"] * sc / 12.0)
        self.notes = {}
        self.located_by = {}        # id(edge) -> reason (no string needed)
        self.strings = []
        self.gname = dict((gi, g.Name) for gi, (g, g0, u, n) in enumerate(model.grids))

    def note(self, k):
        self.notes[k] = self.notes.get(k, 0) + 1

    # ---------------- geometry helpers ----------------
    def gref(self, gi):
        return (0.0, DB.Reference(self.m.grid(gi)[0]), "grid")

    def frame(self, face):
        """(fi, gi, off, s_lo, s_hi): family parallel to the face, nearest
        grid of it, offset, extent along the grid."""
        fi = self.m.family_parallel(face.d)
        if fi is None:
            return None
        ng = self.m.nearest_grid(face.mid(), fi, self.c["MAX_DIST"])
        if ng is None:
            return None
        gi, off = ng
        s0, s1 = self.m.station(face.p0, gi), self.m.station(face.p1, gi)
        return fi, gi, off, min(s0, s1), max(s0, s1)

    def spans_overlap(self, a0, a1, b0, b1, slack=0.0):
        return a0 - slack <= b1 and b0 - slack <= a1

    def flush(self, face, members, share=0.0, line=False):
        """The member whose face lies on this face (within FLUSH_TOL) and
        overlaps it - when share is given, by at least that share of the
        face's length, or (line) with a member face at least as long (the
        edge continues a wall line: L3N's 9 ft edge off a 70 ft wall)."""
        for mbr in members:
            for f in mbr.sides or mbr.faces:
                if not P.parallel(f.d, face.d):
                    continue
                n = (-face.d[1], face.d[0])
                gap = (f.mid()[0] - face.p0[0]) * n[0] + (f.mid()[1] - face.p0[1]) * n[1]
                if abs(gap) > self.c["FLUSH_TOL"]:
                    continue
                b0 = (f.p0[0] - face.p0[0]) * face.d[0] + (f.p0[1] - face.p0[1]) * face.d[1]
                b1 = (f.p1[0] - face.p0[0]) * face.d[0] + (f.p1[1] - face.p0[1]) * face.d[1]
                if self.spans_overlap(0.0, face.length, min(b0, b1), max(b0, b1)):
                    if share and min(face.length, max(b0, b1)) - max(0.0, min(b0, b1)) < share * face.length \
                            and not (line and abs(b1 - b0) >= face.length):
                        continue        # a stub at its end; a longer wall line it continues still counts
                    return mbr
        return None

    def anchor(self, fi, gi, off, side, s_lo, s_hi, cap=None, walls=True, force_walls=False):
        """Nearest locating reference on one side (+1 higher offsets, -1
        lower) within cap: a grid of family fi or a facing parallel wall
        face overlapping [s_lo, s_hi]. -> (offset, ref, kind, name)."""
        c = self.c
        cap = c["LOC_MAX"] if cap is None else cap
        best = None
        grid_near = False
        for gj in self.m.families[fi]:
            o = self.m.offset(self.m.grid(gj)[1], gi)
            if abs(o - off) <= c["LOC_MAX"]:
                grid_near = True                 # either side
            if (o - off) * side < -c["ON_GRID_TOL"] or abs(o - off) > cap:
                continue
            if best is None or abs(o - off) < abs(best[0] - off):
                best = (o, DB.Reference(self.m.grid(gj)[0]), "grid", self.gname[gj])
        if walls and c["WALL_ANCHOR_IF_NO_GRID"] and grid_near and not force_walls:
            walls = False
        if walls:
            u = self.m.grid(gi)[2]
            for w in self.m.walls:
                for f in w.sides:
                    if not P.parallel(f.d, u):
                        continue
                    o = self.m.offset(f.mid(), gi)
                    if (o - off) * side < c["FLUSH_TOL"] or abs(o - off) > cap:
                        continue
                    pr = [self.m.station(q, gi) for q in (w.poly or [f.p0, f.p1])]
                    if not self.spans_overlap(s_lo, s_hi, min(pr), max(pr), -0.25):
                        continue
                    if best is None or abs(o - off) < abs(best[0] - off) - c["FLUSH_TOL"]:
                        best = (o, f.ref, "wall face", "wall")
        return best

    def end_parts(self, s_lo, s_hi, both=None):
        """'A dimension at each end for ease of reading' (Adolfo 2026-10-05):
        longer than TURN_BOTH (or 'both') -> one part per end, each with its
        own half span (so dedupe doesn't fold the two into one, as it used to
        for runs). -> [(span, prefer, outward)]; outward points at that end."""
        ci = self.c["CORNER_IN"]
        if s_hi - s_lo <= (self.c["TURN_BOTH"] if both is None else both):
            return [((s_lo, s_hi), None, None)]
        mid = (s_lo + s_hi) / 2.0
        g = 1.5
        return [((s_lo, mid - g), s_lo + ci, -1), ((mid + g, s_hi), s_hi - ci, 1)]

    def add(self, fi, gi, refs, span, label, feature, role="locate", **kw):
        refs = sorted(refs, key=lambda r: r[0])
        names = [r[3] if len(r) > 3 else r[2] for r in refs]
        refs3 = [(r[0], r[1], r[2]) for r in refs]
        if len(refs3) < 2 or refs3[-1][0] - refs3[0][0] < 1.0 / 96:
            self.note("empty string dropped")
            return None
        s = String(fi, gi, refs3, span, label, feature, role=role, names=names, **kw)
        self.strings.append(s)
        return s

    # ---------------- per feature ----------------
    def do_run(self, f):
        e = f.edges[0]
        fr = self.frame(e)
        if fr is None:
            self.note("run: no grid family / grid")
            return
        fi, gi, off, s_lo, s_hi = fr
        if abs(off) < self.c["ON_GRID_TOL"]:
            self.located_by[id(e)] = "on grid"; return
        # the member must run along most of the edge: a wall or column that
        # only touches its end doesn't locate it (L7: the 39 ft top edge above
        # AA, 0.6 ft of wall at its east end; the 5'-1" edges off 7 either side
        # of a 6.7 ft column - Adolfo drew both by hand in both rounds)
        if self.flush(e, self.m.walls, share=0.5, line=True):
            self.located_by[id(e)] = "wall face"; return
        if self.flush(e, self.m.columns, share=0.5):
            # slab cut around a column: the edge IS the column face - the
            # column is dimensioned on other plans (Adolfo 2026-10-05)
            self.located_by[id(e)] = "column face"; self.note("slab edge on a column face (skipped)"); return
        if self.flush(e, self.m.beams):
            self.located_by[id(e)] = "beam face"; return
        cands = [a for a in (self.anchor(fi, gi, off, -1, s_lo, s_hi),
                             self.anchor(fi, gi, off, +1, s_lo, s_hi)) if a]
        if not cands:
            cands = [a for a in (self.anchor(fi, gi, off, -1, s_lo, s_hi, cap=self.c["MAX_DIST"], walls=False),
                                 self.anchor(fi, gi, off, +1, s_lo, s_hi, cap=self.c["MAX_DIST"], walls=False)) if a]
            if cands:
                self.note("run: anchor beyond LOC_MAX")
        if not cands:
            self.note("run: no anchor")
            return
        anc = min(cands, key=lambda a: abs(a[0] - off))
        refs = [anc, (off, e.ref, "slab edge", "edge")]
        free = (self.free_end(gi, off, s_lo, -1), self.free_end(gi, off, s_hi, +1))
        # "dimensions where the slab edge turns corners - to the outer corners,
        # outside the footprint where possible" (Adolfo, L7 round 1): a run is
        # located at BOTH corners once it is longer than RUN_BOTH (the 20-40 ft
        # "doubles" he deleted on L3N were the two end dims landing mid-edge -
        # the reversed-outward bug, fixed above)
        parts = self.end_parts(s_lo, s_hi, both=self.c["RUN_BOTH"])
        if len(parts) == 2 and (s_hi - s_lo) <= self.c["RUN_BOTH_ALWAYS"]:
            # "...outside the footprint where possible": below TURN_BOTH the
            # second corner dim only where the margin past that corner is open
            # (L3N run 91: both-corner dims inside the slab crowded the
            # neighbours 1-6" off Adolfo's spots)
            keep = [k for k in (0, 1) if free[k]]
            if len(keep) == 1:
                parts = [parts[keep[0]]]
                parts_k = keep
            elif not keep:
                parts = [((s_lo, s_hi), None, None)]
                parts_k = [0]
            else:
                parts_k = [0, 1]
        else:
            parts_k = list(range(len(parts)))
        gap = self.c["BEAM_END_GAP"]
        for k, (span, _, _) in zip(parts_k, parts):
            # outward points AT this end (-1 low, +1 high) - it was reversed,
            # so the two end dims of a 175 ft edge met in its middle (L7 round
            # 1, run#17 / #18); and a run dim sits just PAST its corner when the
            # margin there is open (all 9 of Adolfo's run moves on L7), else
            # CORNER_IN inside the edge
            low = (k == 0)
            out = -1 if low else 1
            fr_ = free[0] if low else free[1]
            if fr_:
                pref = (s_lo - gap) if low else (s_hi + gap)
            else:
                pref = (s_lo + self.c["CORNER_IN"]) if low else (s_hi - self.c["CORNER_IN"])
            s = self.add(fi, gi, refs, span, "run -> " + anc[3], f, prefer=pref, outward=out)
            if s is not None:
                # the dim can sit in the margin past this end of the edge
                # (hand sheets run a column of these beside the slab)
                s.free = fr_

    def free_end(self, gi, off, st, side):
        """Is the strip just past this end of an edge (2..6 ft along, on
        both sides of the edge line) clear of slab and members - i.e. open
        margin beside the slab?"""
        m = self.m
        g, g0, u, n = m.grids[gi]
        for d in (2.0, 4.0, 6.0):
            for k in (-1.0, 1.0):
                x = g0[0] + u[0] * (st + side * d) + n[0] * (off + k * 1.0)
                y = g0[1] + u[1] * (st + side * d) + n[1] * (off + k * 1.0)
                for sl in m.slabs:
                    if P.point_in_poly(x, y, sl.outer):
                        return False
                if m.member_at(x, y, cats=("column", "wall", "beam")) is not None:
                    return False
        return True

    def notch_side(self, gi, st, off):
        """Which side (+1 / -1 along gi) of station st is open at offset off
        (outside every slab) while the other is slab - the notch beside a
        step face. 0 when both or neither are."""
        m = self.m
        g, g0, u, n = m.grids[gi]
        open_ = []
        for side in (-1, 1):
            x = g0[0] + u[0] * (st + side * 1.0) + n[0] * off
            y = g0[1] + u[1] * (st + side * 1.0) + n[1] * off
            open_.append(not any(P.point_in_poly(x, y, sl.outer) for sl in m.slabs))
        if open_[0] == open_[1]:
            return 0
        return -1 if open_[0] else 1

    def on_column(self, f, edges=None):
        """Any edge of the feature lying on a column face -> the bump/notch/step
        is the slab cut around a column, not a soffit shape: skip it. For a
        STEP only the step face counts (Adolfo 2026-10-06: the 3'-11 3/4" jog
        west of beam#232 is a non-90 perimeter corner, its face is wanted in
        the field - the run beside it on the beam/column is not the point)."""
        hit = [e for e in (edges or f.edges) if self.flush(e, self.m.columns)]
        # a real cut around a column has two or three faces on the column; one
        # face touching a column is a perimeter corner that happens to meet it
        # (the notch at beam#232's end: Adolfo wants its 12'-1 3/8" face)
        if edges is None and len(hit) < 2:
            hit = []
        if hit:
            for e in f.edges:
                self.located_by[id(e)] = "column face"
            self.note("%s around a column (skipped)" % f.kind)
        return bool(hit)

    def do_bump(self, f):
        if self.on_column(f):
            return
        a, b, cdg = f.edges            # legs a, c ; top b
        # string across the bump (family parallel to the legs): anchor | a | c | anchor
        fr = self.frame(a)
        if fr is not None:
            fi, gi, oa, _, _ = fr
            oc = self.m.offset(cdg.mid(), gi)
            s_lo, s_hi = sorted([self.m.station(a.p0, gi), self.m.station(a.p1, gi)])
            lo, hi = min(oa, oc), max(oa, oc)
            al = self.anchor(fi, gi, lo, -1, s_lo, s_hi)
            ah = self.anchor(fi, gi, hi, +1, s_lo, s_hi)
            refs = [(oa, a.ref, "slab edge", "leg"), (oc, cdg.ref, "slab edge", "leg")]
            if al: refs.insert(0, al)
            if ah: refs.append(ah)
            self.add(fi, gi, refs, (s_lo, s_hi), "%s across" % f.kind, f,
                     prefer=(s_lo + s_hi) / 2.0,
                     role="locate" if (al or ah) else "check")
        # top face located in the other direction
        fr = self.frame(b)
        if fr is not None:
            fi, gi, ob, s_lo, s_hi = fr
            if abs(ob) >= self.c["ON_GRID_TOL"]:
                cands = [x for x in (self.anchor(fi, gi, ob, -1, s_lo, s_hi),
                                     self.anchor(fi, gi, ob, +1, s_lo, s_hi)) if x]
                if cands:
                    anc = min(cands, key=lambda x: abs(x[0] - ob))
                    self.add(fi, gi, [anc, (ob, b.ref, "slab edge", "top")], (s_lo, s_hi),
                             "%s top -> %s" % (f.kind, anc[3]), f, prefer=(s_lo + s_hi) / 2.0)
                else:
                    self.note("bump top: no anchor")

    do_notch = do_bump

    def do_step(self, f):
        if self.on_column(f, edges=[f.edges[0]]):
            return
        s = f.edges[0]
        a, b = f.meta["run_before"], f.meta["run_after"]
        # locate the step face along the runs
        fr = self.frame(s)
        if fr is not None:
            fi, gi, os_, s_lo, s_hi = fr
            if abs(os_) >= self.c["ON_GRID_TOL"]:
                cands = [x for x in (self.anchor(fi, gi, os_, -1, s_lo, s_hi),
                                     self.anchor(fi, gi, os_, +1, s_lo, s_hi)) if x]
                if cands:
                    anc = min(cands, key=lambda x: abs(x[0] - os_))
                    self.add(fi, gi, [anc, (os_, s.ref, "slab edge", "step")], (s_lo, s_hi),
                             "step -> " + anc[3], f, prefer=(s_lo + s_hi) / 2.0)
                else:
                    self.note("step: no anchor")
            else:
                self.located_by[id(s)] = "on grid"
        # jog check: run a face | run b face - not for the gap beside a beam
        # in a wall line (a face on the beam side AND the step edge on a wall
        # face): "stop dimensioning the openings off of beam faces" (Adolfo
        # 2026-10-06, the 1'-9 3/8" / 6 1/8" at the L3N core's bottom beam).
        # A real step in the slab that happens to end at a beam keeps its
        # check (he kept the 3'-11 3/4" NW and the 8" at the CJ corner)
        fr = self.frame(a)
        if fr is not None:
            fi, gi, oa, _, _ = fr
            ob = self.m.offset(b.mid(), gi)
            if any(self.flush(e, self.m.beams) for e in (a, b)) and self.flush(s, self.m.walls):
                self.note("jog check: gap beside a beam in a wall line (skipped)")
            elif abs(oa - ob) > self.c["SAME_OFF_TOL"]:
                # "dimension at every turn": when a grid runs between the two
                # run faces, both are located off it right at the step -
                # face | grid | face, with the jog check one row outside
                # (Adolfo's L7 round 1: 3'-4 1/2" | 5 | 1'-7 1/2" at all 10
                # steps of the west sawtooth)
                sj = self.m.station(s.mid(), gi)
                # on the open (notch) side of the step face, the jog check one
                # row further out (Adolfo moved 6 of the 10 L7 pairs from over
                # the slab tooth into the notch, rounds 1 and 2)
                notch = self.notch_side(gi, sj, (oa + ob) / 2.0)
                kw = {"prefer": sj}
                if notch:
                    pref = sj + notch * self.c["OPEN_OFFSET"]
                    kw = {"prefer": pref, "outward": notch,
                          "span": (pref, pref + 1.0) if notch > 0 else (pref - 1.0, pref)}
                span = kw.pop("span", (sj - 2.0, sj + 2.0))
                key = (id(f), "step")
                gb = self.m.grid_between(a.mid(), b.mid(), fi)
                if gb is not None:
                    t = self.add(fi, gi, [(oa, a.ref, "slab edge", "edge"), self.gref(gb) + (self.gname[gb],),
                                          (ob, b.ref, "slab edge", "edge")],
                                 span, "step faces|%s|faces" % self.gname[gb], f, **kw)
                    if t is not None and notch:
                        t.stack = (key, 0, 2)
                    self.note("step: faces located off the grid between them")
                t = self.add(fi, gi, [(oa, a.ref, "slab edge", "edge"), (ob, b.ref, "slab edge", "edge")],
                             span, "jog check", f, role="check", **kw)
                if t is not None and notch and gb is not None:
                    t.stack = (key, 1, 2)

    def do_opening(self, f):
        kind = f.sub
        cx, cy = f.meta["centroid"]
        # an angled opening is dimensioned off the grid set its edges follow
        # (Adolfo 2026-10-05); short edges of the other set (chamfers, jogs)
        # get straight-grid dims only when no aligned grid is within the tape
        fam_len = {}
        for e in f.edges:
            fj = self.m.family_parallel(e.d)
            if fj is not None:
                fam_len[fj] = fam_len.get(fj, 0.0) + e.length
        dom = max(fam_len.items(), key=lambda kv: kv[1])[0] if fam_len else None
        # its own grid set = the dominant family and the one square to it; a
        # short edge in another family (a chamfer on an angled opening) gets
        # no straight-grid dim when one of its own grids is within the tape
        own = set()
        if dom is not None:
            du = self.m.grids[self.m.families[dom][0]][2]
            for fj in range(len(self.m.families)):
                v = self.m.grids[self.m.families[fj][0]][2]
                dot = abs(du[0] * v[0] + du[1] * v[1])
                if dot > 0.995 or dot < 0.1:
                    own.add(fj)
        # ... but only while the DOMINANT family itself has a grid in the
        # vicinity: the angled shaft by the L3N core (shaft#114) follows a
        # direction with no gridline within 60 ft, and Adolfo located its
        # straight jog off grids 7 and B (2026-10-06)
        dom_near = dom is not None and self.m.nearest_grid((cx, cy), dom, self.c["LOC_MAX"]) is not None
        for fi in range(len(self.m.families)):
            par = [e for e in f.edges if self.m.family_parallel(e.d) == fi]
            if fi not in own and dom_near:
                short = [e for e in par if e.length < self.c["MINOR_EDGE"]]
                if short:
                    self.note("opening: short edges off its grid set skipped (aligned grid near)")
                    for e in short:
                        self.located_by[id(e)] = "minor edge of an angled opening"
                par = [e for e in par if e.length >= self.c["MINOR_EDGE"]]
            if not par:
                continue
            keep_chain = False
            ng = self.m.nearest_grid((cx, cy), fi, self.c["MAX_DIST"])
            if ng is None:
                # no grid of this direction within the tape: an edge lying on
                # a wall makes the wall the anchor (Adolfo 2026-10-06, the
                # angled shaft by the L3N core: edge | 3'-9 3/4" | edge |
                # 4'-10 1/4" | core wall) - a far grid of the family only
                # lends its frame; anchor() still caps grids at LOC_MAX
                if any(self.flush(e, self.m.walls) for e in par):
                    ng = self.m.nearest_grid((cx, cy), fi)
                    self.note("opening: no grid near, located off the wall it touches")
                    keep_chain = True
            if ng is None:
                self.note("opening: too far from any grid")
                continue
            gi, _ = ng
            offs = {}
            for e in par:
                off = self.m.offset(e.mid(), gi)
                key = round(off * 96)
                if key not in offs or e.length > offs[key][1].length:
                    offs[key] = (off, e)
            faces = sorted(offs.values(), key=lambda t: t[0])
            sts = [self.m.station(p, gi) for e in par for p in (e.p0, e.p1)]
            s_lo, s_hi = min(sts), max(sts)
            # which side does the other direction's string go? ours goes away
            away = 1
            other = None
            for fj in range(len(self.m.families)):
                if fj == fi:
                    continue
                ngj = self.m.nearest_grid((cx, cy), fj, self.c["MAX_DIST"])
                if ngj and (other is None or abs(ngj[1]) < abs(other[1])):
                    other = ngj
            if other is not None:
                st_g = self.m.station(self.m.grid(other[0])[1], gi)
                away = 1 if st_g < self.m.station((cx, cy), gi) else -1
            if kind in ("core", "shaft"):
                away = 0 if away > 0 else 0        # both sides equal; layout decides
                away = 0
            pref = (s_hi + self.c["OPEN_OFFSET"]) if away >= 0 else (s_lo - self.c["OPEN_OFFSET"])
            span = (pref, pref + 1.0) if away >= 0 else (pref - 1.0, pref)
            if away == 0:
                # home station in the middle of the opening; lanes go either way
                pref = (s_lo + s_hi) / 2.0
                span = (s_lo, s_hi)
            alt_pref = (s_lo - self.c["OPEN_OFFSET"]) if away > 0 else (s_hi + self.c["OPEN_OFFSET"])
            alt = ((alt_pref - 1.0, alt_pref) if away > 0 else (alt_pref, alt_pref + 1.0), alt_pref, -away)
            in_wall = any(P.point_in_poly(cx, cy, P.inflate(w.poly, 1.0)) for w in self.m.walls if w.poly)
            if in_wall and kind != "void" and (faces[-1][0] - faces[0][0]) < self.c["SMALL_OPEN"]:
                # a small hole sitting in a wall line (the 9" x 5" "shaft" in
                # the L3N core wall, 2026-10-06) is a hole in the wall, not the
                # slab - the core wall plans cover it, like a void in a wall
                for off, e in faces:
                    self.located_by[id(e)] = "opening in a wall"
                self.note("small opening in a wall line (skipped)")
                continue
            if kind == "void":
                # a void in a wall line is covered by the core wall / vertical
                # plans (Adolfo 2026-10-05) - skip it here
                if in_wall:
                    for off, e in faces:
                        self.located_by[id(e)] = "void in a wall"
                    self.note("void in a wall line (skipped)")
                    continue
                # each edge locally from its nearest anchor
                for off, e in faces:
                    if self.flush(e, self.m.walls):
                        self.located_by[id(e)] = "wall face"; continue
                    if self.flush(e, self.m.columns):
                        self.located_by[id(e)] = "column face"; continue
                    t0, t1 = sorted([self.m.station(e.p0, gi), self.m.station(e.p1, gi)])
                    cands = [x for x in (self.anchor(fi, gi, off, -1, t0, t1),
                                         self.anchor(fi, gi, off, +1, t0, t1)) if x]
                    if not cands:
                        self.note("void edge: no anchor"); continue
                    anc = min(cands, key=lambda x: abs(x[0] - off))
                    if abs(anc[0] - off) < self.c["ON_GRID_TOL"]:
                        self.located_by[id(e)] = "on grid"; continue
                    self.add(fi, gi, [anc, (off, e.ref, "opening edge", "edge")], (t0, t1),
                             "void edge -> " + anc[3], f, prefer=(t0 + t1) / 2.0)
                continue
            lo, hi = faces[0][0], faces[-1][0]
            # an outer edge lying on a wall face IS the anchor on that side
            # (elevator openings come off the wall face)
            lo_wall = self.flush(faces[0][1], self.m.walls) is not None
            hi_wall = self.flush(faces[-1][1], self.m.walls) is not None
            # grids first, even inside a core: "there's grids nearby, no need
            # to dimension off the walls" (Adolfo 2026-10-06, the L3N shaft he
            # drew edge | 8'-4 1/8" | BB | 9'-3 7/8" | edge where the tool had
            # 7'-0 7/8" / 24'-8 7/8" off the core wall). A wall face only when
            # no grid of the family is within LOC_MAX (anchor's own rule); the
            # earlier "core/shaft off the core wall even with a grid near"
            # (card 14, 2026-10-05) now only holds for an opening hugging a
            # core wall (a face within CORE_WALL_NEAR): the 1'-5" x 3'-3" hole
            # in the L3N core he dims 7" / 5" off the walls, not 15'-0" off CC
            fw = False
            if kind in ("core", "shaft"):
                for off_, sd in ((lo, -1), (hi, +1)):
                    a_ = self.anchor(fi, gi, off_, sd, s_lo, s_hi, cap=self.c["CORE_WALL_NEAR"], force_walls=True)
                    if a_ and a_[2] == "wall face":
                        fw = True
            al = None if lo_wall else self.anchor(fi, gi, lo, -1, s_lo, s_hi, force_walls=fw)
            ah = None if hi_wall else self.anchor(fi, gi, hi, +1, s_lo, s_hi, force_walls=fw)
            if lo_wall:
                al = (lo, faces[0][1].ref, "opening edge", "edge@wall")
            if hi_wall:
                ah = (hi, faces[-1][1].ref, "opening edge", "edge@wall")
            # a gridline running THROUGH the opening, closer to its edges than
            # any outside anchor, is the one to dimension from (Adolfo
            # 2026-10-05: always the closest gridline) -> edges | grid | edges
            mid_grid = None
            if not (lo_wall and hi_wall):
                # (one face on a wall doesn't rule the through-grid out: the L7
                # core shafts read edge@wall | ... | 7 | edge, like the L3N
                # pocket - round 1 of L7)
                tol = self.c["ON_GRID_TOL"]
                gaps = ([abs(lo - al[0])] if (al and not lo_wall) else []) + ([abs(ah[0] - hi)] if (ah and not hi_wall) else [])
                out_gap = min(gaps) if gaps else 1e9
                for gj in self.m.families[fi]:
                    o = self.m.offset(self.m.grid(gj)[1], gi)
                    if lo + tol < o < hi - tol:
                        d = min(o - lo, hi - o)
                        if d < out_gap and (mid_grid is None or d < mid_grid[0]):
                            mid_grid = (d, (o, DB.Reference(self.m.grid(gj)[0]), "grid", self.gname[gj]))
                if mid_grid is not None:
                    if not lo_wall: al = None
                    if not hi_wall: ah = None
            if mid_grid is None and al is None and ah is None:
                al = self.anchor(fi, gi, lo, -1, s_lo, s_hi, cap=self.c["MAX_DIST"], walls=False)
                ah = self.anchor(fi, gi, hi, +1, s_lo, s_hi, cap=self.c["MAX_DIST"], walls=False)
                if al and ah:
                    if abs(al[0] - lo) <= abs(ah[0] - hi): ah = None
                    else: al = None
                if al or ah:
                    self.note("opening: anchor beyond LOC_MAX")
            if al and ah and dom is not None and fi not in own and mid_grid is None:
                # an angled opening's straight-grid string: the near leg only -
                # the far leg (12'-8 1/2" at the L3N angled shaft) was deleted
                # three rounds running (Adolfo 2026-10-06: "correct")
                if abs(al[0] - lo) <= abs(ah[0] - hi): ah = None
                else: al = None
                self.note("angled opening: far leg off a straight grid dropped")
            refs = []
            for off, e in faces:
                if (off == lo and lo_wall) or (off == hi and hi_wall):
                    self.located_by[id(e)] = "wall face"
                    continue                     # already in as the anchor
                if self.flush(e, self.m.walls):
                    self.located_by[id(e)] = "wall face"
                refs.append((off, e.ref, "opening edge", "edge"))
            if al: refs.insert(0, al)
            if ah: refs.append(ah)
            if mid_grid is not None:
                refs.append(mid_grid[1])
                label = "%s opening edges|%s|edges" % (kind, mid_grid[1][3])
            else:
                label = "%s opening %s" % (kind, "anchor|edges|anchor" if (al and ah) else "anchor|edges")
            s = self.add(fi, gi, refs, span, label, f, prefer=pref, outward=(away or None), reach=12.0,
                         role="locate" if (al or ah or mid_grid) else "check")
            if s is not None:
                s.alt = alt
                s.keep_chain = keep_chain
            # a stepped opening also gets its overall size - "an overall goes
            # outside its chain" (Adolfo added 3'-0" outside 1'-2" | 8" | 1'-2"
            # at the L3N pilaster hole; analyst B6)
            # ... only when the chain has three or more segments (1'-2" | 8" |
            # 1'-2" gets its 3'-0"; the two-segment 3'-0" | 8" already spans the
            # hole on its locating line - its 3'-8" deleted, Adolfo 2026-10-07)
            if f.meta.get("stepped") and len(faces) > 3:
                self.add(fi, gi, [(lo, faces[0][1].ref, "opening edge", "edge"),
                                  (hi, faces[-1][1].ref, "opening edge", "edge")],
                         span, "stepped opening overall", f, prefer=pref, outward=(away or None),
                         reach=12.0, role="check")
                self.note("stepped opening: overall size added")
            # one-sided and large: the far edge gets its own anchor dim
            # (not needed when openings are stacked - the stack has it)
            one_sided = (al is None) != (ah is None)
            stacked = self.c["STACK"] and "opening" in self.c["STACK_KINDS"]
            if one_sided and not stacked and len(faces) >= 2 and (hi - lo) > self.c["FAR_EDGE_MIN"]:
                anc = al or ah
                far = faces[-1] if al else faces[0]
                if not self.flush(far[1], self.m.walls):
                    pref2 = pref + away * self.c["LANE_STEP"]
                    self.add(fi, gi, [anc, (far[0], far[1].ref, "opening edge", "far edge")],
                             (min(span[0], pref2), max(span[1], pref2)),
                             "opening far edge -> " + anc[3], f, prefer=pref2, outward=away, reach=12.0)

    def do_beam(self, f):
        b = f.meta["member"]
        fi = self.m.family_parallel(b.d)
        if fi is None:
            self.note("beam: angled (no grid family)")
            return
        mid = ((b.p0[0] + b.p1[0]) / 2.0, (b.p0[1] + b.p1[1]) / 2.0)
        ng = self.m.nearest_grid(mid, fi, self.c["MAX_DIST"])
        if ng is None:
            self.note("beam: too far from any grid")
            return
        gi, _ = ng
        sides = sorted(b.sides, key=lambda x: self.m.offset(x.mid(), gi))
        near, far = sides[0], sides[-1]
        on, of = self.m.offset(near.mid(), gi), self.m.offset(far.mid(), gi)
        if abs(of - on) < self.c["SAME_OFF_TOL"]:
            return
        s0, s1 = sorted([self.m.station(b.p0, gi), self.m.station(b.p1, gi)])
        # a beam capped by walls at both ends, its sides in line with them
        # (a link beam in a core wall line), has an assumed location - the
        # core wall plans cover it (Adolfo 2026-10-05)
        def wall_past(st, d):
            g_, g0_, u_, n_ = self.m.grids[gi]
            mo = (on + of) / 2.0
            x = g0_[0] + u_[0] * (st + d * 0.75) + n_[0] * mo
            y = g0_[1] + u_[1] * (st + d * 0.75) + n_[1] * mo
            return self.m.member_at(x, y, cats=("wall",)) is not None
        if wall_past(s0, -1) and wall_past(s1, 1) and \
                (self.flush(near, self.m.walls) or self.flush(far, self.m.walls)):
            for e in list(b.sides) + list(f.meta["free_ends"]):
                self.located_by[id(e)] = "beam in a wall line"
            self.note("beam in line with walls, capped by walls (skipped)")
            return
        # width dims sit just PAST an end of the beam, off the grey area
        # (Adolfo 2026-10-05) - the free end (beam stopping in the slab) if it
        # has one; past a framed end it may cross the other beam to open
        # margin. Beams longer than BEAM_BOTH at both ends - only ends inside
        # the view's crop (Adolfo 2026-10-06; the halfway width dim is gone:
        # no past McClone sheet has one).
        end_dir = -1
        free_st = [self.m.station(e.mid(), gi) for e in f.meta["free_ends"]]
        if len(free_st) == 1:
            end_dir = 1 if abs(free_st[0] - s1) < abs(free_st[0] - s0) else -1
        # a beam continuing in line with the same sides past an end (two
        # pieces of one band) has no END there - a width dim at that joint
        # sits mid-band, and the other piece's real-end dim gets thrown out as
        # its duplicate (Adolfo: beam 14895567 + 14181407)
        def continues(st, d):
            g_, g0_, u_, n_ = self.m.grids[gi]
            mo = (on + of) / 2.0
            x = g0_[0] + u_[0] * (st + d * 1.0) + n_[0] * mo
            y = g0_[1] + u_[1] * (st + d * 1.0) + n_[1] * mo
            for o in self.m.beams:
                if o is b or not o.poly or not o.sides or not P.point_in_poly(x, y, o.poly):
                    continue
                oo = sorted(self.m.offset(sd.mid(), gi) for sd in o.sides)
                if o.d is not None and P.parallel(o.d, b.d) and abs(oo[0] - on) < 0.1 and abs(oo[-1] - of) < 0.1:
                    return True
            return False
        cont_lo, cont_hi = continues(s0, -1), continues(s1, 1)
        if cont_lo and not cont_hi:
            end_dir = 1
        elif cont_hi and not cont_lo:
            end_dir = -1
        gap = self.c["BEAM_END_GAP"]
        ext = 8.0                                   # ft of open space past an end the dim may use
        g_, g0_, u_, n_ = self.m.grids[gi]
        def beam_past(st, d, k):
            mo = (on + of) / 2.0
            x = g0_[0] + u_[0] * (st + d * k) + n_[0] * mo
            y = g0_[1] + u_[1] * (st + d * k) + n_[1] * mo
            return self.m.member_at(x, y, cats=("beam",)) is not None
        self._over_band = {}
        self._inside_end = {}
        def at_end(d):
            e_st = s1 if d > 0 else s0
            span = (e_st - 1.0, e_st + ext) if d > 0 else (e_st - ext, e_st + 1.0)
            # an end framed into another beam: the width crosses that band to
            # open slab only when open slab is within FRAMED_CROSS of the end;
            # otherwise it sits just past the end, OVER the band (Adolfo
            # 2026-10-06, answer 2b: the grid-7 beam into the angled band)
            if beam_past(e_st, d, 0.5):
                opens = [k for k in (1.0, 2.0, 3.0, 4.0, 5.0, 6.0) if k <= self.c["FRAMED_CROSS"] and not beam_past(e_st, d, k)]
                if not opens:
                    span = (e_st - 1.0, e_st + gap + 1.5) if d > 0 else (e_st - gap - 1.5, e_st + 1.0)
                    self._over_band[d] = True
            elif self.m.member_at(g0_[0] + u_[0] * (e_st + d * 0.5) + n_[0] * (on + of) / 2.0,
                                  g0_[1] + u_[1] * (e_st + d * 0.5) + n_[1] * (on + of) / 2.0, cats=("wall",)) is not None:
                # an end AT A WALL: nothing past the end is legal ("over a wall"
                # is hard), so the width is read across the beam just inside
                # the end (beam#242 at the core wall went 22 ft away, L3N round 5)
                span = (e_st - 4.0, e_st - 0.5) if d > 0 else (e_st + 0.5, e_st + 4.0)
                self._inside_end[-d] = True
                return (span, e_st - d * 2.0, -d, False)
            return (span, e_st + d * gap, d, False)
        def in_view(st):
            mo = (on + of) / 2.0
            return self.fs._inside((g0_[0] + u_[0] * st + n_[0] * mo, g0_[1] + u_[1] * st + n_[1] * mo))
        ends_ok = [d for d, c in ((-1, cont_lo), (1, cont_hi)) if not c and in_view(s1 if d > 0 else s0)]
        if end_dir not in ends_ok and ends_ok:
            end_dir = ends_ok[0]
        if (s1 - s0) > self.c["BEAM_BOTH"]:
            b_parts = [at_end(d) for d in ends_ok]
        else:
            b_parts = [at_end(end_dir)] if ends_ok else []
        if cont_lo or cont_hi:
            self.note("beam continues in line past an end (no width dim at the joint)")
        # a side lying on a wall face below used to get the width only (the
        # wall "located" it) - but the wall isn't dimensioned on the soffit
        # plan, so the beam was never tied to a grid (Adolfo 2026-10-05):
        # beams always get width + the closest grid
        if on < -self.c["ON_GRID_TOL"] and of > self.c["ON_GRID_TOL"]:
            for span, pref, out, inter in b_parts:
                s = self.add(fi, gi, [(on, near.ref, "beam side", "side"), self.gref(gi) + (self.gname[gi],),
                                      (of, far.ref, "beam side", "side")], span,
                             "beam side|%s|side%s" % (self.gname[gi], " (intermediate)" if inter else ""),
                             f, prefer=pref, outward=out)
                if s is not None:
                    s.beam_width, s.intermediate = True, inter
                    s.over_band = self._over_band.get(out, False)
                    s.inside_end = self._inside_end.get(out, False)
        else:
            # hand sheets: width + ONE face to the nearest anchor (a second
            # anchor on the far side made 15-18 ft strings across the core)
            al = self.anchor(fi, gi, on, -1, s0, s1, walls=False)    # grids only (Adolfo)
            ah = self.anchor(fi, gi, of, +1, s0, s1, walls=False)
            if al is None and ah is None:
                g = self.gref(gi) + (self.gname[gi],)
                if on > 0: al = g
                else: ah = g
                self.note("beam: anchor beyond LOC_MAX")
            elif al and ah:
                if abs(al[0] - on) <= abs(ah[0] - of): ah = None
                else: al = None
            refs = [(on, near.ref, "beam side", "side"), (of, far.ref, "beam side", "side")]
            if al: refs.insert(0, al)
            if ah: refs.append(ah)
            for span, pref, out, inter in b_parts:
                s = self.add(fi, gi, list(refs), span, "beam anchor|sides%s" % (" (intermediate)" if inter else ""),
                             f, prefer=pref, outward=out)
                if s is not None:
                    s.beam_width, s.intermediate = True, inter
                    s.over_band = self._over_band.get(out, False)
                    s.inside_end = self._inside_end.get(out, False)
        for end in f.meta["free_ends"]:
            fr = self.frame(end)
            if fr is None:
                continue
            fj, gj, eoff, t0, t1 = fr
            if abs(eoff) < self.c["ON_GRID_TOL"]:
                self.located_by[id(end)] = "on grid"; continue
            # an end AT a column is framed into it - no end dim (Adolfo deleted
            # the 1'-0 1/2" at the NE corner column three rounds running)
            if self.flush(end, self.m.columns) or \
                    self.m.member_at(end.mid()[0], end.mid()[1], cats=("column",)) is not None:
                self.located_by[id(end)] = "at a column"
                self.note("beam end at a column (framed, skipped)"); continue
            cands = [x for x in (self.anchor(fj, gj, eoff, -1, t0, t1, walls=False),
                                 self.anchor(fj, gj, eoff, +1, t0, t1, walls=False)) if x]
            if not cands:
                cands = [x for x in (self.anchor(fj, gj, eoff, -1, t0, t1, cap=self.c["MAX_DIST"], walls=False),
                                     self.anchor(fj, gj, eoff, +1, t0, t1, cap=self.c["MAX_DIST"], walls=False)) if x]
            if not cands:
                self.note("beam end: no anchor"); continue
            anc = min(cands, key=lambda x: abs(x[0] - eoff))
            self.add(fj, gj, [anc, (eoff, end.ref, "beam end", "end")], (t0, t1),
                     "beam end -> " + anc[3], f, prefer=(t0 + t1) / 2.0)
        for end in f.meta["framed_ends"]:
            self.located_by[id(end)] = "framed into member"

    def do_cj(self, f):
        cj = f.edges[0]
        fi = self.m.family_parallel(cj.d)
        if fi is None:
            self.note("cj: angled"); return
        mid = ((cj.p0[0] + cj.p1[0]) / 2.0, (cj.p0[1] + cj.p1[1]) / 2.0)
        ng = self.m.nearest_grid(mid, fi, self.c["MAX_DIST"])
        if ng is None:
            return
        gi, off = ng
        if abs(off) < self.c["ON_GRID_TOL"]:
            self.located_by[id(cj)] = "on grid"; return
        # a CJ running along a beam side or a slab edge is located by that
        # element's dims (Adolfo: CJ 3'-8 15/16" off B sat on the beam side
        # 1/16" away - a third "3'-9"" nobody needs)
        slab_faces = [type("_E", (), {"sides": sl.edges, "faces": sl.edges})() for sl in self.m.slabs]
        on_face = self.flush(cj, slab_faces)
        # (a "CJ on a floor-to-floor seam is a real CJ" exception was tried in
        # run 85: it produced 4 CJ dims Adolfo doesn't draw and still not his
        # 3 | 7'-11" | CJ for CJ 20572305 - reverted; that CJ needs a model look)
        if self.flush(cj, self.m.beams) or on_face:
            self.located_by[id(cj)] = "on a beam side / slab edge"
            self.note("CJ on a beam side or slab edge (skipped)")
            return
        s0, s1 = sorted([self.m.station(cj.p0, gi), self.m.station(cj.p1, gi)])
        cands = [x for x in (self.anchor(fi, gi, off, -1, s0, s1, walls=False),
                             self.anchor(fi, gi, off, +1, s0, s1, walls=False)) if x]
        anc = min(cands, key=lambda x: abs(x[0] - off)) if cands else self.gref(gi) + (self.gname[gi],)
        # a CJ about halfway between two grids is dimensioned from BOTH, so the
        # field can use either (Adolfo 2026-10-06: 18'-0 3/8" to FF and
        # 18'-1 5/8" to EE; 6'-6 1/4" to 5 and 7'-6 3/4" to 4)
        anchors = [anc]
        if len(cands) == 2 and abs(abs(cands[0][0] - off) - abs(cands[1][0] - off)) <= self.c["CJ_MID_TOL"]:
            anchors.append(cands[1] if cands[0] is anc else cands[0])
            self.note("CJ halfway between two grids: dimensioned from both")
        # CJ dims stand just PAST an end of the CJ line, not across its middle
        # (Adolfo's edits: 21 of them moved ~1/4" past the end); long CJs at
        # both ends, otherwise the end with open slab past it
        gap, ext = self.c["BEAM_END_GAP"], 8.0
        g_, g0_, u_, n_ = self.m.grids[gi]
        def open_past(st, d, o=off):
            x = g0_[0] + u_[0] * (st + d * 2.0) + n_[0] * o
            y = g0_[1] + u_[1] * (st + d * 2.0) + n_[1] * o
            return self.m.member_at(x, y, cats=("wall", "beam", "column")) is None
        def meets_cj(st, o):
            # does another CJ line touch this end? (the dims of the CJ pair off
            # grid 5 go where the CJs meet the cross CJ - Adolfo, rounds 2-4)
            x = g0_[0] + u_[0] * st + n_[0] * o
            y = g0_[1] + u_[1] * st + n_[1] * o
            for other in self.m.cjs:
                if other is cj:
                    continue
                ax, ay, bx, by = other.p0[0], other.p0[1], other.p1[0], other.p1[1]
                L2 = (bx - ax) ** 2 + (by - ay) ** 2
                if L2 < 1e-6:
                    continue
                t = max(0.0, min(1.0, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / L2))
                if math.hypot(x - (ax + t * (bx - ax)), y - (ay + t * (by - ay))) < 0.5:
                    return True
            return False
        def natural_end(a0, a1, o):
            # (preferring the end at a CJ junction was tried in runs 85-88: it
            # flipped CJ -> 9 off Adolfo's spot and didn't move the pair - off)
            return 1 if (open_past(a1, 1, o) and not open_past(a0, -1, o)) else -1
        if s1 - s0 > self.c["TURN_BOTH"]:
            ends = [-1, 1]
        else:
            ends = [natural_end(s0, s1, off)]
        # two parallel CJs within CJ_PAIR (3 ft apart off grid 5 on L3N): one
        # dim each, at OPPOSITE ends, plus their spacing CJ | 3'-0" | CJ joined
        # to the lower one's locate dim (Adolfo 2026-10-06, drawn both rounds)
        pair = None
        for g in self.fs.features:
            if g.kind != "cj" or g is f or not g.in_crop:
                continue
            o = g.edges[0]
            if self.m.family_parallel(o.d) != fi:
                continue
            off2 = self.m.offset(((o.p0[0] + o.p1[0]) / 2.0, (o.p0[1] + o.p1[1]) / 2.0), gi)
            if not (self.c["ON_GRID_TOL"] < abs(off2 - off) <= self.c["CJ_PAIR"]):
                continue
            t0, t1 = sorted([self.m.station(o.p0, gi), self.m.station(o.p1, gi)])
            if min(s1, t1) - max(s0, t0) < 2.0:
                continue                            # must run side by side
            pair = (o, off2, t0, t1)
            break
        spacing = None
        if pair is not None and s1 - s0 <= self.c["TURN_BOTH"]:
            # the pair shares ONE end (Adolfo's round 2: 4'-5 1/2" | 3'-0" chain
            # inside, 7'-5 1/2" outside, both at the bottom end): the end that
            # is natural for both, else the farther CJ's natural end. The
            # nearer CJ carries the spacing, joined to its locate dim; the
            # longer dim stacks outside it (W_ORDER)
            o, off2, t0, t1 = pair
            nearer = abs(off) <= abs(off2)
            n_self, n_other = natural_end(s0, s1, off), natural_end(t0, t1, off2)
            ends = [n_self] if n_self == n_other else [n_other if nearer else n_self]
            if nearer:
                spacing = (off2, o.ref)
            self.note("parallel CJs: dims at one shared end, spacing joined")
        def end_of(d):
            e_st = s1 if d > 0 else s0
            span = (e_st - 1.0, e_st + ext) if d > 0 else (e_st - ext, e_st + 1.0)
            return span, e_st + d * gap
        for d in ends:
            span, pref = end_of(d)
            # a pair may go to the OTHER end if that is less cluttered (Adolfo
            # 2026-10-06: "more open space when moved to the bottom") - the
            # layout weighs both ends (String.alt)
            alt = None      # (an alternative end split the pair in round 4 - the junction rule decides instead)
            for anc in anchors:
                s = self.add(fi, gi, [anc, (off, cj.ref, "cj", "CJ")], span, "CJ -> " + anc[3], f,
                             prefer=pref, outward=d)
                if s is not None and alt:
                    s.alt = alt
            if spacing is not None:
                s = self.add(fi, gi, [(off, cj.ref, "cj", "CJ"), (spacing[0], spacing[1], "cj", "CJ")], span,
                             "CJ | CJ spacing", f, prefer=pref, outward=d, role="check")
                if s is not None and alt:
                    s.alt = alt

    def do_shaft_pockets(self):
        """Shafts the slab outline wraps around (Adolfo 2026-10-05: the shaft at
        the L3N core's lower right had no size - it isn't a hole in the slab,
        so no opening feature): a slab edge whose open side faces a parallel
        wall face across open space (no slab between, <= SHAFT_MAX) gets an
        overall-size string edge | wall face, role 'check'. The one case a dim
        goes to a wall: it is the shaft's size."""
        import mcc_model as M
        c = self.c
        m = self.m
        run_of = {}
        for f in self.fs.features:
            if f.kind in ("run", "corner", "step", "bump", "notch"):
                for e in f.edges:
                    run_of.setdefault(id(e), f)
        added = 0
        pockets = []
        for sl in m.slabs:
            for e in sl.edges:
                if e.length < c["SHAFT_MIN_EDGE"] or id(e) not in run_of or not run_of[id(e)].in_crop:
                    continue
                if run_of[id(e)].label() in (getattr(self, "enlarged", None) or []):
                    continue                    # left for an enlarged plan (the 8" pocket size of notch#0, round 4)
                if self.flush(e, m.walls) or self.flush(e, m.columns) or self.flush(e, m.beams):
                    continue
                fr = self.frame(e)
                if fr is None:
                    continue
                fi, gi, off, s_lo, s_hi = fr
                g, g0, u, n = m.grids[gi]
                mid = (s_lo + s_hi) / 2.0
                def pt(st, o):
                    return (g0[0] + u[0] * st + n[0] * o, g0[1] + u[1] * st + n[1] * o)
                def in_slab(x, y):
                    for s2 in m.slabs:
                        if P.point_in_poly(x, y, s2.outer) and not any(
                                P.point_in_poly(x, y, [q[:2] for q in h]) for h in s2.openings if h):
                            return True
                    return False
                # the open side of the edge (no slab just past it)
                side = None
                for sd in (1, -1):
                    x, y = pt(mid, off + sd * 0.25)
                    if not in_slab(x, y):
                        side = sd
                        break
                if side is None:
                    continue
                best = None
                for w in m.walls:
                    for wf in w.sides:
                        if not P.parallel(wf.d, u):
                            continue
                        o = m.offset(wf.mid(), gi)
                        gap = (o - off) * side
                        if gap < 0.5 or gap > c["SHAFT_MAX"]:
                            continue
                        w0, w1 = sorted([m.station(wf.p0, gi), m.station(wf.p1, gi)])
                        lo, hi = max(s_lo, w0), min(s_hi, w1)
                        if hi - lo < 0.5 * (s_hi - s_lo):
                            continue                  # must face most of the edge
                        if best is None or gap < best[0]:
                            best = (gap, o, wf, lo, hi)
                if best is None:
                    continue
                gap, o, wf, lo, hi = best
                st = (lo + hi) / 2.0
                if any(in_slab(*pt(st, off + side * gap * k)) for k in (0.25, 0.5, 0.75)):
                    continue                          # slab between: not a shaft
                s = self.add(fi, gi, [(off, e.ref, "slab edge", "edge"), (o, wf.ref, "wall face", "wall")],
                             (lo, hi), "shaft size (edge | wall)", run_of[id(e)], role="check", prefer=st)
                if s is not None:
                    added += 1
                    # the pocket is a no-go zone like an opening (only its own
                    # size may sit inside): shrink 0.1 ft off the edge and wall
                    a, b = off + side * 0.1, off + side * (gap - 0.1)
                    rect = [pt(lo + 0.1, a), pt(hi - 0.1, a), pt(hi - 0.1, b), pt(lo + 0.1, b)]
                    ob = M.Obst(rect, -1, "opening", raw=rect)
                    m.obstacles.append(ob)
                    pockets.append((s, ob))
        # each size string may sit in its pocket (both directions' rectangles of one shaft)
        for s, ob in pockets:
            cx = sum(p[0] for p in ob.raw) / 4.0; cy = sum(p[1] for p in ob.raw) / 4.0
            s.own_voids = set(id(o2) for _, o2 in pockets
                              if P.point_in_poly(cx, cy, o2.raw) or
                              P.point_in_poly(sum(p[0] for p in o2.raw) / 4.0, sum(p[1] for p in o2.raw) / 4.0, ob.raw))
        self.notes["shaft sizes (slab edge | wall across a shaft)"] = added

    # ---------------- consistency + dedupe ----------------
    def make_consistent(self):
        """Neighbouring locate strings along the same family prefer the
        same grid when the alternative is within CONSISTENCY x."""
        c = self.c
        switched = 0
        locs = [s for s in self.strings if s.role == "locate"]
        for s in locs:
            gi_refs = [(i, r) for i, r in enumerate(s.refs) if r[2] == "grid"]
            if len(gi_refs) != 1:
                continue
            i, (goff, gref_, _) = gi_refs[0]
            # the object offset this anchor serves
            obj = s.refs[1][0] if i == 0 else s.refs[-2][0]
            side = -1 if i == 0 else 1
            d0 = abs(goff - obj)
            # neighbours: same family, overlapping span, one grid ref
            votes = {}
            for t in locs:
                if t is s or t.fi != s.fi or t.gi != s.gi:
                    continue
                if not self.spans_overlap(s.span[0], s.span[1], t.span[0], t.span[1], 3.0):
                    continue
                for r in t.refs:
                    if r[2] == "grid":
                        votes[round(r[0] * 96)] = votes.get(round(r[0] * 96), 0) + 1
            if not votes:
                continue
            best = max(votes.items(), key=lambda kv: kv[1])[0] / 96.0
            if abs(best - goff) < c["ON_GRID_TOL"]:
                continue
            if (best - obj) * side < c["ON_GRID_TOL"]:
                continue                         # wrong side
            d1 = abs(best - obj)
            if d1 <= c["CONSISTENCY"] * d0 and d1 <= c["LOC_MAX"]:
                # find that grid
                for gj in self.m.families[s.fi]:
                    o = self.m.offset(self.m.grid(gj)[1], s.gi)
                    if abs(o - best) < c["ON_GRID_TOL"]:
                        s.refs[i] = (o, DB.Reference(self.m.grid(gj)[0]), "grid")
                        s.names[i] = self.gname[gj]
                        s.label = s.label.rsplit("->", 1)[0] + "-> " + self.gname[gj] if "->" in s.label else s.label
                        switched += 1
                        break
        self.notes["anchor switched for consistency"] = switched

    def drop_wall_where_grid(self):
        """A locate dim from a wall face to an edge that a grid-anchored dim
        already locates is a double (Adolfo deleted 26'-3" / 24'-8 7/8" off the
        core wall: "we had dimensions off of grid already locating the edges")."""
        tol = 1.0 / 96
        def fam_off(s, r):
            g, g0, u, n = self.m.grids[s.gi]
            return round((r[0] + self.m.offset(g0, self.m.families[self.m.fam_of[s.gi]][0])) / tol)
        by_grid = set()
        for s in self.strings:
            if s.role == "locate" and any(r[2] == "grid" for r in s.refs):
                for r in s.refs:
                    if r[2] != "grid":
                        by_grid.add((s.fi, fam_off(s, r)))
        keep, dropped = [], 0
        for s in self.strings:
            wall_anchor = any(r[2] == "wall face" or nm == "edge@wall" for r, nm in zip(s.refs, s.names))
            if s.role == "locate" and wall_anchor and not any(r[2] == "grid" for r in s.refs):
                targets = [r for r, nm in zip(s.refs, s.names) if r[2] != "wall face" and nm != "edge@wall"]
                if targets and all((s.fi, fam_off(s, r)) in by_grid for r in targets):
                    dropped += 1
                    continue
            keep.append(s)
        self.strings = keep
        if dropped:
            self.notes["wall-anchored dims of edges a grid already locates (dropped)"] = dropped

    def cluttered_small(self):
        """Small openings and notches (< SMALL_OPEN both ways) with two or more
        other small ones within CLUTTER_R: too crowded for this scale - they
        belong in an enlarged plan (Adolfo 2026-10-05: the small openings and
        notch around the L3N core). Core / shaft openings stay (the 3' x 3'-8"
        pilaster hole he kept) unless they are mere SLOTS - narrower than
        SLOT_MAX one way (the pair of 2'-0" x 6" holes in the L3N core wall he
        deleted, run 50 edits); a slot needs only ONE other small one near it."""
        small = []
        for f in self.fs.features:
            if not f.in_crop or f.kind not in ("opening", "notch"):
                continue
            xs = [p for e in f.edges for p in (e.p0[0], e.p1[0])]
            ys = [p for e in f.edges for p in (e.p0[1], e.p1[1])]
            if not xs or max(xs) - min(xs) >= self.c["SMALL_OPEN"] or max(ys) - min(ys) >= self.c["SMALL_OPEN"]:
                continue
            slot = min(max(xs) - min(xs), max(ys) - min(ys)) < self.c["SLOT_MAX"]
            if f.kind == "opening" and getattr(f, "sub", None) in ("core", "shaft") and not slot:
                continue
            small.append((f, (sum(xs) / len(xs), sum(ys) / len(ys)), slot))
        r2 = self.c["CLUTTER_R"] ** 2
        out = set()
        for f, (x, y), slot in small:
            near = sum(1 for g, (x2, y2), _ in small if g is not f and (x - x2) ** 2 + (y - y2) ** 2 <= r2)
            if near >= (1 if slot else 2):
                out.add(f)
        return out

    def build(self):
        order = {"run": 0, "bump": 1, "notch": 1, "step": 1, "opening": 2, "beam": 3, "cj": 4}
        enlarged = self.cluttered_small()
        self.enlarged = sorted(f.label() for f in enlarged)
        for f in sorted(self.fs.features, key=lambda f: order.get(f.kind, 9)):
            if not f.in_crop or f.kind == "corner":
                continue
            if f in enlarged:
                for e in f.edges:
                    self.located_by[id(e)] = "for an enlarged plan"
                continue
            getattr(self, "do_" + f.kind)(f)
        if enlarged:
            self.notes["small openings/notches crowded together (left for an enlarged plan)"] = len(enlarged)
        self.do_shaft_pockets()
        self.do_angled_corners()
        self.make_consistent()
        n0 = len(self.strings)
        m = self.m
        def base(it):
            g, g0, u, n = m.grids[it.gi]
            g_fam = m.families[m.fam_of[it.gi]][0]
            return m.offset(g0, g_fam), m.station(g0, g_fam)
        self.strings = dedupe(self.strings, notes=self.notes, base=base)
        self.notes["duplicates dropped"] = n0 - len(self.strings)
        self.merge_through_anchor()
        self.stack_from_anchor()
        self.drop_wall_where_grid()
        self.mark_ro()
        return self.strings

    def do_angled_corners(self):
        """A corner where the outline turns at a non-90 degree angle: the end of
        the straight edge is located ALONG that edge, from the nearest grid of
        the family crossing it, to the slab's vertical corner edge (a point in
        plan). Adolfo 2026-10-06: BB | 12'-1 3/8" | corner where the 6 ft
        vertical run meets the angled perimeter west of beam#232; B | 3'-11 1/8" |
        corner at the angled shaft's jog - "it helps to have this in the field".
        Right-angle corners are located by the other edge's across-dims."""
        m = self.m
        if not getattr(m, "corner_refs", None):
            return
        feat_of = {}
        for f in self.fs.features:
            for e in f.edges:
                feat_of.setdefault(id(e), f)
        units = [m.grids[fam[0]][2] for fam in m.families]
        def crossing(fi):
            # the family squarest to fi (the 30-degree family came back first
            # for the angled shaft's fam-3 edges at |dot| 0.087 - B's is 0.0)
            u = units[fi]
            best = None
            for fj, v in enumerate(units):
                d = abs(u[0] * v[0] + u[1] * v[1])
                if fj != fi and d < 0.1 and (best is None or d < best[0]):
                    best = (d, fj)
            return best[1] if best else None
        n = 0
        seen = set()
        for sl in m.slabs:
            loops = [list(sl.edges)] + [list(l) for l in sl.open_edges]
            for loop in loops:
                for k in range(len(loop)):
                    e1, e2 = loop[k], loop[(k + 1) % len(loop)]
                    # the shared vertex, whichever way the loop's edges run
                    v = None
                    for pa in (e1.p0, e1.p1):
                        for pb in (e2.p0, e2.p1):
                            if math.hypot(pa[0] - pb[0], pa[1] - pb[1]) <= 1.0 / 48:
                                v = pa
                    if v is None:
                        continue                        # not consecutive
                    dot = abs(e1.d[0] * e2.d[0] + e1.d[1] * e2.d[1])
                    if dot < 0.1 or dot > 0.995:
                        continue                        # square corner / straight
                    key = (int(round(v[0] * 96)), int(round(v[1] * 96)))
                    if key in seen:
                        continue
                    ref = m.corner_ref(v)
                    if ref is None:
                        continue
                    best = None
                    for e in (e1, e2):
                        if e.length < self.c["CORNER_MIN_EDGE"]:
                            continue                    # "as long as it doesn't clutter" - long edges only
                        fi = m.family_parallel(e.d)
                        if fi is None:
                            continue
                        fx = crossing(fi)
                        if fx is None:
                            continue
                        ng = m.nearest_grid(v, fx, self.c["LOC_MAX"])
                        if ng is None:
                            continue
                        gi, off = ng
                        if abs(off) < self.c["ON_GRID_TOL"]:
                            continue
                        if best is None or abs(off) < abs(best[2]):
                            best = (e, fx, off, gi)
                    if best is None:
                        continue
                    e, fx, off, gi = best
                    seen.add(key)
                    st = m.station(v, gi)
                    f = feat_of.get(id(e))
                    if f is not None and not f.in_crop:
                        continue
                    s = self.add(fx, gi, [self.gref(gi) + (self.gname[gi],),
                                          (m.offset(v, gi), ref, "slab corner", "corner")],
                                 (st - 2.0, st + 2.0), "corner -> " + self.gname[gi], f, prefer=st)
                    if s is not None:
                        s.late = True               # placed after the element's own rows (run 83: it took
                        n += 1                      # the shaft's first lane and split the B stack)
        if n:
            self.notes["non-90 corners located along the edge from a grid"] = n

    def mark_ro(self):
        """'R.O.' on the overall size of a shaft / core opening: a string of exactly
        two refs, both edges of that opening (or a shaft pocket's slab edge | wall
        face). Dims off a grid never get it (Adolfo 2026-10-06)."""
        suf = self.c.get("RO_SUFFIX")
        n = 0
        for s in self.strings:
            f = s.feature
            if not suf:
                continue
            if len(s.refs) > 2:
                # the opening's width as ONE SEGMENT of a chain (edge@wall |
                # 8'-3" R.O. | edge | 11'-9" | 7 at the L3N elevator shafts,
                # Adolfo's round 2): mark that segment only
                if f is not None and f.kind == "opening" and f.sub in ("core", "shaft"):
                    offs = [self.m.offset(p, s.gi) for e in f.edges for p in (e.p0, e.p1)]
                    sts = [self.m.station(p, s.gi) for e in f.edges for p in (e.p0, e.p1)]
                    if min(max(offs) - min(offs), max(sts) - min(sts)) >= self.c["RO_MIN"]:
                        nm0 = getattr(s, "names", None) or [r[2] for r in s.refs]
                        order = sorted(range(len(s.refs)), key=lambda k: s.refs[k][0])
                        refs = [s.refs[k] for k in order]
                        names = [nm0[k] for k in order]
                        for k in range(len(refs) - 1):
                            a, b = refs[k], refs[k + 1]
                            if names[k] in ("edge", "edge@wall") and names[k + 1] in ("edge", "edge@wall") \
                                    and abs((b[0] - a[0]) - (max(offs) - min(offs))) < 1.0 / 96:
                                # remembered by the segment's two offsets (the layout may
                                # join this string with another, shifting indexes)
                                s.suffix_pairs = list(getattr(s, "suffix_pairs", None) or []) + [(a[0], b[0], suf)]
                                n += 1
                continue
            if len(s.refs) != 2:
                continue
            shaft_open = f is not None and f.kind == "opening" and f.sub in ("core", "shaft") and \
                all(r[2] == "opening edge" for r in s.refs)
            if shaft_open:
                # the overall only: edge to edge across the whole opening, not a
                # step inside a stepped hole (the 8" of 1'-2" | 8" | 1'-2")
                offs = [self.m.offset(p, s.gi) for e in f.edges for p in (e.p0, e.p1)]
                shaft_open = abs(abs(s.refs[1][0] - s.refs[0][0]) - (max(offs) - min(offs))) < 1.0 / 96
                # ... and only a LARGE opening: at least RO_MIN both ways
                # (stair / elevator shafts), measured along and across the string
                sts = [self.m.station(p, s.gi) for e in f.edges for p in (e.p0, e.p1)]
                if min(max(offs) - min(offs), max(sts) - min(sts)) < self.c["RO_MIN"]:
                    shaft_open = False
            # a pocket narrower than a shaft side (the 8" slab edge to core wall gap) is a gap, not an R.O.;
            # and it must be RO_MIN wide too
            pocket = s.label.startswith("shaft size") and \
                abs(s.refs[1][0] - s.refs[0][0]) >= max(self.c["SHAFT_MIN_EDGE"], self.c["RO_MIN"])
            if shaft_open or pocket:
                s.suffix = suf
                n += 1
        self.notes["shaft overall sizes marked " + (suf or "-")] = n

    def stack_from_anchor(self):
        """Stacked dims (Adolfo 2026-10-05; 67-75% of hand dims on Kalae and
        Alia share a baseline): a locate chain anchor | e1 | e2 ... also gets
        anchor -> e1, anchor -> e2, ... as separate dims, shortest first; the
        chain becomes a check. Stacked from the anchor nearest its object."""
        if not self.c["STACK"]:
            return
        m = self.m
        def fam_offs(s, refs):
            g, g0, u, n = m.grids[s.gi]
            b = m.offset(g0, m.families[m.fam_of[s.gi]][0])
            # ... and roughly WHERE along the grid (30 ft buckets): the same
            # offsets at another element 107 ft away are not the same dim
            # (L7 round 1: plain#63's 6 | 8" was skipped for run#22's)
            fam_g = m.families[m.fam_of[s.gi]][0]
            mid = (s.span[0] + s.span[1]) / 2.0
            g_, g0_, u_, n_ = m.grids[s.gi]
            pt = (g0_[0] + u_[0] * mid, g0_[1] + u_[1] * mid)
            bucket = int(round(m.station(pt, fam_g) / 30.0))
            return tuple(round((r[0] + b) * 96) for r in refs) + (bucket,)
        have = set()
        for s in self.strings:
            if s.role == "locate":
                have.add((s.fi, fam_offs(s, s.refs)))
        added, chains = 0, 0
        drop = set()
        for s in list(self.strings):
            if s.role != "locate" or len(s.refs) < 3 or s.feature is None \
                    or s.feature.kind not in self.c["STACK_KINDS"]:
                continue
            # anchor: a grid anywhere in the string (one may run through an
            # opening) or a wall face / edge on a wall at an end - whichever
            # is closest to the object it locates
            ends = []
            last = len(s.refs) - 1
            for i, r in enumerate(s.refs):
                if r[2] == "grid" or (i in (0, last) and (r[2] == "wall face" or s.names[i] == "edge@wall")):
                    near = [abs(q[0] - r[0]) for k, q in enumerate(s.refs) if k != i and q[2] != "grid"]
                    if near:
                        ends.append((min(near), i))
            if not ends:
                continue
            i = min(ends)[1]
            anc, an = s.refs[i], s.names[i]
            if getattr(s, "keep_chain", False):
                # an opening located off a wall because no grid of that
                # direction is near stays one chain, as Adolfo draws it
                # (2026-10-06: edge | 3'-9 3/4" | edge | 4'-10 1/4" | wall at
                # the angled shaft by the L3N core). Tried for every
                # wall-anchored chain (run 56): at the core openings he keeps
                # the stacks (7", 3'-3", 5", 17'-8" off the core walls)
                self.note("no-grid chain off a wall kept as drawn (not stacked)")
                continue
            targets = [(r, nm) for k, (r, nm) in enumerate(zip(s.refs, s.names))
                       if k != i and r[2] not in ("grid", "wall face")]   # never TO a wall
            if len(targets) < 2:
                continue
            if max(abs(t[0][0] - anc[0]) for t in targets) > self.c["LOC_MAX"]:
                # a stacked dim past the tape (30 ft) can't be pulled in the
                # field; the chain measures segment by segment - keep it
                self.note("not stacked: a stacked dim would pass the 30 ft tape")
                continue
            targets.sort(key=lambda t: abs(t[0][0] - anc[0]))
            # a small opening needs only its near edge tied to the grid; the
            # size (the chain check) gives the other (Adolfo 2026-10-05)
            t_offs = [t[0][0] for t in targets]
            if s.feature.kind == "opening" and max(t_offs) - min(t_offs) < self.c["SMALL_OPEN"]:
                near = targets[0]
                targets = [near]
                self.note("small opening: near edge only off the grid")
            elif s.feature.kind == "opening" and i in (0, last) and \
                    (getattr(s.feature, "sub", None) == "core" or
                     (getattr(s.feature, "sub", None) == "shaft" and "edge@wall" in s.names)):
                # (a shaft with a face on the core wall too - L7 shaft#46, Adolfo: "near edge and size only")
                # inside a core the space is tight: the OUTSIDE anchor's dim to
                # the near edge plus the opening's size is enough - no far-edge
                # row (Adolfo round 2: deleted the 14'-4" / 14'-10" rows off CC).
                # A grid running THROUGH the opening keeps both its rows
                # (9'-3 7/8" | BB | 8'-4 1/8" he kept); shafts outside a core
                # keep their far-edge row (the 23'-2 1/2" off EE)
                targets = [targets[0]]
                self.note("core opening: near edge only off the outside grid (size covers the rest)")
            elif s.feature.kind == "opening" and len(set(t[0][0] > anc[0] for t in targets)) == 1                     and len(targets) < 3:
                # Adolfo 2026-10-07 (L7 round 2, "1a"/"2a"): an opening's
                # near edge off the grid + its size is enough - no far-edge
                # row, no second leg to the next grid. Only when the grid is
                # outside the opening: a grid THROUGH it keeps a row each side
                # (L3N 9'-6 3/4" | B | 5'-3 1/4", kept every round); a stepped
                # side (3+ faces) keeps its rows. (Tried: no row to a face on
                # a wall - he deleted core#49's 7 | 4'-5" | edge@wall but keeps
                # core#47's edge@wall | 4'-6" | CC; lost 2 of his dims, reverted)
                targets = [targets[0]]
                self.note("opening: near edge only off the grid (no far-edge row)")
            # a grid in the middle: the targets on each side of it form their own
            # stack - dims on opposite sides are end to end, not stacked (they
            # get joined into edge | grid | edge by the layout)
            ranks, keys = [], []
            seen = {}
            for r, nm in targets:
                sd = 1 if r[0] > anc[0] else -1
                seen[sd] = seen.get(sd, -1) + 1
                ranks.append(seen[sd])
                keys.append((id(s), sd))
            for (r, nm), rank, key in zip(targets, ranks, keys):
                pair = sorted([(anc, an), (r, nm)], key=lambda t: t[0][0])
                refs = [p[0] for p in pair]
                sig = (s.fi, fam_offs(s, refs))
                if sig in have:
                    self.note("stacked dim already planned (skipped)")
                    continue
                have.add(sig)
                t = String(s.fi, s.gi, refs, s.span, "stack %d -> %s" % (rank + 1, an), s.feature,
                           names=[p[1] for p in pair], prefer=s.prefer, outward=s.outward, reach=s.reach)
                t.alt = s.alt
                t.stack = (key, rank, len(targets))
                self.strings.append(t)
                added += 1
            # the chain stays as the check, without the anchor: its first
            # segment would only repeat the first stacked dim (Adolfo: doubles)
            keep = [k for k in range(len(s.refs)) if k != i and s.refs[k][2] not in ("grid", "wall face")]
            check_refs = [s.refs[k] for k in keep]
            sig = (s.fi, fam_offs(s, check_refs))
            if len(check_refs) < 2 or sig in have:
                drop.add(id(s))
            else:
                have.add(sig)
                s.refs = check_refs
                s.names = [s.names[k] for k in keep]
                s.role = "check"
                s.label += " (chain check)"
                chains += 1
        self.strings = [s for s in self.strings if id(s) not in drop]
        self.notes["stacked dims added (from one anchor)"] = added
        self.notes["chains kept as checks (edges only)"] = chains
        self.notes["chains dropped (stack says it all)"] = len(drop)

    def merge_through_anchor(self):
        """Two 2-line strings off the same grid, one each side of it, with
        overlapping spans (a slab face and a step face either side of a
        gridline) become one string: edge | grid | edge - the way a
        detailer chains them."""
        m = self.m
        by_grid = {}
        for s in self.strings:
            if len(s.refs) != 2 or s.role != "locate":
                continue
            if s.feature is not None and s.feature.kind == "cj":
                continue        # CJ dims stay separate either side of a grid (Adolfo split the chain)
            kinds = [r[2] for r in s.refs]
            if "grid" not in kinds:
                continue
            gi_ref = s.refs[kinds.index("grid")]
            other = s.refs[1 - kinds.index("grid")]
            by_grid.setdefault((s.fi, s.gi, round(gi_ref[0] * 96)), []).append((s, gi_ref, other))
        merged = 0
        drop = set()
        for key, items in by_grid.items():
            lo = [t for t in items if t[2][0] < t[1][0]]
            hi = [t for t in items if t[2][0] > t[1][0]]
            for a in lo:
                if id(a[0]) in drop:
                    continue
                for b in hi:
                    if id(b[0]) in drop:
                        continue
                    (a0, a1), (b0, b1) = a[0].span, b[0].span
                    if not self.spans_overlap(a0, a1, b0, b1, slack=1.0):
                        continue
                    sa, sb = a[0], b[0]
                    na = dict(zip([id(r) for r in sa.refs], sa.names))
                    nb = dict(zip([id(r) for r in sb.refs], sb.names))
                    sa.refs = [a[2], a[1], b[2]]
                    sa.names = [na.get(id(a[2]), "edge"), na.get(id(a[1]), "grid"), nb.get(id(b[2]), "edge")]
                    sa.span = (min(a0, b0), max(a1, b1))
                    sa.label = sa.label + " + " + sb.label
                    sa.owners = set(sa.owners) | set(sb.owners)
                    drop.add(id(sb))
                    merged += 1
                    break
        if drop:
            self.strings = [s for s in self.strings if id(s) not in drop]
            self.notes["merged through a gridline (edge | grid | edge)"] = merged

    # ---------------- report ----------------
    def describe(self, s):
        vals = [ftin(v) for v in s.values()]
        parts = []
        for k, (nm, v) in enumerate(zip(s.names, vals + [None])):
            parts.append(nm if nm in ("wall", "CJ", "edge", "leg", "top", "step", "side", "end", "far edge", "edge@wall") or nm.isupper() or nm[0].isdigit() or nm[0] in "ABCDEFGHJ" else nm)
            if v is not None:
                parts.append(v)
        fam = "/".join(self.gname[g] for g in self.m.families[s.fi][:2]) + ".."
        return "%-5s %-28s across %-9s %s" % (s.role, s.label, fam, " | ".join(parts))

    def coverage_rows(self):
        """Planned strings as rows for mcc_coverage.grade()."""
        rows = []
        for s in self.strings:
            g, g0, u, n = self.m.grids[s.gi]
            base = n[0] * g0[0] + n[1] * g0[1]
            kinds = []
            for off, ref, k in s.refs:
                kinds.append("grid" if k == "grid" else ("wall" if k == "wall face" else ("beam" if "beam" in k else ("cj" if k == "cj" else "slab"))))
            sts = [(base + off, k) for (off, _, _), k in zip(s.refs, kinds)]
            st = s.prefer if s.prefer is not None else sum(s.span) / 2.0
            mo = (s.refs[0][0] + s.refs[-1][0]) / 2.0
            o = (g0[0] + u[0] * st + n[0] * mo, g0[1] + u[1] * st + n[1] * mo)
            rows.append(({"stations": sts, "kinds": " > ".join(kinds)}, (n[0], n[1]), o))
        return rows


def plan_view(model, crop):
    fs = F.FeatureSet(model, crop=crop)
    pl = Planner(model, fs)
    pl.build()
    return fs, pl
