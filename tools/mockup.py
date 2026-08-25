"""
Mock 240x160 screens - the real GBA resolution, built from the real metatiles
and the real sprites, so the art can be judged in context instead of as a
sheet of loose frames.
"""

import art_bosses
import art_enemies
import art_items
import art_luv
import art_tiles as T
import palette as pal
from pixel import Canvas

SCREEN_W, SCREEN_H = 240, 160
COLS, ROWS = SCREEN_W // T.T, SCREEN_H // T.T      # 15 x 10 metatiles

# One hand-laid screen per world. '.' is open air; see the legend below.
LEGEND = {
    '.': None, '#': T.GROUND_TOP, '=': T.GROUND_FILL, 'B': T.BLOCK,
    'b': T.BREAKABLE, '-': T.PLATFORM, '^': T.SPIKES, '<': T.LEDGE_L,
    '>': T.LEDGE_R, 'I': T.PILLAR, 'o': T.DECOR, ',': T.BG_A, ';': T.BG_B,
    'D': T.DOOR, '|': T.CHAIN, '~': T.HAZARD,
}

LAYOUTS = [
    # I. Pride - mirrored cathedral gallery
    [',,,,,,,,,,,,,,,',
     ',,I,,,,,,,,,I,,',
     ',,I,,,,o,,,,I,,',
     ',,I,,,,,,,,,I,,',
     ',,I,,---,,,,I,D',
     ',,I,,,,,,,,,I,;',
     ',,I,,,,,,b,,I,;',
     '<###,,,,,,,,###',
     '====,,,,,,,,===',
     '====^^^^^^^^==='],
    # II. Greed - collapsing vault
    [',,,,,,,,,,,,,,,',
     ',,,,,,,,,,,,,,,',
     ',,,,,,,,,,,,,,D',
     ',,,,,,,bbb,,,,;',
     ',,,--,,,,,,,,##',
     ',,,,,,,,,,,,,==',
     ',,o,,,,,--,,,==',
     '###,,,,,,,,,,==',
     '===<,,,,,,,,,==',
     '====,,~~~~,,,=='],
    # III. Lust - thorned garden
    [';;;;;;;;;;;;;;;',
     ';;;;;;;;;;;;;;;',
     ';;;,,,,,,,,,;;;',
     ';;,,,,,--,,,,;D',
     ';,,,,,,,,,,,,,;',
     ';,,,--,,,,,b,,;',
     ';,,,,,,,,,,,,,;',
     '####>,,,,,<####',
     '====,,,,,,,====',
     '====^^^^^^^===='],
    # IV. Envy - the mire
    [',,,,,,,,,,,,,,,',
     ',,,,,,,,,,,,,,,',
     ',,,,,,,,,,,,,,D',
     ',,,,,,,,,,,,,,;',
     ',,,--,,,,,--,,;',
     ',,,,,,b,,,,,,,;',
     '#>,,,,,,,,,,,<#',
     '=,,,,,,,,,,,,,=',
     '=,,~~~~~~~~~,,=',
     '===~~~~~~~~~==='],
    # V. Gluttony - the long table
    [';;;;;;;;;;;;;;;',
     ';,,,,,,,,,,,,,;',
     ';,,,,,,,,,,,,,D',
     ';,,,,b,,,b,,,,;',
     ';,,,,,,,,,,,,,;',
     '#####----######',
     '=====,,,,======',
     '=====,,,,======',
     '==,,,,,,,,,,,==',
     '==^^^^^^^^^^^=='],
    # VI. Wrath - the faultline
    [',,,,,,,,,,,,,,,',
     ',,,,,,,,,,,,,,,',
     ',,,,,,,,,,,,,,D',
     ',,,,,,,,,,,,,,;',
     ',,--,,,,,,--,,;',
     ',,,,,,,,,,,,,,;',
     '##>,,,,,,,,,<##',
     '==,,,,,,,,,,,==',
     '==,,,,,,,,,,,==',
     '==~~~~~~~~~~~=='],
    # VII. Sloth - the decaying manor
    [',,,,,,,,,,,,,,,',
     ',|,,,,,|,,,,|,,',
     ',|,,,,,|,,,,|,D',
     ',|,,,,,|,,,,|,;',
     ',o,,,,,,,,,,,,;',
     ',,,,---,,,,,,,;',
     ',,,,,,,,,,b,,,;',
     '#######,,,#####',
     '=======,,,=====',
     '=======^^^====='],
    # VIII. Hades - the throne approach
    [';;;;;;;;;;;;;;;',
     ';;I;;;;;;;;;I;;',
     ';;I;;;;;;;;;I;D',
     ';;I;;;;;;;;;I;;',
     ';;I;;;--;;;;I;;',
     ';;I;;;;;;;;;I;;',
     ';;I;;;;;;;;;I;;',
     '###,,,,,,,,,###',
     '===,,,,,,,,,===',
     '===~~~~~~~~~==='],
]

# (enemy builder, metatile column, metatile row, pixel nudge)
CAST = [
    (art_enemies.halo_imp,     10, 6, (0, 0)),
    (art_enemies.cherub_fiend,  6, 3, (0, 4)),
    (art_enemies.gnasher,       4, 6, (0, 0)),
    (art_enemies.censer_wraith, 9, 2, (0, 6)),
    (art_enemies.bone_bat,      5, 2, (0, 2)),
    (art_enemies.halo_imp,      8, 6, (0, 0)),
    (art_enemies.bone_bat,     10, 4, (0, 0)),
    (art_enemies.gnasher,       9, 6, (0, 0)),
]

PICKUPS = [
    art_items.pu_soul_flame, art_items.pu_purple_soul, art_items.pu_devil_dash,
    art_items.pu_wisp_wings, art_items.one_up, art_items.pu_soul_flame,
    art_items.pu_purple_soul, art_items.pu_wisp_wings,
]


def screen(world, frame=0, with_boss=False):
    """One 240x160 frame of world `world`, laid out like a real stage."""
    c = Canvas(SCREEN_W, SCREEN_H)
    tiles = T.world_tiles(world)
    layout = LAYOUTS[world]

    # backdrop, so the transparent slots aren't just void
    for ry in range(ROWS):
        for rx in range(COLS):
            c.paste(tiles[T.BG_A], rx * T.T, ry * T.T)

    for ry, row in enumerate(layout):
        for rx, ch in enumerate(row):
            slot = LEGEND.get(ch)
            if slot is not None:
                c.paste(tiles[slot], rx * T.T, ry * T.T)

    if with_boss:
        name, fn, size, title = art_bosses.BOSSES[world]
        boss = fn(frame % 2)
        c.paste(boss, 150 - size // 2, 112 - size)
    else:
        fn, cx, cy, (ox, oy) = CAST[world]
        c.paste(fn(frame % 4), cx * T.T + ox, cy * T.T + oy)
        pu = PICKUPS[world](frame % 2)
        c.paste(pu, 5 * T.T, 4 * T.T + 4)
        for i in range(3):
            c.paste(art_items.soul_orb(frame % 4), 7 * T.T + i * 10, 5 * T.T + 4)

    # Luv, standing on the floor at the left
    luv = art_luv.sheet_frames()[[0, 2, 3, 4][frame % 4]]
    c.paste(luv, 2 * T.T, 7 * T.T - 26)

    # HUD
    for i in range(3):
        c.paste(art_items.hud_halo(0), 6 + i * 10, 6)
    for i in range(6):
        c.paste(art_items.hud_meter(1 if i < 4 else 0), 200 + (i % 6) * 6 - 30, 6)
    return c
