"""Emit the emulator script that captures the scrape screenshots.

Stage select is the only reliable way to land on a specific level, so each shot
is its own reset-then-navigate pass rather than one long playthrough.
"""
import sys

TOTAL = 27          # every entry stage select lists on a test build
LINES = []


def out(s):
    LINES.append(s)


def goto(index, settle=70):
    """From a cold boot, walk stage select onto `index` and start it."""
    out('reset')
    out('wait 220')
    for _ in range(4):      # CONTINUE, NEW GAME, 2 PLAYER, LEVEL CODE, STAGE SELECT
        out('tap down 8')
        out('wait 14')

    out('tap a 8')
    out('wait 30')

    for _ in range(TOTAL - 1 - index):
        out('tap up 6')
        out('wait 8')

    out('tap a 8')
    out('wait %d' % settle)


def play(frames, shots):
    """Hold right and fire the named shots at the given frame offsets."""
    out('hold right')
    seen = 0

    for at, name in shots:
        out('wait %d' % (at - seen))
        out('shot %s' % name)
        seen = at

    out('wait %d' % max(frames - seen, 1))
    out('release all')


# Front end first, before any stage has been entered.
out('wait 220')
out('shot 01_title')
out('wait 20')

# World 1-1: the establishing shot, card included.
goto(0, settle=10)
out('wait 40')
out('shot 02_card')
out('wait 150')
play(420, [(120, '03_play_1_1'), (300, '04_play_1_1b')])

# Mid-game, so the sheet is not all one tileset.
goto(12)
play(360, [(140, '05_play_5_1'), (300, '06_play_5_1b')])

goto(18)
play(300, [(150, '07_play_7_1')])

# A boss arena.
goto(2)
play(260, [(120, '08_boss_1')])

goto(23)
play(260, [(120, '09_boss_hades')])

open(sys.argv[1], 'w').write('\n'.join(LINES) + '\n')
print('%s  (%d lines)' % (sys.argv[1], len(LINES)))
