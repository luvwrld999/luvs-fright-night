#!/usr/bin/env python3
"""
Measure the difficulty curve.

Reads the generated stages and reports what a player actually meets: how long
each one is, how much of it is enemies, how much is holes, and whether the
clock leaves enough room. Difficulty is supposed to climb; this is how we find
out whether it does.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import level_kit as K

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREEN = 15                     # metatiles across a GBA screen

ENEMY_CHARS = 'icgwvf'
PICKUP_CHARS = '1234us' + ''.join(K.PRIZE_CHARS)
HAZARD_CHARS = K.SPIKE + K.LAVA


def tunables():
    src = open(os.path.join(ROOT, 'include', 'lfn_tune.h')).read()

    def value(name):
        return float(re.search(r'%s\s*=\s*(-?[\d.]+)' % name, src).group(1))

    return value('run_max'), int(value('stage_time')), int(value('time_frames'))


RUN, STAGE_TIME, TIME_FRAMES = tunables()


def read(path):
    meta, rows = {}, []

    for line in open(path):
        line = line.rstrip('\n')

        if line.startswith('!'):
            k, v = line[1:].split(':', 1)
            meta[k.strip()] = v.strip()
        elif line:
            rows.append(line)

    return meta, rows


def gaps(rows):
    """Widths of every run of open air in the floor."""
    width = len(rows[0])
    out, run = [], 0

    for col in range(width):
        solid = any(rows[r][col] in (K.GROUND, K.FILL) for r in range(K.FLOOR, K.ROWS))

        if solid:
            if run:
                out.append(run)
            run = 0
        else:
            run += 1

    if run:
        out.append(run)

    return out


def hazard_regions(rows):
    """
    Contiguous stretches of spikes or lava, not individual tiles.

    A six-tile lava pit is one hazard you jump, not six - counting tiles makes
    a world that fills its pits look far harder than one that leaves them empty
    when the jump is identical.
    """
    width = len(rows[0])
    count, inside = 0, False

    for col in range(width):
        here = any(rows[r][col] in HAZARD_CHARS for r in range(K.ROWS))

        if here and not inside:
            count += 1

        inside = here

    return count


def measure(path):
    meta, rows = read(path)
    flat = ''.join(rows)
    width = len(rows[0])
    screens = width / SCREEN
    holes = gaps(rows)

    enemies = sum(flat.count(c) for c in ENEMY_CHARS)
    pickups = sum(flat.count(c) for c in PICKUP_CHARS)
    hazards = hazard_regions(rows)

    # Rough traversal: the whole width at running speed, plus a beat per hazard
    # and per hole for the jump and the hesitation before it.
    frames = (width * 16 / RUN) + (len(holes) * 45) + (enemies * 25)
    budget = STAGE_TIME * TIME_FRAMES

    return {
        'key': os.path.basename(path)[:-4],
        'name': meta.get('name', '?'),
        'boss': int(meta.get('boss', 0)),
        'width': width,
        'screens': screens,
        'enemies': enemies,
        'enemy_density': enemies / screens,
        'pickups': pickups,
        'hazards': hazards,
        'gaps': len(holes),
        'widest_gap': max(holes) if holes else 0,
        'frames': frames,
        'clock_headroom': budget / frames if frames else 99,
        # What the player is actually up against per screen.
        'pressure': (enemies / screens) + (len(holes) / screens) * 1.5
                    + (hazards / screens) * 1.0,
    }


def main():
    files = sorted(f for f in os.listdir(os.path.join(ROOT, 'levels'))
                   if f.endswith('.txt'))
    rows = [measure(os.path.join(ROOT, 'levels', f)) for f in files]

    print('%-9s %-22s %5s %6s %6s %5s %5s %6s %7s %6s'
          % ('stage', 'name', 'width', 'scrns', 'enemy', 'gaps', 'hazrd',
             'pickup', 'clock', 'press'))

    for r in rows:
        flag = ''

        if r['clock_headroom'] < 1.6 and not r['boss']:
            flag += '  CLOCK TIGHT'

        print('%-9s %-22s %5d %6.1f %6d %5d %5d %6d %6.1fx %6.1f%s'
              % (r['key'], r['name'][:22], r['width'], r['screens'], r['enemies'],
                 r['gaps'], r['hazards'], r['pickups'], r['clock_headroom'],
                 r['pressure'], flag))

    # Does the pressure actually climb, world by world?
    print('\nper world (normal stages only):')
    worst = 0

    for world in range(8):
        pair = [r for r in rows if r['key'].startswith('w%d_' % (world + 1))
                and not r['boss']]
        avg = sum(r['pressure'] for r in pair) / len(pair)
        bar = '#' * int(avg * 4)
        print('  world %d  pressure %5.2f  %s' % (world + 1, avg, bar))

        if avg < worst - 0.15:
            print('           ^ easier than the world before it')

        worst = max(worst, avg)


if __name__ == '__main__':
    main()
