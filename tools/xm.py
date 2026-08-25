"""
A minimal Extended Module (.xm) writer, plus a matching software renderer.

Maxmod (devkitPro's mmutil) reads .xm directly, so composing straight into this
format means the music in the ROM is exactly the music we preview on the Mac -
the renderer below walks the same song structure the writer serialises.

Tuning convention: every instrument is synthesised at 8363 Hz with a cycle
length that divides evenly, so relative_note 0 / finetune 0 makes note C-4
(49) play back at the pitch it was drawn at.
"""

import math
import os
import struct

BASE_RATE = 8363          # XM's reference sample rate for C-4
C4 = 49                   # note number of C-4 (note 1 == C-0)
NOTE_OFF = 97


def note(octave, semitone):
    """Note number from octave/semitone, where C-4 is octave 4, semitone 0."""
    return 1 + octave * 12 + semitone


def note_hz(n):
    """Playback frequency of note `n` for a sample tuned at C-4."""
    return BASE_RATE * (2.0 ** ((n - C4) / 12.0))


class Instrument:
    def __init__(self, name, data, loop_start=0, loop_len=0, volume=48):
        self.name = name[:22]
        self.data = data                 # list of ints, -128..127
        self.loop_start = loop_start
        self.loop_len = loop_len
        self.volume = volume

    @property
    def looped(self):
        return self.loop_len > 0


class Pattern:
    """rows[row][channel] = (note, instrument, volume, effect, param)."""

    def __init__(self, rows, channels):
        self.row_count = rows
        self.channels = channels
        self.rows = [[(0, 0, 0, 0, 0) for _ in range(channels)] for _ in range(rows)]

    def put(self, row, ch, n=0, inst=0, vol=0, eff=0, par=0):
        if 0 <= row < self.row_count:
            self.rows[row][ch] = (n, inst, vol, eff, par)


class Song:
    def __init__(self, name, channels=8, bpm=128, speed=6):
        self.name = name[:20]
        self.channels = channels
        self.bpm = bpm
        self.speed = speed
        self.instruments = []
        self.patterns = []
        self.order = []

    def add_instrument(self, inst):
        self.instruments.append(inst)
        return len(self.instruments)          # XM instrument numbers are 1-based

    def new_pattern(self, rows=64):
        p = Pattern(rows, self.channels)
        self.patterns.append(p)
        return p


# ---------------------------------------------------------------------------
def _pack_pattern(pattern):
    out = bytearray()
    for row in pattern.rows:
        for (n, inst, vol, eff, par) in row:
            mask = 0
            if n:
                mask |= 0x01
            if inst:
                mask |= 0x02
            if vol:
                mask |= 0x04
            if eff:
                mask |= 0x08
            if par:
                mask |= 0x10
            out.append(0x80 | mask)
            if n:
                out.append(n)
            if inst:
                out.append(inst)
            if vol:
                out.append(vol)
            if eff:
                out.append(eff)
            if par:
                out.append(par)
    return bytes(out)


def _delta(data):
    out = bytearray()
    prev = 0
    for v in data:
        out.append((v - prev) & 0xFF)
        prev = v
    return bytes(out)


def write(song, path):
    o = bytearray()
    o += b'Extended Module: '
    o += song.name.encode('ascii', 'replace').ljust(20, b'\0')
    o += b'\x1a'
    o += b"Luv's Fright Night".ljust(20, b'\0')
    o += struct.pack('<H', 0x0104)

    header = bytearray()
    header += struct.pack('<H', len(song.order))
    header += struct.pack('<H', 0)                       # restart position
    header += struct.pack('<H', song.channels)
    header += struct.pack('<H', len(song.patterns))
    header += struct.pack('<H', len(song.instruments))
    header += struct.pack('<H', 1)                       # linear frequency table
    header += struct.pack('<H', song.speed)
    header += struct.pack('<H', song.bpm)
    order = bytearray(256)
    for i, p in enumerate(song.order):
        order[i] = p
    header += order
    o += struct.pack('<I', len(header) + 4)
    o += header

    for pattern in song.patterns:
        packed = _pack_pattern(pattern)
        o += struct.pack('<I', 9)
        o += bytes([0])
        o += struct.pack('<H', pattern.row_count)
        o += struct.pack('<H', len(packed))
        o += packed

    for inst in song.instruments:
        o += struct.pack('<I', 263)
        o += inst.name.encode('ascii', 'replace').ljust(22, b'\0')
        o += bytes([0])
        o += struct.pack('<H', 1)                        # one sample per instrument
        o += struct.pack('<I', 40)
        o += bytes(96)                                   # note -> sample map (all 0)
        o += bytes(48) + bytes(48)                       # volume/panning envelopes
        # 14 bytes: volume points, panning points, the six sustain/loop point
        # indices, volume type, panning type, then the four vibrato fields.
        # Getting this length wrong silently shifts every sample header that
        # follows, which Maxmod only discovers inside its mixer interrupt.
        o += bytes(14)
        o += struct.pack('<H', 0)                        # volume fadeout
        o += bytes(22)                                   # reserved

        length = len(inst.data)
        stype = 0x01 if inst.looped else 0x00            # forward loop
        o += struct.pack('<I', length)
        o += struct.pack('<I', inst.loop_start)
        o += struct.pack('<I', inst.loop_len)
        o += bytes([inst.volume & 0x3F])
        o += struct.pack('<b', 0)                        # finetune
        o += bytes([stype, 128])                         # type, panning
        o += struct.pack('<b', 0)                        # relative note
        o += bytes([0])
        o += inst.name.encode('ascii', 'replace').ljust(22, b'\0')
        o += _delta(inst.data)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(o)
    return len(o)


# ---------------------------------------------------------------------------
def render_wav(song, path, rate=32768, max_seconds=None, gain=0.9,
               normalize=None):
    """
    Render the song to a 16-bit stereo WAV so it can be auditioned before it
    goes anywhere near the ROM. Deliberately simple: linear-interpolated
    playback of each channel, no effects beyond the volume column.
    """
    rows_per_pattern = [p.row_count for p in song.patterns]
    frames_per_tick = rate * 2.5 / song.bpm
    frames_per_row = int(frames_per_tick * song.speed)
    total_rows = sum(rows_per_pattern[p] for p in song.order)
    total = total_rows * frames_per_row
    if max_seconds:
        total = min(total, int(rate * max_seconds))

    left = [0.0] * total
    right = [0.0] * total

    class Voice:
        __slots__ = ('inst', 'pos', 'step', 'vol', 'on')

        def __init__(self):
            self.inst = None
            self.pos = 0.0
            self.step = 0.0
            self.vol = 0.0
            self.on = False

    voices = [Voice() for _ in range(song.channels)]
    cursor = 0

    for pat_index in song.order:
        pattern = song.patterns[pat_index]
        for row in pattern.rows:
            if cursor >= total:
                break
            for ch, (n, inst_no, vol, eff, par) in enumerate(row):
                v = voices[ch]
                if n == NOTE_OFF:
                    v.on = False
                elif n:
                    if inst_no:
                        v.inst = song.instruments[inst_no - 1]
                    if v.inst is not None:
                        v.pos = 0.0
                        v.step = note_hz(n) / rate
                        v.vol = v.inst.volume / 64.0
                        v.on = True
                if vol and 0x10 <= vol <= 0x50:
                    v.vol = (vol - 0x10) / 64.0

            end = min(cursor + frames_per_row, total)
            for ch, v in enumerate(voices):
                if not v.on or v.inst is None:
                    continue
                data = v.inst.data
                n = len(data)
                ls, ll = v.inst.loop_start, v.inst.loop_len
                # a gentle stereo spread keeps eight channels from stacking up
                pan = 0.5 + 0.32 * math.sin(ch * 1.7)
                amp = v.vol * gain / 3.4
                pos, step = v.pos, v.step
                for i in range(cursor, end):
                    ip = int(pos)
                    if ip >= n:
                        if ll > 0:
                            pos = ls + ((pos - ls) % ll)
                            ip = int(pos)
                        else:
                            v.on = False
                            break
                    a = data[ip]
                    b = data[ip + 1] if ip + 1 < n else (data[ls] if ll else a)
                    frac = pos - ip
                    s = (a + (b - a) * frac) / 128.0 * amp
                    left[i] += s * (1.0 - pan)
                    right[i] += s * pan
                    pos += step
                v.pos = pos
            cursor = end
        if cursor >= total:
            break

    # The ROM plays this music at ambient level; the preview is normalised so it
    # is comfortable to audition on a laptop.
    if normalize:
        peak = max(max(abs(v) for v in left), max(abs(v) for v in right), 1e-6)
        scale = normalize / peak
        left = [v * scale for v in left]
        right = [v * scale for v in right]

    frames = bytearray()
    for i in range(total):
        for s in (left[i], right[i]):
            q = int(max(-1.0, min(1.0, s)) * 32767)
            frames += struct.pack('<h', q)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(b'RIFF' + struct.pack('<I', 36 + len(frames)) + b'WAVE')
        f.write(b'fmt ' + struct.pack('<IHHIIHH', 16, 1, 2, rate, rate * 4, 4, 16))
        f.write(b'data' + struct.pack('<I', len(frames)) + bytes(frames))
    return total / float(rate)
