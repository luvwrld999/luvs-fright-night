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


def case(name):
    def wrap(fn):
        CASES[name] = fn
        return fn
    return wrap


def tap(key, times=1, hold=8, gap=11):
    out = []

    for _ in range(times):
        out.append('tap %s %d' % (key, hold))
        out.append('wait %d' % gap)

    return out


@case('menu')
def _menu():
    """The front end, and the reveal that opens it."""
    return (['wait 60', 'shot 01_reveal', 'wait 40', 'shot 02_reveal_late',
             'wait 150', 'shot 03_menu'])


@case('extras')
def _extras():
    """Every screen behind EXTRAS."""
    out = ['wait 240'] + tap('down', 3) + ['wait 16'] + tap('a')
    out += ['wait 70', 'shot 01_extras']
    out += tap('a') + ['wait 100', 'shot 02_scores']
    out += tap('a') + ['wait 90', 'shot 03_rush_board']
    out += tap('b') + ['wait 70']
    out += tap('down', 3) + ['wait 16'] + tap('a') + ['wait 70', 'shot 04_cheat']
    return out


@case('credits')
def _credits():
    out = ['wait 240'] + tap('down', 3) + ['wait 16'] + tap('a') + ['wait 70']
    out += tap('down', 4) + ['wait 16'] + tap('a') + ['wait 90', 'shot 01_credits']
    return out


@case('files')
def _files():
    """New game asks which of the three cartridge files to use."""
    out = ['wait 240'] + tap('a') + ['wait 80', 'shot 01_files']
    out += tap('down') + ['wait 20', 'shot 02_second']
    return out


@case('story')
def _story():
    """The sin's word on the way in, then the world card."""
    out = ['wait 240'] + tap('a') + ['wait 60'] + tap('a')
    out += ['wait 90', 'shot 01_line_one', 'wait 110', 'shot 02_line_two',
            'wait 110', 'shot 03_line_three', 'wait 240', 'shot 04_card']
    return out


@case('play')
def _play():
    """World 1-1 from the start, and the pause over it."""
    out = ['wait 240'] + tap('a') + ['wait 60'] + tap('a') + ['wait 480']
    out += ['wait 250', 'shot 01_open']
    out += ['hold right', 'wait 260', 'shot 02_running', 'release all', 'wait 20']
    out += tap('start') + ['wait 50', 'shot 03_paused']
    return out


@case('codes')
def _codes():
    """Level code entry, refusing a wrong one and taking a right one."""
    letters = 'BCDFGHJKLMNPRSTV'
    out = ['wait 240'] + tap('down', 2) + ['wait 16'] + tap('a')
    out += ['wait 70', 'shot 01_blank']
    out += tap('a') + ['wait 50', 'shot 02_refused', 'wait 100']

    for i, ch in enumerate('KKKC'):
        out += tap('up', letters.index(ch), hold=6, gap=7)

        if i < 3:
            out += tap('right')

    out += ['wait 20', 'shot 03_typed'] + tap('a') + ['wait 50', 'shot 04_named']
    return out


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


def run_case(name, lines, into):
    script = os.path.join(EMU, 'regress_%s.txt' % name)

    with open(script, 'w') as f:
        f.write('\n'.join(lines) + '\n')

    if os.path.isdir(into):
        shutil.rmtree(into)

    os.makedirs(into)
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
