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
# hazard, ground enemy, second enemy, background, and the one that belongs in
# the air. The flyer is separate because hall() hangs something six tiles up:
# a gnasher or a wraith put there has no floor to walk on, reverses on its
# first step and then sits still for the rest of the stage, which is what world
# II's "floating enemies that do nothing" were.
WORLD_FLAVOUR = [
    (None,    K.IMP,     K.BAT,     K.BG_A, K.BAT),      # I   Pride
    (None,    K.IMP,     K.GNASHER, K.BG_A, K.CHERUB),   # II  Greed
    (K.SPIKE, K.CHERUB,  K.IMP,     K.BG_B, K.CHERUB),   # III Lust
    (K.LAVA,  K.GNASHER, K.CHERUB,  K.BG_A, K.CHERUB),   # IV  Envy
    (None,    K.GNASHER, K.WRAITH,  K.BG_B, K.BAT),      # V   Gluttony
    (K.LAVA,  K.IMP,     K.WRAITH,  K.BG_A, K.BAT),      # VI  Wrath
    (K.SPIKE, K.BAT,     K.WRAITH,  K.BG_A, K.CHERUB),   # VII Sloth
    (K.LAVA,  K.GNASHER, K.BAT,     K.BG_B, K.BAT),      # VIII Hades
]


STAGE_COUNT = 16

# 240px of screen over 16px metatiles, and the stage length the shape weights
# were measured against.
SCREEN_COLS = 15.0
REFERENCE_SCREENS = 10.0

# The curve every stage is solved onto: what balance.py calls pressure, which
# is enemies per screen plus holes per screen weighted half again. Chosen to
# open gently and finish hard, and to climb on every single beat.
PRESSURE_START = 0.95
PRESSURE_END = 2.65

ENEMY_CHARS = (K.IMP, K.CHERUB, K.GNASHER, K.WRAITH, K.BAT, K.JET)
HAZARD_CHARS = (K.SPIKE, K.LAVA)


def target_pressure(index):
    """Where stage `index` is meant to land on the curve."""
    return PRESSURE_START + (PRESSURE_END - PRESSURE_START) * difficulty(index)


def measured_pressure(lv, width):
    """
    balance.py's metric, computed here so the generator can aim at it.

    Kept deliberately identical: a generator that solves onto a different
    number than the one we check against is worse than no solving at all.
    """
    screens = max(width / SCREEN_COLS, 0.1)
    enemies = 0
    holes, run = 0, 0
    hazards, inside = 0, False

    for col in range(width):
        solid = any(lv.g[r][col] in (K.GROUND, K.FILL)
                    for r in range(K.FLOOR, K.ROWS))

        if solid:
            if run:
                holes += 1

            run = 0
        else:
            run += 1

        # A six-tile lava pit is one hazard you jump, not six.
        here = False

        for r in range(K.ROWS):
            if lv.g[r][col] in ENEMY_CHARS:
                enemies += 1

            if lv.g[r][col] in HAZARD_CHARS:
                here = True

        if here and not inside:
            hazards += 1

        inside = here

    if run:
        holes += 1

    return ((enemies / screens) + (holes / screens) * 1.5
            + (hazards / screens) * 1.0)


def difficulty(index):
    """
    Where a stage sits on the curve, 0 at the first and 1 at the last.

    Every beat scales off this rather than off the world number, so which of
    the six shapes a stage happens to use no longer decides how hard it is.
    """
    return index / float(STAGE_COUNT - 1)


class Builder:
    """A cursor that walks left to right laying down beats."""

    def __init__(self, key, name, world, index, music=None, weight=1.0,
                 stretch=1.0):
        hazard, e1, e2, bg, air = WORLD_FLAVOUR[world]
        self.hazard, self.e1, self.e2, self.air = hazard, e1, e2, air
        self.d = difficulty(index)
        # Some shapes are inherently calmer than others, and some run much
        # longer. Compensating for both here lets the shapes stay distinct
        # while what the player actually feels - how much arrives per screen -
        # still climbs, whichever shape a stage happens to use.
        self.comp = stretch / weight
        self.lv = K.Level(key, name, world, width=4096, music=music,
                          background=bg)
        self.x = 0

    def scale(self, base, extra):
        """
        `base` at the start of the game, roughly `base + extra` by the end.

        Compensation applies to the whole count, not just the growth: what the
        player feels is how much arrives per screen, and a long or a calm shape
        is thin at the start of the curve as much as at the end.
        """
        return max(1, int(round((base + self.d * extra) * self.comp)))

    def span(self, base, extra):
        """
        Like `scale`, but for a width rather than a count.

        Compensation exists to control how much arrives per screen. Applying it
        to a distance does the opposite - a gap stretched to four times its
        length is one more hole spread over four times the walking - so widths
        follow the difficulty ramp alone.
        """
        return base + int(round(self.d * extra))

    # -- beats -------------------------------------------------------------
    def flat(self, w, souls=0):
        """
        Open ground, optionally strewn with souls.

        Souls are spaced two columns apart at head height, so a run through
        collects the line without stopping. They cost nothing on the balance
        sheet - pressure counts enemies, holes and hazards - so a stage can be
        generous with them without getting harder.
        """
        self.lv.ground(self.x, self.x + w - 1)

        for i in range(souls):
            sx = self.x + 2 + i * 2

            if sx <= self.x + w - 2:
                self.lv.entity(K.SOUL, sx, K.FLOOR - 2)

        self.x += w
        return self

    def soul_arc(self, w, count=5, peak=6):
        """
        A line of souls curving up over solid ground and back down.

        The shape is the point: it traces the arc of a jump, so following it
        teaches the jump rather than just paying for one.
        """
        self.lv.ground(self.x, self.x + w - 1)
        span = max(count - 1, 1)

        for i in range(count):
            t = (i / float(span)) * 2.0 - 1.0
            x = self.x + 2 + int(round(i * (w - 4) / float(span)))
            y = K.FLOOR - 2 - int(round((1.0 - t * t) * peak))
            self.lv.entity(K.SOUL, x, max(2, y))

        self.x += w
        return self

    def enemies(self, w, kind=None, count=1):
        kind = kind or self.e1
        # Each enemy needs about three columns to itself. Without this the
        # placements clamp to the same tile and quietly overwrite each other,
        # so asking for more than the segment can hold used to be a silent
        # no-op - and the difficulty solver could never reach its target.
        w = max(w, 3 * count + 2)
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
            self.lv.entity(K.SOUL, self.x + i + 3, K.FLOOR - 2)
        self.lv.entity(flyer or self.air, self.x + w // 2, K.FLOOR - 6)
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
            self.lv.entity(K.SOUL, self.x + w // 2, top - 1)
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
            self.lv.entity(K.SOUL, self.x + w // 2, top - 1)
            self.x += w
        for _ in range(steps):
            top = min(K.FLOOR, top + 2)
            self.lv.cliff(self.x, self.x + w - 1, top)
            self.x += w
        return self

    def stair(self, steps=3, w=3, up=True, souls=True):
        """
        A block staircase standing on solid ground.

        Unlike rise(), the ground underneath never moves: this is something to
        climb over rather than a change in floor level. It gives a stretch
        shape without touching the hole, enemy or hazard counts the balance
        pass measures, so terrain can be made interesting without moving the
        difficulty curve.
        """
        self.lv.ground(self.x, self.x + steps * w - 1)

        for i in range(steps):
            height = (i + 1) if up else (steps - i)

            for h in range(height):
                self.lv.blocks(self.x, K.FLOOR - 1 - h, w)

            if souls:
                self.lv.entity(K.SOUL, self.x + w // 2, K.FLOOR - 2 - height)

            self.x += w

        return self

    def arches(self, w, count=2, prize=None):
        """
        Block clusters overhead at alternating heights.

        A single row of breakables at one height is a thing you walk under
        once. Staggering them makes the ceiling something you read, and puts
        the prize somewhere you have to line a jump up for.
        """
        self.lv.ground(self.x, self.x + w - 1)
        step = max(4, w // (count + 1))

        for i in range(count):
            bx = self.x + step * (i + 1) - 1
            top = K.FLOOR - (4 if i % 2 == 0 else 6)
            self.lv.blocks(bx, top, 2, K.BREAK)

            if prize and i == count - 1:
                self.lv.prize_block(bx + 1, top, prize)

        self.x += w
        return self

    def shelf(self, w, height=3, souls=2):
        """
        A one-way ledge above solid ground, with something worth having on it.

        The floor below stays walkable, so this is a choice rather than a
        route: the ground is safe and the shelf pays.
        """
        self.lv.ground(self.x, self.x + w - 1)
        self.lv.platform(self.x + 1, K.FLOOR - height, w - 2)

        for i in range(souls):
            self.lv.entity(K.SOUL, self.x + 2 + i * 2, K.FLOOR - height - 1)

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

    # Anything a soul cannot be placed inside.
    SOLID = (K.GROUND, K.FILL, K.BLOCK, K.BREAK, K.PLAT, K.PILLAR, K.SPIKE,
             K.LAVA, K.LEDGE_L, K.LEDGE_R)

    def _open(self, x, y):
        """True if this cell is free air rather than terrain or an entity."""
        if not (0 <= x < self.x and 0 <= y < K.ROWS):
            return False

        return self.lv.g[y][x] in (K.BG_A, K.BG_B)

    def scatter_bonus(self, count=9):
        """
        Nine bonus souls, spread evenly across the finished stage.

        Placed by reading the built level rather than by any one beat, so every
        shape gets the same nine wherever its ground happens to be - above the
        local surface, never buried in terrain, and never on top of something
        already there.
        """
        width = self.x
        placed = 0

        for i in range(count):
            target = int((i + 0.5) * width / float(count))

            # Search outward from the ideal column for somewhere it fits.
            for dx in list(range(0, 12)):
                for x in ((target + dx), (target - dx)):
                    if not (2 <= x < width - 2):
                        continue

                    # The surface the player actually stands on: the lowest
                    # solid cell with air above it. Scanning from the top
                    # instead finds the ceiling wherever a column has one, and
                    # puts the soul above it where nobody can reach it.
                    surface = None

                    for y in range(K.ROWS - 1, 1, -1):
                        if self.lv.g[y][x] in self.SOLID and not self._open(x, y):
                            if self._open(x, y - 1):
                                surface = y
                                break

                    if surface is None or surface < 4:
                        continue

                    y = surface - 3

                    # Two cells of clear air, so it is never flush against
                    # whatever is overhead.
                    if self._open(x, y) and self._open(x, y - 1):
                        self.lv.entity(K.SOUL_TEN, x, y)
                        placed += 1
                        break

                if placed > i:
                    break

        return self

    def finish(self):
        self.lv.entity(K.EXIT, self.x - 4, K.FLOOR - 2)
        self.lv.width = self.x
        self.scatter_bonus()
        self.lv.g = [row[:self.x] for row in self.lv.g]
        return self.lv


# ---------------------------------------------------------------------------
# Six stage shapes. A stage is one of these, so the two halves of a world play
# differently from each other and from the world before.
def _march(b):
    """Open ground: enemies, a block row overhead, a couple of honest gaps."""
    b.flat(10).start()
    b.soul_arc(12, count=5)
    b.flat(6).pickup(K.PU_FLAME)
    b.enemies(12, count=b.scale(1, 2))
    b.overhead(11, breakables=3, prize=K.PU_SOUL)
    b.gap(b.span(3, 3))
    b.enemies(13, count=b.scale(2, 2))
    b.flat(6, souls=2).checkpoint()
    b.overhead(11, breakables=4, prize=K.PU_FLAME)
    b.enemies(13, kind=b.e2, count=b.scale(1, 3))
    b.gap(b.span(3, 4))
    b.enemies(12, count=b.scale(1, 2))
    b.flat(7, souls=3).pickup(K.PU_DASH)
    b.flat(9)
    return b


def _ledges(b):
    """Stepped terrain: climb, drop, and mind the edges."""
    b.flat(9).start()
    b.soul_arc(12, count=5)
    b.flat(6).pickup(K.PU_SOUL)
    b.rise(3)
    b.enemies(10, count=b.scale(1, 2))
    b.drop(3)
    b.gap(b.span(3, 3))
    b.enemies(11, kind=b.e2, count=b.scale(1, 2))
    b.flat(5).checkpoint().pickup(K.PU_SOUL)
    b.rise(3)
    b.overhead(10, breakables=3, prize=K.ONE_UP)
    b.drop(2)
    b.enemies(12, count=b.scale(2, 2))
    b.gap(b.span(3, 4))
    b.rise(2)
    b.enemies(10, count=b.scale(1, 2))
    b.flat(8, souls=3).pickup(K.PU_WINGS)
    b.flat(8)
    return b


def _hall(b):
    """
    Pillared halls, things in the air, and spikes underfoot.

    The opening stage of the game, so it has to teach without punishing: the
    variety here is in the shape of the ground and what is built on it, not in
    what is trying to kill you. Every beat is a different thing to look at -
    a hall, a staircase to climb, a shelf worth the detour, a low corridor, a
    hill, a stagger of breakables - rather than the same flat run repeated.
    """
    b.flat(7).start()
    b.soul_arc(12, count=5)
    b.flat(6).pickup(K.PU_FLAME)
    b.hall(14)
    b.stair(3, 3, up=True)
    b.shelf(9, height=3, souls=2)
    b.stair(3, 3, up=False)
    b.spikes(9, patch=b.span(1, 2))
    b.enemies(11, count=b.scale(1, 2))
    b.arches(14, count=3, prize=K.PU_SOUL)
    b.flat(5).checkpoint()
    b.ceiling(12, enemies=0)
    b.rise(2, 3)
    b.hall(14)
    b.shelf(10, height=4, souls=3)
    b.overhead(10, breakables=3, prize=K.PU_FLAME)
    b.drop(2, 4)
    b.stair(2, 3, up=True)
    b.spikes(10, patch=b.span(2, 2))
    b.enemies(12, kind=b.e2, count=b.scale(2, 3))
    b.gap(b.span(3, 3))
    b.arches(12, count=2)
    b.flat(8, souls=3)
    b.flat(7)
    return b


def _crossing(b):
    """Mostly air: stepping stones and long gaps over whatever is below."""
    b.flat(9).start()
    b.enemies(10, count=b.scale(1, 1))
    b.stepping(2)
    b.flat(6).pickup(K.PU_SOUL)
    b.gap(b.span(3, 4))
    b.stepping(b.span(2, 1))
    b.flat(6, souls=2).checkpoint()
    b.enemies(11, kind=b.e2, count=b.scale(1, 2))
    b.stepping(b.span(2, 2))
    b.overhead(10, breakables=3, prize=K.PU_WINGS)
    b.gap(b.span(4, 4))
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
    b.spikes(9, patch=b.span(1, 2))
    b.ceiling(13, enemies=b.scale(1, 3))
    b.overhead(10, breakables=4, prize=K.PU_DASH)
    b.enemies(12, kind=b.e2, count=b.scale(1, 3))
    b.gap(b.span(3, 3))
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
    b.stepping(b.span(2, 1))
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

        # Shapes differ in how long they run and how busy they are, and both
        # dilute or concentrate what the player meets per screen. Rather than
        # hand-tune a weight per shape and watch it go stale, solve for it:
        # build the stage, measure the same pressure balance.py will measure,
        # and adjust until it sits on the curve. Counts are integers, so this
        # converges in a handful of passes and then stops moving.
        want = target_pressure(index)
        stretch = 1.0 / weight
        best, best_err = None, None

        for _ in range(24):
            probe = Builder('probe', names[half], world, index, weight=1.0,
                            stretch=stretch)
            shape(probe)
            got = measured_pressure(probe.lv, probe.x)
            err = abs(got - want)

            if best_err is None or err < best_err:
                best, best_err = stretch, err

            if err < 0.02 or got <= 0.0:
                break

            # Enemies dominate the metric and scale with stretch, so nudging
            # by the ratio lands close; the loop mops up the rounding.
            stretch *= 1.0 + 0.6 * ((want - got) / max(want, 0.1))
            stretch = min(max(stretch, 0.2), 6.0)

        b = Builder('w%d_%d' % (world + 1, half + 1), names[half], world, index,
                    weight=1.0, stretch=best)
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
    hazard, e1, e2, bg, _air = WORLD_FLAVOUR[world]
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
    ('warp_deep',  'Straight Down', 5, 'WE ALL FLOAT DOWN HERE', 21),
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
    hazard, e1, e2, bg, _air = WORLD_FLAVOUR[world]

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
