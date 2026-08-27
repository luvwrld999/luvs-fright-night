"""
World tilesets.

Levels are authored in 16x16 metatiles. Each tileset BMP is 16px wide, so grit
emits its 8x8 tiles in the order TL, TR, BL, BR - which means metatile M always
occupies tile indices 4M..4M+3 and the engine can index it with a shift.
"""

import math

import palette as pal
from pixel import Canvas

T = 16          # metatile size
COUNT = 16      # metatiles per world

# Metatile slots, shared by every world so one level file works anywhere.
(EMPTY, GROUND_TOP, GROUND_FILL, BLOCK, BREAKABLE, PLATFORM, SPIKES,
 LEDGE_L, LEDGE_R, PILLAR, DECOR, BG_A, BG_B, DOOR, CHAIN, HAZARD) = range(16)

NAMES = ['empty', 'ground_top', 'ground_fill', 'block', 'breakable', 'platform',
         'spikes', 'ledge_l', 'ledge_r', 'pillar', 'decor', 'bg_a', 'bg_b',
         'door', 'chain', 'hazard']

WORLDS = [
    dict(key='pride',     title='I. Superbia',  rock=pal.PURPLE, dark=pal.SHADOW,
         cap=pal.LILAC,  accent=pal.CYAN,   glow=pal.GOLD,  hazard=pal.CYAN,   motif='mirror'),
    dict(key='greed',     title='II. Avaritia', rock=pal.DGOLD,  dark=pal.SHADOW,
         cap=pal.GOLD,   accent=pal.WHITE,  glow=pal.GOLD,  hazard=pal.GOLD,   motif='coin'),
    dict(key='lust',      title='III. Luxuria', rock=pal.DMAG,   dark=pal.SHADOW,
         cap=pal.MAG,    accent=pal.DGREEN, glow=pal.MAG,   hazard=pal.DGREEN, motif='thorn'),
    dict(key='envy',      title='IV. Invidia',  rock=pal.DGREEN, dark=pal.SHADOW,
         cap=pal.GREEN,  accent=pal.TEAL,   glow=pal.GREEN, hazard=pal.GREEN,  motif='drip'),
    dict(key='gluttony',  title='V. Gula',      rock=pal.DRED,   dark=pal.SHADOW,
         cap=pal.RED,    accent=pal.GOLD,   glow=pal.MAG,   hazard=pal.RED,    motif='bone'),
    dict(key='wrath',     title='VI. Ira',      rock=pal.DGOLD,  dark=pal.SHADOW,
         cap=pal.RED,    accent=pal.GOLD,   glow=pal.GOLD,  hazard=pal.GOLD,   motif='crack'),
    dict(key='sloth',     title='VII. Acedia',  rock=pal.TEAL,   dark=pal.SHADOW,
         cap=pal.LILAC,  accent=pal.DGOLD,  glow=pal.DGOLD, hazard=pal.PURPLE, motif='cobweb'),
    dict(key='hades',     title='VIII. Hades',  rock=pal.DMAG,   dark=pal.SHADOW,
         cap=pal.PURPLE, accent=pal.MAG,    glow=pal.MAG,   hazard=pal.MAG,    motif='skull'),
]

# The front end's own masonry, and deliberately not a world's.
#
# The menu, the boards and the code screen used to borrow the Hades tileset,
# which meant the one knob that made Hades readable to play in also made every
# screen of text busier to read. This is the near-black wall those screens
# actually want: the same brickwork, drawn so far down that it reads as depth
# behind the letters rather than as pattern competing with them.
FRONTEND = dict(key='menu', title='Front end', rock=pal.SHADOW, dark=pal.INK,
                cap=pal.PURPLE, accent=pal.MAG, glow=pal.MAG, hazard=pal.MAG,
                motif='skull')


def frontend_tiles():
    return [BUILDERS[i](FRONTEND) for i in range(COUNT)]


def _noise(x, y, seed=0):
    """Cheap deterministic hash - gives the rock a bit of grain."""
    n = (x * 374761393 + y * 668265263 + seed * 1442695040888963407) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFF) / 255.0


def _rock_fill(c, th, seed=0, x0=0, y0=0, x1=T - 1, y1=T - 1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            n = _noise(x, y, seed)
            c.set(x, y, th['dark'] if n < 0.16 else th['rock'])


def _mortar(c, th, row_h=8, offset=True):
    for y in range(0, T, row_h):
        c.rect(0, y, T - 1, y, th['dark'])
    for y in range(0, T, row_h):
        x = 8 if (offset and (y // row_h) % 2) else 0
        c.rect(x, y, x, y + row_h - 1, th['dark'])


def _motif(c, th, x, y):
    """A small world-specific flourish, used on blocks and background tiles."""
    m = th['motif']
    a = th['accent']
    if m == 'mirror':
        c.poly([(x, y - 3), (x + 2, y), (x, y + 3), (x - 2, y)], a)
    elif m == 'coin':
        c.disc(x, y, 2.2, a)
        c.set(int(x), int(y), th['dark'])
    elif m == 'thorn':
        c.line(x - 3, y + 2, x, y - 3, a)
        c.line(x, y - 3, x + 3, y + 2, a)
    elif m == 'drip':
        c.disc(x, y - 1, 1.6, a)
        c.rect(x, y, x, y + 3, a)
    elif m == 'bone':
        c.rect(x - 3, y, x + 3, y, a)
        c.disc(x - 3, y, 1.2, a)
        c.disc(x + 3, y, 1.2, a)
    elif m == 'crack':
        c.line(x - 2, y - 3, x + 1, y, a)
        c.line(x + 1, y, x - 1, y + 3, a)
    elif m == 'cobweb':
        for k in range(3):
            c.line(x - 4, y - 4, x - 4 + k * 3, y + 3, a)
        c.line(x - 4, y - 1, x + 1, y + 1, a)
    elif m == 'skull':
        c.ellipse(x, y - 1, 2.6, 2.4, a)
        c.set(int(x - 1), int(y - 1), th['dark'])
        c.set(int(x + 1), int(y - 1), th['dark'])
        c.rect(x - 1, y + 2, x + 1, y + 2, a)


def _grass_cap(c, th, seed=1):
    """The lit crust on top of solid ground."""
    for x in range(T):
        h = 2 + int(_noise(x, 0, seed) * 2)
        c.rect(x, 0, x, h, th['cap'])
        c.set(x, h + 1, th['dark'])


# --- individual metatiles --------------------------------------------------
def _empty(th):
    return Canvas(T, T)


def _ground_top(th):
    c = Canvas(T, T)
    _rock_fill(c, th, 3)
    _grass_cap(c, th)
    return c


def _ground_fill(th):
    c = Canvas(T, T)
    _rock_fill(c, th, 7)
    return c


def _block(th):
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, th['rock'])
    _mortar(c, th)
    c.rect(1, 1, 6, 1, th['cap'])
    c.rect(9, 9, 14, 9, th['cap'])
    return c


def _breakable(th):
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, th['rock'])
    _mortar(c, th, row_h=4)
    _motif(c, th, 8, 8)
    c.rect(0, 0, T - 1, 0, th['cap'])
    return c


def _platform(th):
    """One-way: solid on top, passable from below."""
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, 5, th['rock'])
    c.rect(0, 0, T - 1, 1, th['cap'])
    c.rect(0, 6, T - 1, 6, th['dark'])
    for x in range(1, T, 5):
        c.rect(x, 7, x + 1, 9, th['dark'])
    return c


def _spikes(th):
    c = Canvas(T, T)
    for i in range(4):
        x = i * 4 + 2
        c.poly([(x - 2, T - 1), (x + 2, T - 1), (x, 3)], th['hazard'])
        c.line(x - 1, T - 2, x, 5, pal.WHITE)
    c.rect(0, T - 2, T - 1, T - 1, th['dark'])
    return c


def _ledge(th, right):
    c = Canvas(T, T)
    _rock_fill(c, th, 11)
    _grass_cap(c, th)
    for y in range(T):
        cut = int(y * 0.45)
        for k in range(cut):
            c.set(T - 1 - k if right else k, y, pal.KEY)
    return c


def _pillar(th):
    c = Canvas(T, T)
    c.rect(2, 0, 13, T - 1, th['rock'])
    c.rect(2, 0, 3, T - 1, th['cap'])
    c.rect(12, 0, 13, T - 1, th['dark'])
    for y in range(2, T, 5):
        c.rect(1, y, 14, y + 1, th['dark'])
    return c


def _decor(th):
    """A wall lamp / world flourish that also lights the tile behind it."""
    c = Canvas(T, T)
    c.rect(6, 6, 9, 13, th['dark'])
    c.rect(6, 6, 6, 13, th['rock'])
    c.disc(8, 5, 3.2, th['glow'])
    c.disc(8, 5, 1.6, pal.WHITE)
    return c


def _bg(th, variant):
    """Far-plane masonry. Deliberately low contrast - it is scenery, not level."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            c.set(x, y, th['rock'] if _noise(x, y, 20 + variant) > 0.88 else th['dark'])
    if variant == 0:
        for y in (0, 8):
            c.rect(0, y, T - 1, y, pal.INK)
        c.rect(0 if (0 // 8) % 2 else 8, 0, 0 if False else 8, 7, pal.INK)
        c.rect(0, 8, 0, 15, pal.INK)
    else:
        faint = Canvas(T, T)
        _motif(faint, th, 8, 8)
        for y in range(T):
            for x in range(T):
                if faint.px[y][x] != pal.KEY:
                    c.px[y][x] = th['rock']
    return c


def _door(th):
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, th['dark'])
    c.rect(2, 2, 13, T - 1, pal.INK)
    c.ellipse(8, 3, 6.0, 3.0, th['accent'])
    c.ellipse(8, 3, 4.0, 1.8, pal.INK)
    c.rect(0, 0, 1, T - 1, th['cap'])
    c.rect(14, 0, T - 1, T - 1, th['cap'])
    return c


def _chain(th):
    c = Canvas(T, T)
    for i in range(4):
        c.ellipse(8, i * 4 + 2, 2.0, 1.8, th['accent'])
        c.ellipse(8, i * 4 + 2, 0.9, 0.8, pal.KEY)
    return c


def _hazard(th):
    """Lava / goo - a dark mass with a hot crest. Lethal, and it glows."""
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, pal.DARKER.get(th['hazard'], th['dark']))
    for x in range(T):
        crest = 1 + int(1.5 * (0.5 + 0.5 * math.sin(x * 0.9)))
        c.rect(x, 0, x, crest, th['hazard'])
        c.set(x, 0, pal.WHITE)
    for y in range(5, T):
        for x in range(T):
            if _noise(x, y, 31) < 0.10:
                c.set(x, y, th['hazard'])
    return c


BUILDERS = [
    _empty, _ground_top, _ground_fill, _block, _breakable, _platform, _spikes,
    lambda th: _ledge(th, False), lambda th: _ledge(th, True), _pillar, _decor,
    lambda th: _bg(th, 0), lambda th: _bg(th, 1), _door, _chain, _hazard,
]


def world_tiles(world_index):
    """The 16 metatiles of one world, in slot order."""
    th = WORLDS[world_index]
    return [BUILDERS[i](th) for i in range(COUNT)]
