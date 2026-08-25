"""
Synthesised instruments for the soundtrack.

Every pitched instrument is drawn at 32 samples per cycle so that, at XM's
8363 Hz reference rate, one cycle is exactly C-4 - loops are click-free and the
whole orchestra is in tune with itself by construction.
"""

import math

CYCLE = 32


def _clip(v):
    return max(-128, min(127, int(round(v))))


def _centre(data):
    """
    Shift a looping waveform so its average is zero.

    A narrow pulse spends most of its cycle at one level, so its mean sits well
    away from centre. Eight of those looping under a mix pull the whole output
    off-centre: headroom goes to a constant the speaker cannot reproduce, and
    every note starts and ends with a step.
    """
    if not data:
        return data

    mean = sum(data) / float(len(data))
    return [_clip(v - mean) for v in data]


class _Rng:
    """Deterministic noise source, so a rebuild produces identical audio."""

    def __init__(self, seed=1):
        self.s = seed & 0x7FFFFFFF or 1

    def next(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s

    def uniform(self):
        return self.next() / 0x7FFFFFFF * 2.0 - 1.0


def sub_bass():
    """Round sine sub - the floor the whole track sits on."""
    data = [_clip(120 * math.sin(2 * math.pi * i / CYCLE)) for i in range(CYCLE)]
    return data, 0, CYCLE


def saw_pad(detune=0.006, cycles=8):
    """Two saws pulling against each other; the beating is the whole point."""
    n = CYCLE * cycles
    data = []
    for i in range(n):
        a = ((i / CYCLE) % 1.0) * 2 - 1
        b = ((i * (1 + detune) / CYCLE) % 1.0) * 2 - 1
        data.append(_clip(52 * (a + b)))
    return data, 0, n


def choir(cycles=4):
    """Breathy vowel tone - sounds like something in the room with you."""
    n = CYCLE * cycles
    partials = [(1, 1.0), (2, 0.42), (3, 0.30), (4, 0.16), (5, 0.22), (7, 0.10)]
    data = []
    for i in range(n):
        t = i / CYCLE
        v = 0.0
        for h, amp in partials:
            v += amp * math.sin(2 * math.pi * h * t + h * 0.7)
        data.append(_clip(46 * v / 1.6))
    return data, 0, n


def glass_bell(length=1600):
    """Inharmonic struck bell, one shot - the eerie top end."""
    data = []
    partials = [(1.0, 1.0, 2.6), (2.76, 0.55, 1.7), (5.40, 0.32, 1.1),
                (8.93, 0.18, 0.8), (13.3, 0.10, 0.6)]
    for i in range(length):
        t = i / float(CYCLE)
        env_t = i / float(length)
        v = 0.0
        for ratio, amp, decay in partials:
            v += amp * math.sin(2 * math.pi * ratio * t) * math.exp(-decay * env_t * 6)
        data.append(_clip(58 * v / 2.0))
    return data, 0, 0


def hollow_pulse(duty=0.22, cycles=2):
    """Narrow pulse for the arpeggio - cuts through without being loud."""
    n = CYCLE * cycles
    data = []
    for i in range(n):
        phase = (i / CYCLE) % 1.0
        data.append(_clip(70 if phase < duty else -70))
    return _centre(data), 0, n


def whisper(length=2048, seed=7):
    """Filtered noise bed. Barely there, but the room feels wrong without it."""
    r = _Rng(seed)
    raw = [r.uniform() for _ in range(length)]
    data = []
    lp = 0.0
    for i in range(length):
        lp += (raw[i] - lp) * 0.06                       # one-pole low pass
        # crossfade the tail into the head so the loop point is inaudible
        fade = min(1.0, (length - i) / 256.0)
        head = raw[length - i - 1] if i < 256 else 0.0
        data.append(_clip(70 * (lp * fade + head * (1 - fade) * 0.06)))
    return data, 0, length


def heart_kick(length=900):
    """Soft pitch-dropping thud. A heartbeat, not a dance kick."""
    data = []
    phase = 0.0
    for i in range(length):
        t = i / float(length)
        freq = 3.2 * math.exp(-5.5 * t) + 0.28           # cycles per CYCLE samples
        phase += freq / CYCLE
        env = math.exp(-4.0 * t)
        data.append(_clip(118 * math.sin(2 * math.pi * phase) * env))
    return data, 0, 0


def ash_hat(length=200, seed=11):
    """Dry noise tick for the offbeat."""
    r = _Rng(seed)
    data = []
    for i in range(length):
        env = math.exp(-9.0 * i / length)
        data.append(_clip(75 * r.uniform() * env))
    return data, 0, 0


def riser(length=6000, seed=13):
    """Reverse-swell noise used to walk into a new section."""
    r = _Rng(seed)
    data = []
    lp = 0.0
    for i in range(length):
        t = i / float(length)
        lp += (r.uniform() - lp) * (0.02 + 0.25 * t)
        data.append(_clip(90 * lp * (t ** 2)))
    return data, 0, 0
