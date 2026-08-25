#!/usr/bin/env python3
"""
Level linter: prove every stage can actually be crossed.

Walks each level left to right, and from the right edge of every standing
surface simulates a full-speed jump using the engine's own constants. If no
jump - with or without hovering - lands on the next surface, the gap is
reported. This is what stops a level generator from quietly producing a stage
that cannot be finished.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import level_kit as K

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILE = 16

SOLID = {K.GROUND, K.FILL, K.BLOCK, K.BREAK, K.LEDGE_L, K.LEDGE_R}
STAND = SOLID | {K.PLAT}
DEADLY = {K.SPIKE, K.LAVA}


def tunables():
    """Read the physics straight out of the engine header, so they can't drift."""
    src = open(os.path.join(ROOT, 'include', 'lfn_tune.h')).read()

    def value(name):
        m = re.search(r'%s\s*=\s*(-?[\d.]+)' % name, src)
        return float(m.group(1))

    return {n: value(n) for n in
            ('run_max', 'gravity', 'fall_max', 'jump_speed',
             'hover_gravity', 'hover_fall_max', 'hover_frames',
             'luv_half_w', 'luv_half_h')}


T = tunables()


def load(path):
    rows = [l.rstrip('\n') for l in open(path) if not l.startswith('!') and l.strip()]
    width = max(len(r) for r in rows)
    return [r.ljust(width, K.BG_A) for r in rows], width


def cell(grid, c, r):
    if r < 0 or r >= len(grid) or c < 0 or c >= len(grid[0]):
        return K.BG_A
    ch = grid[r][c]
    return K.BREAK if ch in K.PRIZE_CHARS else (K.BG_A if ch in K.ENTITY_CHARS else ch)


def surfaces(grid, width):
    """Contiguous runs of standable ground, as (row, first_col, last_col)."""
    out = []
    for r in range(len(grid)):
        run = None
        for c in range(width + 1):
            standable = (c < width and cell(grid, c, r) in STAND
                         and cell(grid, c, r - 1) not in SOLID
                         and cell(grid, c, r) not in DEADLY)
            if standable and run is None:
                run = c
            elif not standable and run is not None:
                out.append((r, run, c - 1))
                run = None
    return out


def simulate(grid, width, start_col, start_row, hover, back=0, jump=True):
    """
    Jump from a surface and report the column landed on.

    `back` launches that many tiles before the edge, which is how a real player
    jumps. A gap that only clears from the last pixel is a gap that plays badly.
    """
    x = (start_col + 1 - back) * TILE - T['luv_half_w']
    y = start_row * TILE - T['luv_half_h']
    # `jump=False` is simply walking off the edge, which is a legitimate
    # way to get down from a ledge and must count as reachable.
    vx, vy = T['run_max'], (T['jump_speed'] if jump else 0.0)
    budget = T['hover_frames'] if hover else 0

    for _ in range(240):
        if vy > 0 and budget > 0 and hover:
            budget -= 1
            vy = min(vy + T['hover_gravity'], T['hover_fall_max'])
        else:
            vy = min(vy + T['gravity'], T['fall_max'])

        x += vx
        y += vy

        col = int(x) // TILE
        foot = int(y + T['luv_half_h'])

        if col >= width:
            return col
        if y > len(grid) * TILE:
            return None
        if vy > 0 and cell(grid, col, foot // TILE) in STAND:
            if cell(grid, col, foot // TILE) in DEADLY:
                return None
            return col

    return None


def check(path):
    grid, width = load(path)
    segs = sorted(surfaces(grid, width), key=lambda s: s[1])
    problems = []

    for row, first, last in segs:
        # Is there anything standable immediately to the right? Then no jump.
        if cell(grid, last + 1, row) in STAND:
            continue

        # Ignore the tail end of the level.
        if last + 1 >= width - 1:
            continue

        ahead = [s for s in segs if s[1] > last]

        if not ahead:
            continue

        walk = simulate(grid, width, last, row, hover=False, jump=False) is not None
        edge = walk or \
               simulate(grid, width, last, row, hover=True) is not None or \
               simulate(grid, width, last, row, hover=False) is not None
        # The standard: reachable by walking off, or by a plain jump launched a
        # tile early. Hover should make a gap comfortable, never be the only way
        # over it.
        forgiving = walk or \
                    simulate(grid, width, last, row, hover=False, back=1) is not None

        if not edge:
            problems.append(('unreachable', row, last, ahead[0][1]))
        elif not forgiving:
            problems.append(('pixel-perfect', row, last, ahead[0][1]))

    return problems


# Kinds with no way to fly. Hung in the air with no floor under them they
# reverse on their first step and then stand still for the whole stage, which
# is exactly what "the floating enemies do nothing" looked like.
GROUNDED = (K.IMP, K.GNASHER, K.WRAITH)

SOLID = (K.GROUND, K.FILL, K.BLOCK, K.BREAK, K.PLAT, K.PILLAR, K.SPIKE,
         K.LAVA, K.LEDGE_L, K.LEDGE_R)


def placements(path):
    """
    Two things a gap check cannot see: enemies that cannot stand where they
    were put, and pickups nobody can reach.
    """
    rows, _width = load(path)
    height = len(rows)
    problems = []

    def floor_within(x, y, reach):
        for k in range(1, reach + 1):
            if y + k < height and rows[y + k][x] in SOLID:
                return True

        return False

    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in GROUNDED and not floor_within(x, y, 3):
                problems.append(('walker in the air', x, y))

            # A bonus soul is worth ten, so one placed out of reach is worth
            # complaining about. Six rows is a comfortable jump.
            elif ch == K.SOUL_TEN and not floor_within(x, y, 6):
                problems.append(('soul out of reach', x, y))

    return problems


def main():
    levels = sorted(f for f in os.listdir(os.path.join(ROOT, 'levels'))
                    if f.endswith('.txt'))
    total = 0
    misplaced = 0

    print('jump: rise from %.1f at gravity %.2f, run %.1f px/frame'
          % (-T['jump_speed'], T['gravity'], T['run_max']))

    for name in levels:
        problems = check(os.path.join(ROOT, 'levels', name))
        total += len(problems)
        flag = 'OK  ' if not problems else 'FAIL'
        detail = '' if not problems else '  ' + ', '.join(
            '%s row %d col %d->%d' % p for p in problems[:3])
        placed = placements(os.path.join(ROOT, 'levels', name))
        misplaced += len(placed)

        if placed:
            detail += '  ' + ', '.join('%s at %d,%d' % q for q in placed[:3])
            flag = 'FAIL'

        print('  %s %-10s %d bad gap(s)%s' % (flag, name[:-4], len(problems), detail))

    print('%d bad gaps, %d misplaced entities across %d levels'
          % (total, misplaced, len(levels)))
    return 1 if total or misplaced else 0


if __name__ == '__main__':
    sys.exit(main())
