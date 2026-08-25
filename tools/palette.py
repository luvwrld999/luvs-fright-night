"""
Luv's Fright Night - the shared "Halloween neon" palette.

16 colors, 4bpp. Index 0 is the GBA transparency slot and is never drawn.
Every value is snapped to the GBA's 5-bit-per-channel color space so what we
preview on the Mac is exactly what the hardware shows.
"""

KEY    = 0   # transparent
INK    = 1   # near-black outline, purple tinted
SHADOW = 2   # deep purple
PURPLE = 3   # mid purple
WHITE  = 4   # bone white
LILAC  = 5   # ghost body shade
CYAN   = 6   # spectral rim light
TEAL   = 7   # dim cyan
MAG    = 8   # hot magenta
DMAG   = 9   # dark magenta
RED    = 10  # devil red
DRED   = 11  # dark devil red
GOLD   = 12  # halo gold
DGOLD  = 13  # dark halo gold
GREEN  = 14  # toxic green
DGREEN = 15  # dark toxic green

NAMES = ['KEY', 'INK', 'SHADOW', 'PURPLE', 'WHITE', 'LILAC', 'CYAN', 'TEAL',
         'MAG', 'DMAG', 'RED', 'DRED', 'GOLD', 'DGOLD', 'GREEN', 'DGREEN']


def _snap(c):
    """Snap an 8-bit channel to the GBA's 5-bit color depth."""
    return (c >> 3) * 255 // 31


RGB = [_tuple for _tuple in [
    (255,   0, 255),   # 0  KEY
    ( 16,   8,  24),   # 1  INK
    ( 48,  24,  72),   # 2  SHADOW
    ( 96,  48, 136),   # 3  PURPLE
    (248, 248, 255),   # 4  WHITE
    (192, 160, 232),   # 5  LILAC
    (104, 240, 255),   # 6  CYAN
    ( 40, 144, 176),   # 7  TEAL
    (255,  48, 176),   # 8  MAG
    (160,  16, 104),   # 9  DMAG
    (255,  56,  40),   # 10 RED
    (136,  24,  16),   # 11 DRED
    (255, 216,  56),   # 12 GOLD
    (192, 136,   0),   # 13 DGOLD
    (124, 255,  56),   # 14 GREEN
    ( 40, 136,  16),   # 15 DGREEN
]]
RGB = [tuple(_snap(v) for v in c) for c in RGB]

# Darker counterpart of each color, used by the automatic shading pass.
DARKER = {
    WHITE: LILAC, LILAC: PURPLE, CYAN: TEAL, TEAL: SHADOW,
    MAG: DMAG, DMAG: SHADOW, RED: DRED, DRED: SHADOW,
    GOLD: DGOLD, DGOLD: DRED, GREEN: DGREEN, DGREEN: SHADOW,
    PURPLE: SHADOW, SHADOW: INK, INK: INK, KEY: KEY,
}


def flat_palette():
    """256-entry flat RGB list for Pillow's putpalette()."""
    out = []
    for c in RGB:
        out.extend(c)
    out.extend([0, 0, 0] * (256 - len(RGB)))
    return out
