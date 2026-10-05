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
    "TURN_BOTH": 20.0,      # ft; runs longer than this located at both ends
    "OPEN_OFFSET_IN": 0.25, # paper inches; opening strings sit this far outside (hand sheets: ~1/4")
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
    "STACK": True,
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

    def flush(self, face, members):
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
                    return mbr
        return None

    def anchor(self, fi, gi, off, side, s_lo, s_hi, cap=None, walls=True):
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
        if walls and c["WALL_ANCHOR_IF_NO_GRID"] and grid_near:
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

    def end_parts(self, s_lo, s_hi):
        """'A dimension at each end for ease of reading' (Adolfo 2026-10-05):
        longer than TURN_BOTH -> one part per end, each with its own half span
        (so dedupe doesn't fold the two into one, as it used to for runs).
        -> [(span, prefer, outward)]; outward points at that end."""
        ci = self.c["CORNER_IN"]
        if s_hi - s_lo <= self.c["TURN_BOTH"]:
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
        if self.flush(e, self.m.walls):
            self.located_by[id(e)] = "wall face"; return
        if self.flush(e, self.m.columns):
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
        parts = self.end_parts(s_lo, s_hi)
        for k, (span, _, _) in enumerate(parts):
            pref = s_lo + self.c["CORNER_IN"] if k == 0 else s_hi - self.c["CORNER_IN"]
            s = self.add(fi, gi, refs, span, "run -> " + anc[3], f,
                         prefer=pref, outward=(1 if k == 0 else -1))
            if s is not None:
                # the dim can sit in the margin past this end of the edge
                # (hand sheets run a column of these beside the slab)
                s.free = free[0] if k == 0 else free[1]

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

    def on_column(self, f):
        """Any edge of the feature lying on a column face -> the bump/notch/step
        is the slab cut around a column, not a soffit shape: skip it."""
        hit = [e for e in f.edges if self.flush(e, self.m.columns)]
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
        if self.on_column(f):
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
        # jog check: run a face | run b face
        fr = self.frame(a)
        if fr is not None:
            fi, gi, oa, _, _ = fr
            ob = self.m.offset(b.mid(), gi)
            if abs(oa - ob) > self.c["SAME_OFF_TOL"]:
                sj = self.m.station(s.mid(), gi)
                self.add(fi, gi, [(oa, a.ref, "slab edge", "edge"), (ob, b.ref, "slab edge", "edge")],
                         (sj - 2.0, sj + 2.0), "jog check", f, role="check", prefer=sj)

    def do_opening(self, f):
        kind = f.sub
        cx, cy = f.meta["centroid"]
        for fi in range(len(self.m.families)):
            par = [e for e in f.edges if self.m.family_parallel(e.d) == fi]
            if not par:
                continue
            ng = self.m.nearest_grid((cx, cy), fi, self.c["MAX_DIST"])
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
            if kind == "void":
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
            al = None if lo_wall else self.anchor(fi, gi, lo, -1, s_lo, s_hi)
            ah = None if hi_wall else self.anchor(fi, gi, hi, +1, s_lo, s_hi)
            if lo_wall:
                al = (lo, faces[0][1].ref, "opening edge", "edge@wall")
            if hi_wall:
                ah = (hi, faces[-1][1].ref, "opening edge", "edge@wall")
            # a gridline running THROUGH the opening, closer to its edges than
            # any outside anchor, is the one to dimension from (Adolfo
            # 2026-10-05: always the closest gridline) -> edges | grid | edges
            mid_grid = None
            if not (lo_wall or hi_wall):
                tol = self.c["ON_GRID_TOL"]
                gaps = ([abs(lo - al[0])] if al else []) + ([abs(ah[0] - hi)] if ah else [])
                out_gap = min(gaps) if gaps else 1e9
                for gj in self.m.families[fi]:
                    o = self.m.offset(self.m.grid(gj)[1], gi)
                    if lo + tol < o < hi - tol:
                        d = min(o - lo, hi - o)
                        if d < out_gap and (mid_grid is None or d < mid_grid[0]):
                            mid_grid = (d, (o, DB.Reference(self.m.grid(gj)[0]), "grid", self.gname[gj]))
                if mid_grid is not None:
                    al = ah = None
            if mid_grid is None and al is None and ah is None:
                al = self.anchor(fi, gi, lo, -1, s_lo, s_hi, cap=self.c["MAX_DIST"], walls=False)
                ah = self.anchor(fi, gi, hi, +1, s_lo, s_hi, cap=self.c["MAX_DIST"], walls=False)
                if al and ah:
                    if abs(al[0] - lo) <= abs(ah[0] - hi): ah = None
                    else: al = None
                if al or ah:
                    self.note("opening: anchor beyond LOC_MAX")
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
        # width dims sit at an END of the beam, just inside it (Adolfo
        # 2026-10-05) - the free end (beam stopping in the slab) if it has one
        end_dir = -1
        free_st = [self.m.station(e.mid(), gi) for e in f.meta["free_ends"]]
        if len(free_st) == 1:
            end_dir = 1 if abs(free_st[0] - s1) < abs(free_st[0] - s0) else -1
        end_st = s1 if end_dir > 0 else s0
        b_pref = end_st - end_dir * min(self.c["CORNER_IN"], (s1 - s0) / 3.0)
        # long beam: a width dim at EACH end (Adolfo: "dimensions at each end")
        b_parts = self.end_parts(s0, s1)
        if len(b_parts) == 1:
            b_parts = [((s0, s1), b_pref, end_dir)]
        # a side lying on a wall face below used to get the width only (the
        # wall "located" it) - but the wall isn't dimensioned on the soffit
        # plan, so the beam was never tied to a grid (Adolfo 2026-10-05):
        # beams always get width + the closest grid
        if on < -self.c["ON_GRID_TOL"] and of > self.c["ON_GRID_TOL"]:
            for span, pref, out in b_parts:
                self.add(fi, gi, [(on, near.ref, "beam side", "side"), self.gref(gi) + (self.gname[gi],),
                                  (of, far.ref, "beam side", "side")], span,
                         "beam side|%s|side" % self.gname[gi], f, prefer=pref, outward=out)
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
            for span, pref, out in b_parts:
                self.add(fi, gi, list(refs), span, "beam anchor|sides", f, prefer=pref, outward=out)
        for end in f.meta["free_ends"]:
            fr = self.frame(end)
            if fr is None:
                continue
            fj, gj, eoff, t0, t1 = fr
            if abs(eoff) < self.c["ON_GRID_TOL"]:
                self.located_by[id(end)] = "on grid"; continue
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
        s0, s1 = sorted([self.m.station(cj.p0, gi), self.m.station(cj.p1, gi)])
        cands = [x for x in (self.anchor(fi, gi, off, -1, s0, s1, walls=False),
                             self.anchor(fi, gi, off, +1, s0, s1, walls=False)) if x]
        anc = min(cands, key=lambda x: abs(x[0] - off)) if cands else self.gref(gi) + (self.gname[gi],)
        for span, pref, out in self.end_parts(s0, s1):        # long CJ: one at each end
            self.add(fi, gi, [anc, (off, cj.ref, "cj", "CJ")], span, "CJ -> " + anc[3], f,
                     prefer=(s0 + s1) / 2.0 if pref is None else pref, outward=out)

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

    def build(self):
        order = {"run": 0, "bump": 1, "notch": 1, "step": 1, "opening": 2, "beam": 3, "cj": 4}
        for f in sorted(self.fs.features, key=lambda f: order.get(f.kind, 9)):
            if not f.in_crop or f.kind == "corner":
                continue
            getattr(self, "do_" + f.kind)(f)
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
        return self.strings

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
            return tuple(round((r[0] + b) * 96) for r in refs)
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
