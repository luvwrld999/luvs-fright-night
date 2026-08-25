#!/usr/bin/env python3
"""
Measure every piece of audio in the game.

Nobody working on this can hear it, so the things a pair of ears would catch
instantly - one track mixed twice as loud as its neighbours, an effect clipping
into distortion, a sample sitting off-centre so it thumps when it starts - have
to be caught by measurement instead.

Reports peak, RMS, DC offset, clipped-sample count and, for the music, how far
each track sits from the median of the set. Music is re-rendered here without
normalisation - the previews on disk are normalised for auditioning, which
would make every track measure the same. Exits non-zero if anything trips a
threshold, so it can gate a build.

    python3 tools/check_audio.py
"""

import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EFFECTS = os.path.join(ROOT, 'audio')
SCRATCH = os.path.join(ROOT, 'preview', 'audio', 'level')

# Long enough to cover every pattern of the longest track at its slowest.
SAMPLE_SECONDS = 40

# What counts as wrong.
CLIP_LIMIT = 0.002      # fraction of samples allowed to sit at full scale
DC_LIMIT = 0.02         # offset from centre, as a fraction of full scale
QUIET_RMS = 0.008       # below this a sample is effectively inaudible
SPREAD = 2.5            # a track this many times the median RMS is out of line


def read_wav(path):
    """Return samples in -1..1, whatever bit depth the file uses."""
    with open(path, 'rb') as f:
        blob = f.read()

    if blob[:4] != b'RIFF' or blob[8:12] != b'WAVE':
        raise ValueError('%s: not a RIFF/WAVE file' % path)

    pos = 12
    bits = channels = 0
    data = b''

    while pos + 8 <= len(blob):
        name = blob[pos:pos + 4]
        size = struct.unpack('<I', blob[pos + 4:pos + 8])[0]
        body = blob[pos + 8:pos + 8 + size]

        if name == b'fmt ':
            channels = struct.unpack('<H', body[2:4])[0]
            bits = struct.unpack('<H', body[14:16])[0]
        elif name == b'data':
            data = body

        pos += 8 + size + (size & 1)

    if bits == 8:
        # Unsigned, centred on 128 - the GBA's native format.
        out = [(b - 128) / 127.0 for b in data]
    elif bits == 16:
        count = len(data) // 2
        out = [v / 32768.0
               for v in struct.unpack('<%dh' % count, data[:count * 2])]
    else:
        raise ValueError('%s: unsupported bit depth %d' % (path, bits))

    if channels > 1:
        out = out[::channels]

    return out


def measure(path, rate=8363):
    s = read_wav(path)

    if not s:
        return None

    peak = max(abs(v) for v in s)
    rms = math.sqrt(sum(v * v for v in s) / len(s))
    dc = sum(s) / len(s)
    clipped = sum(1 for v in s if abs(v) >= 0.999)

    return {
        'name': os.path.basename(path)[:-4],
        'seconds': len(s) / float(rate),
        'peak': peak,
        'rms': rms,
        'dc': dc,
        'clip': clipped / float(len(s)),
        # An exponential tail that never reaches zero clicks when it stops.
        'tail': abs(s[-1]),
    }


def median(values):
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2.0


def report(title, rows, compare):
    print('\n%s' % title)
    print('  %-16s %6s %6s %6s %7s %6s %6s  %s'
          % ('name', 'secs', 'peak', 'rms', 'dc', 'clip%', 'tail', 'notes'))

    faults = 0
    mid = median([r['rms'] for r in rows]) if compare and rows else 0.0

    for r in rows:
        notes = []

        if r['clip'] > CLIP_LIMIT:
            notes.append('CLIPPING')

        if abs(r['dc']) > DC_LIMIT:
            notes.append('DC OFFSET')

        if r['rms'] < QUIET_RMS:
            notes.append('INAUDIBLE')

        # Only one-shot effects have to land on silence. A module loops, so
        # wherever the render stopped is the middle of the music, not its end.
        if not compare and r['tail'] > 0.05:
            notes.append('ENDS ABRUPTLY')

        if compare and mid > 0:
            if r['rms'] > mid * SPREAD:
                notes.append('LOUD vs SET')
            elif r['rms'] * SPREAD < mid:
                notes.append('QUIET vs SET')

        faults += len(notes)
        print('  %-16s %6.2f %6.3f %6.3f %7.3f %6.2f %6.3f  %s'
              % (r['name'], r['seconds'], r['peak'], r['rms'], r['dc'],
                 r['clip'] * 100, r['tail'], ', '.join(notes)))

    return faults


def render_flat(theme, path):
    """
    Render one track with no normalisation.

    The previews in preview/audio are peak normalised so they are comfortable
    to audition, which makes their levels useless for comparing one track
    against another: normalising to a fixed peak turns a difference in mix into
    a difference in crest factor and hides the thing being looked for.
    """
    import gen_music
    import xm

    xm.render_wav(gen_music.compose(theme), path, rate=16000,
                  max_seconds=SAMPLE_SECONDS, normalize=None)


def main():
    import gen_music

    music, effects = [], []
    os.makedirs(SCRATCH, exist_ok=True)

    for theme in gen_music.THEMES:
        path = os.path.join(SCRATCH, theme['key'] + '.wav')

        if not os.path.exists(path):
            render_flat(theme, path)

        m = measure(path, rate=16000)

        if m:
            music.append(m)

    for path in sorted(os.listdir(EFFECTS)):
        if path.endswith('.wav'):
            m = measure(os.path.join(EFFECTS, path))

            if m:
                effects.append(m)

    faults = report('music (rendered previews)', music, compare=True)
    faults += report('effects (as they ship)', effects, compare=False)

    print('\n%d thing(s) to look at across %d files'
          % (faults, len(music) + len(effects)))
    return 1 if faults else 0


if __name__ == '__main__':
    sys.exit(main())
