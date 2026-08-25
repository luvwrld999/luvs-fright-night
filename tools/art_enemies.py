"""
The demons of Fright Night - every one of them wears a halo it has no right to.

All 16x16 so they share one OAM shape and can be pooled freely by the engine.
Vertical anatomy is shared across the cast: halo 0-3, horns 2-6, head 4-10,
body 6-13, feet 13-15. Keeping to it is what makes them read as one species.
"""

import math

import palette as pal
from pixel import Canvas

S = 16

# The halo is the joke of the whole cast, so it never gets shaded flat.
NO_SHADE = {pal.GOLD, pal.DGOLD}


def halo(c, cx=8.0, cy=1.6, rx=3.2, ry=1.5):
    """A stolen halo: a closed ring, bright on top and dull underneath."""
    c.ellipse(cx, cy, rx, ry, pal.GOLD)
    c.ellipse(cx, cy, rx - 1.5, ry - 0.75, pal.KEY)
    for y in range(S):
        for x in range(S):
            if c.px[y][x] == pal.GOLD and y > cy:
                c.px[y][x] = pal.DGOLD


def horns(c, cx, crown, spread=3.0, height=3.2, color=pal.DRED):
    """
    Horns rooted below the crown and drawn before the head, so only the part
    that breaks the silhouette shows.
    """
    for side in (-1, 1):
        bx = cx + side * spread * 0.5
        for k in range(9):
            t = k / 8.0
            x = bx + side * spread * 0.5 * t
            y = crown + 1.4 - height * t
            c.disc(x, y, 0.8 * (1 - t) + 0.35, color)


def eyes(c, cx, y, spread=2.0, color=pal.GOLD, socket=True):
    """Sunken sockets with a hot pinpoint - readable at 16px."""
    for side in (-1, 1):
        x = int(cx + side * spread)
        if socket:
            c.rect(x - 1, y - 1, x, y + 1, pal.INK)
        c.set(x if side < 0 else x - 1, y, color)


def finish(c, rim_over=None):
    c.shade(light=(-1, -1),
            colors={pal.RED, pal.MAG, pal.GREEN, pal.PURPLE, pal.WHITE})
    c.outline(pal.INK)
    return c


# ---------------------------------------------------------------------------
def halo_imp(f):
    """Ground walker: squat, stomping, permanently furious."""
    c = Canvas(S, S)
    bob = f % 2
    lead = 1 if f in (1, 2) else -1

    halo(c, 8, 1.6 + bob * 0.3, 3.1, 1.5)
    horns(c, 8, 4.6 + bob, spread=3.4, height=3.4, color=pal.RED)
    for side in (-1, 1):                                    # stamping feet
        c.rect(8 + side * 3 - 1, 13 + (1 if side == lead else 0),
               8 + side * 3, 14, pal.DRED)
    c.ellipse(8, 10.0 + bob, 4.0, 3.2, pal.RED)             # torso
    c.ellipse(8, 6.9 + bob, 3.0, 2.5, pal.RED)              # head
    eyes(c, 8, 7 + bob, 1.8, pal.GOLD)
    c.rect(6, 9 + bob, 9, 9 + bob, pal.INK)                 # grin
    for x in (6, 8):
        c.set(x, 9 + bob, pal.WHITE)
    return finish(c, {pal.RED})


def cherub_fiend(f):
    """Flier: a fat cherub gone wrong, wings beating out of time."""
    c = Canvas(S, S)
    flap = [0, 1, 2, 1][f % 4]

    for side in (-1, 1):
        c.ellipse(8 + side * 4.8, 8.0 - flap * 0.9, 2.3, 3.2 - flap * 0.6, pal.DGREEN)
        c.ellipse(8 + side * 4.4, 8.4 - flap * 0.9, 1.6, 2.4 - flap * 0.5, pal.GREEN)
    c.outline(pal.INK)
    halo(c, 8, 1.6, 2.9, 1.5)
    horns(c, 8, 4.6, spread=2.8, height=2.8, color=pal.DGREEN)
    c.ellipse(8, 9.0, 3.4, 3.6, pal.GREEN)
    eyes(c, 8, 8, 1.8, pal.MAG)
    c.rect(7, 10, 8, 10, pal.INK)
    return finish(c, {pal.GREEN})


def gnasher(f):
    """Charger: mostly jaw. Winds up, then commits."""
    c = Canvas(S, S)
    gape = [0, 1, 3, 1][f % 4]

    halo(c, 8, 1.6, 3.2, 1.5)
    horns(c, 8, 4.4, spread=4.0, height=3.0, color=pal.MAG)
    c.ellipse(8, 9.4, 4.6, 4.2, pal.MAG)
    eyes(c, 8, 7, 2.2, pal.GOLD)
    c.rect(4, 10, 11, 10 + gape, pal.INK)                   # jaw
    for x in range(4, 12, 2):
        c.set(x, 10, pal.WHITE)
        c.set(x + 1, 10 + gape, pal.WHITE)
    return finish(c, {pal.MAG})


def censer_wraith(f):
    """Spitter: hovers, swings a censer, coughs embers at you."""
    c = Canvas(S, S)
    swing = [-2, -1, 1, 2][f % 4]

    halo(c, 8, 1.6, 2.8, 1.5)
    c.poly([(8, 3.2), (12.6, 13.5), (3.4, 13.5)], pal.PURPLE)
    c.ellipse(8, 6.0, 2.3, 2.1, pal.INK)                    # hood void
    for side in (-1, 1):
        c.set(int(8 + side * 1.2), 6, pal.CYAN)
    cx = 8 + swing
    c.line(8, 9, cx, 12, pal.DGOLD)
    c.disc(cx, 13.2, 1.4, pal.GOLD)
    c.set(int(cx), 13, pal.RED)
    return finish(c, {pal.PURPLE})


def bone_bat(f):
    """
    The drop enemy: hangs in the air on slow wingbeats, then falls on you.

    Frames 0-1 are the hover, 2 is the wind-up, 3 is the dive with the wings
    swept back, so the attack is telegraphed instead of arriving out of nowhere.
    """
    c = Canvas(S, S)
    diving = f == 3
    flap = [0, 2, 3, -1][f % 4]

    # Wings: a scalloped membrane with a lighter leading edge.
    for side in (-1, 1):
        tip_x = 8 + side * (7.4 if not diving else 4.6)
        tip_y = 6.5 - flap
        elbow_x = 8 + side * 4.0
        wing = [(8 + side * 1.6, 7.0), (elbow_x, tip_y - 1.0), (tip_x, tip_y),
                (tip_x - side * 0.8, tip_y + 3.6), (elbow_x, 10.0 + flap * 0.3),
                (8 + side * 2.0, 11.0)]
        c.poly(wing, pal.SHADOW)
        c.curve([(8 + side * 1.6, 7.0), (elbow_x, tip_y - 0.6), (tip_x, tip_y + 0.4)],
                pal.PURPLE)
        for k in range(2):                     # membrane ribs
            rx = elbow_x + side * k * 1.6
            c.line(8 + side * 1.8, 8.0, rx, 10.4 + flap * 0.3, pal.PURPLE)

    c.outline(pal.INK)
    halo(c, 8, 1.6, 2.6, 1.5)
    horns(c, 8, 5.2, spread=2.4, height=2.4, color=pal.SHADOW)

    c.ellipse(8, 8.6, 2.8, 3.0, pal.WHITE)     # skull
    c.ellipse(8, 11.4, 1.8, 1.4, pal.WHITE)    # jaw
    for side in (-1, 1):                       # sockets, lit red
        c.ellipse(8 + side * 1.3, 8.2, 1.2, 1.2, pal.INK)
        c.set(int(8 + side * 1.3), 8, pal.RED)
    for x in (7, 9):
        c.set(x, 12, pal.INK)                  # teeth

    return finish(c)


def spike_flame(f):
    """Static hazard: a jet of hellfire that breathes in and out."""
    c = Canvas(S, S)
    h = [0, 1, 2, 1][f % 4]
    c.poly([(3.5, 16), (12.5, 16), (10, 9 - h), (8, 12 - h), (6, 8 - h)], pal.RED)
    c.poly([(5.5, 16), (10.5, 16), (9, 11 - h), (7, 10 - h)], pal.GOLD)
    c.poly([(7, 16), (9, 16), (8.2, 13 - h)], pal.WHITE)
    c.outline(pal.INK)
    return c


ENEMIES = [
    ('halo_imp', halo_imp, 4),
    ('cherub_fiend', cherub_fiend, 4),
    ('gnasher', gnasher, 4),
    ('censer_wraith', censer_wraith, 4),
    ('bone_bat', bone_bat, 4),
    ('spike_flame', spike_flame, 4),
]
