#!/usr/bin/env python3
"""
Capture the screenshots the scrape package ships, from the ROM it ships.

These used to be taken by hand-written emulator scripts that were not kept, so
the box art and the game drifted apart the moment either changed - the shipped
screenshots were four days older than the levels in them. The sessions live
here now, driven the same way the regression suite drives its own: real level
codes, no test flags, and the same release ROM that goes in the package.

    python3 tools/gen_shots.py          # recapture everything
    python3 tools/gen_shots.py --sheet  # and write a contact sheet to look at
"""

import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import regress
import shots as shots_tool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMU = os.path.join(ROOT, 'tools', 'emu')
ROM = os.path.join(ROOT, 'LuvsFrightNight.gba')

# The first stage of each world, and each world's boss arena. A boss is the
# third stage of its world, so world W's arena is at W*3 - 1.
BOSS = {w: w * 3 - 1 for w in range(1, 9)}

# How long to let each arena run before the shutter. Long enough for the boss
# to be on screen and fighting; Hades reaches a standing player faster than
# the rest, and 45 frames there caught the hit rather than the boss.
BOSS_SETTLE = {8: 20}


def enter(index, settle, story=True):
    """
    Type a level code, sit through the cards, then wait `settle` frames.

    The sin only speaks on the way into its world, so a boss - the third
    stage of its world - goes straight from the code screen to the world
    card. Waiting for a card that never comes left an idle player standing
    in the arena for fourteen seconds, and six of the eight arena shots came
    back as the continue screen.
    """
    out = regress.boot() + regress.tap('down', 2) + ['wait 16']
    out += regress.tap('a') + ['wait 70']
    out += regress.type_code(regress.level_code(index))
    out += ['wait 120']                     # the code screen holds the name

    if story:
        out += ['wait 560']                 # the sin gets its say

    out += ['wait 200']                     # the world card, 190 frames
    return out + ['wait %d' % settle]


def title():
    return ['wait 150', 'shot 01_title']


def card():
    """The world card itself, caught while it is still on screen."""
    out = regress.boot() + regress.tap('down', 2) + ['wait 16']
    out += regress.tap('a') + ['wait 70']
    out += regress.type_code(regress.level_code(BOSS[5] - 2))
    # The card is only 190 frames wide and the stage starts the moment it
    # ends, so this lands in the middle of it rather than just after.
    out += ['wait 120', 'wait 560', 'wait 100', 'shot 02_card']
    return out


def world_one(name, running=False):
    """
    World 1-1 through NEW GAME rather than a code.

    Stage zero is the one stage a level code cannot reach cleanly: main.cpp
    plays Luv's opening whenever the run starts at index 0, so the code route
    lands on the story card instead of the game.
    """
    out = regress.boot() + regress.tap('a') + ['wait 60'] + regress.tap('a')
    out += ['wait 600', 'wait 480', 'wait 250']

    if running:
        out += ['hold right', 'wait 200', 'release all', 'wait 20']

    return out + ['shot ' + name]


def stage(name, index, extra=0, story=True):
    out = enter(index, 24 + extra, story)
    return out + ['shot ' + name]


def run(name, lines, into):
    script = os.path.join(EMU, 'shot_%s.txt' % name)

    with open(script, 'w') as f:
        f.write('\n'.join(lines) + '\n')

    os.makedirs(into, exist_ok=True)
    subprocess.run(
        ['docker', 'run', '--rm', '-v', '%s:/w' % ROOT, '-w', '/w', 'lfn-mgba',
         '/w/' + os.path.relpath(ROM, ROOT),
         '/w/' + os.path.relpath(script, ROOT),
         '/w/' + os.path.relpath(into, ROOT)],
        check=True, capture_output=True)
    os.remove(script)


def build():
    """A release ROM - no asserts, no test flags. The one that ships."""
    print('building the release ROM...')
    subprocess.run(['./build.sh', 'clean'], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL)
    proc = subprocess.run(['./build.sh'], cwd=ROOT, capture_output=True,
                          text=True)

    if proc.returncode or 'error:' in proc.stdout:
        print(proc.stdout[-2000:])
        raise SystemExit('build failed')

    for line in proc.stdout.splitlines():
        if 'warning:' in line:
            print('  ' + line)


def main(argv):
    if '--no-build' not in argv:
        build()
    elif not os.path.exists(ROM):
        raise SystemExit('no ROM to capture from; drop --no-build')

    stages = os.path.join(EMU, 'shots')
    arenas = os.path.join(EMU, 'shots2')

    for d in (stages, arenas):
        if os.path.isdir(d):
            shutil.rmtree(d)

        os.makedirs(d)

    run('title', title(), stages)
    run('card', card(), stages)
    # Two frames of world one, then a mid-game world and a late one, so the
    # package shows the game changing rather than three shots of the same wall.
    run('play1', world_one('03_play_1_1'), stages)
    run('play1b', world_one('04_play_1_1b', running=True), stages)
    run('play5', stage('05_play_5_1', BOSS[5] - 2), stages)
    run('play7', stage('07_play_7_1', BOSS[7] - 2), stages)

    for w in range(1, 9):
        # Long enough for the boss to walk in, short enough that it has not
        # yet killed a player who is standing still: three lives go in about
        # three seconds down there, and six of these came back CONTINUE?.
        run('boss%d' % w,
            stage('boss_%d' % w, BOSS[w], extra=BOSS_SETTLE.get(w, 45),
                  story=False),
            arenas)

    got = sorted(f for f in os.listdir(stages) + os.listdir(arenas)
                 if f.endswith('.ppm'))
    print('%d frame(s) captured' % len(got))

    if '--sheet' in argv:
        shots_tool.sheet(os.path.join(EMU, 'shots_sheet.png'), 2, 3,
                         'Scrape package frames')

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
