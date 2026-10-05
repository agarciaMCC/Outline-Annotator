# -*- coding: utf-8 -*-
"""DECIDE: McClone soffit-plan dimensioning conventions as rules.

Numbers come from the audit of the hand-dimensioned Kalae sheets
(claude/dim-audit-findings.md): detailers place ONE short two-reference
dimension per fact, right beside the object. So every rule here yields
small Intents, not chained strings.

  slab edge   : edge -> nearest grid (each edge, locally); jogs edge->edge
  opening     : size across the opening (every step), plus near edge ->
                nearest grid, or -> wall face when a wall is right there
  beam        : width across it, plus near side -> nearest grid, or
                side | grid | side when centred; free ends -> grid /
                column face
  wall        : side -> nearest grid, or side | grid | side when centred
  CJ line     : line -> nearest grid
"""
from pyrevit import DB
import mcc_plan as P
from mcc_place import Intent, view_crop_poly, _pip

DEFAULTS = {
    "MAX_DIST": 40.0,        # ft; farther than this from any grid -> skip
    "ON_GRID_TOL": 1.0 / 192,
    "FLUSH_TOL": 1.0 / 48,   # ft; slab edge on a wall/beam face -> skip
    "JOG_MAX": 6.0,          # ft; perimeter jogs up to this get edge->edge
    "WALL_REACH": 8.0,       # ft; opening located from a wall face within this
    "COL_REACH": 4.0,        # ft; beam end located from a column face within this
    "OPEN_OFFSET": 1.5,      # ft; opening dims sit this far outside it
    "SAME_OFFSET_TOL": 1.0 / 96,
    "MIN_EDGE": 0.5,         # ft; ignore edges shorter than this
    "CORNER_IN": 2.0,        # ft; edge dims sit this far in from a corner
    "TURN_BOTH": 20.0,       # ft; edges longer than this get a dim at both ends
    "LOC_MAX": 20.0,         # ft; preferred max length of a locating dim
    "SMALL_OPENING": 2.0,    # ft; openings this small get one compact string
    "BIG_OPENING": 20.0,     # ft; wider than this, or stepped (>2 faces):
                             # each edge located locally instead of a string
    "ANCHOR_WALLS": True,    # wall faces may anchor openings / beams
}


class Rules(object):
    def __init__(self, model, cfg=None):
        self.m = model
        self.c = dict(DEFAULTS)
        if cfg:
            self.c.update(cfg)
        self.notes = {}

    def note(self, key):
        self.notes[key] = self.notes.get(key, 0) + 1

    # ---------------- helpers ----------------
    def face_frame(self, face):
        """(fi, gi, offset, s_lo, s_hi) of a face against its parallel
        family's nearest grid, or None."""
        fi = self.m.family_parallel(face.d)
        if fi is None:
            return None
        ng = self.m.nearest_grid(face.mid(), fi, self.c["MAX_DIST"])
        if ng is None:
            self.note("too far from any grid")
            return None
        gi, off = ng
        s0, s1 = self.m.station(face.p0, gi), self.m.station(face.p1, gi)
        return fi, gi, off, min(s0, s1), max(s0, s1)

    def spans_overlap(self, a0, a1, b0, b1, slack=0.0):
        return not (a1 + slack < b0 or b1 + slack < a0)

    def flush_member_face(self, face, members, tol):
        """A member side face parallel to 'face', on the same line, with
        overlapping extent."""
        for mbr in members:
            for f in mbr.sides or mbr.faces:
                if not P.parallel(f.d, face.d):
                    continue
                n = (-face.d[1], face.d[0])
                gap = (f.mid()[0] - face.p0[0]) * n[0] + \
                      (f.mid()[1] - face.p0[1]) * n[1]
                if abs(gap) > tol:
                    continue
                a0 = 0.0
                a1 = face.length
                b0 = (f.p0[0] - face.p0[0]) * face.d[0] + \
                     (f.p0[1] - face.p0[1]) * face.d[1]
                b1 = (f.p1[0] - face.p0[0]) * face.d[0] + \
                     (f.p1[1] - face.p0[1]) * face.d[1]
                if self.spans_overlap(a0, a1, min(b0, b1), max(b0, b1)):
                    return f
        return None

    def near_member_face(self, face, members, reach, gi):
        """Nearest parallel member face within 'reach' (measured across),
        overlapping the face's extent, not flush. Returns (face, offset)."""
        best = None
        s0, s1 = self.m.station(face.p0, gi), self.m.station(face.p1, gi)
        s0, s1 = min(s0, s1), max(s0, s1)
        off0 = self.m.offset(face.mid(), gi)
        for mbr in members:
            for f in mbr.sides or mbr.faces:
                if not P.parallel(f.d, face.d):
                    continue
                off = self.m.offset(f.mid(), gi)
                gap = abs(off - off0)
                if gap < self.c["FLUSH_TOL"] or gap > reach:
                    continue
                t0, t1 = self.m.station(f.p0, gi), self.m.station(f.p1, gi)
                if not self.spans_overlap(s0, s1, min(t0, t1), max(t0, t1), 0.5):
                    continue
                if best is None or gap < best[2]:
                    best = (f, off, gap)
        return (best[0], best[1]) if best else None

    # ---------------- crop / anchors ----------------
    def in_crop(self, pt):
        """Only dimension what is inside the view's crop - the other zone's
        sheet handles the rest."""
        if not hasattr(self, "_crop"):
            self._crop = view_crop_poly(self.m.view) or None
            if self._crop is None:
                try:
                    import mcc_coverage as _CV
                    self._crop = _CV.crop_poly(self.m.view)
                except Exception:
                    self._crop = None
        return self._crop is None or _pip(pt[0], pt[1], self._crop)

    def anchor(self, fi, gi, off, side, s_lo, s_hi, cap=None, walls=True):
        """Nearest locating reference on one side of offset 'off' (side -1 =
        lower offsets, +1 = higher), measured across family fi in grid gi's
        frame: a grid of the family, or (walls=True) a parallel wall face
        that faces the object (overlaps its extent along the grid).
        Returns (offset, DB.Reference, kind) or None."""
        c = self.c
        cap = c["LOC_MAX"] if cap is None else cap
        best = None
        for gj in self.m.families[fi]:
            o = self.m.offset(self.m.grid(gj)[1], gi)
            d = (o - off) * side
            if d < -c["ON_GRID_TOL"] or abs(o - off) > cap:
                continue
            if best is None or abs(o - off) < abs(best[0] - off):
                best = (o, DB.Reference(self.m.grid(gj)[0]), "grid")
        if walls and c.get("ANCHOR_WALLS", True):
            u = self.m.grid(gi)[2]
            for w in self.m.walls:
                for f in w.sides:
                    if not P.parallel(f.d, u):
                        continue
                    o = self.m.offset(f.mid(), gi)
                    if (o - off) * side < c["FLUSH_TOL"] or abs(o - off) > cap:
                        continue
                    t0, t1 = self.m.station(f.p0, gi), self.m.station(f.p1, gi)
                    if not self.spans_overlap(s_lo, s_hi, min(t0, t1), max(t0, t1), -0.25):
                        continue
                    if best is None or abs(o - off) < abs(best[0] - off) - c["FLUSH_TOL"]:
                        best = (o, f.ref, "wall face")
        return best

    # ---------------- slab edges ----------------
    def slab_edges(self):
        out = []
        c = self.c
        for slab in self.m.slabs:
            edges = slab.edges
            for i, e in enumerate(edges):
                if not self.in_crop(e.mid()):
                    continue
                if e.length < c["MIN_EDGE"]:
                    self.note("short edge")
                    continue
                fr = self.face_frame(e)
                if fr is None:
                    if self.m.family_parallel(e.d) is None:
                        self.note("angled edge (no grid family)")
                    continue
                fi, gi, off, s_lo, s_hi = fr
                if abs(off) < c["ON_GRID_TOL"]:
                    self.note("edge on a grid")
                    continue
                if self.flush_member_face(e, self.m.walls, c["FLUSH_TOL"]):
                    self.note("edge flush with wall (wall dim covers it)")
                    continue
                if self.flush_member_face(e, self.m.beams, c["FLUSH_TOL"]):
                    self.note("edge flush with beam (beam dim covers it)")
                    continue
                gref = (0.0, DB.Reference(self.m.grid(gi)[0]), "grid")
                # at a turn (near a corner), and at BOTH turns of a long
                # edge so no corner is far from its dimension
                ends = [s_lo + c["CORNER_IN"]]
                if s_hi - s_lo > c["TURN_BOTH"]:
                    ends.append(s_hi - c["CORNER_IN"])
                for k, pref in enumerate(ends):
                    out.append(Intent(fi, gi, [gref, (off, e.ref, "slab edge")],
                                      (s_lo, s_hi), "slab edge -> grid",
                                      owners=(slab.eid,), prefer=pref,
                                      outward=(1 if k == 0 else -1)))
            # jogs: edge i and i+2 parallel, joined by a short edge i+1
            n_e = len(edges)
            for i in range(n_e):
                a, j, b = edges[i], edges[(i + 1) % n_e], edges[(i + 2) % n_e]
                if not P.parallel(a.d, b.d) or j.length > c["JOG_MAX"] \
                        or j.length < c["MIN_EDGE"]:
                    continue
                if not P.perpendicular(j.d, a.d, 0.05):
                    continue
                fr = self.face_frame(a)
                if fr is None:
                    continue
                fi, gi, off_a, s_lo, s_hi = fr
                off_b = self.m.offset(b.mid(), gi)
                if abs(off_a - off_b) < c["SAME_OFFSET_TOL"]:
                    continue
                sj = self.m.station(j.mid(), gi)
                out.append(Intent(fi, gi, [(off_a, a.ref, "slab edge"),
                                           (off_b, b.ref, "slab edge")],
                                  (sj - 2.0, sj + 2.0), "slab jog",
                                  owners=(slab.eid,), prefer=sj))
        return out

    # ---------------- openings ----------------
    def openings(self):
        """Each opening, per grid direction: ONE string
            anchor | edge | (steps) | edge | anchor
        where each anchor is the nearest grid - or the facing wall face, as
        in the elevator cores - on that side (Adolfo, 2026-10-01). Every
        outer edge sits next to an anchor, so nothing is located off
        another edge; the edge-to-edge segment is the size check. Small
        openings / no far anchor: anchor | edge | edge (one compact string),
        plus a separate dim for the far edge when the opening is large."""
        out = []
        c = self.c
        for slab in self.m.slabs:
            for loop, poly in zip(slab.open_edges, slab.openings):
                if not loop:
                    continue
                cx, cy = P.centroid(poly)
                if not self.in_crop((cx, cy)):
                    self.note("opening outside the view crop")
                    continue
                xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
                small = max(max(xs) - min(xs), max(ys) - min(ys)) <= c["SMALL_OPENING"]
                any_family = False
                for fi in range(len(self.m.families)):
                    par = [e for e in loop
                           if P.parallel(e.d, self.m.grid(self.m.families[fi][0])[2])
                           and e.length >= c["MIN_EDGE"]]
                    if not par:
                        continue
                    any_family = True
                    ng = self.m.nearest_grid((cx, cy), fi, c["MAX_DIST"])
                    if ng is None:
                        self.note("opening too far from any grid")
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
                    lo_off, hi_off = faces[0][0], faces[-1][0]
                    if len(faces) > 2 or hi_off - lo_off > c["BIG_OPENING"]:
                        # big / stepped void: locate each edge on its own,
                        # right beside it, from the nearest anchor (like a
                        # slab edge) - no long chained string
                        for off, e in faces:
                            if self.flush_member_face(e, self.m.walls, c["FLUSH_TOL"]):
                                self.note("opening edge on a wall face")
                                continue
                            t0, t1 = self.m.station(e.p0, gi), self.m.station(e.p1, gi)
                            e_lo, e_hi = min(t0, t1), max(t0, t1)
                            if not self.in_crop(e.mid()):
                                continue
                            cands = [a for a in (self.anchor(fi, gi, off, -1, e_lo, e_hi),
                                                 self.anchor(fi, gi, off, +1, e_lo, e_hi)) if a]
                            if not cands:
                                cands = [a for a in (self.anchor(fi, gi, off, -1, e_lo, e_hi, cap=c["MAX_DIST"], walls=False),
                                                     self.anchor(fi, gi, off, +1, e_lo, e_hi, cap=c["MAX_DIST"], walls=False)) if a]
                            if not cands:
                                self.note("opening too far from any grid")
                                continue
                            anc = min(cands, key=lambda a: abs(a[0] - off))
                            if abs(anc[0] - off) < c["ON_GRID_TOL"]:
                                self.note("opening edge on a grid")
                                continue
                            out.append(Intent(fi, gi, [anc, (off, e.ref, "opening edge")],
                                              (e_lo, e_hi), "opening edge -> anchor",
                                              prefer=(e_lo + e_hi) / 2.0))
                        continue
                    a_lo = self.anchor(fi, gi, lo_off, -1, s_lo, s_hi)
                    a_hi = self.anchor(fi, gi, hi_off, +1, s_lo, s_hi)
                    if a_lo is None and a_hi is None:
                        # nothing within LOC_MAX: nearest grid, however far
                        a_lo = self.anchor(fi, gi, lo_off, -1, s_lo, s_hi, cap=c["MAX_DIST"], walls=False)
                        a_hi = self.anchor(fi, gi, hi_off, +1, s_lo, s_hi, cap=c["MAX_DIST"], walls=False)
                        if a_lo and a_hi:
                            if abs(a_lo[0] - lo_off) <= abs(a_hi[0] - hi_off):
                                a_hi = None
                            else:
                                a_lo = None
                        self.note("opening located from a far grid (> LOC_MAX)")
                    refs = [(off, e.ref, "opening edge") for off, e in faces]
                    if a_lo is not None:
                        refs = [a_lo] + refs
                    if a_hi is not None:
                        refs = refs + [a_hi]
                    # place it on the side of the opening that faces away
                    # from its other-direction string (they never cross)
                    away = 1
                    other = None
                    for fj in range(len(self.m.families)):
                        if fj == fi:
                            continue
                        ngj = self.m.nearest_grid((cx, cy), fj, c["MAX_DIST"])
                        if ngj and (other is None or abs(ngj[1]) < abs(other[1])):
                            other = ngj
                    if other is not None:
                        st_g = self.m.station(self.m.grid(other[0])[1], gi)
                        away = 1 if st_g < self.m.station((cx, cy), gi) else -1
                    if away > 0:
                        span_l = (s_hi + c["OPEN_OFFSET"], s_hi + c["OPEN_OFFSET"] + 1.0)
                        pref_l = s_hi + c["OPEN_OFFSET"]
                    else:
                        span_l = (s_lo - c["OPEN_OFFSET"] - 1.0, s_lo - c["OPEN_OFFSET"])
                        pref_l = s_lo - c["OPEN_OFFSET"]
                    label = "opening (anchor|edges|anchor)" if (a_lo and a_hi) else "opening (anchor|edges)"
                    it = Intent(fi, gi, refs, span_l, label, prefer=pref_l,
                                outward=away, reach=12.0)
                    if away > 0:
                        it.alt = ((s_lo - c["OPEN_OFFSET"] - 1.0, s_lo - c["OPEN_OFFSET"]),
                                  s_lo - c["OPEN_OFFSET"], -1)
                    else:
                        it.alt = ((s_hi + c["OPEN_OFFSET"], s_hi + c["OPEN_OFFSET"] + 1.0),
                                  s_hi + c["OPEN_OFFSET"], 1)
                    out.append(it)
                    # one-sided, large opening: the far edge also gets its own
                    # dim off the same anchor (never located off the near edge)
                    if not (a_lo and a_hi) and not small and len(faces) >= 2:
                        anc = a_lo or a_hi
                        far = faces[-1] if a_lo else faces[0]
                        if anc is not None:
                            pref2 = pref_l + away * c.get("LANE_STEP", 1.75)
                            out.append(Intent(fi, gi, [anc, (far[0], far[1].ref, "opening edge")],
                                              (min(span_l[0], pref2), max(span_l[1], pref2)),
                                              "opening far edge -> anchor", prefer=pref2,
                                              outward=away, reach=12.0))
                if not any_family:
                    self.note("angled opening (no grid family)")
        return out

    # ---------------- beams ----------------
    def beams(self):
        out = []
        c = self.c
        for b in self.m.beams:
            if b.d is None:
                self.note("beam without a straight location line")
                continue
            fi = self.m.family_parallel(b.d)
            if fi is None:
                self.note("angled beam (no grid family)")
                continue
            if len(b.sides) < 2:
                self.note("beam without side faces")
                continue
            mid = ((b.p0[0] + b.p1[0]) / 2.0, (b.p0[1] + b.p1[1]) / 2.0)
            ng = self.m.nearest_grid(mid, fi, c["MAX_DIST"])
            if ng is None:
                self.note("beam too far from any grid")
                continue
            gi, goff = ng
            sides = sorted(b.sides, key=lambda f: self.m.offset(f.mid(), gi))
            near, far = sides[0], sides[-1]
            o_near, o_far = self.m.offset(near.mid(), gi), self.m.offset(far.mid(), gi)
            if abs(o_far - o_near) < c["SAME_OFFSET_TOL"]:
                continue
            s0, s1 = self.m.station(b.p0, gi), self.m.station(b.p1, gi)
            span = (min(s0, s1), max(s0, s1))
            gref = (0.0, DB.Reference(self.m.grid(gi)[0]), "grid")
            mid_in = self.in_crop(mid)
            if not mid_in:
                self.note("beam outside the view crop")
            elif o_near < -c["ON_GRID_TOL"] and o_far > c["ON_GRID_TOL"]:
                out.append(Intent(fi, gi, [(o_near, near.ref, "beam side"), gref,
                                           (o_far, far.ref, "beam side")],
                                  span, "beam side|grid|side", owners=(b.eid,)))
            else:
                # anchor | side | side | anchor - each side next to the
                # nearest grid (or facing wall) on its own side
                a_lo = self.anchor(fi, gi, o_near, -1, span[0], span[1])
                a_hi = self.anchor(fi, gi, o_far, +1, span[0], span[1])
                if a_lo is None and a_hi is None:
                    a_lo = (0.0, DB.Reference(self.m.grid(gi)[0]), "grid") \
                        if o_near > 0 else None
                    a_hi = (0.0, DB.Reference(self.m.grid(gi)[0]), "grid") \
                        if o_far < 0 else None
                    self.note("beam located from a far grid (> LOC_MAX)")
                refs = [(o_near, near.ref, "beam side"), (o_far, far.ref, "beam side")]
                if a_lo is not None:
                    refs = [a_lo] + refs
                if a_hi is not None:
                    refs = refs + [a_hi]
                out.append(Intent(fi, gi, refs, span,
                                  "beam (anchor|sides|anchor)" if (a_lo and a_hi) else "beam (anchor|sides)",
                                  owners=(b.eid,)))
            # free ends
            for end in b.ends:
                fj = self.m.family_parallel(end.d)
                if fj is None:
                    continue
                em = end.mid()
                if not self.in_crop(em):
                    self.note("beam end outside the view crop")
                    continue
                # end buried in a column / wall: nothing to locate
                probe = (em[0] + b.d[0] * 0.25, em[1] + b.d[1] * 0.25)
                probe2 = (em[0] - b.d[0] * 0.25, em[1] - b.d[1] * 0.25)
                hit = self.m.member_at(probe[0], probe[1]) or \
                    self.m.member_at(probe2[0], probe2[1])
                if hit is not None and hit.eid != b.eid:
                    self.note("beam end framed into column/wall")
                    continue
                ng2 = self.m.nearest_grid(em, fj, c["MAX_DIST"])
                if ng2 is None:
                    continue
                gj, eoff = ng2
                if abs(eoff) < c["ON_GRID_TOL"]:
                    continue
                t0, t1 = self.m.station(end.p0, gj), self.m.station(end.p1, gj)
                # Adolfo: locate beam ends off a grid, not off a nearby
                # column face (BEAM_END_TO_COLUMN restores the old way)
                cf = self.near_member_face(end, self.m.columns, c["COL_REACH"], gj) \
                    if c.get("BEAM_END_TO_COLUMN") else None
                if cf is not None:
                    refs = [(cf[1], cf[0].ref, "column face"),
                            (eoff, end.ref, "beam end")]
                    label = "beam end -> column"
                else:
                    refs = [(0.0, DB.Reference(self.m.grid(gj)[0]), "grid"),
                            (eoff, end.ref, "beam end")]
                    label = "beam end -> grid"
                out.append(Intent(fj, gj, refs, (min(t0, t1), max(t0, t1)),
                                  label, owners=(b.eid,)))
        return out

    # ---------------- walls ----------------
    def walls(self):
        out = []
        c = self.c
        for w in self.m.walls:
            if w.d is None or len(w.sides) < 2:
                self.note("wall without straight sides")
                continue
            fi = self.m.family_parallel(w.d)
            if fi is None:
                self.note("angled wall (no grid family)")
                continue
            mid = ((w.p0[0] + w.p1[0]) / 2.0, (w.p0[1] + w.p1[1]) / 2.0)
            ng = self.m.nearest_grid(mid, fi, c["MAX_DIST"])
            if ng is None:
                self.note("wall too far from any grid")
                continue
            gi, goff = ng
            sides = sorted(w.sides, key=lambda f: self.m.offset(f.mid(), gi))
            near, far = sides[0], sides[-1]
            o_near, o_far = self.m.offset(near.mid(), gi), self.m.offset(far.mid(), gi)
            s0, s1 = self.m.station(w.p0, gi), self.m.station(w.p1, gi)
            span = (min(s0, s1), max(s0, s1))
            gref = (0.0, DB.Reference(self.m.grid(gi)[0]), "grid")
            if o_near < -c["ON_GRID_TOL"] and o_far > c["ON_GRID_TOL"]:
                out.append(Intent(fi, gi, [(o_near, near.ref, "wall face"), gref,
                                           (o_far, far.ref, "wall face")],
                                  span, "wall face|grid|face", owners=(w.eid,)))
            else:
                nearest, o_n = (near, o_near) if abs(o_near) <= abs(o_far) \
                    else (far, o_far)
                if abs(o_n) < c["ON_GRID_TOL"]:
                    self.note("wall face on a grid")
                    continue
                out.append(Intent(fi, gi, [gref, (o_n, nearest.ref, "wall face")],
                                  span, "wall face -> grid", owners=(w.eid,)))
        return out

    # ---------------- CJ lines ----------------
    def cjs(self):
        out = []
        c = self.c
        for cj in self.m.cjs:
            fi = self.m.family_parallel(cj.d)
            if fi is None:
                self.note("angled CJ line")
                continue
            mid = ((cj.p0[0] + cj.p1[0]) / 2.0, (cj.p0[1] + cj.p1[1]) / 2.0)
            if not self.in_crop(mid):
                continue
            ng = self.m.nearest_grid(mid, fi, c["MAX_DIST"])
            if ng is None:
                continue
            gi, off = ng
            if abs(off) < c["ON_GRID_TOL"]:
                self.note("CJ on a grid")
                continue
            s0, s1 = self.m.station(cj.p0, gi), self.m.station(cj.p1, gi)
            out.append(Intent(fi, gi, [(0.0, DB.Reference(self.m.grid(gi)[0]), "grid"),
                                       (off, cj.ref, "cj")],
                              (min(s0, s1), max(s0, s1)), "CJ -> grid"))
        return out
