"""Pickups, projectiles and HUD bits."""

import math

import palette as pal
from pixel import Canvas


def soul_orb(f):
    """The level currency: a drifting soul. 8x8."""
    c = Canvas(8, 8)
    r = 3.2 + 0.35 * math.sin(f * math.pi / 2)
    c.disc(4, 4, r, pal.TEAL)
    c.disc(4, 4, r - 1.0, pal.CYAN)
    c.disc(4, 3.6, r - 2.2, pal.WHITE)
    c.outline(pal.INK)
    return c


def soul_flame(f):
    """Luv's projectile: a bouncing blue flame. 8x8."""
    c = Canvas(8, 8)
    lean = [0.0, 0.5, 0.0, -0.5][f % 4]
    c.ellipse(4 + lean, 5.2, 3.0, 2.8, pal.TEAL)          # teardrop body
    c.poly([(1.6 + lean, 5.0), (6.4 + lean, 5.0), (4 + lean * 2, 0.2)], pal.TEAL)
    c.ellipse(4 + lean, 5.4, 1.9, 1.8, pal.CYAN)
    c.poly([(2.6 + lean, 5.4), (5.4 + lean, 5.4), (4 + lean * 2, 2.0)], pal.CYAN)
    c.ellipse(4 + lean, 5.6, 0.9, 0.9, pal.WHITE)
    c.outline(pal.INK)
    return c


def _capsule(c, color):
    """Shared pickup shell so the four power-ups read as a set."""
    c.ellipse(8, 8.5, 6.5, 6.5, color)
    c.ellipse(8, 8.5, 5.0, 5.0, pal.INK)


def pu_soul_flame(f):
    c = Canvas(16, 16)
    _capsule(c, pal.TEAL)
    b = f % 2
    c.poly([(5, 13), (11, 13), (9.5, 6 - b), (8, 8 - b), (6, 5 - b)], pal.CYAN)
    c.poly([(7, 13), (9.5, 13), (8.5, 8 - b)], pal.WHITE)
    c.outline(pal.INK)
    return c


def pu_purple_soul(f):
    """
    The extra hit. Drawn as a tiny version of what Luv turns into, so the
    pickup tells you what it does before you touch it.
    """
    c = Canvas(16, 16)
    _capsule(c, pal.DGREEN)
    b = f % 2

    # The ghost is outlined on its own, so the lime edge belongs to it rather
    # than becoming a fat ring around the whole pickup.
    ghost = Canvas(16, 16)
    ghost.ellipse(8, 8 - b, 3.2, 3.0, pal.PURPLE)
    ghost.rect(5, 8 - b, 10, 11 - b, pal.PURPLE)
    for x, h in ((5, 0), (6, 1), (7, 0), (8, 1), (9, 0), (10, 1)):
        ghost.set(x, 12 - b - h, pal.PURPLE)

    for side in (-1, 1):
        ghost.set(int(8 + side * 2), 8 - b, pal.GREEN)
    ghost.rect(7, 10 - b, 8, 10 - b, pal.GREEN)
    ghost.outline(pal.GREEN)

    c.paste(ghost)
    c.outline(pal.INK)
    return c


def pu_devil_dash(f):
    c = Canvas(16, 16)
    _capsule(c, pal.DRED)
    b = f % 2
    c.poly([(9, 3), (12, 8), (9.5, 8), (11, 13), (5, 7.5), (8, 7.5), (6.5, 3)], pal.RED)
    if b:
        c.poly([(9, 4), (10.5, 7.5), (9, 7.5), (10, 11)], pal.GOLD)
    c.outline(pal.INK)
    return c


def pu_wisp_wings(f):
    c = Canvas(16, 16)
    _capsule(c, pal.TEAL)
    b = f % 2
    for side in (-1, 1):
        c.poly([(8, 6), (8 + side * 6, 4 - b), (8 + side * 5, 9 + b), (8, 10)], pal.CYAN)
    c.ellipse(8, 8, 1.4, 2.4, pal.WHITE)
    c.outline(pal.INK)
    return c


def one_up(f):
    """A spare life: a tiny green Luv."""
    c = Canvas(16, 16)
    b = f % 2
    c.ellipse(8, 6.5 - b, 3.6, 3.4, pal.GREEN)
    for x in range(4, 12):
        c.rect(x, 9 - b, x, 11 - b + ((x // 2) % 2), pal.GREEN)
    for side in (-1, 1):                      # horns
        c.line(8 + side * 2, 4 - b, 8 + side * 3, 2 - b, pal.DGREEN)
    c.ellipse(8, 1.6 - b, 3.0, 1.2, pal.GOLD)
    for side in (-1, 1):
        c.set(int(8 + side * 1.5), 6 - b, pal.INK)
    c.outline(pal.INK)
    return c


def checkpoint(f):
    """A candle that lights when Luv passes it."""
    c = Canvas(16, 16)
    lit = f >= 2
    c.rect(6, 8, 9, 15, pal.LILAC)
    c.rect(6, 8, 6, 15, pal.WHITE)
    c.rect(5, 14, 10, 15, pal.PURPLE)
    c.line(8, 8, 8, 7, pal.INK)
    if lit:
        h = f % 2
        c.poly([(5.6, 6.5), (10.4, 6.5), (8, 1.0 + h)], pal.RED)
        c.poly([(6.4, 6.0), (9.6, 6.0), (8, 2.2 + h)], pal.GOLD)
        c.poly([(7.2, 5.5), (8.8, 5.5), (8, 3.6 + h)], pal.WHITE)
    c.outline(pal.INK)
    return c


def gate(f):
    """Level exit: a torn seam between worlds. 16x32."""
    c = Canvas(16, 32)
    b = f % 2
    c.rect(2, 4, 13, 31, pal.SHADOW)
    for y in range(4, 32):
        w = 4.5 + 1.5 * math.sin(y * 0.5 + b)
        c.rect(8 - w, y, 8 + w, y, pal.PURPLE)
        if y % 3 == b:
            c.rect(8 - w * 0.4, y, 8 + w * 0.4, y, pal.MAG)
    c.ellipse(8, 4, 6.0, 2.5, pal.MAG)
    c.ellipse(8, 4, 3.5, 1.2, pal.CYAN)
    c.outline(pal.INK)
    return c


def hud_halo(f):
    """Life icon. 8x8."""
    c = Canvas(8, 8)
    c.ellipse(4, 4, 3.4, 2.2, pal.GOLD)
    c.ellipse(4, 4, 1.8, 0.9, pal.KEY)
    c.outline(pal.INK)
    return c


def hud_meter(f):
    """Hover-meter segment: 0 empty, 1 full. 8x8."""
    c = Canvas(8, 8)
    c.rect(1, 2, 6, 5, pal.SHADOW if f == 0 else pal.CYAN)
    if f:
        c.rect(1, 2, 6, 2, pal.WHITE)
    c.outline(pal.INK)
    return c


ITEMS_8 = [
    ('soul_orb', soul_orb, 4),
    ('soul_flame', soul_flame, 4),
    ('hud_halo', hud_halo, 1),
    ('hud_meter', hud_meter, 2),
]
ITEMS_16 = [
    ('pu_soul_flame', pu_soul_flame, 2),
    ('pu_purple_soul', pu_purple_soul, 2),
    ('pu_devil_dash', pu_devil_dash, 2),
    ('pu_wisp_wings', pu_wisp_wings, 2),
    ('one_up', one_up, 2),
    ('checkpoint', checkpoint, 4),
]
ITEMS_16x32 = [
    ('gate', gate, 2),
]
