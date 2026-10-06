"""Inventory past McClone outline sets for training the outline annotator.

Reads (never writes) Z:\\Shared\\MCC Shared\\Archives\\Project Folders\\<job> <name>\\CONTRACT DOCS\\MCC Drawings,
jobs 1038 and newer. Uses the Outlines subfolder when there is one, otherwise the whole MCC Drawings folder
(a few jobs split it by building). Writes one row per PDF page to inventory.csv with the words that tell what
the sheet is, so classify.py can pick out the soffit plans.

CPython 3 + PyMuPDF.  Run:  python inventory.py   (re-run picks up where it stopped)
"""
import csv
import multiprocessing
import os
import re
import sys

import pymupdf

ROOT = r"Z:\Shared\MCC Shared\Archives\Project Folders"
MIN_JOB = 1038
MAX_JOB = 6999          # 7400 - Yard is not a job
WORKERS = 8           # jobs scanned at once (the share is the bottleneck)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "inventory.csv")
FIELDS = ["job", "project", "pdf", "size_kb", "mtime", "page", "pages", "w_in", "h_in", "tb_sheet", "tb_title", "keywords", "error"]
KEY = re.compile(r"SOFFIT|OUTLINE|TOP OF SLAB|\bTOS\b|FALSEWORK|RESHOR|SHORING|SECTION|DETAIL|ELEVATION|"
                 r"ENLARGED|PLAN|WALL|COLUMN|STAIR|RAMP|\b\d{1,2}\.[A-Z0-9]{1,3}(\.\d+){1,2}\b")
SKIP_DIRS = re.compile(r"archive|supersede|\bold\b|\bvoid", re.I)


def project_dirs():
    for name in sorted(os.listdir(ROOT)):
        m = re.match(r"(\d{4})", name)
        if not m or not (MIN_JOB <= int(m.group(1)) <= MAX_JOB):
            continue
        mcc = os.path.join(ROOT, name, "CONTRACT DOCS", "MCC Drawings")
        if not os.path.isdir(mcc):
            continue
        outl = os.path.join(mcc, "Outlines")
        yield m.group(1), name, (outl if os.path.isdir(outl) else mcc)


SHEET_NO = re.compile(r"^\d{1,2}\.(?:[A-Z]{1,2}\d{0,2}|\d{1,2})(\.\d+){0,3}[A-Z]?$")


def read_page(page):
    """(keywords, title-block big text, sheet number).  The McClone title block is the strip along the right
    edge of the sheet as viewed (lines ending past 95 % of the width); its big lines are the sheet title, project name and sheet number."""
    lines, big, nums = [], [], []
    m, vw = page.rotation_matrix, page.rect.width      # page.rect is already the as-viewed size
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            t = " ".join(" ".join(s["text"] for s in l["spans"]).split()).upper()
            if not t:
                continue
            if 3 <= len(t) <= 90 and KEY.search(t) and t not in lines:
                lines.append(t)
            sz = max(s["size"] for s in l["spans"])
            r = pymupdf.Rect(l["bbox"]) * m
            if r.x0 > 0.85 * vw and r.x1 > 0.95 * vw and sz >= 14:
                if SHEET_NO.match(t):
                    nums.append((sz, t))
                elif t not in big:
                    big.append(t)
    sheet = max(nums)[1] if nums else ""
    return " | ".join(lines[:60]), " | ".join(big[:8]), sheet


def scan_project(args):
    """All page rows for one job (runs in a worker process)."""
    job, name, base, done = args
    rows = []
    for dp, dns, fns in os.walk(base):
        dns[:] = [d for d in dns if not SKIP_DIRS.search(d)]
        for fn in fns:
            p = os.path.join(dp, fn)
            if not fn.lower().endswith(".pdf") or p in done:
                continue
            st = os.stat(p)
            row = dict(job=job, project=name, pdf=p, size_kb=st.st_size // 1024, mtime=int(st.st_mtime))
            try:
                doc = pymupdf.open(p)
                for i, pg in enumerate(doc):
                    kw, tb, sh = read_page(pg)
                    rows.append(dict(row, page=i + 1, pages=doc.page_count, w_in=round(pg.rect.width / 72, 1),
                                     h_in=round(pg.rect.height / 72, 1), tb_sheet=sh, tb_title=tb, keywords=kw,
                                     error=""))
                doc.close()
            except Exception as e:  # noqa: BLE001 - log and keep going
                rows.append(dict(row, page=0, pages=0, error=str(e)[:200]))
    return name, rows


def main():
    pymupdf.TOOLS.mupdf_display_errors(False)
    done = set()
    if os.path.exists(OUT):
        with open(OUT, newline="", encoding="utf-8") as f:
            done = {r["pdf"] for r in csv.DictReader(f)}
    new = not os.path.exists(OUT)
    jobs = [(j, n, b, done) for j, n, b in project_dirs()]
    with open(OUT, "a", newline="", encoding="utf-8") as f, multiprocessing.Pool(WORKERS) as pool:
        w = csv.DictWriter(f, FIELDS)
        if new:
            w.writeheader()
        for name, rows in pool.imap_unordered(scan_project, jobs):
            w.writerows(rows)      # a job is written whole, so a re-run after a stop never half-repeats one
            f.flush()
            print("%s  %d pdfs" % (name, len({r["pdf"] for r in rows})))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
