"""
Human-facing contact sheets. Pillow is used here and only here - the ROM
assets themselves are generated with the standard library alone.
"""

import os

from PIL import Image, ImageDraw

import palette as pal

BG = (14, 8, 20)
PANEL = (26, 16, 38)
CHECK_A = (40, 26, 56)
CHECK_B = (30, 19, 44)
TEXT = (210, 190, 235)
TITLE = (255, 216, 56)


def to_image(canvas, scale=1, checker=True):
    img = Image.new('RGB', (canvas.w * scale, canvas.h * scale))
    px = img.load()
    for y in range(canvas.h):
        for x in range(canvas.w):
            c = canvas.px[y][x]
            if c == pal.KEY:
                rgb = CHECK_A if ((x // 2 + y // 2) % 2 == 0) else CHECK_B
                if not checker:
                    rgb = PANEL
            else:
                rgb = pal.RGB[c]
            for sy in range(scale):
                for sx in range(scale):
                    px[x * scale + sx, y * scale + sy] = rgb
    return img


def contact_sheet(path, title, groups, scale=4, columns=None):
    """
    groups: list of (group_name, [(label, canvas), ...])
    Lays every group out as a labelled row block on a dark page.
    """
    pad = 12
    label_h = 12
    group_gap = 10
    header_h = 34

    # measure
    blocks = []
    total_h = header_h + pad
    max_w = 520
    for name, frames in groups:
        if not frames:
            continue
        cols = columns or max(1, min(len(frames), 12))
        rows = (len(frames) + cols - 1) // cols
        cw = max(c.w for _, c in frames) * scale + 10
        ch = max(c.h for _, c in frames) * scale + label_h + 6
        w = pad * 2 + cols * cw
        h = 16 + rows * ch
        blocks.append((name, frames, cols, cw, ch, h))
        total_h += h + group_gap
        max_w = max(max_w, w)

    img = Image.new('RGB', (max_w, total_h + pad), BG)
    d = ImageDraw.Draw(img)
    d.text((pad, 10), title, fill=TITLE)
    d.line((pad, header_h - 8, max_w - pad, header_h - 8), fill=(70, 45, 95))

    y = header_h + 4
    for name, frames, cols, cw, ch, h in blocks:
        d.rectangle((pad - 4, y - 2, max_w - pad + 4, y + h - 6), fill=PANEL)
        d.text((pad, y + 2), name, fill=TEXT)
        gy = y + 16
        for i, (label, canvas) in enumerate(frames):
            col, row = i % cols, i // cols
            cx = pad + col * cw + 5
            cy = gy + row * ch
            img.paste(to_image(canvas, scale), (cx, cy))
            d.text((cx, cy + canvas.h * scale + 2), label[:cw // 6],
                   fill=(150, 130, 180))
        y += h + group_gap

    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path
