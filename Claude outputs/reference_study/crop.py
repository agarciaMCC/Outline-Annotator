import pymupdf, sys
pymupdf.TOOLS.mupdf_display_errors(False)
f, n, x0, y0, x1, y1, dpi, out = sys.argv[1], int(sys.argv[2]), *map(float, sys.argv[3:7]), int(sys.argv[7]), sys.argv[8]
p = pymupdf.open(f)[n-1]; W, H = p.rect.width, p.rect.height
pix = p.get_pixmap(dpi=dpi, clip=pymupdf.Rect(x0*W, y0*H, x1*W, y1*H)); pix.save(out); print(out, pix.width, pix.height)
