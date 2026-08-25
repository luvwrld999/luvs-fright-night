#!/usr/bin/env python3
"""
The soundtrack: eight world loops, a boss theme, title, victory and game over.

Written to audio/*.xm for Maxmod, and rendered to preview/audio/*.wav so the
music can be judged before it is inside a ROM.

House style: dark modes only, a slow chord drift under a 16th-note arpeggio, a
heartbeat instead of a dance kick, and every instrument authored quiet - the
music is meant to sit under the game as ambience, not to be performed at you.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import instruments as ins
import xm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(ROOT, 'audio')
PREVIEW = os.path.join(ROOT, 'preview', 'audio')

# Dark modes. Nothing here contains a plain major third in the tonic chord.
SCALES = {
    'harmonic_minor':   [0, 2, 3, 5, 7, 8, 11],
    'phrygian_dominant': [0, 1, 4, 5, 7, 8, 10],
    'hungarian_minor':  [0, 2, 3, 6, 7, 8, 11],
    'locrian':          [0, 1, 3, 5, 6, 8, 10],
    'phrygian':         [0, 1, 3, 5, 7, 8, 10],
    'octatonic':        [0, 1, 3, 4, 6, 7, 9, 10],
}

# channel map
SUB, KICK, PAD_A, PAD_B, ARP, LEAD, AIR, HAT = range(8)

# Authored quiet on purpose; the engine also caps music at 0.35. The pads sit
# further back than they used to and the bell comes forward: at this volume the
# tune was the first thing the pads buried, and a loop you cannot hear the
# melody of is just texture.
VOL = {SUB: 30, KICK: 26, PAD_A: 15, PAD_B: 12, ARP: 16, LEAD: 24, AIR: 8, HAT: 10}

# Where the eight notes of a motif fall inside a bar, in half-rows. Rhythm
# identifies a tune faster than pitch does, so each world gets its own rather
# than every track sharing one and differing only in which notes land on it.
RHYTHMS = [
    [0, 3, 6, 10, 16, 22, 26, 31],   # even, walking
    [0, 2, 7, 9, 14, 18, 24, 30],    # front-loaded, then hanging back
    [0, 5, 8, 11, 16, 19, 27, 30],   # syncopated middle
    [0, 4, 6, 12, 15, 20, 25, 29],   # limping
    [0, 6, 9, 12, 18, 21, 24, 28],   # triplet-feeling
    [0, 1, 6, 8, 13, 17, 23, 31],    # jittery
    [0, 4, 8, 12, 17, 21, 25, 29],   # square, marching
    [0, 3, 5, 11, 14, 16, 22, 29],   # lopsided, leaning early
]


class Rng:
    def __init__(self, seed):
        self.s = (seed * 2654435761) & 0x7FFFFFFF or 1

    def next(self, n):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s % n


THEMES = [
    dict(key='w1_pride',    name='Hall of Mirrors',   scale='harmonic_minor',
         root=9,  bpm=126, prog=[0, 5, 3, 4], octave=3, seed=11, air=True),
    dict(key='w2_greed',    name='The Counting Vault', scale='phrygian_dominant',
         root=4,  bpm=130, prog=[0, 1, 0, 4], octave=3, seed=22, air=True),
    dict(key='w3_lust',     name='Thornlight',        scale='hungarian_minor',
         root=2,  bpm=122, prog=[0, 3, 5, 1], octave=3, seed=33, air=True),
    dict(key='w4_envy',     name='The Green Mire',    scale='locrian',
         root=7,  bpm=128, prog=[0, 4, 2, 5], octave=2, seed=44, air=True),
    dict(key='w5_gluttony', name='Long Table',        scale='phrygian',
         root=0,  bpm=134, prog=[0, 1, 3, 1], octave=3, seed=55, air=True),
    dict(key='w6_wrath',    name='Faultline',         scale='octatonic',
         root=6,  bpm=140, prog=[0, 3, 6, 4], octave=3, seed=66, air=False),
    dict(key='w7_sloth',    name='Nothing Stirs',     scale='harmonic_minor',
         root=11, bpm=108, prog=[0, 5, 0, 3], octave=2, seed=77, air=True),
    dict(key='w8_hades',    name='Below Everything',  scale='hungarian_minor',
         root=9,  bpm=132, prog=[0, 6, 3, 1], octave=2, seed=88, air=True),
    dict(key='boss',        name='Seven Ways Down',   scale='phrygian_dominant',
         root=2,  bpm=148, prog=[0, 1, 0, 6], octave=3, seed=99, air=False,
         boss=True),
    dict(key='title',       name="Fright Night",      scale='harmonic_minor',
         root=9,  bpm=100, prog=[0, 5, 3, 4], octave=3, seed=5, air=True,
         sparse=True),
    dict(key='victory',     name='One Sin Down',      scale='harmonic_minor',
         root=9,  bpm=124, prog=[0, 4], octave=4, seed=7, air=False,
         short=True),
    dict(key='game_over',   name='Claimed',           scale='locrian',
         root=9,  bpm=84,  prog=[0, 1], octave=2, seed=9, air=True,
         short=True, sparse=True),
]


def build_instruments(song):
    """Returns 1-based XM instrument numbers keyed by role."""
    def add(name, spec, volume):
        data, ls, ll = spec
        return song.add_instrument(xm.Instrument(name, data, ls, ll, volume))

    return {
        'sub':   add('sub',     ins.sub_bass(),      52),
        'pad':   add('pad',     ins.saw_pad(),       40),
        'choir': add('choir',   ins.choir(),         38),
        'bell':  add('bell',    ins.glass_bell(),    46),
        'pulse': add('pulse',   ins.hollow_pulse(),  36),
        'air':   add('air',     ins.whisper(),       30),
        'kick':  add('kick',    ins.heart_kick(),    50),
        'hat':   add('hat',     ins.ash_hat(),       30),
        'riser': add('riser',   ins.riser(),         34),
    }


def chord_tones(scale, degree):
    """Triad built on a scale degree, as semitone offsets from the root."""
    n = len(scale)
    return [scale[degree % n] + 12 * (degree // n),
            scale[(degree + 2) % n] + 12 * ((degree + 2) // n),
            scale[(degree + 4) % n] + 12 * ((degree + 4) // n)]


def compose(theme):
    """
    Build one track.

    The four patterns are not four copies of the same bar: pattern 0 states the
    theme sparsely, 1 brings in the pulse, 2 answers the motif and adds a
    counter-line, and 3 is the turnaround that walks back to the top. That
    shape is what stops a thirty-second loop sounding like eight seconds played
    four times.
    """
    scale = SCALES[theme['scale']]
    root = theme['root']
    octv = theme['octave']
    prog = theme['prog']
    rng = Rng(theme['seed'])
    sparse = theme.get('sparse', False)
    boss = theme.get('boss', False)
    short = theme.get('short', False)

    song = xm.Song(theme['name'], channels=8, bpm=theme['bpm'], speed=6)
    inst = build_instruments(song)

    pattern_count = 2 if short else 4
    rows = 64

    motif = [rng.next(len(scale)) for _ in range(8)]
    motif_rhythm = RHYTHMS[theme['rhythm'] % len(RHYTHMS)]
    # The answer walks the motif backwards and a third higher - recognisably
    # the same idea, coming back the other way.
    answer = [(d + 2) % len(scale) for d in reversed(motif)]

    def pitch(degree, octave_shift=0):
        n = len(scale)
        return xm.note(octv + octave_shift + degree // n, 0) + root + scale[degree % n]

    for pat_index in range(pattern_count):
        intro = pat_index == 0 and not short
        answering = pat_index >= 2
        turnaround = pat_index == pattern_count - 1 and not short

        p = song.new_pattern(rows)

        for bar in range(rows // 16):
            degree = prog[(pat_index * (rows // 16) + bar) % len(prog)]
            tones = chord_tones(scale, degree)
            base = bar * 16
            bass_note = xm.note(octv - 1, 0) + root + tones[0]

            # --- sub: a walking figure rather than a held root
            p.put(base, SUB, bass_note, inst['sub'], 0x10 + VOL[SUB])

            if not sparse:
                walk = [(6, tones[0]), (10, tones[2]), (13, tones[1])]

                if turnaround:
                    walk.append((15, tones[2] + 12))

                for row, tone in walk:
                    p.put(base + row, SUB, xm.note(octv - 1, 0) + root + tone,
                          inst['sub'], 0x10 + VOL[SUB] - 7)

            # --- heartbeat, absent from the sparse intro
            if not sparse and not intro:
                for r in (0, 6, 8, 14):
                    v = VOL[KICK] if r in (0, 8) else VOL[KICK] - 9
                    p.put(base + r, KICK, xm.note(4, 0), inst['kick'], 0x10 + v)

            # --- pads, swelling across the bar
            p.put(base, PAD_A, xm.note(octv, 0) + root + tones[1],
                  inst['pad'], 0x10 + VOL[PAD_A] - (5 if intro else 0))
            p.put(base + 8, PAD_A, xm.note(octv, 0) + root + tones[1],
                  inst['pad'], 0x10 + VOL[PAD_A] + 3)
            p.put(base, PAD_B, xm.note(octv, 0) + root + tones[2],
                  inst['choir'], 0x10 + VOL[PAD_B])

            # --- the arpeggio: the engine of the thing
            if not sparse and not intro:
                step = 1 if boss else 2
                for r in range(0, 16, step):
                    tone = tones[(r // step) % 3]
                    lift = 12 if ((r // step) % 6) >= 3 else 0
                    p.put(base + r, ARP,
                          xm.note(octv + 1, 0) + root + tone + lift, inst['pulse'],
                          0x10 + VOL[ARP] - (4 if r % 4 else 0))

            # --- counter-line, once the track has something to answer
            if answering and not sparse:
                p.put(base + 4, AIR, xm.note(octv, 0) + root + tones[2] + 12,
                      inst['choir'], 0x10 + VOL[AIR] + 6)

            if not sparse and not intro:
                for r in range(2, 16, 4):
                    p.put(base + r, HAT, xm.note(4, 0), inst['hat'],
                          0x10 + VOL[HAT] - (r % 8 and 3))

        # --- the tune itself: stated, then answered
        line = answer if answering else motif
        for i, r in enumerate(motif_rhythm):
            if sparse and i % 2:
                continue

            deg = line[i] + (2 if pat_index % 2 else 0)
            p.put(r * 2, LEAD, pitch(deg, 1), inst['bell'],
                  0x10 + VOL[LEAD] - (5 if i % 3 else 0))

        if theme.get('air') and not answering:
            p.put(0, AIR, xm.note(octv, 0) + root, inst['air'], 0x10 + VOL[AIR])
            p.put(32, AIR, xm.note(octv, 0) + root + scale[1], inst['air'],
                  0x10 + VOL[AIR])

        if turnaround:
            p.put(48, AIR, xm.note(octv + 1, 0) + root, inst['riser'],
                  0x10 + VOL[AIR] + 6)

            # A fill across the last bar, so the loop point arrives instead of
            # simply happening. Sixteenths on the hat tightening into the top,
            # and a kick pickup on the last two rows.
            if not sparse:
                for r in range(56, 64):
                    p.put(r, HAT, xm.note(4, 0), inst['hat'],
                          0x10 + VOL[HAT] - 4 + ((r - 56) // 2))

                for r in (61, 63):
                    p.put(r, KICK, xm.note(4, 0), inst['kick'], 0x10 + VOL[KICK] - 4)

                # And the sub climbs back to the root it started on.
                p.put(62, SUB, xm.note(octv - 1, 0) + root + scale[4], inst['sub'],
                      0x10 + VOL[SUB] - 5)

    song.order = list(range(pattern_count))
    return song


for _slot, _theme in enumerate(THEMES):
    _theme.setdefault('rhythm', _slot)


def main(render_previews=True):
    os.makedirs(AUDIO, exist_ok=True)
    os.makedirs(PREVIEW, exist_ok=True)
    total = 0
    for theme in THEMES:
        song = compose(theme)
        path = os.path.join(AUDIO, theme['key'] + '.xm')
        size = xm.write(song, path)
        secs = 0.0

        if render_previews:
            secs = xm.render_wav(song, os.path.join(PREVIEW, theme['key'] + '.wav'),
                                 rate=22050, max_seconds=34, normalize=0.72)
        total += size
        print('  %-12s %-20s %3d BPM  %-18s %5.1fs  %6.1f KB'
              % (theme['key'], song.name, theme['bpm'], theme['scale'], secs,
                 size / 1024.0))
    print('%d modules, %.1f KB of .xm in audio/' % (len(THEMES), total / 1024.0))


if __name__ == '__main__':
    # `--modules-only` skips the slow software render when only the ROM needs
    # rebuilding.
    main(render_previews='--modules-only' not in sys.argv)
