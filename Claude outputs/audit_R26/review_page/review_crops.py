"""Calibrate the exported view PNG from the two red corner crosses, then cut
one close-up per review item (its red intended line in the middle).
python review_crops.py <json> <png> <outdir>"""
import sys, json, os
import numpy as np
import pymupdf

js, png, outdir = sys.argv[1:4]
os.makedirs(outdir, exist_ok=True)
data = json.load(open(js, encoding="utf-8"))
pix = pymupdf.Pixmap(png)
if pix.alpha:
    pix = pymupdf.Pixmap(pix, 0)
W, H = pix.width, pix.height
a = np.frombuffer(pix.samples, dtype=np.uint8).reshape(H, pix.stride)[:, :W * pix.n].reshape(H, W, pix.n)
grn = (a[:, :, 1] > 150) & (a[:, :, 0] < 90) & (a[:, :, 2] < 90)
ys, xs = np.nonzero(grn)
print("green pixels", len(xs), "image", W, H)

def corner_center(cx, cy):
    d = (xs - cx) ** 2 + (ys - cy) ** 2
    i = np.argmin(d)
    near = ((xs - xs[i]) ** 2 + (ys - ys[i]) ** 2) < 80 ** 2
    return xs[near].mean(), ys[near].mean()

bl = corner_center(0, H)          # lower-left green cross  = cal[0]
tr = corner_center(W, 0)          # upper-right green cross = cal[1]
(X0, Y0), (X1, Y1) = data["cal"]
ax = (tr[0] - bl[0]) / (X1 - X0); bx = bl[0] - ax * X0
ay = (tr[1] - bl[1]) / (Y1 - Y0); by = bl[1] - ay * Y0
print("px per ft x %.3f y %.3f (should match, y negative)" % (ax, ay))

doc = pymupdf.open()
page = doc.new_page(width=W, height=H)
page.insert_image(page.rect, filename=png)
OUT_W = 720
for it in data["items"]:
    (px_, py_), (qx, qy) = it["p"], it["q"]
    mx, my = (px_ + qx) / 2.0, (py_ + qy) / 2.0
    L = ((px_ - qx) ** 2 + (py_ - qy) ** 2) ** 0.5
    half = max(L / 2.0 + 10.0, 18.0)                 # ft around the line
    cx, cy = ax * mx + bx, ay * my + by
    hp = half * ax
    r = pymupdf.Rect(cx - hp, cy - hp * 0.75, cx + hp, cy + hp * 0.75) & page.rect
    if r.is_empty or r.width < 20 or r.height < 20:
        print("skip (off picture)", it["id"])
        continue
    zoom = OUT_W / r.width
    out = page.get_pixmap(clip=r, matrix=pymupdf.Matrix(zoom, zoom))
    # draw this item's wanted line (and end ticks) on its own close-up
    d2 = pymupdf.open()
    pg = d2.new_page(width=out.width, height=out.height)
    pg.insert_image(pg.rect, pixmap=out)
    def tp(x, y):
        return pymupdf.Point((ax * x + bx - r.x0) * zoom, (ay * y + by - r.y0) * zoom)
    A, B = tp(px_, py_), tp(qx, qy)
    col = (0.55, 0.0, 0.85)                       # violet: not used elsewhere on the plan
    sh = pg.new_shape()
    sh.draw_line(A, B)
    sh.finish(color=col, width=7, stroke_opacity=0.55, lineCap=1)
    vx, vy = B.x - A.x, B.y - A.y
    n = (vx * vx + vy * vy) ** 0.5 or 1.0
    nx, ny = -vy / n * 14, vx / n * 14
    for P_ in (A, B):
        sh.draw_line(pymupdf.Point(P_.x - nx, P_.y - ny), pymupdf.Point(P_.x + nx, P_.y + ny))
    sh.finish(color=col, width=4, lineCap=1)
    sh.commit()
    fn = os.path.join(outdir, it["id"] + ".png")
    pg.get_pixmap().save(fn)
    it["img"] = "img/" + it["id"] + ".png"
json.dump(data, open(os.path.join(outdir, "..", "items.json"), "w", encoding="utf-8"), indent=1)
print("wrote", len(data["items"]), "crops")
