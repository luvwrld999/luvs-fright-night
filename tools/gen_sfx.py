#!/usr/bin/env python3
"""
Sound effects: mono 8-bit WAVs, which is what Maxmod wants for GBA samples.

Kept short and dry - the music is deliberately quiet ambience, so the effects
are what actually punctuate the action and they must not smear over it.
"""

import math
import os
import struct
import sys

RATE = 11025
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(ROOT, 'audio')
PREVIEW = os.path.join(ROOT, 'preview', 'audio')


class Rng:
    def __init__(self, seed=1):
        self.s = seed & 0x7FFFFFFF or 1

    def uniform(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s / 0x7FFFFFFF * 2.0 - 1.0


def write_wav16(name, samples, folder=PREVIEW):
    """16-bit copy for auditioning; the ROM gets the 8-bit version."""
    peak = max(abs(v) for v in samples) or 1.0
    data = b''.join(struct.pack('<h', int(max(-1.0, min(1.0, v / peak * 0.85)) * 32767))
                    for v in samples)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, name + '.wav'), 'wb') as f:
        f.write(b'RIFF' + struct.pack('<I', 36 + len(data)) + b'WAVE')
        f.write(b'fmt ' + struct.pack('<IHHIIHH', 16, 1, 1, RATE, RATE * 2, 2, 16))
        f.write(b'data' + struct.pack('<I', len(data)) + data)


def write_wav(name, samples, folder=AUDIO):
    """8-bit unsigned mono, the GBA's native sample format."""
    data = bytes(max(0, min(255, int(round(s * 127)) + 128)) for s in samples)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, name + '.wav'), 'wb') as f:
        f.write(b'RIFF' + struct.pack('<I', 36 + len(data)) + b'WAVE')
        f.write(b'fmt ' + struct.pack('<IHHIIHH', 16, 1, 1, RATE, RATE, 1, 8))
        f.write(b'data' + struct.pack('<I', len(data)) + data)
    return len(data)


def env(i, n, attack=0.01, decay=3.0, release=0.08):
    """
    Attack, exponential decay, and - the part that was missing - a release.

    An exponential decay never reaches zero, so a sample that simply stops is
    still moving when it ends. On hardware that step is a click on the front of
    every effect that follows it. The last few percent ramps to silence.
    """
    t = i / float(n)
    a = min(1.0, t / attack) if attack > 0 else 1.0
    r = 1.0 if t < 1.0 - release else max(0.0, (1.0 - t) / release)
    return a * math.exp(-decay * t) * r


def sweep(n, f0, f1, wave='sine', decay=3.0, amp=0.7, seed=1, curve=1.0):
    r = Rng(seed)
    out = []
    phase = 0.0
    for i in range(n):
        t = (i / float(n)) ** curve
        f = f0 + (f1 - f0) * t
        phase += f / RATE
        if wave == 'sine':
            v = math.sin(2 * math.pi * phase)
        elif wave == 'square':
            v = 1.0 if (phase % 1.0) < 0.5 else -1.0
        elif wave == 'pulse':
            v = 1.0 if (phase % 1.0) < 0.2 else -1.0
        elif wave == 'saw':
            v = (phase % 1.0) * 2 - 1
        else:
            v = r.uniform()
        out.append(v * env(i, n, 0.008, decay) * amp)
    return out


def mix(*layers):
    n = max(len(l) for l in layers)
    out = [0.0] * n
    for layer in layers:
        for i, v in enumerate(layer):
            out[i] += v
    return [max(-1.0, min(1.0, v)) for v in out]


def noise(n, decay=5.0, amp=0.6, seed=1, lp=0.3):
    r = Rng(seed)
    out = []
    v = 0.0
    for i in range(n):
        v += (r.uniform() - v) * lp
        out.append(v * env(i, n, 0.004, decay) * amp)
    return out


SFX = {}


def sfx(fn):
    SFX[fn.__name__] = fn
    return fn


@sfx
def sfx_jump():
    """Airy upward whoosh - he doesn't push off, he lets go."""
    return mix(sweep(2400, 320, 900, 'sine', 4.0, 0.5, curve=0.6),
               noise(1600, 7.0, 0.22, 3, lp=0.5))


@sfx
def sfx_hover():
    """Short breathy loop tick while the hover meter drains."""
    return mix(noise(2000, 1.2, 0.16, 5, lp=0.08),
               sweep(2000, 210, 190, 'sine', 1.0, 0.12))


@sfx
def sfx_land():
    return mix(sweep(1300, 180, 70, 'sine', 6.0, 0.55),
               noise(900, 10.0, 0.3, 7, lp=0.4))


@sfx
def sfx_stomp():
    """The satisfying one. Crunch plus a downward thud."""
    return mix(noise(1400, 9.0, 0.55, 11, lp=0.55),
               sweep(1400, 420, 90, 'square', 7.0, 0.45))


@sfx
def sfx_shot():
    """Soul flame leaving the halo."""
    return mix(sweep(1500, 1400, 500, 'pulse', 6.0, 0.42),
               noise(900, 9.0, 0.2, 13, lp=0.6))


@sfx
def sfx_flame_hit():
    return mix(sweep(900, 700, 240, 'saw', 9.0, 0.4),
               noise(700, 12.0, 0.3, 17, lp=0.7))


@sfx
def sfx_dash():
    return mix(sweep(2000, 200, 1100, 'saw', 4.0, 0.4, curve=0.5),
               noise(2000, 4.0, 0.35, 19, lp=0.35))


@sfx
def sfx_hurt():
    """Descending, sour, unmistakable."""
    return mix(sweep(3000, 620, 180, 'square', 3.0, 0.5, curve=1.6),
               sweep(3000, 610, 176, 'square', 3.0, 0.35, curve=1.6))


@sfx
def sfx_death():
    return mix(sweep(9000, 700, 90, 'square', 1.6, 0.45, curve=1.8),
               sweep(9000, 350, 60, 'sine', 1.4, 0.35, curve=1.8),
               noise(9000, 2.0, 0.14, 23, lp=0.1))


@sfx
def sfx_pickup():
    """Two rising blips - a soul joining the count."""
    a = sweep(700, 880, 880, 'pulse', 8.0, 0.4)
    b = [0.0] * 700 + sweep(900, 1320, 1320, 'pulse', 7.0, 0.4)
    return mix(a, b)


@sfx
def sfx_power_up():
    """Four-note rise for taking a power-up."""
    out = []
    for k, f in enumerate((523, 659, 784, 1047)):
        out += sweep(950, f, f, 'pulse', 6.0, 0.38)
    return out


@sfx
def sfx_one_up():
    out = []
    for f in (784, 988, 1175, 1568, 1976):
        out += sweep(800, f, f, 'pulse', 5.5, 0.4)
    return out


@sfx
def sfx_checkpoint():
    """A candle catching."""
    return mix(noise(2600, 3.0, 0.3, 29, lp=0.25),
               sweep(2600, 300, 760, 'sine', 2.4, 0.35, curve=0.7))


@sfx
def sfx_boss_hit():
    return mix(sweep(1800, 260, 110, 'saw', 5.0, 0.55),
               noise(1400, 8.0, 0.4, 31, lp=0.5))


@sfx
def sfx_boss_die():
    layers = [noise(16000, 1.4, 0.35, 37, lp=0.12),
              sweep(16000, 420, 45, 'saw', 1.2, 0.45, curve=2.0)]
    for k in range(5):                              # a string of collapses
        pad = [0.0] * (k * 2600)
        layers.append(pad + sweep(2200, 500 - k * 60, 90, 'square', 6.0, 0.3))
    return mix(*layers)


@sfx
def sfx_menu():
    return sweep(500, 1050, 1050, 'pulse', 9.0, 0.35)


@sfx
def sfx_boss_tell():
    """
    The half second before a boss commits to something.

    Two rising thirds and a breath under them: enough warning to react to,
    short enough not to step on the music every time.
    """
    return mix(sweep(2600, 300, 620, 'square', 2.2, 0.30, curve=0.7),
               sweep(2600, 452, 934, 'square', 2.4, 0.16, curve=0.7),
               noise(2200, 3.0, 0.14, 23, lp=0.06))


@sfx
def sfx_warp():
    """Falling out of the world and into somewhere else."""
    return mix(sweep(6000, 900, 120, 'sine', 1.6, 0.42, curve=1.8),
               sweep(6000, 1350, 180, 'sine', 1.8, 0.20, curve=1.8),
               noise(5200, 2.2, 0.20, 29, lp=0.04))


@sfx
def sfx_level_clear():
    out = []
    for f in (523, 622, 784, 1047, 1245, 1568):
        out += sweep(1500, f, f, 'pulse', 3.6, 0.38)
    return out


def main():
    total = 0
    for name in sorted(SFX):
        samples = SFX[name]()
        short = name[4:] if name.startswith('sfx_') else name
        size = write_wav(short, samples)
        write_wav16('sfx_' + short, samples)
        total += size
        print('  %-14s %5.2fs  %5.1f KB' % (short, len(samples) / float(RATE),
                                            size / 1024.0))
    print('%d effects, %.1f KB of .wav in audio/' % (len(SFX), total / 1024.0))


if __name__ == '__main__':
    main()
