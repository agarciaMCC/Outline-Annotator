# -*- coding: utf-8 -*-
"""PLACE: turn dimension intents into Revit dimensions.

An Intent says WHAT to dimension (references, measured across grid family
fi) and WHERE it would like to sit (a home station range along the grids,
a preferred station). The Placer finds a clear station near that, keeps
strings from stacking or crossing, creates the dimension, pulls short text
off the line, and journals the ids so a rerun can replace them."""
from mcc_compat import eid_int, make_eid
import json
from pyrevit import DB, script
import mcc_plan as P


class Intent(object):
    def __init__(self, fi, gi_ref, refs, span, label, owners=(),
                 prefer=None, reach=15.0, outward=None):
        self.fi = fi                # family measured across
        self.gi = gi_ref            # grid whose frame (u, n) we use
        self.refs = refs            # [(offset along n, DB.Reference, kind)]
        self.span = span            # (s_lo, s_hi) stations along u where
                                    # witness lines are short
        self.label = label
        self.owners = set(owners)   # element ids that are not obstacles
        self.prefer = prefer        # preferred station (default: mid span)
        self.reach = reach          # ft past the span we may search
        self.outward = outward      # +1/-1 sign along u to prefer, or None
        self.alt = None             # (span, prefer, outward) to try when the
                                    # first side has no room in the crop


class Placer(object):
    def __init__(self, model, config):
        self.m = model
        self.c = config
        self.placed = []            # (fi, station_f, lo_f, hi_f, seg)
        self.count = {}
        self.skipped = {}
        self.pulled = 0
        self.failed = 0
        self.errors = []
        # dims must land inside the annotation crop or Revit hides them
        self.crop = view_crop_poly(model.view)
        self.crop_margin = config.get("CROP_MARGIN", 1.0)

    # ---------------- frames ----------------
    def frame(self, gi):
        return self.m.grids[gi]

    def world(self, gi, s, off):
        g, g0, u, n = self.m.grids[gi]
        return (g0[0] + u[0] * s + n[0] * off, g0[1] + u[1] * s + n[1] * off)

    def to_fam(self, gi, s, off):
        """(station, offset) in the family's reference-grid frame."""
        p = self.world(gi, s, off)
        gr = self.m.families[self.m.fam_of[gi]][0]
        return self.m.station(p, gr), self.m.offset(p, gr)

    # ---------------- conflict tests ----------------
    def conflicts(self, it, s, lo, hi):
        """0 = clear; >0 = soft penalty; None = blocked."""
        c = self.c
        p = self.world(it.gi, s, lo - 0.5)
        q = self.world(it.gi, s, hi + 0.5)
        g, g0, u, n = self.m.grids[it.gi]
        # a grid of another family running roughly ALONG our dim line and
        # close to it would sit under the text: keep clear of it
        mid = self.world(it.gi, s, (lo + hi) / 2.0)
        for gj, (g2, g20, u2, n2) in enumerate(self.m.grids):
            if self.m.fam_of[gj] == it.fi:
                continue
            if not P.parallel(u2, n, 0.35):
                continue
            dist = (mid[0] - g20[0]) * n2[0] + (mid[1] - g20[1]) * n2[1]
            if abs(dist) < c["GRID_CLEAR"]:
                return None
        penalty = 0.0
        # placed strings: same direction, too close and overlapping -> block;
        # crossing -> block
        sf, a = self.to_fam(it.gi, s, lo)
        _, b = self.to_fam(it.gi, s, hi)
        a, b = min(a, b), max(a, b)
        for fi, st, lo_f, hi_f, seg in self.placed:
            if fi == it.fi:
                # too close AND overlapping by more than a shared witness
                if abs(st - sf) < c["STATION_GAP"] and \
                        not (b <= lo_f + 0.1 or a >= hi_f - 0.1):
                    return None
            else:
                if P.seg_intersect(p, q, seg[0], seg[1]):
                    return None
        # obstacles
        for o in self.m.obstacles:
            if o.eid in it.owners:
                continue
            rc = o.rect
            if max(p[0], q[0]) < rc[0] or min(p[0], q[0]) > rc[2] or \
                    max(p[1], q[1]) < rc[1] or min(p[1], q[1]) > rc[3]:
                continue
            if P.seg_hits_poly(p, q, o.poly):
                if o.kind == "beam" and c["BEAMS_SOFT"]:
                    penalty += c["SOFT_PENALTY"]
                else:
                    return None
        return penalty

    # ---------------- station search ----------------
    def find_station(self, it, lo, hi):
        c = self.c
        s_lo, s_hi = it.span
        prefer = it.prefer if it.prefer is not None else (s_lo + s_hi) / 2.0
        step = c["STEP"]
        best = None
        k = 0
        limit = (s_hi - s_lo) / 2.0 + it.reach
        while k * step <= limit:
            for sgn in ((1, -1) if k else (1,)):
                s = prefer + sgn * k * step
                if s < s_lo - it.reach or s > s_hi + it.reach:
                    continue
                if not self.in_crop(it.gi, s, lo, hi):
                    continue
                pen = self.conflicts(it, s, lo, hi)
                if pen is None:
                    continue
                outside = max(0.0, s_lo - s, s - s_hi)
                score = abs(s - prefer) + pen + outside * c["OUTSIDE_W"]
                if it.outward is not None and sgn != it.outward and k:
                    score += c["OUTWARD_W"]
                if best is None or score < best[0]:
                    best = (score, s)
            if best is not None and best[0] <= k * step:
                break               # nothing farther can beat it
            k += 1
        return best[1] if best else None

    # ---------------- crop ----------------
    def in_crop(self, gi, s, lo, hi):
        if not self.crop:
            return True
        m = self.crop_margin
        for off in (lo, hi):
            x, y = self.world(gi, s, off)
            for dx, dy in ((0, 0), (m, 0), (-m, 0), (0, m), (0, -m)):
                if not _pip(x + dx, y + dy, self.crop):
                    return False
        return True

    def any_station_in_crop(self, it, lo, hi):
        """Nearest station to the preferred one that fits the crop,
        ignoring conflicts (last resort before skipping)."""
        s_lo, s_hi = it.span
        prefer = it.prefer if it.prefer is not None else (s_lo + s_hi) / 2.0
        step = self.c["STEP"]
        k = 0
        while k * step <= (s_hi - s_lo) / 2.0 + it.reach:
            for sgn in ((1, -1) if k else (1,)):
                s = prefer + sgn * k * step
                if s_lo - it.reach <= s <= s_hi + it.reach and \
                        self.in_crop(it.gi, s, lo, hi):
                    return s
            k += 1
        return None

    # ---------------- create ----------------
    def place(self, it, dim_type, z, transaction_open=True):
        refs = sorted(it.refs, key=lambda t: t[0])
        offs = [r[0] for r in refs]
        lo, hi = min(offs), max(offs)
        if hi - lo < self.c["MIN_VALUE"]:
            self._skip("zero length")
            return None
        s = self.find_station(it, lo, hi)
        over = False
        if s is None:
            s = it.prefer if it.prefer is not None else sum(it.span) / 2.0
            over = True
            if not self.in_crop(it.gi, s, lo, hi):
                s = self.any_station_in_crop(it, lo, hi)
                if s is None and it.alt is not None:
                    # other side of the object
                    it.span, it.prefer, it.outward = it.alt
                    it.alt = None
                    s = self.find_station(it, lo, hi)
                    if s is None:
                        s = self.any_station_in_crop(it, lo, hi)
                    else:
                        over = False
                if s is None:
                    self._skip("no room inside the view crop")
                    return None
        p = self.world(it.gi, s, lo)
        q = self.world(it.gi, s, hi)
        line = DB.Line.CreateBound(DB.XYZ(p[0], p[1], z), DB.XYZ(q[0], q[1], z))
        ra = DB.ReferenceArray()
        for off, ref, kind in refs:
            ra.Append(ref)
        try:
            if dim_type is not None:
                dim = self.m.doc.Create.NewDimension(self.m.view, line, ra,
                                                     dim_type)
            else:
                dim = self.m.doc.Create.NewDimension(self.m.view, line, ra)
        except Exception as ex:
            self.failed += 1
            self.errors.append("{}: {}".format(it.label, ex))
            return None
        if dim is None:
            self.failed += 1
            return None
        sf, a = self.to_fam(it.gi, s, lo)
        _, b = self.to_fam(it.gi, s, hi)
        self.placed.append((it.fi, sf, min(a, b), max(a, b), (p, q)))
        self.count[it.label] = self.count.get(it.label, 0) + 1
        if over:
            self._skip("placed over obstacle")
        if self.c["PULL_TEXT"]:
            try:
                self.m.doc.Regenerate()
                g, g0, u, n = self.m.grids[it.gi]
                self.pulled += pull_short_text(
                    self.m.doc, self.m.view, dim, DB.XYZ(u[0], u[1], 0),
                    DB.XYZ(n[0], n[1], 0), self.c, self.errors)
            except Exception as ex:
                self.errors.append("pull: {}".format(ex))
        return dim

    def _skip(self, key):
        self.skipped[key] = self.skipped.get(key, 0) + 1


# ---------------- view crop ----------------
def view_crop_poly(view):
    """Plan polygon of the region where annotations show (crop shape or
    box) when the view crops annotations; None when they aren't cropped."""
    try:
        if not view.CropBoxActive:
            return None
        p = view.get_Parameter(DB.BuiltInParameter.VIEWER_ANNOTATION_CROP_ACTIVE)
        if p is None or p.AsInteger() != 1:
            return None
        sm = view.GetCropRegionShapeManager()
        if sm.ShapeSet:
            loop = sm.GetCropShape()[0]
            return [(c.GetEndPoint(0).X, c.GetEndPoint(0).Y) for c in loop]
        bb = view.CropBox
        tr = bb.Transform
        pts = [tr.OfPoint(DB.XYZ(x, y, 0)) for x, y in
               ((bb.Min.X, bb.Min.Y), (bb.Max.X, bb.Min.Y),
                (bb.Max.X, bb.Max.Y), (bb.Min.X, bb.Max.Y))]
        return [(q.X, q.Y) for q in pts]
    except Exception:
        return None


def _pip(x, y, poly):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and \
                x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            c = not c
        j = i
    return c


# ---------------- journal (rerun cleanup) ----------------
def journal_path():
    return script.get_document_data_file("mcc_autodims", "json")


def journal_load():
    try:
        with open(journal_path(), "r") as fh:
            return json.load(fh)
    except Exception:
        return {}


def journal_save(data):
    try:
        with open(journal_path(), "w") as fh:
            json.dump(data, fh)
    except Exception:
        pass


def previous_ids(doc, view):
    data = journal_load()
    ids = data.get(str(eid_int(view.Id)), [])
    out = []
    for i in ids:
        e = doc.GetElement(make_eid(i))
        if isinstance(e, DB.Dimension):
            out.append(e.Id)
    return out


def remember(view, dims):
    data = journal_load()
    data[str(eid_int(view.Id))] = [eid_int(d.Id) for d in dims]
    journal_save(data)


# ---------------- text pull-out ----------------
_CW = {"'": 0.16, '"': 0.29, "-": 0.27, "/": 0.23, " ": 0.23, ".": 0.23,
       "1": 0.46}
TEXT_EM = 1.40


def text_size_ft(dtype):
    p = dtype.get_Parameter(DB.BuiltInParameter.TEXT_SIZE) if dtype else None
    return p.AsDouble() if p else 3.0 / 32 / 12


def text_width(txt, tsize, wf=1.0):
    em = tsize * TEXT_EM * wf
    if not txt:
        return 4 * 0.46 * em
    return sum(_CW.get(ch, 0.46) for ch in txt) * em


def pull_short_text(doc, view, dim, dline, outward, c, errors):
    """Move text of segments narrower than the text out past the end of
    the string with a leader (Revit only honours a leader once the text is
    displaced: nudge, leader on, then final spot)."""
    dtype_ = doc.GetElement(dim.GetTypeId())
    tsize = text_size_ft(dtype_) * view.Scale
    wf = 1.0
    try:
        p = dtype_.get_Parameter(DB.BuiltInParameter.TEXT_WIDTH_SCALE)
        wf = p.AsDouble() if p and p.AsDouble() > 0 else 1.0
    except Exception:
        pass
    segs = list(dim.Segments) if dim.NumberOfSegments > 1 else [dim]
    items = []
    for sg in segs:
        try:
            val = sg.Value
            pos = sg.TextPosition
            txt = sg.ValueString or ""
        except Exception:
            continue
        if val is None:
            continue
        width = text_width(txt, tsize, wf)
        along = pos.X * dline.X + pos.Y * dline.Y
        items.append((along, sg, val, width, pos))
    items.sort(key=lambda t: t[0])

    def fits(v, w):
        return v >= w + c["TEXT_FIT_MARGIN"] * tsize
    short = [it for it in items if not fits(it[2], it[3])]
    if not short:
        return 0
    occupied = {0: [(a - w / 2.0, a + w / 2.0) for a, sg, v, w, p in items
                    if fits(v, w)]}
    pulled = 0
    row_h = 1.4 * tsize
    s_lo = items[0][0] - items[0][2] / 2.0
    s_hi = items[-1][0] + items[-1][2] / 2.0
    s_mid = (s_lo + s_hi) / 2.0
    for along, sg, val, width, pos in short:
        try:
            sg.TextPosition = DB.XYZ(pos.X + dline.X * 0.05,
                                     pos.Y + dline.Y * 0.05, pos.Z)
        except Exception as ex:
            errors.append("nudge: {}".format(ex))
            continue
        try:
            if not dim.HasLeader:
                dim.HasLeader = True
        except Exception as ex:
            errors.append("HasLeader: {}".format(ex))
        pref = 1 if along >= s_mid else -1
        placed = False
        for side in (pref, -pref):
            e = s_hi if side > 0 else s_lo
            centre = e + side * (width / 2.0 + 0.5 * tsize)
            for k in range(4):
                lo, hi = centre - width / 2.0, centre + width / 2.0
                if any(not (hi < a or lo > b)
                       for a, b in occupied.get(k + 1, [])):
                    continue
                d = c["TEXT_PULL"] * tsize + k * row_h
                try:
                    sg.TextPosition = DB.XYZ(
                        pos.X + dline.X * (centre - along) + outward.X * d,
                        pos.Y + dline.Y * (centre - along) + outward.Y * d,
                        pos.Z)
                except Exception as ex:
                    errors.append("set: {}".format(ex))
                    placed = True
                    break
                occupied.setdefault(k + 1, []).append((lo, hi))
                pulled += 1
                placed = True
                break
            if placed:
                break
    return pulled



# ---------------- warnings (no dialogs) ----------------
class WarningLog(DB.IFailuresPreprocessor):
    """Collects Revit warnings at commit and dismisses them, so no dialog
    stops the run. Errors are left to Revit (it rolls back / resolves)."""
    def __init__(self):
        self.messages = []

    def PreprocessFailures(self, fa):
        resolved = False
        for f in list(fa.GetFailureMessages()):
            try:
                self.messages.append(f.GetDescriptionText())
            except Exception:
                self.messages.append("?")
            sev = f.GetSeverity()
            if sev == DB.FailureSeverity.Warning:
                fa.DeleteWarning(f)
            elif f.HasResolutions():
                # e.g. "dimension reference removed" - take Revit's default
                # fix (delete the dim) instead of showing a dialog
                fa.ResolveFailure(f)
                resolved = True
        if resolved:
            return DB.FailureProcessingResult.ProceedWithCommit
        return DB.FailureProcessingResult.Continue


def transaction_with_log(doc, name):
    """-> (started DB.Transaction, WarningLog). Caller commits."""
    t = DB.Transaction(doc, name)
    log = WarningLog()
    opts = t.GetFailureHandlingOptions()
    opts.SetFailuresPreprocessor(log)
    opts.SetClearAfterRollback(True)
    t.SetFailureHandlingOptions(opts)
    t.Start()
    return t, log



# ---------------- de-duplication (before placing) ----------------
# Different elements often share one plane (slab pieces meeting at a joint,
# an opening edge on a slab jog, two floors stacked at an edge). Their
# references are distinct, so the passes produce dims that read identically.
REF_RANK = {"grid": 0, "beam side": 1, "beam end": 1, "wall face": 2, "column face": 3,
            "cj": 4}                    # lower = keep this ref when coincident
LABEL_RANK = ("beam", "wall", "cj", "column", "opening", "slab")


def _label_rank(label):
    l = (label or "").lower()
    for i, k in enumerate(LABEL_RANK):
        if k in l:
            return i
    return len(LABEL_RANK)


def dedupe(intents, tol=1.0 / 24, slack=2.0, notes=None, base=None, merge_tol=0.4 / 12):
    """Collapse coincident witness lines inside each intent, then drop
    intents that repeat an earlier one (same family, same witness offsets,
    overlapping span). Returns the kept intents in their original order.
    base(intent) -> offset of the intent's grid in the family frame, so
    strings anchored to different grids of one family still compare."""
    def bump(k):
        if notes is not None:
            notes[k] = notes.get(k, 0) + 1
    clean = []
    for it in intents:
        refs = sorted(it.refs, key=lambda r: (r[0], REF_RANK.get(r[2], 9)))
        out = []
        for r in refs:
            # 0.4": a 1/2" face off a grid is a real dim (L7 core#48, Adolfo
            # added it back in both rounds; a 1/2" tolerance merged it into the
            # grid). 1/8" was tried: it made a 3/8" bump-top dim off A on L3N
            # that he never drew
            if out and abs(r[0] - out[-1][0]) <= merge_tol:
                if REF_RANK.get(r[2], 9) < REF_RANK.get(out[-1][2], 9):
                    out[-1] = r
                bump("coincident witness line merged")
                continue
            out.append(r)
        if len(out) < 2:
            bump("dim collapsed to one witness line (dropped)")
            continue
        it.refs = out
        clean.append(it)
    kept = []
    for it in clean:
        b_it, s_it = base(it) if base else (0.0, 0.0)
        offs = [r[0] + b_it for r in it.refs]
        dup = None
        swallowed = []
        for j, k in enumerate(kept):
            if k is None or k.fi != it.fi:
                continue
            b_k, s_k = base(k) if base else (0.0, 0.0)
            koffs = [r[0] + b_k for r in k.refs]
            (a0, a1), (b0, b1) = sorted(k.span), sorted(it.span)
            a0, a1, b0, b1 = a0 + s_k, a1 + s_k, b0 + s_it, b1 + s_it
            if not (a0 - slack <= b1 and b0 - slack <= a1):
                continue
            if _contains(koffs, offs, tol):
                dup = j
                break
            if _contains(offs, koffs, tol):
                swallowed.append(j)         # the new string covers this one
        if dup is None:
            for j in swallowed:
                bump("duplicate dim (witness lines inside a longer string) dropped")
                kept[j] = None
            kept.append(it)
            continue
        if len(kept[dup].refs) == len(offs):
            bump("duplicate dim (same witness lines) dropped")
            if _label_rank(it.label) < _label_rank(kept[dup].label):
                kept[dup] = it              # keep the more meaningful one
        else:
            bump("duplicate dim (witness lines inside a longer string) dropped")
    return [k for k in kept if k is not None]


def _contains(big, small, tol):
    """Every witness line of `small` is in `big`, and consecutive lines of
    `small` are consecutive in `big` (so `big` shows the same segments)."""
    if len(small) > len(big):
        return False
    idx = []
    for v in small:
        hits = [i for i, w in enumerate(big) if abs(w - v) <= tol]
        if not hits:
            return False
        idx.append(hits[0])
    return all(b - a == 1 for a, b in zip(idx, idx[1:]))
