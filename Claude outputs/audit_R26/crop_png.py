import pymupdf, sys
src, x0, y0, x1, y1, out = sys.argv[1], *map(int, sys.argv[2:6]), sys.argv[6]
pix = pymupdf.Pixmap(src)
c = pymupdf.Pixmap(pix.colorspace, pymupdf.IRect(x0, y0, x1, y1), pix.alpha)
c.copy(pix, c.irect); c.set_origin(0, 0); c.save(out); print(out, c.width, c.height)
