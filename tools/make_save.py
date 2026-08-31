#!/usr/bin/env python3
"""
Write a cartridge save, so a harness can start wherever it needs to.

The test scripts used to reach an arbitrary stage by typing its level code.
Level codes are gone - stage select does that job now - so instead they seed
the battery. Seeding `furthest` to the stage you want is enough on its own:
stage select opens with its cursor on the furthest level, so the script picks
the stage by pressing A rather than by counting keypresses down a list.

The format is lfn::save::file from include/lfn_save.h, written straight to
SRAM with a magic and no checksum, so it can be built from the outside.

    python3 tools/make_save.py LuvsFrightNight.sav --furthest 23
"""

import argparse
import struct
import sys

MAGIC = 0x4C464E35          # "LFN5"
TABLE = 8                   # high score rows, twice: story and rush
TIMED = 24                  # stages carrying a best time
SLOTS = 3
SRAM = 32 * 1024


def build(furthest=0, lives=3, souls=0, slot=0):
    out = bytearray()
    out += struct.pack('<I', MAGIC)

    # entry { char name[3]; uint32_t score; } - four-byte aligned, so eight
    # bytes each with a pad after the name.
    for _ in range(TABLE * 2):
        out += b'\x00\x00\x00\x00' + struct.pack('<I', 0)

    out += struct.pack('<%dH' % TIMED, *([0] * TIMED))

    # progress { uint16 furthest_level; uint16 souls; uint8 lives; uint8 used;
    #            uint8 pad[2]; }
    for i in range(SLOTS):
        if i == slot:
            out += struct.pack('<HHBBxx', furthest, souls, lives, 1)
        else:
            out += struct.pack('<HHBBxx', 0, 0, 0, 0)

    out += struct.pack('<Bxxx', slot)
    return bytes(out)


def write(path, **kwargs):
    blob = build(**kwargs)
    with open(path, 'wb') as f:
        f.write(blob + b'\x00' * (SRAM - len(blob)))

    return path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('path')
    ap.add_argument('--furthest', type=int, default=0)
    ap.add_argument('--lives', type=int, default=3)
    ap.add_argument('--souls', type=int, default=0)
    args = ap.parse_args(argv)
    write(args.path, furthest=args.furthest, lives=args.lives,
          souls=args.souls)
    print('%s: furthest=%d lives=%d' % (args.path, args.furthest, args.lives))
    return 0


if __name__ == '__main__':
    sys.exit(main())
