"""
The title wordmark.

The front end had been using Butano's stock system font with a gold tint, which
is the one thing that reads as unfinished the moment the game boots - no
cartridge of this era ever had a system-font title. This draws letterforms
instead: a chunky block face, big for the name and smaller for the rest, with
the game's own outline and shadow treatment.

Emitted as one 64x64 sprite item of two frames, left half and right half, so
the menu places two sprites side by side for a 128x64 logo. That costs 64 tiles
of sprite VRAM on a screen that has almost nothing else on it.
"""

import palette as pal
from pixel import Canvas

W, H = 64, 64          # one half; the logo is two of these side by side
FULL = 128

# A 5x7 block face. Only the letters the title needs, which is the whole point
# of drawing it here rather than shipping a font.
GLYPHS = {
    'L': ('X....', 'X....', 'X....', 'X....', 'X....', 'X....', 'XXXXX'),
    'U': ('X...X', 'X...X', 'X...X', 'X...X', 'X...X', 'X...X', '.XXX.'),
    'V': ('X...X', 'X...X', 'X...X', 'X...X', 'X...X', '.X.X.', '..X..'),
    "'": ('..X..', '..X..', '.....', '.....', '.....', '.....', '.....'),
    'S': ('.XXXX', 'X....', 'X....', '.XXX.', '....X', '....X', 'XXXX.'),
    'F': ('XXXXX', 'X....', 'X....', 'XXXX.', 'X....', 'X....', 'X....'),
    'R': ('XXXX.', 'X...X', 'X...X', 'XXXX.', 'X..X.', 'X...X', 'X...X'),
    'I': ('XXXXX', '..X..', '..X..', '..X..', '..X..', '..X..', 'XXXXX'),
    'G': ('.XXX.', 'X...X', 'X....', 'X..XX', 'X...X', 'X...X', '.XXX.'),
    'H': ('X...X', 'X...X', 'X...X', 'XXXXX', 'X...X', 'X...X', 'X...X'),
    'T': ('XXXXX', '..X..', '..X..', '..X..', '..X..', '..X..', '..X..'),
    'N': ('X...X', 'XX..X', 'X.X.X', 'X.X.X', 'X..XX', 'X...X', 'X...X'),
    ' ': ('.....', '.....', '.....', '.....', '.....', '.....', '.....'),
}

GLYPH_W, GLYPH_H = 5, 7


def measure(word, scale, gap, space_gap):
    total = 0

    for i, ch in enumerate(word):
        total += (space_gap if ch == ' ' else GLYPH_W * scale)

        if i < len(word) - 1:
            total += gap

    return total


def stamp(c, word, x, y, scale, colour, gap=3, space_gap=6):
    """Draw `word` with the block face, one filled rectangle per set pixel."""
    for ch in word:
        if ch == ' ':
            x += space_gap + gap
            continue

        rows = GLYPHS[ch]

        for ry, row in enumerate(rows):
            for rx, on in enumerate(row):
                if on == 'X':
                    c.rect(x + rx * scale, y + ry * scale,
                           x + rx * scale + scale - 1, y + ry * scale + scale - 1,
                           colour)

        x += GLYPH_W * scale + gap

    return x


def logo():
    """The whole 128x64 wordmark, before it is cut in half."""
    c = Canvas(FULL, H)

    top, bottom = "LUV'S", 'FRIGHT NIGHT'
    big, small = 3, 2

    # The lower line has to leave room for its own outline at both ends, or
    # the first F and the last T come back with a flat side.
    tw = measure(top, big, 3, 6)
    bw = measure(bottom, small, 1, 3)

    tx = (FULL - tw) // 2
    bx = (FULL - bw) // 2

    # A magenta ghost of the letters behind, offset down and right. It reads as
    # a printed mis-registration, which is exactly the look this wants.
    stamp(c, top, tx + 2, 8 + 3, big, pal.DMAG, gap=3)
    stamp(c, bottom, bx + 1, 34 + 2, small, pal.DMAG, gap=1, space_gap=3)

    stamp(c, top, tx, 8, big, pal.GOLD, gap=3)
    stamp(c, bottom, bx, 34, small, pal.MAG, gap=1, space_gap=3)

    c.outline(pal.INK)
    return c


def halves():
    """Left and right 64x64 frames of the wordmark."""
    full = logo()
    out = []

    for side in (0, 1):
        half = Canvas(W, H)

        for y in range(H):
            for x in range(W):
                half.px[y][x] = full.px[y][x + side * W]

        out.append(half)

    return out
