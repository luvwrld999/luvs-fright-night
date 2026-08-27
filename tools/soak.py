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
    regress.fresh_cartridge(ROM)
    proc = subprocess.run(
        ['docker', 'run', '--rm', '-v', '%s:/w' % ROOT, '-w', '/w', 'lfn-mgba',
         '/w/' + os.path.relpath(ROM, ROOT),
         '/w/' + os.path.relpath(path, ROOT),
         '/w/' + os.path.relpath(into, ROOT)],
        capture_output=True, text=True)
    os.remove(path)
    return proc.stdout + proc.stderr


def wanted_track(index):
    """Which track index the level table says this stage should ask for."""
    import re
    src = open(os.path.join(ROOT, 'include', 'lfn_levels.h')).read()
    rows = re.findall(
        r'\{"[^"]+",\s*\w+_tiles,\s*\w+_spawns,\s*[-\d]+,\s*[-\d]+,'
        r'\s*[-\d]+,\s*([-\d]+),', src)
    return int(rows[index]) if index < len(rows) else -1


def judge(index, log):
    """What the log has to show for this stage to count as passing."""
    problems = []

    if BAD.search(log):
        first = next(l for l in log.splitlines() if BAD.search(l))
        problems.append('crashed: %s' % first.strip()[:70])

    if 'main: starting stage %d' % index not in log:
        problems.append('never entered')

    want = wanted_track(index)

    if want >= 0:
        if 'audio: no such track' in log:
            problems.append('asked for a track that does not exist')
        elif 'audio: track %d playing 1' % want not in log:
            got = re.findall(r'audio: track (\d+) playing (\d)', log)
            problems.append('music: wanted track %d, saw %s'
                            % (want, got[-3:] or 'nothing'))

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


# Which stage warps where, and where that room lets you out again.
WARPS = [(1, 24, 2), (10, 25, 15), (16, 26, 21)]


def warp_script(index):
    """Enter a stage that has a secret door; the harness takes it for us."""
    out = regress.boot() + regress.tap('down', 3) + ['wait 16'] + regress.tap('a')
    out += ['wait 70'] + regress.type_code(regress.level_code(index))
    out += ['wait 120']

    if index % 3 == 0:
        out += ['wait 560']

    out += ['wait 200', 'wait 2000', 'shot final']
    return out


def check_warps():
    """
    Every secret door goes somewhere, and every room lets you back out.

    Straight Down had an exit and no entrance for its whole life. This walks
    each route in the game rather than trusting the table.
    """
    print('building the warp ROM...')
    subprocess.run(['./build.sh', 'clean'], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL)
    flags = FLAGS.replace('-DLFN_TEST_AUTOPILOT=1',
                          '-DLFN_TEST_AUTOPILOT=1 -DLFN_TEST_WARP=240')
    proc = subprocess.run(['./build.sh', 'USERFLAGS=' + flags], cwd=ROOT,
                          capture_output=True, text=True)

    if proc.returncode or 'error:' in proc.stdout:
        print(proc.stdout[-2000:])
        raise SystemExit('build failed')

    shutil.move(os.path.join(ROOT, 'LuvsFrightNight.gba'), ROM)
    bad = 0

    for stage, room, out_to in WARPS:
        name = 'warp%02d' % stage
        path = os.path.join(EMU, 'soak_%s.txt' % name)

        with open(path, 'w') as f:
            f.write('\n'.join(warp_script(stage)) + '\n')

        into = os.path.join(WORK, name)
        os.makedirs(into, exist_ok=True)
        regress.fresh_cartridge(ROM)
        log = subprocess.run(
            ['docker', 'run', '--rm', '-v', '%s:/w' % ROOT, '-w', '/w',
             'lfn-mgba', '/w/' + os.path.relpath(ROM, ROOT),
             '/w/' + os.path.relpath(path, ROOT),
             '/w/' + os.path.relpath(into, ROOT)],
            capture_output=True, text=True)
        os.remove(path)
        text = log.stdout + log.stderr

        problems = []

        if 'main: starting stage %d' % room not in text:
            problems.append('door does not reach room %d' % room)
        elif 'main: starting stage %d' % out_to not in text:
            problems.append('room %d does not let out at %d' % (room, out_to))

        if BAD.search(text):
            problems.append('crashed')

        import lfn_names

        if problems:
            bad += 1
            print('  FAIL  %-22s %s' % (lfn_names.of(stage),
                                        '; '.join(problems)))
        else:
            print('  ok    %-22s -> %s -> %s'
                  % (lfn_names.of(stage), lfn_names.of(room),
                     lfn_names.of(out_to)))

    os.remove(ROM)
    print('\n%d route(s) walked, %d failed' % (len(WARPS), bad))
    return 1 if bad else 0


def check_sram():
    """
    A save written by one run is still there for the next one.

    This has to use a release ROM: the test flags deliberately unlock every
    stage on load, which would answer the question before it was asked.
    """
    print('building a release ROM...')
    subprocess.run(['./build.sh', 'clean'], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL)
    proc = subprocess.run(['./build.sh'], cwd=ROOT, capture_output=True,
                          text=True)

    if proc.returncode or 'error:' in proc.stdout:
        print(proc.stdout[-2000:])
        raise SystemExit('build failed')

    rom = os.path.join(EMU, 'lfn_sram.gba')
    shutil.move(os.path.join(ROOT, 'LuvsFrightNight.gba'), rom)
    sav = rom[:-4] + '.sav'

    if os.path.exists(sav):
        os.remove(sav)                  # a brand new cartridge

    def session(name, lines):
        path = os.path.join(EMU, 'soak_%s.txt' % name)

        with open(path, 'w') as f:
            f.write('\n'.join(lines) + '\n')

        into = os.path.join(WORK, name)
        os.makedirs(into, exist_ok=True)
        subprocess.run(
            ['docker', 'run', '--rm', '-v', '%s:/w' % ROOT, '-w', '/w',
             'lfn-mgba', '/w/' + os.path.relpath(rom, ROOT),
             '/w/' + os.path.relpath(path, ROOT),
             '/w/' + os.path.relpath(into, ROOT)],
            check=True, capture_output=True)
        os.remove(path)
        return into

    # A blank cartridge has a four-row menu - NEW GAME, 2 PLAYER, LEVEL CODE,
    # EXTRAS. CONTINUE and STAGE SELECT only appear once there is something to
    # continue, which is the whole thing being tested, so the rows move.
    first = regress.boot() + ['shot 01_menu_blank']
    first += regress.tap('down', 2) + ['wait 16'] + regress.tap('a')
    first += ['wait 70'] + regress.type_code(regress.level_code(6))
    first += ['wait 120', 'wait 560', 'wait 300', 'shot 02_playing']
    a = session('sram_a', first)

    raw = open(sav, 'rb').read() if os.path.exists(sav) else b''
    written = sum(1 for byte in raw if byte not in (0, 255))

    if not written:
        print('  FAIL  the battery file is %d bytes of nothing' % len(raw))
        os.remove(rom)
        return 1

    # Second boot, same cartridge: CONTINUE should be on the menu now.
    second = regress.boot() + ['shot 01_menu_after']
    b = session('sram_b', second)

    from PIL import Image

    def frame(d, n):
        return Image.open(os.path.join(d, n + '.ppm')).convert('RGB')

    blank = frame(a, '01_menu_blank')
    after = frame(b, '01_menu_after')
    same = sum(1 for x, y in zip(blank.getdata(), after.getdata()) if x == y)
    share = same / float(blank.width * blank.height)

    os.remove(rom)
    print('  battery file: %d bytes' % os.path.getsize(sav))

    if share > 0.999:
        print('  FAIL  the menu is identical after saving and rebooting - '
              'nothing was remembered')
        return 1

    print('  ok    %d byte(s) of progress written, and the menu came back '
          'changed (%.1f%% redrawn)' % (written, (1 - share) * 100))
    print('  look:  %s' % os.path.join(b, '01_menu_after.ppm'))
    return 0


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
    if '--warps' in argv:
        return check_warps()

    if '--sram' in argv:
        return check_sram()

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
