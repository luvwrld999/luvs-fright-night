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


# Where each claw sits and how long it is. Two of them reach past the rim of
# the hole, two are still climbing out - a hand caught mid-grab reads as
# something arriving, where four matched spikes would read as a fence.
_CLAWS = [
    (4.0, 9.0, -0.50),
    (6.0, 14.0, -0.16),
    (9.0, 13.0, 0.16),
    (11.0, 8.0, 0.50),
]


def gate(f):
    """
    Level exit: a glowing black hole with demon claws coming out of it. 16x32.

    The hole is drawn as rings from the outside in, ending on flat black - the
    glow has to be at the edge, because a bright centre would swallow the claws
    silhouetted against it.
    """
    c = Canvas(16, 32)
    b = f % 2
    pulse = 0.6 * math.sin(f * 1.6)

    # The hole: a standing oval of nothing with a lit rim.
    cy = 21.0
    for i, (rx, ry, colour) in enumerate((
            (7.2, 10.6, pal.MAG),
            (6.6, 9.8, pal.PURPLE),
            (6.0, 9.0, pal.SHADOW),
            (5.2, 8.0, pal.INK))):
        c.ellipse(8, cy, rx + (pulse if i == 0 else 0), ry + (pulse if i == 0 else 0),
                  colour, fill=True)

    # A few sparks caught in the rim light, turning with the frame.
    for k in range(3):
        a = (f * 0.9) + k * 2.1
        c.set(int(round(8 + 6.4 * math.cos(a))),
              int(round(cy + 9.4 * math.sin(a))), pal.CYAN)

    # The claws: a tapering finger with a hooked tip, hooking inward.
    # Rooted well down inside the hole, so they read as coming out of it
    # rather than standing on the rim.
    root = cy + 3.0

    for x0, length, lean in _CLAWS:
        reach = length + (1.0 if b else 0.0)

        for step in range(int(reach)):
            t = step / max(reach - 1, 1.0)
            x = int(round(x0 + lean * step * 0.6))
            y = int(round(root - step))

            # One pixel wide for most of its length, two only at the knuckle.
            # Three-wide claws merged into a pair of blobs at this size.
            c.set(x, y, pal.RED)

            if t < 0.45:
                c.set(x + (1 if lean > 0 else -1), y, pal.DRED)

            if step == int(reach) - 1:
                # The hook: the tip bends back over the hole, and catches the
                # light so it separates from whatever is behind it.
                hook = 1 if lean > 0 else -1
                c.set(x + hook, y, pal.RED)
                c.set(x + hook, y - 1, pal.WHITE)

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
