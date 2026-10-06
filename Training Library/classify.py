"""Pick the soffit plans out of inventory.csv and copy them into Soffit Plans/<job project>/, one page per PDF.

A page is a soffit plan when its title block names it: SOFFIT ... PLAN / OUTLINE / VIEW
("LEVEL 3 NORTH - SOFFIT PLAN VIEW", "LEVEL 6-7 SOFFIT PLAN & DETAILS", "SLAB ELEVATION PLAN (SOFFIT)").
Falsework, reshore, shoring and insert sheets are left out.  Sheets titled by level only ("LEVEL 2 - PLAN VIEW")
are not kept (Adolfo, 2026-10-06).
Pages without a readable title block fall back to the view titles on the drawing, and
one-page scans with no text to the file name.  Pages of scanned sets are listed as "scanned set - check".
Enlarged plans (5.X sheets, ENLARGED / PARTIAL in the title) are kept and marked kind=enlarged.

Writes soffit_index.csv (every page found, newest clean issue of each sheet marked latest=1) and copies only the
latest issue of each sheet.  Sources on Z: are only read.

CPython 3 + PyMuPDF.  Run after inventory.py:  python classify.py  [--no-copy]
"""
import csv
import os
import re
import shutil
import sys

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
INV = os.path.join(HERE, "inventory.csv")
OUT = os.path.join(HERE, "soffit_index.csv")
DEST = os.path.join(HERE, "Soffit Plans")

NOT_SOFFIT = re.compile(r"FALSEWORK|RESHOR|SHORING|SHORE|INSERT|DECK PLACEMENT|POUR ?BACK|SECTION AT|"
                        r"\bFW\b|\bRS\b|\dFW|\dRS", re.I)
SOFFIT_TITLE = re.compile(r"SOFFIT.{0,12}(PLAN|OUTLINE|VIEW)|PLAN.{0,4}\(SOFFIT\)|OUTLINE PLAN", re.I)
NOT_FILE = re.compile(r"FALSEWORK|RESHOR|SHOR|INSERT|POUR ?BACK|\bFW\b|\bRS\b|\dFW|\dRS|FOUNDATION|"
                      r"SECTION|ELEVATION|TOP OF SLAB|\bTOS\b|SAW[- ]?CUT|SEQUENCE", re.I)
MARKUP = re.compile(r"MARK ?UP|\bRFI\b|\bCM\b|COMMENT|REDLINE|RETURNED", re.I)
SHEET_NO = re.compile(r"(?<![\d.])(\d{1,2}\.(?:[A-Z]{1,2}\d{0,2}|\d{1,2})(?:\.\d+){0,3})(?![\d])")


def soffit_title(text):
    """First title line naming a soffit plan; a title wrapped onto two lines ("SLAB ELEVATION PLAN" /
    "(SOFFIT)") is read as one."""
    lines = text.split(" | ")
    for cand in lines + [a + " " + b for a, b in zip(lines, lines[1:])]:
        if SOFFIT_TITLE.search(cand) and not NOT_SOFFIT.search(cand):
            return cand
    return ""


def classify(row):
    """Title block first; if the page has no readable title block, the view titles in the drawing; if it has
    no text at all (scan), the file name."""
    fn = os.path.basename(row["pdf"])
    sheet = row["tb_sheet"]
    if row["tb_title"]:
        title, src = soffit_title(row["tb_title"]), "title block"
    elif row["keywords"].strip():
        title, src = soffit_title(row["keywords"]), "view title"
    elif re.search(r"soffit|outline", fn, re.I) and not NOT_FILE.search(fn):
        # scan with no text: trust the file name only for a one-page PDF; pages of a scanned set need a look
        title = os.path.splitext(fn)[0]
        src = "file name" if row["pages"] == "1" else "scanned set - check"
    else:
        title = ""
    if not title:
        return None
    if not sheet:
        m = SHEET_NO.search(fn)
        sheet = m.group(1) if m else ""
    enlarged = bool(re.search(r"ENLARGED|PARTIAL", title, re.I)) or sheet.startswith("5.")
    return dict(job=row["job"], project=row["project"], sheet=sheet, title=title,
                kind="enlarged" if enlarged else "plan", found_by=src, pdf=row["pdf"], page=row["page"],
                pages=row["pages"], w_in=row["w_in"], h_in=row["h_in"], mtime=row["mtime"],
                markup=int(bool(MARKUP.search(row["pdf"]))),
                key=sheet or row["tb_title"] or title)    # same sheet across files / issues


def safe(s):
    return re.sub(r'[<>:"/\\|?*]+', "-", s).strip(" .")[:120]


def main():
    copy = "--no-copy" not in sys.argv
    with open(INV, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["page"] not in ("", "0")]
    hits = [h for h in (classify(r) for r in rows) if h]

    # newest clean issue of each sheet per job (no sheet number: the whole title block text); markups and RFI
    # sketches only when nothing else has that sheet; pages of scanned sets are never picked
    best = {}
    rank = lambda h: (-h["markup"], int(h["mtime"]))  # noqa: E731
    for h in hits:
        if h["found_by"] == "scanned set - check":
            continue
        key = (h["job"], h["key"])
        if key not in best or rank(h) > rank(best[key]):
            best[key] = h
    for h in hits:
        h["latest"] = int(best.get((h["job"], h["key"])) is h)
        h["copied_to"] = ""

    if copy:
        used = set()
        for h in hits:
            if not h["latest"]:
                continue
            d = os.path.join(DEST, safe(h["project"]))
            os.makedirs(d, exist_ok=True)
            stem = safe("%s %s" % (h["sheet"], h["title"]) if h["sheet"] else h["title"])
            out, n = os.path.join(d, stem + ".pdf"), 1
            while out.lower() in used:                 # two sheets with the same title and no sheet number
                n += 1
                out = os.path.join(d, "%s (%d).pdf" % (stem, n))
            used.add(out.lower())
            if not os.path.exists(out):
                if h["pages"] == "1":
                    shutil.copy2(h["pdf"], out)
                else:
                    src, one = pymupdf.open(h["pdf"]), pymupdf.open()
                    one.insert_pdf(src, from_page=int(h["page"]) - 1, to_page=int(h["page"]) - 1)
                    one.save(out, garbage=3, deflate=True)
                    one.close()
                    src.close()
            h["copied_to"] = os.path.relpath(out, HERE)

    fields = ["job", "project", "sheet", "title", "kind", "found_by", "markup", "latest", "pdf", "page",
              "pages", "w_in", "h_in", "mtime", "copied_to"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(hits, key=lambda h: (h["job"], h["sheet"], h["title"])))
    jobs = {h["job"] for h in hits}
    print("%d soffit pages (%d latest) in %d jobs; %d pages scanned"
          % (len(hits), sum(h["latest"] for h in hits), len(jobs), len(rows)))


if __name__ == "__main__":
    main()
