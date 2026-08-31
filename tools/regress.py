#!/usr/bin/env python3
"""
Golden-frame regression: prove the screens still look like they did.

Every screen in this game has been checked by a person looking at a contact
sheet exactly once. This runs the same scripted sessions again on a fresh ROM
and compares each captured frame against a blessed baseline, so a change that
was never meant to touch the front end cannot quietly redraw it.

    python3 tools/regress.py            # check against the baselines
    python3 tools/regress.py --bless    # accept what it sees as the new truth
    python3 tools/regress.py --only menu extras

Frames that differ are written to tools/emu/regress/ as a side-by-side sheet,
golden on the left and current on the right, so the change can be looked at
rather than guessed about.

Exits non-zero if anything changed, so it can gate a commit.
"""

import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image

import make_save

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMU = os.path.join(ROOT, 'tools', 'emu')
GOLDEN = os.path.join(EMU, 'golden')
WORK = os.path.join(EMU, 'regress')
ROM = os.path.join(EMU, 'lfn_regress.gba')

# A frame is "changed" past this share of differing pixels. Not zero: the
# emulator is deterministic, but a one-pixel sprite bob landing on a different
# frame of its cycle is not a regression worth failing a build over.
TOLERANCE = 0.004

FLAGS = ('-DBN_CFG_ASSERT_ENABLED=true '
         '-DBN_CFG_AUDIO_MAX_SOUND_CHANNELS=8 -DBN_CFG_AUDIO_MAX_COMMANDS=32 '
         '-DBN_CFG_SPRITE_TILES_MAX_ITEMS=256 -DBN_CFG_SPRITES_MAX_ITEMS=192 '
         '-DBN_CFG_SPRITE_PALETTES_MAX_ITEMS=32')

# Each case is a scripted session and the name its frames are filed under.
# Built by the generators below rather than checked in, so a menu that gains a
# row is a one-line change here instead of a hand-edited script.
CASES = {}

# Cases needing a cartridge with progress on it, and how far it reaches.
# Seeding the save to exactly the stage under test puts stage select's cursor
# on it, so the script picks it with one button instead of counting its way
# down a list.
SEEDS = {}


def case(name, seed=None):
    def wrap(fn):
        CASES[name] = fn

        if seed is not None:
            SEEDS[name] = seed

        return fn
    return wrap


def boot():
    """
    Past the title gate and onto the menu.

    The front end holds on the wordmark until START, once per boot, so every
    case has to get through that before it can drive anything.
    """
    return ['wait 140'] + tap('start') + ['wait 70']


def tap(key, times=1, hold=8, gap=11):
    out = []

    for _ in range(times):
        out.append('tap %s %d' % (key, hold))
        out.append('wait %d' % gap)

    return out


@case('menu')
def _menu():
    """The title gate, the wordmark, and the menu behind it."""
    return (['wait 40', 'shot 01_logo_drop', 'wait 60', 'shot 02_press_start']
            + tap('start') + ['wait 70', 'shot 03_menu'])


# A blank cartridge shows NEW GAME, 2 PLAYER, EXTRAS. Level codes used to sit
# between the last two.
MENU_EXTRAS_BLANK = 2


@case('extras')
def _extras():
    """Every screen behind EXTRAS."""
    out = boot() + tap('down', MENU_EXTRAS_BLANK) + ['wait 16'] + tap('a')
    out += ['wait 70', 'shot 01_extras']
    out += tap('a') + ['wait 100', 'shot 02_scores']
    out += tap('a') + ['wait 90', 'shot 03_rush_board']
    out += tap('b') + ['wait 70']
    out += tap('down', 3) + ['wait 16'] + tap('a') + ['wait 70', 'shot 04_cheat']
    return out


@case('credits')
def _credits():
    out = boot() + tap('down', MENU_EXTRAS_BLANK) + ['wait 16'] + tap('a')
    out += ['wait 70']
    out += tap('down', 4) + ['wait 16'] + tap('a') + ['wait 90', 'shot 01_credits']
    return out


@case('files')
def _files():
    """New game asks which of the three cartridge files to use."""
    out = boot() + tap('a') + ['wait 80', 'shot 01_files']
    out += tap('down') + ['wait 20', 'shot 02_second']
    return out


@case('story')
def _story():
    """Luv's opening, then the sin's word on the way in, then the world card."""
    out = boot() + tap('a') + ['wait 60'] + tap('a')
    out += ['wait 80', 'shot 01_opening']
    # The opening runs about nine seconds before the world's own card starts.
    out += ['wait 520', 'shot 02_line_one', 'wait 110', 'shot 03_line_two',
            'wait 220', 'shot 04_card']
    return out


@case('play')
def _play():
    """World 1-1 from the start, and the pause over it."""
    out = boot() + tap('a') + ['wait 60'] + tap('a')
    out += ['wait 600', 'wait 480', 'wait 250', 'shot 01_open']
    out += ['hold right', 'wait 260', 'shot 02_running', 'release all', 'wait 20']
    out += tap('start') + ['wait 50', 'shot 03_paused']
    return out


# The first stage of each world.
WORLD_ENTRY = {2: 3, 3: 6, 4: 9, 5: 12, 6: 15, 7: 18, 8: 21}

# With a save on the cartridge the front page reads CONTINUE, NEW GAME,
# 2 PLAYER, STAGE SELECT, EXTRAS.
MENU_STAGE_SELECT = 3


def pick_stage(target, start):
    """
    Open stage select and choose a stage.

    The cursor opens on the furthest level the save has reached, so a case
    that seeded its save to its own stage needs no movement at all, while one
    running on a build that unlocks everything walks up from the end.
    """
    out = tap('down', MENU_STAGE_SELECT) + ['wait 16'] + tap('a') + ['wait 60']

    if start > target:
        out += tap('up', start - target, hold=6, gap=8) + ['wait 16']

    return out + tap('a')


def world_case(world):
    """
    One stage of one world, reached by typing its level code.

    World 1-1 is already covered by `play`; this is worlds two through eight,
    so a tileset, palette or layout change anywhere in the game shows up here
    instead of only in whichever world someone happened to look at. The frame
    is taken where Luv lands, not after a blind run right: walking right into
    VII-1's spike bed only proves the autopilot cannot see, and a baseline
    that depends on surviving is a baseline that changes for the wrong reason.
    Camera scroll and parallax are covered by `play` in world one.
    """
    def build():
        out = boot() + pick_stage(WORLD_ENTRY[world], WORLD_ENTRY[world])
        # The sin gets its say (560 frames), then the world card (190).
        out += ['wait 600', 'wait 200', 'wait 120']
        out += ['shot 01_stage']
        return out

    build.__doc__ = 'World %d, from stage select.' % world
    return build


def boss_case(world):
    """
    One boss arena, entered by code.

    A boss is the third stage of its world, so no sin speaks on the way in -
    the card goes straight to the fight. The frame is taken once the boss has
    walked in but before it has reached a player who is standing still, which
    down there is about a second.
    """
    # Most arenas read well a second in. Invidia charges wall to wall at
    # 1.5px a frame and is off the side of the screen by then; Hades reaches
    # a standing player faster than anything else and the frame caught the
    # hit rather than the boss.
    settle = {4: 22, 8: 20}.get(world, 60)

    def build():
        out = boot() + pick_stage(world * 3 - 1, world * 3 - 1)
        # No sin speaks before a boss; the card goes straight to the fight.
        out += ['wait 200', 'wait %d' % settle]
        out += ['shot 01_arena']
        return out

    build.__doc__ = 'World %d boss arena.' % world
    return build


for _w in sorted(WORLD_ENTRY):
    case('world%d' % _w, seed=WORLD_ENTRY[_w])(world_case(_w))

for _w in range(1, 9):
    case('boss%d' % _w, seed=_w * 3 - 1)(boss_case(_w))


def build_rom():
    print('building a clean ROM...')
    subprocess.run(['./build.sh', 'clean'], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL)
    proc = subprocess.run(['./build.sh', 'USERFLAGS=' + FLAGS], cwd=ROOT,
                          capture_output=True, text=True)

    if proc.returncode or 'error:' in proc.stdout:
        print(proc.stdout[-2000:])
        raise SystemExit('build failed')

    shutil.move(os.path.join(ROOT, 'LuvsFrightNight.gba'), ROM)


def fresh_cartridge(rom):
    """
    Start every run on a blank battery.

    The runner keeps SRAM in a .sav beside the ROM now, so without this each
    run inherits the last one's save - and a cartridge with a save on it has
    CONTINUE and STAGE SELECT on the menu, which moves every row these scripts
    count down to. Only the save test wants the battery kept.
    """
    sav = rom[:-4] + '.sav'

    if os.path.exists(sav):
        os.remove(sav)


def run_case(name, lines, into):
    script = os.path.join(EMU, 'regress_%s.txt' % name)

    with open(script, 'w') as f:
        f.write('\n'.join(lines) + '\n')

    if os.path.isdir(into):
        shutil.rmtree(into)

    os.makedirs(into)

    if name in SEEDS:
        make_save.write(ROM[:-4] + '.sav', furthest=SEEDS[name])
    else:
        fresh_cartridge(ROM)
    subprocess.run(
        ['docker', 'run', '--rm', '-v', '%s:/w' % ROOT, '-w', '/w', 'lfn-mgba',
         '/w/tools/emu/lfn_regress.gba',
         '/w/tools/emu/regress_%s.txt' % name,
         '/w/' + os.path.relpath(into, ROOT)],
        check=True, capture_output=True)
    os.remove(script)


def compare(golden_path, shot_path):
    """Share of pixels that differ between two frames."""
    a = Image.open(golden_path).convert('RGB')
    b = Image.open(shot_path).convert('RGB')

    if a.size != b.size:
        return 1.0

    pa, pb = a.getdata(), b.getdata()
    differing = sum(1 for x, y in zip(pa, pb) if x != y)
    return differing / float(a.width * a.height)


def sheet(pairs, path):
    """Golden on the left, current on the right, one row per changed frame."""
    w, h, scale, pad = 240, 160, 2, 10
    rows = len(pairs)
    img = Image.new('RGB', (w * scale * 2 + pad * 3, (h * scale + 26) * rows + pad),
                    (14, 9, 20))

    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)

    for i, (label, golden, shot) in enumerate(pairs):
        y = pad + i * (h * scale + 26)
        draw.text((pad, y - 1), label, fill=(255, 216, 56))

        for j, src in enumerate((golden, shot)):
            x = pad + j * (w * scale + pad)

            if src and os.path.exists(src):
                frame = Image.open(src).convert('RGB').resize(
                            (w * scale, h * scale), Image.NEAREST)
                img.paste(frame, (x, y + 14))
            else:
                draw.rectangle([x, y + 14, x + w * scale, y + 14 + h * scale],
                               fill=(40, 24, 48))
                draw.text((x + 8, y + 22), 'missing', fill=(255, 80, 160))

    img.save(path)
    return path


def main(argv):
    bless = '--bless' in argv
    only = []

    if '--only' in argv:
        only = argv[argv.index('--only') + 1:]

    names = [n for n in CASES if not only or n in only]

    if not names:
        raise SystemExit('no cases match %s' % only)

    build_rom()
    os.makedirs(GOLDEN, exist_ok=True)

    if os.path.isdir(WORK):
        shutil.rmtree(WORK)

    os.makedirs(WORK)

    changed, checked, blessed = [], 0, 0

    for name in sorted(names):
        shots = os.path.join(WORK, name)
        run_case(name, CASES[name](), shots)
        gold_dir = os.path.join(GOLDEN, name)
        os.makedirs(gold_dir, exist_ok=True)

        for frame in sorted(os.listdir(shots)):
            if not frame.endswith('.ppm'):
                continue

            shot = os.path.join(shots, frame)
            gold = os.path.join(gold_dir, frame[:-4] + '.png')
            label = '%s / %s' % (name, frame[:-4])

            if bless or not os.path.exists(gold):
                Image.open(shot).convert('RGB').save(gold)
                blessed += 1
                print('  blessed  %s' % label)
                continue

            checked += 1
            drift = compare(gold, shot)

            if drift > TOLERANCE:
                changed.append((label, gold, shot))
                print('  CHANGED  %-28s %5.2f%% of pixels' % (label, drift * 100))
            else:
                print('  ok       %-28s %5.2f%%' % (label, drift * 100))

    os.remove(ROM)
    print('\n%d frame(s) checked, %d blessed, %d changed'
          % (checked, blessed, len(changed)))

    if changed:
        out = sheet(changed, os.path.join(WORK, 'changed.png'))
        print('side by side: %s' % out)
        print('if the change was intended: python3 tools/regress.py --bless')
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
