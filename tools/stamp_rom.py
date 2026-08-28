#!/usr/bin/env python3
"""
Stamp the cartridge header with an identity that is ours.

devkitARM's gbafix is called without a maker code, so it writes 01 - which is
Nintendo's licensee code. Nothing in the game is Nintendo's, and a homebrew
cartridge should not claim to be licensed by anyone. This writes a neutral
code and repairs the header checksum that depends on it.

    python3 tools/stamp_rom.py LuvsFrightNight.gba
"""

import sys

MAKER = b'00'          # unlicensed / homebrew, the usual code for a self-release


def stamp(path, maker=MAKER):
    with open(path, 'rb') as f:
        rom = bytearray(f.read())

    if len(rom) < 0xC0:
        raise SystemExit('%s is too small to be a GBA ROM' % path)

    was = bytes(rom[0xB0:0xB2])
    rom[0xB0:0xB2] = maker

    # The header checksum covers 0xA0..0xBC and lives at 0xBD.
    total = 0

    for byte in rom[0xA0:0xBD]:
        total -= byte

    rom[0xBD] = (total - 0x19) & 0xFF

    with open(path, 'wb') as f:
        f.write(rom)

    return was.decode('ascii', 'replace'), maker.decode()


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'LuvsFrightNight.gba'
    old, new = stamp(target)
    print('maker code %s -> %s, header checksum repaired' % (old, new))
