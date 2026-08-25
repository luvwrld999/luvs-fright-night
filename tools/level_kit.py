"""
Level authoring.

Levels are grids of 16x16 metatiles, 16 rows tall (256px, exactly the height of
a hardware bg map) and as wide as they need to be. They are written out as ASCII
so a level stays readable and diffable; `build_levels.py` compiles the ASCII
into a header.

The same character legend the mock screens use, so anything drawn here can be
previewed with the art tools.
"""

import os

ROWS = 16
FLOOR = 13          # the row the ground surface normally sits on

WORLD_MUSIC = ['w1_pride', 'w2_greed', 'w3_lust', 'w4_envy',
               'w5_gluttony', 'w6_wrath', 'w7_sloth', 'w8_hades']

# terrain
EMPTY, GROUND, FILL, BLOCK, BREAK, PLAT, SPIKE = '.', '#', '=', 'B', 'b', '-', '^'
LEDGE_L, LEDGE_R, PILLAR, LAMP = '<', '>', 'I', 'o'
BG_A, BG_B, DOOR, CHAIN, LAVA = ',', ';', 'D', '|', '~'

# entities (stripped out at compile time and turned into spawns)
PLAYER, EXIT, CHECKPOINT, BOSS = 'p', 'x', 'k', 'Z'
WARP, SIGN = 'O', 'S'          # a door somewhere else, and writing on a wall
IMP, CHERUB, GNASHER, WRAITH, BAT, JET = 'i', 'c', 'g', 'w', 'v', 'f'
PU_FLAME, PU_SOUL, PU_DASH, PU_WINGS, ONE_UP, SOUL = '1', '2', '3', '4', 'u', 's'
SOUL_TEN = '*'                 # a bonus soul: worth ten of the plain ones

ENTITY_CHARS = set('pxkZOSicgwvf1234us*')

# A prize block is one cell that is both a breakable block and the thing inside
# it. Writing the pickup on its own would replace the block with empty air and
# leave the pickup floating in the hole.
PRIZE_BLOCKS = {
    PU_FLAME: 'Q', PU_SOUL: 'W', PU_DASH: 'E', PU_WINGS: 'R', ONE_UP: 'T',
}
PRIZE_CHARS = set(PRIZE_BLOCKS.values())


class Level:
    def __init__(self, key, name, world, width, music=None, background=BG_A,
                 boss=0, warp=-1, exit_to=-1, secret='', hidden=False):
        self.boss = boss
        self.warp = warp          # where a warp door in this stage leads
        self.exit_to = exit_to    # where this stage's exit gate leads
        self.secret = secret      # writing shown at the sign marker
        self.hidden = hidden      # kept out of the story order and stage select
        self.key = key
        self.name = name
        self.world = world
        self.width = width
        self.music = music or WORLD_MUSIC[world]
        self.g = [[background] * width for _ in range(ROWS)]

    # -- primitives ---------------------------------------------------------
    def put(self, x, y, ch):
        if 0 <= x < self.width and 0 <= y < ROWS:
            self.g[y][x] = ch

    def fill(self, x0, y0, x1, y1, ch):
        for y in range(max(0, y0), min(ROWS, y1 + 1)):
            for x in range(max(0, x0), min(self.width, x1 + 1)):
                self.g[y][x] = ch

    def ground(self, x0, x1, top=FLOOR):
        """Solid ground from `top` down to the bottom of the level."""
        self.fill(x0, top, x1, ROWS - 1, FILL)
        self.fill(x0, top, x1, top, GROUND)

    def cliff(self, x0, x1, top=FLOOR, left_edge=True, right_edge=True):
        self.ground(x0, x1, top)
        if left_edge:
            self.put(x0, top, LEDGE_L)
        if right_edge:
            self.put(x1, top, LEDGE_R)

    def pit(self, x0, x1, hazard=None):
        """Open the floor. Pass a hazard character to make the bottom lethal."""
        self.fill(x0, 0, x1, ROWS - 1, BG_A)
        if hazard:
            self.fill(x0, ROWS - 2, x1, ROWS - 1, hazard)

    def platform(self, x, y, w):
        self.fill(x, y, x + w - 1, y, PLAT)

    def blocks(self, x, y, w, ch=BLOCK):
        self.fill(x, y, x + w - 1, y, ch)

    def spikes(self, x0, x1, y=None):
        y = FLOOR if y is None else y
        self.fill(x0, y, x1, y, SPIKE)

    def pillar(self, x, y0=0, y1=None):
        self.fill(x, y0, x, FLOOR - 1 if y1 is None else y1, PILLAR)

    def lamp(self, x, y):
        self.put(x, y, LAMP)

    def entity(self, ch, x, y):
        self.put(x, y, ch)

    def prize_block(self, x, y, pickup):
        """A breakable block with `pickup` sealed inside it."""
        self.put(x, y, PRIZE_BLOCKS[pickup])

    def text_rows(self):
        return [''.join(row) for row in self.g]

    def save(self, folder):
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, self.key + '.txt')
        with open(path, 'w') as f:
            f.write('! name: %s\n' % self.name)
            f.write('! world: %d\n' % self.world)
            f.write('! music: %s\n' % self.music)
            f.write('! width: %d\n' % self.width)
            f.write('! boss: %d\n' % self.boss)
            f.write('! warp: %d\n' % self.warp)
            f.write('! exit_to: %d\n' % self.exit_to)
            f.write('! hidden: %d\n' % (1 if self.hidden else 0))

            if self.secret:
                f.write('! secret: %s\n' % self.secret)
            for row in self.text_rows():
                f.write(row + '\n')
        return path


def stats(level):
    """Counts used to sanity-check pacing without opening the level."""
    flat = ''.join(level.text_rows())
    return {
        'width': level.width,
        'enemies': sum(flat.count(c) for c in 'icgwvf'),
        'pickups': sum(flat.count(c) for c in '1234us'),
        'gaps': _gap_count(level),
    }


def _gap_count(level):
    gaps, run = 0, 0
    for x in range(level.width):
        solid = any(level.g[y][x] in (GROUND, FILL) for y in range(FLOOR, ROWS))
        if solid:
            if run:
                gaps += 1
            run = 0
        else:
            run += 1
    return gaps + (1 if run else 0)
