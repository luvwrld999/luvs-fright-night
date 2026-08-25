"""
Luv's Fright Night - tiny indexed-pixel drawing library.

Everything in the game's art is built from these primitives, which keeps the
whole cast on-model: the same outline, shading and rim-light passes run over
every sprite, so Luv, a demon and a boss all read as the same game.

Canvases hold palette indices (see palette.py), never RGB.
"""

import os
import struct

import palette as pal


class Canvas:
    def __init__(self, width, height, fill=pal.KEY):
        self.w = width
        self.h = height
        self.px = [[fill] * width for _ in range(height)]

    # -- basics -------------------------------------------------------------
    def copy(self):
        c = Canvas(self.w, self.h)
        c.px = [row[:] for row in self.px]
        return c

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def get(self, x, y):
        return self.px[y][x] if self.inside(x, y) else pal.KEY

    def set(self, x, y, c):
        if self.inside(x, y):
            self.px[y][x] = c

    def set_if(self, x, y, c, only_over=pal.KEY):
        """Paint only where the existing pixel is `only_over`."""
        if self.inside(x, y) and self.px[y][x] == only_over:
            self.px[y][x] = c

    # -- shapes -------------------------------------------------------------
    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.set(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c, fill=True):
        if rx <= 0 or ry <= 0:
            return
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                dx = (x + 0.5 - cx) / rx
                dy = (y + 0.5 - cy) / ry
                d = dx * dx + dy * dy
                if d <= 1.0:
                    if fill:
                        self.set(x, y, c)
                    else:
                        # ring: keep only the outer band
                        idx = ((x + 0.5 - cx) / max(rx - 1.0, 0.4)) ** 2 + \
                              ((y + 0.5 - cy) / max(ry - 1.0, 0.4)) ** 2
                        if idx > 1.0:
                            self.set(x, y, c)

    def disc(self, cx, cy, r, c):
        self.ellipse(cx, cy, r, r, c)

    def line(self, x0, y0, x1, y1, c, thick=1):
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            if thick <= 1:
                self.set(x0, y0, c)
            else:
                r = thick / 2.0
                self.disc(x0 + 0.5, y0 + 0.5, r, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def curve(self, points, c, thick=1):
        """Polyline through a list of (x, y) points."""
        for i in range(len(points) - 1):
            (ax, ay), (bx, by) = points[i], points[i + 1]
            self.line(ax, ay, bx, by, c, thick)

    def poly(self, points, c):
        """Scanline-fill a polygon given as [(x, y), ...]."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            yc = y + 0.5
            xs = []
            for i in range(len(points)):
                ax, ay = points[i]
                bx, by = points[(i + 1) % len(points)]
                if (ay <= yc < by) or (by <= yc < ay):
                    t = (yc - ay) / (by - ay)
                    xs.append(ax + t * (bx - ax))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(round(xs[i])), int(round(xs[i + 1]))):
                    self.set(x, y, c)

    # -- compositing --------------------------------------------------------
    def paste(self, other, ox=0, oy=0, key=pal.KEY):
        for y in range(other.h):
            for x in range(other.w):
                c = other.px[y][x]
                if c != key:
                    self.set(x + ox, y + oy, c)

    def flip_h(self):
        c = self.copy()
        c.px = [row[::-1] for row in self.px]
        return c

    def shifted(self, dx, dy):
        c = Canvas(self.w, self.h)
        c.paste(self, dx, dy)
        return c

    def replace(self, old, new):
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] == old:
                    self.px[y][x] = new
        return self

    def mask(self):
        """Set of (x, y) that are not transparent."""
        return {(x, y) for y in range(self.h) for x in range(self.w)
                if self.px[y][x] != pal.KEY}

    # -- automatic finishing passes ----------------------------------------
    def outline(self, color=pal.INK, diagonal=True):
        """Wrap the silhouette in an outline, drawn outward into empty space."""
        offs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if diagonal:
            offs += [(-1, -1), (1, -1), (-1, 1), (1, 1)]
        todo = []
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] != pal.KEY:
                    continue
                for dx, dy in offs:
                    if self.get(x + dx, y + dy) not in (pal.KEY, color):
                        todo.append((x, y))
                        break
        for x, y in todo:
            self.px[y][x] = color
        return self

    def shade(self, light=(-1, -1), colors=None, depth=1, region=None):
        """
        Darken pixels facing away from the light. `light` is the direction the
        light comes FROM, so the default lights from the upper left. Interior
        detail (eyes, mouth) counts as solid, so it casts no false shadow.
        """
        lx, ly = light
        todo = []
        for y in range(self.h):
            for x in range(self.w):
                c = self.px[y][x]
                if c in (pal.KEY, pal.INK):
                    continue
                if colors is not None and c not in colors:
                    continue
                if region is not None and not region(x, y):
                    continue
                # In shadow if stepping away from the light leaves the shape.
                if self.get(x - lx * (depth + 1), y - ly * (depth + 1)) == pal.KEY:
                    todo.append((x, y, pal.DARKER.get(c, c)))
        for x, y, c in todo:
            self.px[y][x] = c
        return self

    def rim(self, color=pal.CYAN, direction=(-1, 0), over=None, region=None):
        """
        Spectral rim light on the edge facing `direction`. Pass `region` to
        keep the highlight on one side only - a rim that wraps the whole
        silhouette just reads as a coloured outline.
        """
        dx, dy = direction
        todo = []
        for y in range(self.h):
            for x in range(self.w):
                c = self.px[y][x]
                if c in (pal.KEY, pal.INK):
                    continue
                if over is not None and c not in over:
                    continue
                if region is not None and not region(x, y):
                    continue
                if self.get(x + dx, y + dy) == pal.KEY:
                    todo.append((x, y))
        for x, y in todo:
            self.px[y][x] = color
        return self


# -- ASCII authoring --------------------------------------------------------
CHARS = {
    '.': pal.KEY, 'K': pal.INK, 'D': pal.SHADOW, 'P': pal.PURPLE,
    'W': pal.WHITE, 'L': pal.LILAC, 'C': pal.CYAN, 'c': pal.TEAL,
    'M': pal.MAG, 'm': pal.DMAG, 'R': pal.RED, 'r': pal.DRED,
    'G': pal.GOLD, 'g': pal.DGOLD, 'T': pal.GREEN, 't': pal.DGREEN,
}


def from_ascii(rows):
    """Build a Canvas from a list of strings using the CHARS legend."""
    h = len(rows)
    w = max(len(r) for r in rows)
    c = Canvas(w, h)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            c.px[y][x] = CHARS[ch]
    return c


# -- export -----------------------------------------------------------------
def write_bmp(canvas, path, palette=None):
    """
    Write an 8bpp uncompressed BMP with a 40-byte header - exactly what
    Butano's importer and grit accept. (Pillow is not used here so the
    build has no host dependencies beyond the standard library.)

    Pass `palette` to override the colour table, which is how the recoloured
    text palettes are built: index 1 is the glyph colour the font draws with.
    """
    w, h = canvas.w, canvas.h
    row_pad = (-w) % 4
    pixel_bytes = (w + row_pad) * h
    palette_bytes = 256 * 4
    offset = 14 + 40 + palette_bytes
    size = offset + pixel_bytes

    out = bytearray()
    out += b'BM' + struct.pack('<IHHI', size, 0, 0, offset)
    out += struct.pack('<IiiHHIIiiII', 40, w, h, 1, 8, 0, pixel_bytes,
                       2835, 2835, 256, 256)
    colors = palette or pal.RGB
    for i in range(256):
        r, g, b = colors[i] if i < len(colors) else (0, 0, 0)
        out += bytes((b, g, r, 0))
    # BMP rows are stored bottom-up.
    for y in range(h - 1, -1, -1):
        out += bytes(canvas.px[y]) + bytes(row_pad)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(out)


def stack(canvases):
    """Stack equally sized canvases vertically into one sheet."""
    w = canvases[0].w
    fh = canvases[0].h
    sheet = Canvas(w, fh * len(canvases))
    for i, c in enumerate(canvases):
        assert c.w == w and c.h == fh, 'frame size mismatch'
        sheet.paste(c, 0, i * fh)
    return sheet
