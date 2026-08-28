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

def _cart_label(w, h):
    """
    The printed label, drawn landscape.

    The box front is portrait, and cropping it to a cartridge label loses
    either the wordmark or the ghost. This lays the same pieces out for the
    shape the label actually is, in bands that cannot collide.
    """
    img = gs.backdrop(w, h, seed=17)

    lock, _pad = gs.title_block(4, 3)
    lock.thumbnail((int(w * 0.70), int(h * 0.38)), Image.LANCZOS)
    img.alpha_composite(lock, ((w - lock.width) // 2, int(h * 0.06)))

    # Luv sits in the middle band, sized so his feet stop above the credit.
    feet = int(h * 0.80)
    luv = gs.sprite('luv', 0, 32, 3)
    img.alpha_composite(luv, ((w - luv.width) // 2, feet - luv.height))

    for i, name in enumerate(('halo_imp', 'cherub_fiend')):
        art = gs.sprite(name, 0, 16, 3)
        x = int(w * (0.18 if i == 0 else 0.82)) - art.width // 2
        img.alpha_composite(art, (x, feet - art.height))

    strip = Image.new('RGBA', (w, 30), (0, 0, 0, 0))
    boxfont.centered(strip, 'RETRO RUMBLE', 0, gs.DGOLD, 2)
    img.alpha_composite(strip, (0, int(h * 0.85)))

    gs.neon_frame(img, 5, 2)
    return img


def cartridge(path, w=940, h=600):
    """
    A Game Boy Advance cartridge, seen face on.

    Landscape at about 1.7 to 1, with the shallow dome moulded into the band
    above the label, the two tabs at the upper corners and the thumb notch at
    the foot. Proportions are taken off a real shell: the label leaves a wide
    margin at the top - that band is where the moulded lettering goes - and
    tighter ones at the sides and foot.

    That lettering reads "GAME BOY ADVANCE" on a real cartridge and is not
    reproduced here. The silhouette is what makes it read as a cartridge; the
    wordmark is Nintendo's and this game is not theirs.
    """
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))

    bw, bh = 840, 494
    bx, by = (w - bw) // 2, (h - bh) // 2
    shell = (58, 58, 66, 255)
    lit = (88, 88, 98, 255)
    dark = (34, 34, 40, 255)

    body = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)

    # Tabs at the upper corners: they clear the top edge by a few pixels only,
    # which is what stops them reading as ears.
    for side in (0, 1):
        tx = bx + 34 if side == 0 else bx + bw - 96
        bd.rounded_rectangle([tx, by - 9, tx + 62, by + 42], radius=7,
                             fill=shell)

    bd.rounded_rectangle([bx, by, bx + bw, by + bh], radius=32, fill=shell)
    bd.rounded_rectangle([bx + 10, by + 7, bx + bw - 10, by + 19], radius=6,
                         fill=lit)
    bd.rounded_rectangle([bx + 10, by + bh - 20, bx + bw - 10, by + bh - 9],
                         radius=6, fill=dark)

    # The dome, moulded into the band above the label - inside the shell, not
    # floating over its top edge.
    bd.arc([bx + 132, by + 8, bx + bw - 132, by + 150], 203, 337, fill=lit,
           width=5)
    bd.arc([bx + 132, by + 15, bx + bw - 132, by + 157], 203, 337, fill=dark,
           width=3)

    # Label: measured off the reference - 14% margins at the sides, 21% above,
    # 14% below, so the band that carries the moulding stays clear.
    lx = bx + int(bw * 0.14)
    ly = by + int(bh * 0.21)
    lw = bw - 2 * int(bw * 0.14)
    lh = bh - int(bh * 0.21) - int(bh * 0.14)

    bd.rounded_rectangle([lx - 7, ly - 7, lx + lw + 6, ly + lh + 6], radius=14,
                         fill=(24, 22, 30, 255))

    label = _cart_label(lw, lh)
    mask = Image.new('L', (lw, lh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, lw - 1, lh - 1], radius=10,
                                           fill=255)
    flat = Image.new('RGBA', (lw, lh), (0, 0, 0, 0))
    flat.paste(label, (0, 0), mask)
    body.alpha_composite(flat, (lx, ly))

    # The thumb notch at the foot.
    cx = bx + bw // 2
    fy = by + bh - 34
    bd.polygon([(cx - 32, fy), (cx + 32, fy), (cx, fy + 19)], fill=dark)
    bd.line([(cx - 32, fy), (cx + 32, fy)], fill=lit, width=2)

    blur, at = shadow(body, 22, 0.65, (12, 18))
    img.alpha_composite(blur, at)
    img.alpha_composite(body)
    img.save(path)
    return path


# ------------------------------------------------------------------ 3D box

def box_3d(path, w=1180, h=1020):
    """
    The box turned a few degrees, with its spine showing.

    A retail box wears the silver platform strip twice - down the left edge of
    the face, and again on the spine, which is what you actually see on a
    shelf. The face carries its own already, so this builds the spine to
    match it rather than inventing a different one.
    """
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    front_src = Image.open(
                os.path.join(MEDIA, 'box', 'box-front.png')).convert('RGBA')

    # Right edge nearer, so taller; the spine falls away to the left.
    front_q = [(372, 92), (1104, 40), (1104, 968), (372, 916)]
    spine_q = [(84, 196), (372, 92), (372, 916), (84, 812)]

    spine = gs._platform_band(300, 920, 'LUV\'S FRIGHT NIGHT')
    sd = ImageDraw.Draw(spine)
    sd.rectangle([0, 0, 6, spine.height], fill=(48, 48, 56, 255))

    panel = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    panel.alpha_composite(warp(spine, spine_q, (w, h)))
    panel.alpha_composite(warp(front_src, front_q, (w, h)))

    # The fold where the two faces meet.
    ed = ImageDraw.Draw(panel)
    ed.line([front_q[0], front_q[3]], fill=(255, 255, 255, 70), width=3)

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


# --------------------------------------------------------------- pdf manual

PAGE = (1240, 1754)          # A4 at 150 dpi


def _sheet():
    img = gs.backdrop(PAGE[0], PAGE[1], seed=11)
    gs.neon_frame(img, 46, 3)
    return img


def _heading(img, words, y):
    block = Image.new('RGBA', (PAGE[0], 120), (0, 0, 0, 0))
    boxfont.centered(block, words, 0, gs.GOLD, 7)
    bloom, off = gs.glow(block, 9, 1.8, gs.MAG)
    img.alpha_composite(bloom, (off, y + off))
    img.alpha_composite(block, (0, y))


def _body(img, lines, y, size=30, colour=(214, 206, 236, 255), x=140):
    d = ImageDraw.Draw(img)
    f = font(size)

    for line in lines:
        d.text((x, y), line, font=f, fill=colour)
        y += int(size * 1.55)

    return y


def _entry(img, sheet_name, title, text, y, height=16, scale=5):
    """One creature or pickup: its own sprite, its name, what it does."""
    art = gs.sprite(sheet_name, 0, height, scale)
    img.alpha_composite(art, (150, y))
    d = ImageDraw.Draw(img)
    d.text((150 + art.width + 40, y + 4), title, font=font(34), fill=gs.GOLD)
    wrapped = []
    words, line = text.split(), ''

    for word in words:
        trial = (line + ' ' + word).strip()

        if len(trial) > 52:
            wrapped.append(line)
            line = word
        else:
            line = trial

    wrapped.append(line)
    _body(img, wrapped, y + 52, 26, x=150 + art.width + 40)
    return y + max(art.height, 52 + len(wrapped) * 40) + 34


def manual_pdf(path):
    """
    The manual as a booklet.

    Headings in the game's own block face, body text in a plain mono so it can
    actually be read at arm's length, and every creature illustrated with the
    sprite the ROM ships rather than a drawing of it.
    """
    pages = []

    # -- cover
    cover = _sheet()
    lockup, _pad = gs.title_block(15, 10)
    cover.alpha_composite(lockup, ((PAGE[0] - lockup.width) // 2, 190))
    luv = gs.sprite('luv', 0, 32, 11)
    cover.alpha_composite(luv, ((PAGE[0] - luv.width) // 2, 780))
    tag = Image.new('RGBA', (PAGE[0], 120), (0, 0, 0, 0))
    boxfont.centered(tag, 'A GHOST IN BAD COMPANY', 0, gs.CYAN, 5)
    cover.alpha_composite(tag, (0, 1240))
    boxfont.centered(cover, 'INSTRUCTION BOOKLET', 1400, gs.MAG, 4)
    boxfont.centered(cover, 'RETRO RUMBLE', 1560, gs.DGOLD, 4)
    pages.append(cover)

    # -- the story and the controls
    p = _sheet()
    _heading(p, 'THE RUN', 120)
    y = _body(p, [
        'Luv is a ghost with a devil\'s horns and an angel\'s halo,',
        'and neither side will have him. Eight worlds lie between',
        'him and the floor of the underworld. Seven of them are',
        'ruled by a sin. The eighth is ruled by Hades.',
        '',
        'Take each stage from left to right, find the gate at the',
        'end, and put down whatever is waiting in the third room.',
    ], 300)

    _heading(p, 'CONTROLS', y + 70)
    _body(p, [
        'PAD          run, and duck at a gate',
        'A            jump - hold it to hover on the way down',
        'A (held)     the hover meter drains, and fills on the ground',
        'B (tap)      throw a soul flame, once you are carrying one',
        'B (held)     run horns-first, fast enough to break blocks',
        'START        pause: resume, restart, or leave',
        'SELECT       nothing, and it never will',
    ], y + 230, 28, (150, 240, 255, 255))
    pages.append(p)

    # -- what you are carrying
    p = _sheet()
    _heading(p, 'WHAT YOU CARRY', 120)
    y = 320

    for key, title, text in man.POWERS:
        y = _entry(p, key, title.upper(), text, y, 16, 5)

    _body(p, [
        'A hit costs the last thing you picked up.',
        'With nothing left to lose, it costs a life.',
        '',
        'Ninety-nine souls is a life, and the count starts again.',
    ], y + 30, 27, gs.LILAC)
    pages.append(p)

    # -- what is in the way
    p = _sheet()
    _heading(p, 'BAD COMPANY', 120)
    y = 320

    for key, height, title, text in man.ENEMIES:
        y = _entry(p, key, title.upper(), text, y, height, 5)

    pages.append(p)

    # -- the sins, over two pages
    for half in (0, 1):
        p = _sheet()
        _heading(p, 'THE SEVEN' if half == 0 else 'AND THE KING', 120)
        y = 320

        for key, numeral, name, sin, text in man.SINS[half * 4:half * 4 + 4]:
            y = _entry(p, key, '%s  %s' % (numeral, name.upper()),
                       '%s. %s' % (sin, text), y, 32, 4)

        pages.append(p)

    # -- the back page
    p = _sheet()
    _heading(p, 'AND ONE MORE THING', 120)
    _body(p, [
        'Every stage prints a four letter code on its world card.',
        'Write it down and LEVEL CODE will take you back there.',
        '',
        'Some walls are not walls. Some rooms are not on the way.',
        '',
        'Nothing in this cartridge was sampled or borrowed. Every',
        'sprite, every tile and every note was generated by the',
        'tools in this project, and so was this booklet.',
    ], 320, 29)
    boxfont.centered(p, 'RETRO RUMBLE', 1420, gs.GOLD, 5)
    boxfont.centered(p, 'A LUVWRLD GAME', 1520, gs.MAG, 4)
    pages.append(p)

    flat = [q.convert('RGB') for q in pages]
    flat[0].save(path, save_all=True, append_images=flat[1:], resolution=150.0)
    return path


def shelf(path, w=1600, h=900):
    """
    The box and the cartridge together, the way they would sit on a shelf.

    A cover on its own says what the game is called; a cover next to the
    cartridge says it is a thing you own. This is the pairing the README and
    the release page lead with.
    """
    img = gs.backdrop(w, h, seed=21)

    # A pool of light under both, so they stand on something.
    pool = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pool)

    for i in range(70):
        t = i / 70.0
        pd.ellipse([int(w * 0.10 + w * 0.16 * t), int(h * 0.70 + h * 0.10 * t),
                    int(w * 0.90 - w * 0.16 * t), int(h * 0.94 - h * 0.06 * t)],
                   fill=(70, 30, 96, 5))

    img.alpha_composite(pool)

    box = Image.open(os.path.join(MEDIA, 'box3d', 'box-3d.png')).convert('RGBA')
    box.thumbnail((720, 720), Image.LANCZOS)
    cart = Image.open(
                os.path.join(MEDIA, 'cartridge', 'cart.png')).convert('RGBA')
    cart.thumbnail((600, 600), Image.LANCZOS)

    # The box behind and to the left, the cartridge in front of its near edge -
    # the cart is the smaller object, so it comes forward.
    # The cart is a landscape object now, so it is seated on the same line the
    # box stands on rather than floating beside its middle.
    bx, by = 170, (h - box.height) // 2 - 20
    cx, cy = 840, by + box.height - cart.height - 30

    blur, at = shadow(box, 26, 0.75, (20, 26))
    img.alpha_composite(blur, (bx + at[0], by + at[1]))
    img.alpha_composite(box, (bx, by))

    blur, at = shadow(cart, 20, 0.8, (16, 20))
    img.alpha_composite(blur, (cx + at[0], cy + at[1]))
    img.alpha_composite(cart, (cx, cy))

    # No wheel across the top: the box carries the wordmark at full size
    # already, and laying another copy over it read as LUVLUV'S FRIGHT NIGHT.
    strip = Image.new('RGBA', (w, 60), (0, 0, 0, 0))
    boxfont.centered(strip, 'RETRO RUMBLE', 0, gs.DGOLD, 4)
    img.alpha_composite(strip, (0, h - 62))

    img.convert('RGB').save(path)
    return path


def main():
    for sub in ('cartridge', 'box3d', 'mix', 'shelf'):
        os.makedirs(os.path.join(MEDIA, sub), exist_ok=True)

    made = [
        cartridge(os.path.join(MEDIA, 'cartridge', 'cart.png')),
        box_3d(os.path.join(MEDIA, 'box3d', 'box-3d.png')),
        mix(os.path.join(MEDIA, 'mix', 'mix.png')),
        shelf(os.path.join(MEDIA, 'shelf', 'box-and-cart.png')),
        manual_pdf(os.path.join(OUT, 'manual.pdf')),
    ]

    for path in made:
        print('%9d  %s' % (os.path.getsize(path),
                           os.path.relpath(path, ROOT)))


if __name__ == '__main__':
    main()
