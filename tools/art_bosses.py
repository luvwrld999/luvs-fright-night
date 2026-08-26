"""
The seven deadly sins, and the king they answer to.

Sin bosses are 32x32; Hades is 64x64. Each is built from separately outlined
parts and then composited, which is what stops a 32px monster from collapsing
into one unreadable blob - the black seam between a fist and a torso is doing
most of the work at this size.

Poses: 0-1 idle, 2 wind-up, 3-4 attack, 5 hurt, 6-7 death.
"""

import math

import palette as pal
from art_enemies import halo, horns
from pixel import Canvas

B = 32
BIG = 64
POSE_NAMES = ['idle', 'idle2', 'wind', 'atk', 'atk2', 'hurt', 'die', 'die2']


def piece(w, h, draw):
    """Draw one body part on its own canvas and outline it before it is stamped."""
    c = Canvas(w, h)
    draw(c)
    c.shade(light=(-1, -1))
    c.outline(pal.INK)
    return c


def sockets(c, cx, cy, spread, color, r=1.6, lid=False):
    """Deep eye sockets with a burning pinpoint - the sins never blink."""
    for side in (-1, 1):
        x = cx + side * spread
        c.ellipse(x, cy, r + 1.2, r + 1.2, pal.INK)
        if lid:
            c.rect(int(x - r), int(cy), int(x + r), int(cy), pal.INK)
        else:
            c.disc(x, cy, r, color)


def _pose(p):
    """Shared timing: (bob, reach, hurt?, dying?, collapse)."""
    # The two idle frames used to differ by a single pixel of bob, which at
    # this size is no motion at all - every boss looked frozen until it
    # attacked. Two pixels of rise and a pixel of sway is the difference
    # between a statue and something breathing.
    bob = [0, 2, -1, 0, 1, 1, 3, 5][p]
    reach = [0, 0, -2, 3, 5, -1, 0, 0][p]
    return bob, reach, p == 5, p >= 6, (p - 5) * 2 if p >= 6 else 0


# Sideways drift per frame, applied to the finished piece. Doing it here rather
# than inside eight separate boss functions keeps the timing in one place.
SWAY = [0, 1, 0, -1, 1, 0, 0, 0]


def breathing(fn):
    """Wrap a boss so its idle sways as well as bobs."""
    def wrapped(p):
        c = fn(p)
        return c.shifted(SWAY[p], 0) if SWAY[p] else c

    return wrapped


def tint(base, hurt):
    return pal.WHITE if hurt else base


# ---------------------------------------------------------------------------
# I. SUPERBIA - Pride. Fights behind a fan of mirrors and copies your moves.
def superbia(p):
    c = Canvas(B, B)
    bob, reach, hurt, dying, drop = _pose(p)
    body = tint(pal.MAG, hurt)

    if not dying:
        fan = Canvas(B, B)
        for i in range(7):
            a = -2.75 + i * 0.39
            mx, my = 16 + math.cos(a) * 10.5, 13 + math.sin(a) * 10.5 + bob
            fan.poly([(mx - 2.0, my + 3.0), (mx + 2.0, my + 3.0), (mx, my - 3.6)],
                     pal.CYAN if i % 2 else pal.LILAC)
        fan.outline(pal.INK)
        c.paste(fan)

    c.paste(piece(B, B, lambda t: t.ellipse(16, 22 + bob + drop, 6.5, 8.0 - drop, body)))
    c.paste(piece(B, B, lambda t: t.ellipse(16, 13 + bob, 6.2, 5.2, body)))
    mirror = piece(B, B, lambda t: t.ellipse(16, 13 + bob, 4.2, 3.4, pal.WHITE))
    c.paste(mirror)
    if not dying:
        sockets(c, 16, 12 + bob, 2.2, pal.MAG, 1.0)
        c.rect(14, 15 + bob, 17, 15 + bob, pal.INK)
    halo(c, 16, 3.6 + bob, 6.0, 2.4)
    halo(c, 16, 6.6 + bob, 3.6, 1.6)             # a second, vainer halo
    return c


# II. AVARITIA - Greed. Pear-shaped with hoarding arms it cannot retract.
def avaritia(p):
    c = Canvas(B, B)
    bob, reach, hurt, dying, drop = _pose(p)
    body = tint(pal.DGOLD, hurt)

    for side in (-1, 1):                          # long hoarding arms
        ax = 16 + side * (9 + reach)
        c.paste(piece(B, B, lambda t, s=side, x=ax: (
            t.curve([(16 + s * 5, 17 + bob), (x, 20 + bob), (x + s * 2, 25 + bob)],
                    body, thick=3),
            t.ellipse(x + s * 2.5, 26 + bob, 3.2, 2.8, body))))
    c.paste(piece(B, B, lambda t: t.poly(
        [(16, 11 + bob), (27, 29 + bob - drop), (5, 29 + bob - drop)], body)))   # gut
    c.paste(piece(B, B, lambda t: t.ellipse(16, 11 + bob, 5.4, 4.6, body)))      # head
    if not dying:
        for ox, oy in [(-5, 22), (0, 25), (5, 22), (-2, 19), (3, 18)]:
            c.paste(piece(B, B, lambda t, a=ox, b=oy: t.disc(16 + a, b + bob, 1.8, pal.GOLD)))
        sockets(c, 16, 10 + bob, 2.4, pal.GOLD, 1.2)
    c.rect(13, 14 + bob, 18, 14 + bob, pal.INK)
    horns(c, 16, 8.0 + bob, spread=7.0, height=4.4, color=pal.DRED)
    halo(c, 16, 2.6 + bob, 5.0, 2.0)
    return c


# III. LUXURIA - Lust. A thorned lantern-heart; its light charms your enemies.
def luxuria(p):
    c = Canvas(B, B)
    bob, reach, hurt, dying, drop = _pose(p)
    body = tint(pal.DMAG, hurt)

    thorns = Canvas(B, B)
    for i in range(9):
        a = -2.95 + i * 0.33
        thorns.line(16 + math.cos(a) * 8, 17 + math.sin(a) * 8 + bob,
                    16 + math.cos(a) * (10.5 + (reach * 0.5 if i % 2 else 0)),
                    17 + math.sin(a) * (10.5 + (reach * 0.5 if i % 2 else 0)) + bob,
                    pal.DGREEN)
    thorns.outline(pal.INK)
    c.paste(thorns)

    c.paste(piece(B, B, lambda t: t.poly(
        [(16, 8 + bob), (27, 19 + bob), (16, 30 + bob - drop), (5, 19 + bob)], body)))
    if not dying:
        c.paste(piece(B, B, lambda t: t.ellipse(16, 20 + bob, 5.0, 5.4, pal.MAG)))
        c.paste(piece(B, B, lambda t: t.ellipse(16, 20 + bob, 2.8, 3.2, pal.GOLD)))
        sockets(c, 16, 14 + bob, 2.8, pal.CYAN, 1.0)
    for side in (-1, 1):                          # rose vines
        c.curve([(16 + side * 6, 25 + bob), (16 + side * 11, 27 + bob),
                 (16 + side * 13, 23 + bob)], pal.DGREEN)
    halo(c, 16, 3.2 + bob, 4.6, 1.9)
    return c


# IV. INVIDIA - Envy. Hunched, two-headed, and one head is always wearing yours.
def invidia(p):
    c = Canvas(B, B)
    bob, reach, hurt, dying, drop = _pose(p)
    body = tint(pal.DGREEN, hurt)

    for side in (-1, 1):                          # covetous arms
        c.paste(piece(B, B, lambda t, s=side: t.curve(
            [(16 + s * 6, 20 + bob), (16 + s * (11 + reach), 23 + bob),
             (16 + s * (12 + reach), 28 + bob)], body, thick=3)))
    c.paste(piece(B, B, lambda t: t.ellipse(16, 23 + bob, 7.5, 6.5 - drop, body)))
    c.paste(piece(B, B, lambda t: t.ellipse(11, 13 + bob, 5.0, 4.4, body)))     # its face
    c.paste(piece(B, B, lambda t: t.ellipse(22, 15 + bob, 4.4, 4.0, pal.WHITE)))  # yours
    if not dying:
        sockets(c, 11, 12 + bob, 2.0, pal.GREEN, 1.0)
        sockets(c, 22, 14 + bob, 1.8, pal.CYAN, 0.9)
        c.rect(20, 17 + bob, 23, 17 + bob, pal.INK)
    c.rect(9, 16 + bob, 13, 16 + bob, pal.INK)
    horns(c, 11, 10.0 + bob, spread=6.0, height=4.2, color=pal.GREEN)
    halo(c, 11, 4.0 + bob, 4.4, 1.8)
    halo(c, 22, 6.5 + bob, 3.8, 1.6)
    return c


# V. GULA - Gluttony. A mouth that grew a body to carry it around.
def gula(p):
    c = Canvas(B, B)
    bob, reach, hurt, dying, drop = _pose(p)
    body = tint(pal.RED, hurt)
    gape = [3, 4, 2, 8, 10, 3, 5, 7][p]

    for side in (-1, 1):                          # stubby legs
        c.paste(piece(B, B, lambda t, s=side: t.rect(
            16 + s * 7 - 1, 27 + bob, 16 + s * 7 + 1, 30 + bob, pal.DRED)))
    c.paste(piece(B, B, lambda t: t.ellipse(16, 20 + bob, 11.0 - drop, 9.0 - drop, body)))
    maw = Canvas(B, B)
    maw.ellipse(16, 21 + bob, 8.0, gape, pal.INK)
    if not dying:
        maw.ellipse(16, 23 + bob, 4.5, gape * 0.45, pal.MAG)          # tongue
    c.paste(maw)
    for x in range(8, 25, 4):                     # teeth around the gape
        c.poly([(x, 21 + bob - gape), (x + 2.5, 21 + bob - gape), (x + 1.2, 22 + bob - gape * 0.45)], pal.WHITE)
        c.poly([(x, 21 + bob + gape), (x + 2.5, 21 + bob + gape), (x + 1.2, 20 + bob + gape * 0.45)], pal.WHITE)
    if not dying:
        sockets(c, 16, 10 + bob, 4.5, pal.GOLD, 1.4)
    horns(c, 16, 8.0 + bob, spread=6.5, height=4.0, color=pal.DRED)
    halo(c, 16, 2.8 + bob, 4.8, 2.0)
    return c


# VI. IRA - Wrath. Broad, cracked and molten; accuracy is the first thing it loses.
def ira(p):
    c = Canvas(B, B)
    bob, reach, hurt, dying, drop = _pose(p)
    body = tint(pal.PURPLE, hurt)
    crack = pal.GOLD if dying else pal.RED

    for side in (-1, 1):                          # huge swinging fists
        fx = 16 + side * (11 + reach)
        c.paste(piece(B, B, lambda t, s=side, x=fx: (
            t.curve([(16 + s * 6, 18 + bob), (x, 21 + bob)], body, thick=3),
            t.ellipse(x, 24 + bob - max(reach, 0), 4.2, 3.8, body))))
    c.paste(piece(B, B, lambda t: t.ellipse(16, 21 + bob, 8.5, 8.0 - drop, body)))
    c.paste(piece(B, B, lambda t: t.ellipse(16, 11 + bob, 5.0, 4.2, body)))
    for ax, ay, bx, by in [(10, 17, 15, 26), (21, 16, 18, 27), (12, 25, 22, 22)]:
        c.line(ax, ay + bob, bx, by + bob, crack)
    if not dying:
        sockets(c, 16, 10 + bob, 2.2, pal.GOLD, 1.1)
        c.rect(13, 14 + bob, 18, 15 + bob, crack)             # roar
    horns(c, 16, 8.0 + bob, spread=9.0, height=5.5, color=pal.RED)
    halo(c, 16, 2.4 + bob, 5.2, 2.1)
    return c


# VII. ACEDIA - Sloth. Barely moves; the arena does the fighting for it.
def acedia(p):
    """
    Sloth. It never moves, so the silhouette has to do all the work: a mound
    that has given up standing, a head sliding off the front of it, and a halo
    that stopped being held up some time ago.

    The old one was a small purple lump on a dark background - the right idea
    at the wrong size and with nothing to read against. This one fills its
    frame and carries a pale rim along the top so the shape survives whatever
    tileset is behind it.
    """
    c = Canvas(B, B)
    bob, reach, hurt, dying, drop = _pose(p)
    body = tint(pal.PURPLE, hurt)
    droop = [0, 1, 1, 2, 3, 0, 4, 6][p]

    # Chains it cannot be bothered to drag, pooled rather than hanging.
    for side in (-1, 1):
        for k in range(5):
            c.disc(16 + side * (9 + k * 2), 29 + bob + (k % 2), 1.3, pal.DGOLD)

    # The mound, wide and low, sagging further as it dies.
    c.paste(piece(B, B, lambda t: t.ellipse(16, 24 + bob, 14.0,
                                            8.0 - drop * 0.6, body)))

    # A pale band along the top, so it is never a flat shape in a dark room.
    if not dying:
        c.paste(piece(B, B, lambda t: t.ellipse(16, 21 + bob, 11.0, 3.0,
                                                pal.SHADOW)))
        c.paste(piece(B, B, lambda t: t.ellipse(16, 19.5 + bob, 7.5, 1.6,
                                                pal.TEAL)))

    # The head, slumped forward off the mass rather than sitting on it.
    c.paste(piece(B, B, lambda t: t.ellipse(15, 16 + bob + droop, 8.0, 6.5,
                                            body)))

    if not dying:
        # Heavy lids: a lash line with the eye barely under it.
        for side in (-1, 1):
            ex = int(15 + side * 4)
            c.rect(ex - 2, 15 + bob + droop, ex + 1, 15 + bob + droop, pal.INK)
            c.set(ex, 16 + bob + droop, pal.DMAG)

        # A slack mouth, open because closing it is effort.
        c.ellipse(15, 20 + bob + droop, 3.2, 1.8, pal.INK, fill=True)

    # It is melting at the edges.
    for i in range(4):
        c.paste(piece(B, B, lambda t, a=i: t.disc(7 + a * 6, 31 + bob - (a % 2),
                                                  1.6, body)))

    horns(c, 15, 11.5 + bob + droop, spread=8.0, height=4.4, color=pal.SHADOW)

    # Even the halo has given up: off centre and tilted off the head.
    halo(c, 19, 7.5 + bob + droop, 5.4, 2.0)
    return c


# VIII. HADES - king of the underworld, 64x64 and three phases deep.
def hades(p):
    c = Canvas(BIG, BIG)
    bob, reach, hurt, dying, drop = _pose(p)
    body = tint(pal.SHADOW, hurt)
    bone = pal.LILAC if dying else pal.WHITE
    cx = 32

    crown = Canvas(BIG, BIG)
    for i in range(9):                            # crown of black flame
        a = -2.75 + i * 0.34
        fx, fy = cx + math.cos(a) * 16, 26 + math.sin(a) * 16 + bob
        crown.poly([(fx - 2.6, fy + 3.5), (fx + 2.6, fy + 3.5), (fx, fy - 7.0)],
                   pal.MAG if i % 2 else pal.PURPLE)
    crown.outline(pal.INK)
    c.paste(crown)

    for side in (-1, 1):                          # skeletal hands
        hx = cx + side * (20 + reach)
        c.paste(piece(BIG, BIG, lambda t, s=side, x=hx: (
            t.curve([(cx + s * 12, 40 + bob), (x, 44 + bob)], body, thick=4),
            t.ellipse(x, 47 + bob, 5.0, 5.5, bone))))
    c.paste(piece(BIG, BIG, lambda t: t.poly(
        [(cx - 19, 62), (cx + 19, 62), (cx + 12, 34 + bob), (cx - 12, 34 + bob)], body)))
    c.paste(piece(BIG, BIG, lambda t: t.ellipse(cx, 27 + bob, 11.5, 10.5, bone)))
    c.paste(piece(BIG, BIG, lambda t: t.ellipse(cx, 35 + bob, 6.5, 4.0, bone)))
    for side in (-1, 1):
        c.ellipse(cx + side * 5, 26 + bob, 3.6, 3.6, pal.INK)
        if not dying:
            c.disc(cx + side * 5, 26 + bob, 1.8, pal.MAG if p < 3 else pal.GOLD)
    c.ellipse(cx, 31 + bob, 1.6, 1.8, pal.INK)                    # nasal cavity
    for x in range(-5, 6, 3):
        c.rect(cx + x, 33 + bob, cx + x + 1, 36 + bob, pal.INK)
    if not dying:
        c.paste(piece(BIG, BIG, lambda t: (t.ellipse(cx, 48 + bob, 5.0, 5.0, pal.GOLD),
                                           t.ellipse(cx, 48 + bob, 2.4, 2.4, pal.WHITE))))
    horns(c, cx, 20.0 + bob, spread=19.0, height=11.0, color=pal.RED)
    halo(c, cx, 7.0 + bob, 10.0, 3.8)
    return c


BOSSES = [
    ('superbia', breathing(superbia), B, 'I. Pride'),
    ('avaritia', breathing(avaritia), B, 'II. Greed'),
    ('luxuria', breathing(luxuria), B, 'III. Lust'),
    ('invidia', breathing(invidia), B, 'IV. Envy'),
    ('gula', breathing(gula), B, 'V. Gluttony'),
    ('ira', breathing(ira), B, 'VI. Wrath'),
    ('acedia', breathing(acedia), B, 'VII. Sloth'),
    ('hades', breathing(hades), BIG, 'VIII. Hades'),
]
