#!/usr/bin/env python3
"""
Build every level as ASCII in levels/.

Levels are assembled from named beats rather than drawn by hand, so the
difficulty curve is something we can read and tune: each stage lists its beats
in order, a new mechanic is always introduced on safe ground before it is used
over a pit, and the hazard a world kills you with is a per-world parameter.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import level_kit as K

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'levels')

# per-world flavour: (pit hazard, common enemy, second enemy, backdrop)
WORLD_FLAVOUR = [
    (None,    K.IMP,     K.BAT,     K.BG_A),   # I   Pride
    (None,    K.IMP,     K.GNASHER, K.BG_A),   # II  Greed
    (K.SPIKE, K.CHERUB,  K.IMP,     K.BG_B),   # III Lust
    (K.LAVA,  K.GNASHER, K.CHERUB,  K.BG_A),   # IV  Envy
    (None,    K.GNASHER, K.WRAITH,  K.BG_B),   # V   Gluttony
    (K.LAVA,  K.IMP,     K.WRAITH,  K.BG_A),   # VI  Wrath
    (K.SPIKE, K.BAT,     K.WRAITH,  K.BG_A),   # VII Sloth
    (K.LAVA,  K.GNASHER, K.BAT,     K.BG_B),   # VIII Hades
]


STAGE_COUNT = 16


def difficulty(index):
    """
    Where a stage sits on the curve, 0 at the first and 1 at the last.

    Every beat scales off this rather than off the world number, so which of
    the six shapes a stage happens to use no longer decides how hard it is.
    """
    return index / float(STAGE_COUNT - 1)


class Builder:
    """A cursor that walks left to right laying down beats."""

    def __init__(self, key, name, world, index, music=None, weight=1.0):
        hazard, e1, e2, bg = WORLD_FLAVOUR[world]
        self.hazard, self.e1, self.e2 = hazard, e1, e2
        self.d = difficulty(index)
        # Some shapes are inherently calmer than others. Compensating here lets
        # the shapes stay distinct while the curve still climbs, whichever one
        # a given stage happens to use.
        self.comp = 1.0 / weight
        self.lv = K.Level(key, name, world, width=4096, music=music,
                          background=bg)
        self.x = 0

    def scale(self, base, extra):
        """`base` at the start of the game, roughly `base + extra` by the end."""
        return base + int(round(self.d * extra * self.comp))

    # -- beats -------------------------------------------------------------
    def flat(self, w, souls=0):
        self.lv.ground(self.x, self.x + w - 1)
        for i in range(souls):
            sx = self.x + 2 + i * 2
            if sx <= self.x + w - 2:
                self.lv.entity(K.SOUL, sx, K.FLOOR - 2)
        self.x += w
        return self

    def enemies(self, w, kind=None, count=1):
        kind = kind or self.e1
        self.lv.ground(self.x, self.x + w - 1)
        step = max(3, w // (count + 1))
        for i in range(count):
            ex = self.x + step * (i + 1)
            ey = K.FLOOR - 1 if kind not in (K.CHERUB, K.BAT) else K.FLOOR - 5
            self.lv.entity(kind, min(ex, self.x + w - 2), ey)
        self.x += w
        return self

    # A plain jump, launched a tile early and without hovering, clears three
    # columns of air. Anything wider has to be broken into hops.
    MAX_HOP = 3

    def gap(self, w, lead=3, tail=3):
        """
        A jump. Ground on both sides so it always reads as a decision.

        Gaps wider than a plain jump get stepping stones, so hovering makes a
        crossing comfortable but is never the only way over it.
        """
        self.lv.ground(self.x, self.x + lead - 1)
        self.lv.cliff(self.x, self.x + lead - 1, right_edge=True, left_edge=False)
        self.x += lead

        start = self.x
        if self.hazard:
            self.lv.fill(start, K.ROWS - 2, start + w - 1, K.ROWS - 1, self.hazard)

        # Drop stepping stones until no run of open air is wider than one jump.
        pos = start
        far = start + w

        while far - pos > self.MAX_HOP:
            col = min(pos + self.MAX_HOP - 1, far - 2)
            self.lv.platform(col, K.FLOOR - 2, 2)
            pos = col + 2

        self.x += w
        self.lv.cliff(self.x, self.x + tail - 1, left_edge=True, right_edge=False)
        self.x += tail
        return self

    def stepping(self, count, w=5, rise=1):
        """
        Floating platforms over open air.

        They are wide, because Luv's jump clears four and a half metatiles and a
        narrow ledge is something you sail straight over. Spacing is inside a
        plain jump, so hover makes these comfortable rather than mandatory.
        """
        y = K.FLOOR - 2
        for i in range(count):
            self.lv.platform(self.x + 1, y, w)
            if self.hazard:
                self.lv.fill(self.x, K.ROWS - 2, self.x + w + 1, K.ROWS - 1, self.hazard)
            y = max(5, y - rise if i % 2 == 0 else y + rise)
            self.x += w + 2
        return self

    def overhead(self, w, breakables=3, prize=None):
        """A row of breakable blocks overhead, one of them holding a prize."""
        self.lv.ground(self.x, self.x + w - 1)
        bx = self.x + 2
        self.lv.blocks(bx, K.FLOOR - 4, breakables, K.BREAK)
        if prize:
            self.lv.prize_block(bx + breakables // 2, K.FLOOR - 4, prize)
        self.x += w
        return self

    def spikes(self, w, patch=2):
        self.lv.ground(self.x, self.x + w - 1)
        self.lv.spikes(self.x + w // 2 - patch // 2, self.x + w // 2 + patch // 2)
        self.x += w
        return self

    def hall(self, w, flyer=None):
        """Pillared stretch with something in the air."""
        self.lv.ground(self.x, self.x + w - 1)
        for i in range(2, w, 6):
            self.lv.pillar(self.x + i)
            self.lv.lamp(self.x + i, K.FLOOR - 6)
        self.lv.entity(flyer or self.e2, self.x + w // 2, K.FLOOR - 6)
        self.x += w
        return self

    def drop(self, steps=3, w=4):
        """
        A valley: ledges down and back up.

        Every beat starts and ends on the normal floor. A beat that left the
        ground at a different height would silently break whatever came next,
        which is exactly the bug the level linter kept catching.
        """
        top = K.FLOOR
        for _ in range(steps):
            top = min(K.ROWS - 3, top + 1)
            self.lv.cliff(self.x, self.x + w - 1, top)
            self.x += w
        for _ in range(steps):
            top = max(K.FLOOR, top - 1)
            self.lv.cliff(self.x, self.x + w - 1, top)
            self.x += w
        return self

    def ceiling(self, w, enemies=1):
        """A low corridor: blocks overhead, floor below, no room to be careless."""
        self.lv.ground(self.x, self.x + w - 1)
        self.lv.fill(self.x, K.FLOOR - 5, self.x + w - 1, K.FLOOR - 5, K.BLOCK)
        step = max(3, w // (enemies + 1))
        for i in range(enemies):
            self.lv.entity(self.e1, self.x + step * (i + 1), K.FLOOR - 1)
        self.x += w
        return self

    def rise(self, steps=3, w=3):
        """A hill: ledges up, then back down to the floor."""
        top = K.FLOOR
        for _ in range(steps):
            top = max(6, top - 2)
            self.lv.cliff(self.x, self.x + w - 1, top)
            self.x += w
        for _ in range(steps):
            top = min(K.FLOOR, top + 2)
            self.lv.cliff(self.x, self.x + w - 1, top)
            self.x += w
        return self

    def secret_door(self):
        """
        A door on a high ledge, off the main path.

        You need the hover to get up there and you need to have looked up. It
        is deliberately not on the route a player running right would take.
        """
        self.lv.ground(self.x, self.x + 11)
        self.lv.platform(self.x + 3, K.FLOOR - 4, 3)
        self.lv.platform(self.x + 7, K.FLOOR - 8, 4)
        self.lv.entity(K.SOUL, self.x + 4, K.FLOOR - 6)      # a breadcrumb upward
        self.lv.entity(K.SOUL, self.x + 8, K.FLOOR - 10)
        self.lv.entity(K.WARP, self.x + 9, K.FLOOR - 9)
        self.x += 12
        return self

    # -- markers -----------------------------------------------------------
    def start(self):
        """Always three tiles into the opening stretch, on solid ground."""
        self.lv.entity(K.PLAYER, 3, K.FLOOR - 2)
        return self

    def checkpoint(self):
        self.lv.entity(K.CHECKPOINT, self.x - 4, K.FLOOR - 1)
        return self

    def pickup(self, ch, back=3, height=3):
        self.lv.entity(ch, self.x - back, K.FLOOR - height)
        return self

    def finish(self):
        self.lv.entity(K.EXIT, self.x - 4, K.FLOOR - 2)
        self.lv.width = self.x
        self.lv.g = [row[:self.x] for row in self.lv.g]
        return self.lv


# ---------------------------------------------------------------------------
# Six stage shapes. A stage is one of these, so the two halves of a world play
# differently from each other and from the world before.
def _march(b):
    """Open ground: enemies, a block row overhead, a couple of honest gaps."""
    b.flat(10).start()
    b.enemies(12, count=b.scale(1, 2))
    b.overhead(11, breakables=3, prize=K.PU_SOUL)
    b.gap(b.scale(3, 3))
    b.enemies(13, count=b.scale(2, 2))
    b.flat(6, souls=2).checkpoint()
    b.overhead(11, breakables=4, prize=K.PU_FLAME)
    b.enemies(13, kind=b.e2, count=b.scale(1, 3))
    b.gap(b.scale(3, 4))
    b.enemies(12, count=b.scale(1, 2))
    b.flat(7, souls=3).pickup(K.PU_DASH)
    b.flat(9)
    return b


def _ledges(b):
    """Stepped terrain: climb, drop, and mind the edges."""
    b.flat(9).start()
    b.rise(3)
    b.enemies(10, count=b.scale(1, 2))
    b.drop(3)
    b.gap(b.scale(3, 3))
    b.enemies(11, kind=b.e2, count=b.scale(1, 2))
    b.flat(5).checkpoint().pickup(K.PU_SOUL)
    b.rise(3)
    b.overhead(10, breakables=3, prize=K.ONE_UP)
    b.drop(2)
    b.enemies(12, count=b.scale(2, 2))
    b.gap(b.scale(3, 4))
    b.rise(2)
    b.enemies(10, count=b.scale(1, 2))
    b.flat(8, souls=3).pickup(K.PU_WINGS)
    b.flat(8)
    return b


def _hall(b):
    """Pillared halls, things in the air, and spikes underfoot."""
    b.flat(9).start()
    b.hall(16)
    b.spikes(9, patch=b.scale(1, 2))
    b.enemies(11, count=b.scale(1, 2))
    b.hall(16)
    b.flat(5).checkpoint().pickup(K.PU_SOUL)
    b.overhead(10, breakables=3, prize=K.PU_FLAME)
    b.hall(18)
    b.spikes(10, patch=b.scale(2, 2))
    b.enemies(12, kind=b.e2, count=b.scale(2, 3))
    b.gap(b.scale(3, 3))
    b.flat(8, souls=3)
    b.flat(8)
    return b


def _crossing(b):
    """Mostly air: stepping stones and long gaps over whatever is below."""
    b.flat(9).start()
    b.enemies(10, count=b.scale(1, 1))
    b.stepping(2)
    b.flat(6).pickup(K.PU_SOUL)
    b.gap(b.scale(3, 4))
    b.stepping(b.scale(2, 1))
    b.flat(6, souls=2).checkpoint()
    b.enemies(11, kind=b.e2, count=b.scale(1, 2))
    b.stepping(b.scale(2, 2))
    b.overhead(10, breakables=3, prize=K.PU_WINGS)
    b.gap(b.scale(4, 4))
    b.enemies(11, count=b.scale(1, 3))
    b.flat(7, souls=3).pickup(K.PU_FLAME)
    b.flat(8)
    return b


def _cellar(b):
    """Low ceilings and close quarters - nowhere to jump out of trouble."""
    b.flat(9).start()
    b.ceiling(12, enemies=b.scale(1, 1))
    b.enemies(10, count=b.scale(1, 2))
    b.ceiling(13, enemies=b.scale(1, 2))
    b.flat(5).checkpoint().pickup(K.PU_SOUL)
    b.spikes(9, patch=b.scale(1, 2))
    b.ceiling(13, enemies=b.scale(1, 3))
    b.overhead(10, breakables=4, prize=K.PU_DASH)
    b.enemies(12, kind=b.e2, count=b.scale(1, 3))
    b.gap(b.scale(3, 3))
    b.ceiling(12, enemies=b.scale(1, 2))
    b.flat(8, souls=3).pickup(K.ONE_UP)
    b.flat(8)
    return b


def _ascent(b):
    """Climb: every beat gains height, and the exit is at the top."""
    b.flat(9).start()
    b.enemies(10, count=b.scale(1, 2))
    b.rise(2)
    b.stepping(2)
    b.rise(2)
    b.flat(6).checkpoint().pickup(K.PU_SOUL)
    b.enemies(11, kind=b.e2, count=b.scale(1, 2))
    b.rise(2)
    b.overhead(10, breakables=3, prize=K.PU_WINGS)
    b.stepping(b.scale(2, 1))
    b.enemies(11, count=b.scale(1, 3))
    b.rise(3)
    b.flat(7, souls=3).pickup(K.PU_FLAME)
    b.flat(9)
    return b


# Each shape, and how busy it is by nature. The weights come from measuring
# the generated stages with tools/balance.py, not from taste.
SHAPES = {
    'march':    (_march,    1.00),
    'ledges':   (_ledges,   0.95),
    'hall':     (_hall,     0.78),
    'crossing': (_crossing, 1.15),
    'cellar':   (_cellar,   1.22),
    'ascent':   (_ascent,   0.85),
}

# One shape per stage, arranged so the two halves of a world contrast and no
# shape repeats back to back.
# Ordered so the calmest shapes open the game and the busiest close it, with no
# shape twice in a row. A world is a lighter stage followed by a heavier one.
SHAPE_ORDER = [
    'hall',     'ascent',       # I
    'hall',     'ledges',       # II
    'ascent',   'march',        # III
    'ledges',   'crossing',     # IV
    'march',    'crossing',     # V
    'ledges',   'cellar',       # VI
    'crossing', 'cellar',       # VII
    'crossing', 'cellar',       # VIII
]


# Which stages hide a door, and which room it opens onto. Stage indices are
# positions in the compiled list; the rooms themselves live after the story.
SECRET_DOORS = {1: 24, 7: 25, 16: 26}


def world_levels(world, names):
    """The two stages of one world, each built from its own shape."""
    out = []

    for half in (0, 1):
        index = world * 2 + half
        shape, weight = SHAPES[SHAPE_ORDER[index]]
        b = Builder('w%d_%d' % (world + 1, half + 1), names[half], world, index,
                    weight=weight)
        shape(b)

        if index in SECRET_DOORS:
            b.secret_door()
            b.lv.warp = SECRET_DOORS[index]

        out.append(b.finish())

    return out


def secret_room(key, name, world, message, exit_to, reward=K.ONE_UP):
    """
    A small hidden room: something written on the wall, something worth having,
    and a gate out.
    """
    hazard, e1, e2, bg = WORLD_FLAVOUR[world]
    width = 16
    lv = K.Level(key, name, world, width=width, music='title', background=bg,
                 exit_to=exit_to, secret=message, hidden=True)

    lv.ground(0, width - 1)

    for col in (0, width - 1):
        lv.pillar(col, 0, K.FLOOR - 1)

    lv.fill(2, K.FLOOR - 7, width - 3, K.FLOOR - 7, K.BLOCK)   # the wall it is on
    lv.entity(K.SIGN, width // 2, K.FLOOR - 5)
    lv.entity(K.PLAYER, 2, K.FLOOR - 2)
    lv.entity(reward, 7, K.FLOOR - 2)

    for i in range(4):
        lv.entity(K.SOUL, 4 + i * 2, K.FLOOR - 3)

    lv.entity(K.EXIT, width - 3, K.FLOOR - 2)
    return lv


SECRET_ROOMS = [
    # (key, name, world, message, where it lets you out)
    ('secret_999', 'Nine Nine Nine', 0, '999  RIP JUICE WRLD', 2),
    ('warp_0615',  'The Long Way Round', 2, '06/15', 15),
    ('warp_deep',  'Straight Down', 5, 'NO STAIRS FROM HERE', 21),
]


BOSS_NAMES = [
    'Superbia', 'Avaritia', 'Luxuria', 'Invidia',
    'Gula', 'Ira', 'Acedia', 'Hades',
]


def boss_arena(world):
    """
    A closed room, two screens wide, with a floor and two ledges to break the
    line of sight. Wide enough to run away in, small enough that you cannot
    simply keep running.
    """
    hazard, e1, e2, bg = WORLD_FLAVOUR[world]

    # Exactly one screen wide. The level compiler pads a stage up to a multiple
    # of sixteen metatiles, and any padding it adds has no floor - so an arena
    # has to be a whole number of them or the room ends in a pit.
    width = 16
    lv = K.Level('w%d_boss' % (world + 1), BOSS_NAMES[world], world, width=width,
                 music='boss', background=bg, boss=world + 1)

    lv.ground(0, width - 1)

    # Two ledges to jump between, clear of the middle where the fight happens.
    lv.platform(2, K.FLOOR - 4, 4)
    lv.platform(10, K.FLOOR - 4, 4)

    # A pillar at each end so the room reads as a room.
    for col in (0, width - 1):
        lv.pillar(col, 0, K.FLOOR - 1)

    lv.entity(K.PLAYER, 2, K.FLOOR - 2)
    lv.entity(K.BOSS, 12, K.FLOOR - 1)
    return lv


NAMES = [
    ('Chapel of the Mirror', 'The Long Gallery'),
    ('The Counting Floor', 'Vault of Small Coins'),
    ('Thorn Walk', 'The Lantern Beds'),
    ('Green Water', 'What He Has'),
    ('The Larder', 'Second Helpings'),
    ('Cinderpath', 'The Faultline'),
    ('Dust Rooms', 'Nothing Stirs'),
    ('The Descent', 'Below Everything'),
]


def main():
    total = 0
    for world in range(8):
        stages = world_levels(world, NAMES[world])
        stages.append(boss_arena(world))

        for lv in stages:
            lv.save(OUT)
            s = K.stats(lv)
            total += s['width']
            print('  %-8s %-24s w=%3d  enemies=%2d  pickups=%2d  gaps=%2d'
                  % (lv.key, lv.name, s['width'], s['enemies'], s['pickups'],
                     s['gaps']))
    for key, name, world, message, exit_to in SECRET_ROOMS:
        room = secret_room(key, name, world, message, exit_to)
        room.save(OUT)
        print('  %-8s %-24s hidden room, lets out at stage %d'
              % (room.key, room.name, exit_to))

    print('16 levels, %d columns (%d screens of play)' % (total, total // 15))


if __name__ == '__main__':
    main()
