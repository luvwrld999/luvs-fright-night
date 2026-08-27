#!/usr/bin/env python3
"""
The printed matter: a cartridge, a 3D box, the mix image, and a PDF manual.

The scrape package already had the ingredients - a box front, a wheel logo
with a real alpha channel, fanart and eight screenshots - but nothing that
composited them, which is the one asset most frontends actually put on screen.
This draws the rest of the set from those same pieces, so the shelf and the
game cannot drift apart.

    python3 tools/gen_print.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFont

import boxfont
import gen_scrape as gs
import gen_manual as man

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'scrape')
MEDIA = os.path.join(OUT, 'media')

BODY_TTF = '/System/Library/Fonts/Supplemental/Andale Mono.ttf'


def font(size):
    try:
        return ImageFont.truetype(BODY_TTF, size)
    except OSError:
        return ImageFont.load_default()


# ---------------------------------------------------------------- geometry

def _solve(rows, rhs):
    """Plain Gaussian elimination; the system is 8x8 and always small."""
    n = len(rhs)
    m = [list(r) + [v] for r, v in zip(rows, rhs)]

    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        m[col], m[pivot] = m[pivot], m[col]

        for r in range(n):
            if r == col or not m[col][col]:
                continue

            f = m[r][col] / m[col][col]

            for c in range(col, n + 1):
                m[r][c] -= f * m[col][c]

    return [m[i][n] / m[i][i] for i in range(n)]


def warp(src_img, dst_quad, size):
    """
    Put `src_img` onto a quad of a `size` canvas, with perspective.

    Pillow's PERSPECTIVE transform reads output pixels back into the source,
    so the coefficients solve the inverse of the mapping being described here.
    """
    w, h = src_img.size
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    rows, rhs = [], []

    for (sx, sy), (dx, dy) in zip(src, dst_quad):
        rows.append([dx, dy, 1, 0, 0, 0, -dx * sx, -dy * sx])
        rhs.append(sx)
        rows.append([0, 0, 0, dx, dy, 1, -dx * sy, -dy * sy])
        rhs.append(sy)

    coeffs = _solve(rows, rhs)
    return src_img.transform(size, Image.PERSPECTIVE, coeffs,
                             Image.BICUBIC)


def shadow(img, blur=18, strength=0.75, offset=(14, 18)):
    """A soft dark copy of whatever shape `img` is, for dropping behind it."""
    alpha = img.getchannel('A')
    dark = Image.new('RGBA', img.size, (0, 0, 0, 0))
    dark.putalpha(alpha.point(lambda a: int(a * strength)))
    bloom, off = gs.glow(dark, blur, 1.0, (0, 0, 0, 255))
    return bloom, (offset[0] - off, offset[1] - off)


# ---------------------------------------------------------------- cartridge

def cartridge(path, w=800, h=800):
    """
    The cart itself: grey shell, printed label, gold contacts.

    Frontends that show a "support" image expect the thing you would actually
    hold, so the label is the box art cropped to the label's own proportions
    rather than the box shrunk down.
    """
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    bw, bh = 520, 640
    bx, by = (w - bw) // 2, (h - bh) // 2
    shell = (58, 54, 70, 255)
    lip = (86, 80, 104, 255)

    body = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    bd.rounded_rectangle([bx, by, bx + bw, by + bh], radius=26, fill=shell)

    # The two grip notches down the sides, and the bevel that catches light.
    for side in (0, 1):
        x = bx - 1 if side == 0 else bx + bw - 21
        bd.rounded_rectangle([x, by + 150, x + 22, by + 430], radius=10,
                             fill=(38, 35, 48, 255))

    bd.rounded_rectangle([bx + 6, by + 6, bx + bw - 6, by + 22], radius=8,
                         fill=lip)

    # Label: the box art, cropped to the label's shape.
    lw, lh = bw - 84, 400
    lx, ly = bx + 42, by + 52
    art = Image.open(os.path.join(MEDIA, 'box', 'box-front.png')).convert('RGBA')
    scale = max(lw / art.width, lh / art.height)
    art = art.resize((int(art.width * scale), int(art.height * scale)),
                     Image.LANCZOS)
    art = art.crop((0, 0, lw, lh))

    label = Image.new('RGBA', (lw, lh), (0, 0, 0, 0))
    mask = Image.new('L', (lw, lh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, lw - 1, lh - 1], radius=12,
                                           fill=255)
    label.paste(art, (0, 0), mask)
    bd.rounded_rectangle([lx - 4, ly - 4, lx + lw + 3, ly + lh + 3], radius=16,
                         fill=(20, 16, 30, 255))
    body.alpha_composite(label, (lx, ly))

    # Contacts along the bottom edge, and the slot they sit in.
    cy = by + bh - 96
    bd.rectangle([bx + 60, cy, bx + bw - 60, cy + 62], fill=(28, 24, 38, 255))

    pins = 16
    span = (bw - 140) / pins

    for i in range(pins):
        px = bx + 70 + i * span
        bd.rounded_rectangle([px, cy + 8, px + span * 0.6, cy + 54], radius=3,
                             fill=(214, 168, 40, 255))

    boxfont.centered(body, 'GBA', by + bh - 26, (150, 144, 172, 255), 3)

    blur, at = shadow(body, 20, 0.6, (10, 16))
    img.alpha_composite(blur, at)
    img.alpha_composite(body)
    img.save(path)
    return path


# ------------------------------------------------------------------ 3D box

def box_3d(path, w=1000, h=1300):
    """The front turned a few degrees, with its spine showing."""
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    front_src = Image.open(
                os.path.join(MEDIA, 'box', 'box-front.png')).convert('RGBA')

    # Front face: right edge nearer, so taller. Spine falls away to the left.
    front_q = [(330, 96), (946, 44), (946, 1216), (330, 1164)]
    spine_q = [(78, 208), (330, 96), (330, 1164), (78, 1052)]

    spine = Image.new('RGBA', (300, 1000), (26, 14, 40, 255))
    sd = ImageDraw.Draw(spine)
    sd.rectangle([0, 0, 12, spine.height], fill=(52, 26, 78, 255))
    strip = Image.new('RGBA', (1000, 300), (0, 0, 0, 0))
    boxfont.centered(strip, "LUV'S FRIGHT NIGHT", 110, gs.GOLD, 7)
    # Clockwise, so the spine reads top to bottom on a shelf.
    spine.alpha_composite(strip.rotate(-90, expand=True).resize(
                (300, 1000), Image.LANCZOS), (0, 0))

    panel = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    panel.alpha_composite(warp(spine, spine_q, (w, h)))
    panel.alpha_composite(warp(front_src, front_q, (w, h)))

    # The edge where the two faces meet, so the fold reads.
    ed = ImageDraw.Draw(panel)
    ed.line([front_q[0], front_q[3]], fill=(255, 255, 255, 60), width=3)

    blur, at = shadow(panel, 26, 0.7, (18, 24))
    img.alpha_composite(blur, at)
    img.alpha_composite(panel)
    img.save(path)
    return path


# --------------------------------------------------------------- mix image

def mix(path, w=1920, h=1080):
    """
    The composite most frontends actually put on screen.

    Screenshot large and square-on because it is the only part that shows the
    game; the box turned beside it; the wheel across the bottom. The fanart
    behind is pushed down hard so none of it competes with the three things
    that matter.
    """
    art = Image.open(os.path.join(MEDIA, 'fanart', 'fanart.png')).convert('RGBA')
    art = art.resize((w, h), Image.LANCZOS)
    img = Image.new('RGBA', (w, h), gs.INK)
    img.alpha_composite(Image.blend(Image.new('RGBA', (w, h), gs.INK), art, 0.34))

    # Vignette, so the edges fall away and the middle carries the eye.
    veil = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    steps = 90

    for i in range(steps):
        t = i / float(steps)
        # The sweep has to stop before the rectangles turn inside out.
        x0 = int(-w * 0.10 + w * 0.42 * t)
        y0 = int(-h * 0.10 + h * 0.42 * t)
        vd.rectangle([x0, y0, w - 1 - x0, h - 1 - y0], outline=(6, 3, 12, 7))

    img.alpha_composite(veil)

    # The screenshot, at a whole-number pixel scale so it stays crisp.
    shot = Image.open(os.path.join(
                MEDIA, 'screenshot', 'gameplay-world-1.png')).convert('RGBA')
    factor = 4
    shot = shot.resize((shot.width * factor, shot.height * factor),
                       Image.NEAREST)
    frame = Image.new('RGBA', (shot.width + 26, shot.height + 26),
                      (0, 0, 0, 0))
    ImageDraw.Draw(frame).rectangle([0, 0, frame.width - 1, frame.height - 1],
                                    fill=(14, 8, 22, 235))
    frame.alpha_composite(shot, (13, 13))
    gs.neon_frame(frame, 4, 3)

    sx, sy = w - frame.width - 104, 120
    blur, at = shadow(frame, 24, 0.8, (16, 20))
    img.alpha_composite(blur, (sx + at[0], sy + at[1]))
    img.alpha_composite(frame, (sx, sy))

    # The box, turned, overlapping the screenshot's near corner a little.
    box = Image.open(os.path.join(MEDIA, 'box3d', 'box-3d.png')).convert('RGBA')
    box.thumbnail((640, 640), Image.LANCZOS)
    img.alpha_composite(box, (90, 130))

    # The wheel, across the bottom, clear of both.
    wheel = Image.open(os.path.join(
                MEDIA, 'marquee', 'logo.png')).convert('RGBA')
    wheel.thumbnail((720, 230), Image.LANCZOS)
    # Centred under the screenshot rather than the canvas, and below it - a
    # wheel laid over the gameplay hides the one thing the mix is for.
    img.alpha_composite(wheel, (sx + (frame.width - wheel.width) // 2,
                                h - wheel.height - 45))

    img.convert('RGB').save(path)
    return path
