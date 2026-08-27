#!/usr/bin/env python3
"""
Drive every stage in the game and prove none of them falls over.

The bug that ended a play session - ent_kind::warp asserting on a frame index
that sheet did not have - was a one-line fault in a stage nothing had ever
run. Twenty-two stages and eight boss state machines had the same exposure.
This enters all of them, lets each one play, and fails on an assert, a hang,
or a boss that will not die.

What it does not do is play the game end to end in one sitting. The pilot in
lfn_luv.cpp is a smoke-test driver with no path planner: it runs right and
jumps when the floor stops, and on a wide gap it falls in, respawns at the
checkpoint and falls in again - the code says as much where it handles falling
out. Whether a gap can be crossed at all is answered by check_levels.py, which
models the real jump arc against every hole in every stage.

    python3 tools/soak.py              # every stage
    python3 tools/soak.py --only 2 5   # just these level indices
"""

import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import regress

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMU = os.path.join(ROOT, 'tools', 'emu')
ROM = os.path.join(EMU, 'lfn_soak.gba')
WORK = os.path.join(EMU, 'soak')

FLAGS = ('-DLFN_TEST_AUTOPILOT=1 -DLFN_TEST_INVULNERABLE=1 '
         '-DLFN_TRACE_ENABLED=1 -DBN_CFG_ASSERT_ENABLED=true '
         '-DBN_CFG_AUDIO_MAX_SOUND_CHANNELS=8 -DBN_CFG_AUDIO_MAX_COMMANDS=32 '
         '-DBN_CFG_SPRITE_TILES_MAX_ITEMS=256 -DBN_CFG_SPRITES_MAX_ITEMS=192 '
         '-DBN_CFG_SPRITE_PALETTES_MAX_ITEMS=32')

STORY = 24
LEVELS = 27
BOSSES = {w * 3 - 1 for w in range(1, 9)}

# Anything the game prints when it gives up. mGBA relays Butano's assert over
# the same debug channel the trace uses.
BAD = re.compile(r'assert|Assertion|FATAL|abort|Unimplemented|unhandled',
                 re.IGNORECASE)


def budget(index):
    if index == 23:
        return 3000         # Hades, then the ending has to start
    if index in BOSSES:
        return 2400
    return 1500


def script(index):
    """Enter one stage by its level code and let the pilot play it."""
    out = regress.boot() + regress.tap('down', 3) + ['wait 16'] + regress.tap('a')
    out += ['wait 70'] + regress.type_code(regress.level_code(index))
    out += ['wait 120']

    # The sin only speaks on the way into its world.
    if index < STORY and index % 3 == 0:
        out += ['wait 560']

    out += ['wait 200', 'wait %d' % budget(index), 'shot final']
    return out


def run(index):
    name = 'lv%02d' % index
    path = os.path.join(EMU, 'soak_%s.txt' % name)

    with open(path, 'w') as f:
        f.write('\n'.join(script(index)) + '\n')

    into = os.path.join(WORK, name)

    if os.path.isdir(into):
        shutil.rmtree(into)

    os.makedirs(into)
    proc = subprocess.run(
        ['docker', 'run', '--rm', '-v', '%s:/w' % ROOT, '-w', '/w', 'lfn-mgba',
         '/w/' + os.path.relpath(ROM, ROOT),
         '/w/' + os.path.relpath(path, ROOT),
         '/w/' + os.path.relpath(into, ROOT)],
        capture_output=True, text=True)
    os.remove(path)
    return proc.stdout + proc.stderr


def judge(index, log):
    """What the log has to show for this stage to count as passing."""
    problems = []

    if BAD.search(log):
        first = next(l for l in log.splitlines() if BAD.search(l))
        problems.append('crashed: %s' % first.strip()[:70])

    if 'main: starting stage %d' % index not in log:
        problems.append('never entered')

    if index == 23 and 'main: ending' not in log:
        # Beating Hades is the only thing that finishes the story, and the
        # ending used to fire on any warp instead. This is the check that
        # would have caught that the right way round.
        problems.append('Hades died but the ending never played')

    if index in BOSSES:
        if 'boss wounded, hp 0' not in log:
            hits = log.count('boss wounded')
            problems.append('boss not killed (%d hit(s) landed)' % hits)

        if 'boss phase' not in log:
            problems.append('no phase change')

    return problems


def build():
    print('building the soak ROM...')
    subprocess.run(['./build.sh', 'clean'], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL)
    proc = subprocess.run(['./build.sh', 'USERFLAGS=' + FLAGS], cwd=ROOT,
                          capture_output=True, text=True)

    if proc.returncode or 'error:' in proc.stdout:
        print(proc.stdout[-2000:])
        raise SystemExit('build failed')

    shutil.move(os.path.join(ROOT, 'LuvsFrightNight.gba'), ROM)


def main(argv):
    only = [int(a) for a in argv[argv.index('--only') + 1:]] \
        if '--only' in argv else list(range(LEVELS))

    build()

    if os.path.isdir(WORK):
        shutil.rmtree(WORK)

    os.makedirs(WORK)

    import lfn_names
    bad = []

    for index in only:
        log = run(index)
        problems = judge(index, log)
        kind = 'boss ' if index in BOSSES else ''
        label = '%s%2d %s' % (kind, index, lfn_names.of(index))

        if problems:
            bad.append((index, problems))
            print('  FAIL  %-34s %s' % (label, '; '.join(problems)))
        else:
            print('  ok    %s' % label)

        with open(os.path.join(WORK, 'lv%02d' % index, 'trace.log'), 'w') as f:
            f.write(log)

    os.remove(ROM)
    print('\n%d stage(s) driven, %d failed' % (len(only), len(bad)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
