"""Draw what the schedule reader understood on top of a column schedule PDF.

    python schedule_check.py SCHEDULE.pdf OUT.pdf

Red box + text = the size read for that mark at that level ('5 18x32' = level 5,
18x32); blue box = empty (continues from below) or gray (no column). Lets you
check a schedule reading against the sheet at a glance.
"""
import os, sys
import pymupdf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', 'MCC.extension', 'MCC.tab', 'Setup.panel',
                                                 'Columns from PDF.pushbutton', 'pdfcols')))
import schedule as S   # noqa: E402


def check(path, out):
    d = pymupdf.open(path)
    for p in d:
        IM = p.derotation_matrix
        for t in S.parse_schedule_page(p):
            if t['kind'] == 'list':
                continue
            tr = t['kind'] == 'transposed'
            for key, ya, yb in t['bands']:
                k0 = S.expand_range(key)[0]
                for mk, x in t['marks'].items():
                    c = t['table'].get((mk, k0))
                    if not c:
                        continue
                    if tr:
                        rect = pymupdf.Rect(ya, x - t['pitch'] / 2, yb, x + t['pitch'] / 2)
                    else:
                        rect = pymupdf.Rect(x - t['pitch'] / 2 + 1, ya + 0.5, x + t['pitch'] / 2 - 1, yb - 0.5)
                    txt = c.get('steel') or (('%sx%s' % tuple(c['size'])) if c['size'] else
                                             ('%dDIA' % c['dia'] if c['dia'] else ('GRAY' if c['gray'] else '')))
                    col = (0.9, 0, 0) if txt and txt != 'GRAY' else (0.2, 0.4, 1)
                    q = rect * IM
                    q.normalize()
                    p.draw_rect(q, color=col, width=0.6)
                    if txt:
                        p.insert_text(pymupdf.Point(rect.x0 + 2, rect.y0 + 7) * IM, '%s %s' % (key, txt),
                                      fontsize=6, color=col, rotate=p.rotation)
    d.save(out)


if __name__ == '__main__':
    check(sys.argv[1], sys.argv[2])
