#!/usr/bin/env python3
"""Build the scrape package: box art, marquee, screenshots and gamelist.xml.

Everything here is drawn from the game's own assets -- the sprite BMPs the ROM
ships and frames captured out of the emulator -- so the printed material and
the game cannot drift apart.
"""

import os
import random
import shutil
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import boxfont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'scrape')

GOLD = (255, 214, 0, 255)
DGOLD = (156, 106, 0, 255)
MAG = (255, 41, 173, 255)
CYAN = (99, 255, 247, 255)
WHITE = (247, 247, 255, 255)
LILAC = (189, 165, 222, 255)
INK = (16, 8, 24, 255)


def sprite(name, frame, height, scale=1):
    """One frame out of a sprite sheet BMP, palette index 0 knocked out."""
    sheet = Image.open(os.path.join(ROOT, 'graphics', name + '.bmp'))
    w = sheet.size[0]
    cut = sheet.crop((0, frame * height, w, (frame + 1) * height))
    rgb = cut.convert('RGB')
    idx = cut.load()
    out = Image.new('RGBA', cut.size, (0, 0, 0, 0))
    src = rgb.load()
    dst = out.load()

    for y in range(cut.size[1]):
        for x in range(w):
            if idx[x, y] != 0:
                r, g, b = src[x, y]
                dst[x, y] = (r, g, b, 255)

    if scale != 1:
        out = out.resize((w * scale, cut.size[1] * scale), Image.NEAREST)

    return out


def glow(layer, radius, strength=1.0, color=None):
    """A blurred copy of `layer`, optionally recoloured, for neon bloom.

    Returns (image, offset): the blur needs room to spread past the sprite's
    own edges, or it clips into a hard rectangle, so the result is padded and
    the caller shifts by the offset.
    """
    if color is not None:
        tinted = Image.new('RGBA', layer.size, color[:3] + (0,))
        tinted.putalpha(layer.getchannel('A'))
        layer = tinted

    pad = int(radius * 3)
    roomy = Image.new('RGBA', (layer.size[0] + pad * 2, layer.size[1] + pad * 2),
                      (0, 0, 0, 0))
    roomy.alpha_composite(layer, (pad, pad))

    blurred = roomy.filter(ImageFilter.GaussianBlur(radius))
    alpha = blurred.getchannel('A').point(lambda v: int(min(255, v * strength)))
    blurred.putalpha(alpha)
    return blurred, -pad


def backdrop(w, h, seed=6):
    """Night gradient, starfield and a low magenta haze."""
    img = Image.new('RGBA', (w, h), INK)
    px = img.load()

    for y in range(h):
        t = y / (h - 1)
        r = int(30 * (1 - t) + 8 * t)
        g = int(10 * (1 - t) + 4 * t)
        b = int(58 * (1 - t) + 16 * t)

        for x in range(w):
            px[x, y] = (r, g, b, 255)

    rng = random.Random(seed)
    stars = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sp = stars.load()

    for _ in range(int(w * h / 900)):
        x = rng.randrange(w)
        y = rng.randrange(h)
        c = rng.choice([CYAN, LILAC, WHITE, MAG])
        size = rng.choice([1, 1, 1, 2])

        for dy in range(size):
            for dx in range(size):
                if x + dx < w and y + dy < h:
                    sp[x + dx, y + dy] = c[:3] + (rng.randrange(70, 210),)

    bloom, off = glow(stars, 2, 0.6)
    img.alpha_composite(bloom, (off, off))
    img.alpha_composite(stars)
    return img


def title_block(scale_big, scale_small):
    """The stacked LUV'S / FRIGHT / NIGHT lockup, glowing, on transparency."""
    lines = [("LUV'S", scale_small), ('FRIGHT', scale_big), ('NIGHT', scale_big)]
    width = max(boxfont.measure(t, s) for t, s in lines)
    gap = scale_small * 2
    height = sum(boxfont.HEIGHT * s for _, s in lines) + gap * (len(lines) - 1)
    pad = scale_big * 7

    block = Image.new('RGBA', (width + pad * 2, height + pad * 2), (0, 0, 0, 0))
    shadow = Image.new('RGBA', block.size, (0, 0, 0, 0))
    y = pad

    for word, s in lines:
        x = pad + (width - boxfont.measure(word, s)) // 2
        # A hard offset shadow first, so the letters keep their edge against
        # the bloom that goes underneath them.
        boxfont.draw(shadow, word, x + s, y + s, DGOLD, s)
        boxfont.draw(block, word, x, y, GOLD, s)
        y += boxfont.HEIGHT * s + gap

    out = Image.new('RGBA', block.size, (0, 0, 0, 0))
    for radius, strength, colour in ((scale_big * 2.4, 4.0, MAG),
                                     (scale_big * 0.7, 2.6, GOLD)):
        bloom, off = glow(block, radius, strength, colour)
        out.alpha_composite(bloom, (off, off))

    out.alpha_composite(shadow)
    out.alpha_composite(block)
    # The pad goes back to the caller so text below can be placed against the
    # letterforms rather than against the invisible bloom margin.
    return out, pad


def neon_frame(img, inset, thickness=3):
    """Two-tone border, magenta outside, cyan inside."""
    line = Image.new('RGBA', img.size, (0, 0, 0, 0))
    px = line.load()
    w, h = img.size

    for i in range(thickness):
        c = MAG if i < thickness - 1 else CYAN

        for x in range(inset, w - inset):
            px[x, inset + i] = c
            px[x, h - 1 - inset - i] = c

        for y in range(inset, h - inset):
            px[inset + i, y] = c
            px[w - 1 - inset - i, y] = c

    bloom, off = glow(line, 6, 2.6)
    img.alpha_composite(bloom, (off, off))
    img.alpha_composite(line)


def _box_art(w, h):
    """
    The printed artwork, without the platform furniture around it.

    Every size below was tuned against a 1200-tall poster shape. A real Game
    Boy Advance box is nearly square, so they scale off the height they are
    actually given - otherwise the title lands on top of the ghost.
    """
    k = h / 1200.0

    def px(n):
        return max(1, int(round(n * k)))

    img = backdrop(w, h)

    # The moon Luv is haunting, behind the lockup.
    moon = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    mp = moon.load()
    cx, cy, r = int(w * 0.76), int(h * 0.135), int(w * 0.10)

    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if 0 <= x < w and 0 <= y < h and (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                mp[x, y] = (232, 226, 255, 255)

    bloom, off = glow(moon, 30, 2.0, CYAN)
    img.alpha_composite(bloom, (off, off))
    img.alpha_composite(moon)

    # Title first, because everything below is placed off its real height.
    title, pad = title_block(scale_big=px(17), scale_small=px(11))
    # Low enough to clear the publisher's mark in the top corner.
    title_y = int(h * 0.085) - pad
    img.alpha_composite(title, ((w - title.size[0]) // 2, title_y))

    tag_y = title_y + title.size[1] - pad + 14
    tag = Image.new('RGBA', (w, 60), (0, 0, 0, 0))
    boxfont.centered(tag, 'EIGHT WORLDS * SEVEN SINS * ONE GHOST', 4, CYAN,
                     px(3))
    bloom, off = glow(tag, 7, 2.2)
    img.alpha_composite(bloom, (off, tag_y + off))
    img.alpha_composite(tag, (0, tag_y))

    # The floor line the cast stands on -- everything below is the credit band.
    band_top = h - px(170)

    # Small fry drifting through the empty middle band.
    for name, height, scale, fx, fy in (
            ('cherub_fiend', 16, px(5), 0.17, 0.45),
            ('bone_bat', 16, px(4), 0.82, 0.47),
            ('halo_imp', 16, px(5), 0.26, 0.545),
            ('gnasher', 16, px(4), 0.74, 0.575),
            ('soul_orb', 8, px(5), 0.50, 0.455),
            ('soul_orb', 8, px(4), 0.20, 0.62),
            ('soul_orb', 8, px(4), 0.88, 0.60)):
        try:
            fry = sprite(name, 0, height, scale)
        except FileNotFoundError:
            continue

        x = int(w * fx) - fry.size[0] // 2
        y = int(h * fy)
        bloom, off = glow(fry, 11, 1.5, CYAN if 'soul' in name else MAG)
        img.alpha_composite(bloom, (x + off, y + off))
        img.alpha_composite(fry, (x, y))

    # A soft halo behind Luv so the white sprite separates from the night.
    disc = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dp = disc.load()
    dcx, dcy, dr = w // 2, band_top - px(250), px(210)

    for y in range(dcy - dr, dcy + dr + 1):
        for x in range(dcx - dr, dcx + dr + 1):
            if 0 <= x < w and 0 <= y < h and (x - dcx) ** 2 + (y - dcy) ** 2 <= dr * dr:
                dp[x, y] = MAG[:3] + (46,)

    bloom, off = glow(disc, 60, 1.6)
    img.alpha_composite(bloom, (off, off))

    # Two sins flanking, standing on the same floor.
    for name, side in (('boss_superbia', -1), ('boss_ira', 1)):
        sin = sprite(name, 0, 32, px(6))
        x = int(w * 0.5 + side * w * 0.34) - sin.size[0] // 2
        y = band_top - sin.size[1] - 10
        bloom, off = glow(sin, 14, 1.8, MAG)
        img.alpha_composite(bloom, (x + off, y + off))
        img.alpha_composite(sin, (x, y))

    # Luv, front and centre.
    luv = sprite('luv', 6, 32, px(13))
    lx, ly = (w - luv.size[0]) // 2, band_top - luv.size[1] - 6
    bloom, off = glow(luv, 26, 2.2, CYAN)
    img.alpha_composite(bloom, (lx + off, ly + off))
    img.alpha_composite(luv, (lx, ly))

    # Bottom band: who made it.
    bh = px(170)
    band = Image.new('RGBA', (w, bh), (0, 0, 0, 0))
    bp = band.load()

    for y in range(bh):
        a = int(240 * min(1.0, y / (bh * 0.32)))

        for x in range(w):
            bp[x, y] = (10, 5, 16, a)

    # The publisher is on the spine strip and in the corner mark already; down
    # here it only needs to say whose game it is.
    boxfont.centered(band, 'A LUVWRLD GAME', int(bh * 0.44), LILAC, px(4))
    img.alpha_composite(band, (0, h - bh))

    return img


def _platform_band(w, h, words='ADVANCE HOMEBREW'):
    """
    The silver strip down the left edge of a Game Boy Advance box.

    On a real box this carries the platform's own name in this exact place.
    That wordmark is Nintendo's, so the strip says what the thing is instead
    of whose it is.
    """
    band = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = band.load()

    for x in range(w):
        t = x / float(w - 1)
        # Brushed metal: a bright line off-centre, falling away to both edges.
        v = max(0.0, 1.0 - abs(t - 0.38) * 1.9)
        c = int(96 + 150 * v)

        for y in range(h):
            # A little vertical grain, so it reads as metal rather than a
            # flat grey rectangle.
            g = ((y * 7 + x * 3) % 11) - 5
            px[x, y] = (max(0, min(255, c + g)), max(0, min(255, c + g)),
                        max(0, min(255, c + g + 8)), 255)

    strip = Image.new('RGBA', (h, w), (0, 0, 0, 0))

    # Size to whichever runs out first, the strip's width or its length. The
    # spine carries a longer line than the face does, and picking the size off
    # the width alone clipped it to "'S FRIGHT NI".
    scale = max(2, w // 26)

    while scale > 2 and boxfont.measure(words, scale, 2) > h - int(w * 0.5):
        scale -= 1

    boxfont.centered(strip, words, (w - boxfont.HEIGHT * scale) // 2,
                     (26, 26, 34, 255), scale, tracking=2)
    band.alpha_composite(strip.rotate(90, expand=True))

    d = ImageDraw.Draw(band)
    d.line([(w - 1, 0), (w - 1, h)], fill=(40, 40, 48, 255), width=2)
    return band


def box_front(path, w=900, h=960):
    """
    The cover, in the shape a Game Boy Advance box actually is.

    Nearly square rather than poster-shaped, with the silver platform strip
    down the left edge and the publisher's mark in the top corner. The
    proportions and the furniture are taken off a blank retail box.
    """
    img = Image.new('RGBA', (w, h), INK)

    band_w = int(w * 0.17)
    art = _box_art(w - band_w, h)
    img.alpha_composite(art, (band_w, 0))
    img.alpha_composite(_platform_band(band_w, h, 'ADVANCE HOMEBREW'),
                        (0, 0))

    # Publisher's mark, top right, where a label would sit.
    mark = Image.new('RGBA', (196, 60), (0, 0, 0, 0))
    md = ImageDraw.Draw(mark)
    md.rounded_rectangle([0, 0, 195, 59], radius=9, fill=(14, 8, 22, 240),
                         outline=GOLD, width=3)
    boxfont.centered(mark, 'RETRO', 12, GOLD, 2)
    boxfont.centered(mark, 'RUMBLE', 34, GOLD, 2)
    img.alpha_composite(mark, (w - 196 - 20, 20))

    neon_frame(img, 14)
    img.convert('RGB').save(path)
    return path


def marquee(path, w=1200, h=380):
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    word = "LUV'S FRIGHT NIGHT"
    scale = 11
    block = Image.new('RGBA', (boxfont.measure(word, scale) + scale * 6,
                               boxfont.HEIGHT * scale + scale * 6), (0, 0, 0, 0))
    boxfont.draw(block, word, scale * 3 + scale, scale * 3 + scale, DGOLD, scale)
    boxfont.draw(block, word, scale * 3, scale * 3, GOLD, scale)

    x = (w - block.size[0]) // 2
    y = (h - block.size[1]) // 2 - 20
    bloom, off = glow(block, 15, 1.9, MAG)
    img.alpha_composite(bloom, (x + off, y + off))
    img.alpha_composite(block, (x, y))

    sub = Image.new('RGBA', (w, 60), (0, 0, 0, 0))
    boxfont.centered(sub, 'A GHOST IN BAD COMPANY', 0, CYAN, 4)
    bloom, off = glow(sub, 7, 2.2)
    img.alpha_composite(bloom, (off, y + block.size[1] + 10 + off))
    img.alpha_composite(sub, (0, y + block.size[1] + 10))

    img.save(path)
    return path


def fanart(path, shot, w=1920, h=1080):
    """A gameplay frame blown up to a wallpaper, with the lockup over it."""
    base = Image.open(shot).convert('RGBA')
    # Crop the HUD away -- a status bar stretched to wallpaper size reads as
    # a rendering fault, not as part of the picture.
    base = base.crop((0, 28, base.size[0], base.size[1]))
    big = base.resize((w, int(w * base.size[1] / base.size[0])), Image.NEAREST)

    img = Image.new('RGBA', (w, h), INK)
    img.alpha_composite(big, (0, (h - big.size[1]) // 2))

    # Darken from the left so the lockup has something to sit on.
    shade = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sp = shade.load()

    for x in range(w):
        a = int(215 * max(0.0, 1.0 - (x / (w * 0.62)) ** 1.4))

        for y in range(h):
            sp[x, y] = (8, 4, 16, a)

    img.alpha_composite(shade)
    img.alpha_composite(Image.new('RGBA', (w, h), (10, 5, 20, 70)))

    title, pad = title_block(scale_big=14, scale_small=9)
    img.alpha_composite(title, (int(w * 0.05) - pad, (h - title.size[1]) // 2 - 110))

    strip = Image.new('RGBA', (w, 60), (0, 0, 0, 0))
    boxfont.draw(strip, 'RETRO RUMBLE * LUVWRLD', 0, 0, LILAC, 3)
    img.alpha_composite(strip, (int(w * 0.05), h - 120))
    img.convert('RGB').save(path)
    return path


def ppm(name, where='shots'):
    return os.path.join(ROOT, 'tools', 'emu', where, name + '.ppm')


def copy_shot(src, dst, scale=1):
    im = Image.open(src).convert('RGB')

    if scale != 1:
        im = im.resize((im.size[0] * scale, im.size[1] * scale), Image.NEAREST)

    im.save(dst)


DESC = (
    "Luv is a ghost with a halo he did not earn and horns he did not ask for. "
    "Eight worlds of the underworld stand between him and the way out, each "
    "ruled by one of the seven deadly sins, and Hades keeps the door.\n\n"
    "A short, mean platformer in the Super Mario Land tradition: run, jump, "
    "stomp, and hold A to hover on a meter that drains. Four power-ups -- Soul "
    "Flame, Blessed Halo, Devil Dash and Wisp Wings -- plus a Purple Soul that "
    "buys you one extra hit. Sixteen stages, eight boss arenas, hidden rooms "
    "for anyone who checks the walls, and a different eerie trance loop in "
    "every world."
)


def gamelist(path, shots):
    rows = '\n'.join('         %s' % s for s in shots)
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<gameList>
  <game id="1" source="local">
    <path>./LuvsFrightNight.gba</path>
    <name>Luv's Fright Night</name>
    <sortname>Luvs Fright Night</sortname>
    <desc>%s</desc>
    <image>./media/mix/mix.png</image>
    <mix>./media/mix/mix.png</mix>
    <screenshot>./media/screenshot/gameplay-world-1.png</screenshot>
    <thumbnail>./media/box/box-front.png</thumbnail>
    <box>./media/box/box-front.png</box>
    <box3d>./media/box3d/box-3d.png</box3d>
    <support>./media/cartridge/cart.png</support>
    <cartridge>./media/cartridge/cart.png</cartridge>
    <marquee>./media/marquee/logo.png</marquee>
    <wheel>./media/marquee/logo.png</wheel>
    <fanart>./media/fanart/fanart.png</fanart>
    <titleshot>./media/titlescreen/title.png</titleshot>
    <developer>LuvWrld</developer>
    <publisher>Retro Rumble</publisher>
    <manual>./manual.pdf</manual>
    <genre>Platform</genre>
    <genreid>256</genreid>
    <players>2</players>
    <releasedate>20260824T000000</releasedate>
    <region>world</region>
    <lang>en</lang>
    <playcount>0</playcount>
    <favorite>false</favorite>
    <!-- every captured frame, for front ends that show a gallery:
%s
    -->
  </game>
</gameList>
""" % (DESC.replace('&', '&amp;').replace('<', '&lt;'), rows)
    open(path, 'w').write(xml)


def build_manual():
    """The booklet is generated from the same graphics as the ROM."""
    import gen_manual
    gen_manual.build()


def build_print():
    """
    The cartridge, the 3D box, the mix image and the PDF booklet.

    Runs last because every one of them is built out of the flat assets this
    script has just written.
    """
    import gen_print
    gen_print.main()


def main():
    media = os.path.join(OUT, 'media')

    for sub in ('box', 'marquee', 'screenshot', 'titlescreen', 'fanart'):
        os.makedirs(os.path.join(media, sub), exist_ok=True)

    shots = [
        ('01_title', 'shots', 'titlescreen/title.png'),
        ('02_card', 'shots', 'screenshot/world-card.png'),
        ('03_play_1_1', 'shots', 'screenshot/gameplay-world-1.png'),
        ('04_play_1_1b', 'shots', 'screenshot/gameplay-world-1b.png'),
        ('05_play_5_1', 'shots', 'screenshot/gameplay-world-5.png'),
        ('07_play_7_1', 'shots', 'screenshot/gameplay-world-7.png'),
        # boss_N is world N's arena - the numbering used to be off by one
        # against the sin it was named for.
        ('boss_2', 'shots2', 'screenshot/boss-avaritia.png'),
        ('boss_5', 'shots2', 'screenshot/boss-gula.png'),
        ('boss_8', 'shots2', 'screenshot/boss-hades.png'),
    ]

    written = []

    for name, where, dest in shots:
        src = ppm(name, where)

        if not os.path.exists(src):
            print('missing %s' % src)
            continue

        copy_shot(src, os.path.join(media, dest))
        written.append(dest)

    box_front(os.path.join(media, 'box', 'box-front.png'))
    marquee(os.path.join(media, 'marquee', 'logo.png'))
    fanart(os.path.join(media, 'fanart', 'fanart.png'),
           ppm('05_play_5_1'))

    rom = os.path.join(ROOT, 'LuvsFrightNight.gba')

    if os.path.exists(rom):
        shutil.copy(rom, os.path.join(OUT, 'LuvsFrightNight.gba'))

    build_manual()
    build_print()

    gamelist(os.path.join(OUT, 'gamelist.xml'), written)

    for root, _, files in os.walk(OUT):
        for f in sorted(files):
            p = os.path.join(root, f)
            print('%8d  %s' % (os.path.getsize(p), os.path.relpath(p, ROOT)))


if __name__ == '__main__':
    main()
