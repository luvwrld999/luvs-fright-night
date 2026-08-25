#!/usr/bin/env python3
"""
Build the asset-review page: every sprite animated at its real size, eight mock
240x160 screens, and the whole soundtrack playable, in one self-contained HTML
file that can be published as an Artifact.
"""

import base64
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image

import art_bosses
import art_enemies
import art_items
import art_luv
import art_tiles
import mockup
import palette as pal
import preview

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'preview', 'assets.html')
M4A = os.path.join(ROOT, 'preview', 'audio', 'm4a')
WAV = os.path.join(ROOT, 'preview', 'audio')


def _to_image(canvas, target=None, ox=0):
    img = target or Image.new('RGBA', (canvas.w, canvas.h), (0, 0, 0, 0))
    px = img.load()
    for y in range(canvas.h):
        for x in range(canvas.w):
            c = canvas.px[y][x]
            if c != pal.KEY:
                px[x + ox, y] = pal.RGB[c] + (255,)
    return img


def strip(canvases):
    """
    Frames laid side by side as one PNG data URI.

    The page animates these with a CSS steps() background-position sweep rather
    than swapping img.src every frame: one decode per entity instead of one per
    displayed frame, which is the difference between a smooth page and a stalled
    renderer once a hundred sprites are moving at once.
    """
    w, h = canvases[0].w, canvases[0].h
    sheet = Image.new('RGBA', (w * len(canvases), h), (0, 0, 0, 0))
    for i, c in enumerate(canvases):
        _to_image(c, sheet, i * w)
    buf = io.BytesIO()
    sheet.save(buf, 'PNG', optimize=True)
    return {'uri': 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(),
            'w': w, 'h': h, 'n': len(canvases)}


def png_uri(canvas):
    return strip([canvas])


def photo(path):
    """A real screenshot straight off the emulator, as a one-frame strip."""
    img = Image.open(path).convert('RGB')
    buf = io.BytesIO()
    img.save(buf, 'PNG', optimize=True)
    return {'uri': 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(),
            'w': img.width, 'h': img.height, 'n': 1}


def file_uri(path, mime):
    with open(path, 'rb') as f:
        return 'data:%s;base64,%s' % (mime, base64.b64encode(f.read()).decode())


BOSS_NOTES = [
    ("Superbia", "Pride", "Hall of Mirrors",
     "Hides behind a fan of mirror shards and fights you with a recording of "
     "your own last few seconds. Break the shards with shots that bounce off "
     "them - it only takes damage from a move it just watched you make."),
    ("Avaritia", "Greed", "The Counting Vault",
     "Has swallowed the arena's platforms as coins. It hurls the hoard at you, "
     "and every coin in flight is a platform you can stand on - until it "
     "decides to reel that one back in."),
    ("Luxuria", "Lust", "Thornlight",
     "Its lantern-heart charms every demon on screen into fighting for it. Put "
     "the lantern out with a soul flame and the charmed demons turn on it "
     "instead; relight and they turn back."),
    ("Invidia", "Envy", "The Green Mire",
     "Steals whichever power-up you walked in with and uses it against you. "
     "Take a hit on purpose to make the theft worthless, or dash through it to "
     "take the power-up back."),
    ("Gula", "Gluttony", "Long Table",
     "Eats the floor a tile at a time and grows with every mouthful. The fight "
     "is a shrinking island; feed it a soul flame instead of a tile and it "
     "chokes."),
    ("Ira", "Wrath", "Faultline",
     "Every hit you land makes it faster and less accurate. By the last phase "
     "it is barely aiming at all - the fight becomes about surviving its own "
     "momentum long enough to land one more."),
    ("Acedia", "Sloth", "Nothing Stirs",
     "Never moves. The room does the fighting: gravity doubles, the ceiling "
     "descends, chains swing across the floor. You have to wake it up before "
     "you can hurt it, and waking it is the dangerous part."),
    ("Hades", "the end of it", "Below Everything",
     "Three phases. Skeletal hands sweep the floor, then the crown of black "
     "flame rains down, and finally the soul he is holding becomes the only "
     "safe platform in the room."),
]

TRACK_NOTES = {
    'title': 'Title screen. Sparse - motif only, no pulse.',
    'w1_pride': 'World I. Harmonic minor, wide and ceremonial.',
    'w2_greed': 'World II. Phrygian dominant; the bII keeps promising and not paying.',
    'w3_lust': 'World III. Hungarian minor - the augmented second is the thorn.',
    'w4_envy': 'World IV. Locrian, so the tonic chord never resolves.',
    'w5_gluttony': 'World V. Phrygian, faster, the arpeggio never stops eating.',
    'w6_wrath': 'World VI. Octatonic, the fastest loop in the game.',
    'w7_sloth': 'World VII. Slowest tempo; the heartbeat is doing all the work.',
    'w8_hades': 'World VIII. Hungarian minor an octave down.',
    'boss': 'Boss theme. Sixteenth-note arpeggio, no room to breathe.',
    'victory': 'Sin cleared.',
    'game_over': 'Claimed.',
}


def main():
    data = {}

    # -- animated sprite sets ---------------------------------------------
    luv_frames = art_luv.sheet_frames()
    data['luv'] = {
        'idle': strip([luv_frames[i] for i in (0, 1)]),
        'run': strip([luv_frames[i] for i in (2, 3, 4, 5)]),
        'jump': strip([luv_frames[6]]),
        'fall': strip([luv_frames[7]]),
        'hover': strip([luv_frames[i] for i in (8, 9)]),
        'dash': strip([luv_frames[i] for i in (10, 11)]),
        'hurt': strip([luv_frames[12]]),
    }
    soul = art_luv.sheet_frames(art_luv.SKIN_SOUL)
    data['luv_soul'] = {
        'idle': strip([soul[i] for i in (0, 1)]),
        'run': strip([soul[i] for i in (2, 3, 4, 5)]),
    }
    data['luv_extra'] = {
        'aura': strip(art_luv.aura_frames()),
        'wings': strip(art_luv.wing_frames()),
    }
    data['demons'] = {name: strip([fn(i) for i in range(n)])
                      for name, fn, n in art_enemies.ENEMIES}
    data['bosses'] = {name: strip([fn(i) for i in range(8)])
                      for name, fn, size, title in art_bosses.BOSSES}
    data['items'] = {name: strip([fn(i) for i in range(n)])
                     for group in (art_items.ITEMS_8, art_items.ITEMS_16,
                                   art_items.ITEMS_16x32)
                     for name, fn, n in group}
    data['tiles'] = {w['key']: strip(art_tiles.world_tiles(i))
                     for i, w in enumerate(art_tiles.WORLDS)}
    data['screens'] = {w['key']: strip([mockup.screen(i, f) for f in range(4)])
                       for i, w in enumerate(art_tiles.WORLDS)}
    data['boss_screens'] = {w['key']: strip([mockup.screen(i, f, True)
                                             for f in range(2)])
                            for i, w in enumerate(art_tiles.WORLDS)}

    # Real frames, captured by driving the ROM headlessly under mGBA.
    caps = os.path.join(ROOT, 'preview', 'captures')
    data['captures'] = {}

    data['boss_captures'] = {}

    for shot in ('card', 'ending', 'pause'):
        path = os.path.join(caps, shot + '.png')

        if os.path.exists(path):
            data[shot] = photo(path)

    for i, w in enumerate(art_tiles.WORLDS):
        shot = os.path.join(caps, 'world_%d.png' % (i + 1))

        if os.path.exists(shot):
            data['captures'][w['key']] = photo(shot)

        fight = os.path.join(caps, 'boss_%d.png' % (i + 1))

        if os.path.exists(fight):
            data['boss_captures'][w['key']] = photo(fight)

    # -- audio -------------------------------------------------------------
    data['music'] = {}
    for key in ['title', 'w1_pride', 'w2_greed', 'w3_lust', 'w4_envy',
                'w5_gluttony', 'w6_wrath', 'w7_sloth', 'w8_hades', 'boss',
                'victory', 'game_over']:
        p = os.path.join(M4A, key + '.m4a')
        if os.path.exists(p):
            data['music'][key] = file_uri(p, 'audio/mp4')

    data['sfx'] = {}
    for f in sorted(os.listdir(WAV)):
        if f.startswith('sfx_') and f.endswith('.wav'):
            data['sfx'][f[4:-4]] = file_uri(os.path.join(WAV, f), 'audio/wav')

    payload = json.dumps(data)

    import gen_music
    themes = {t['key']: t for t in gen_music.THEMES}

    html = build_html(payload, themes)
    # The artifact host supplies the <head>, so there is nowhere to declare a
    # charset - emit pure ASCII with numeric entities and the page is safe
    # whatever encoding the server guesses.
    html = html.encode('ascii', 'xmlcharrefreplace').decode('ascii')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        f.write(html)
    print('wrote %s  (%.1f MB)' % (OUT, os.path.getsize(OUT) / 1048576.0))


def build_html(payload, themes):
    from page_template import render
    return render(payload, themes)


if __name__ == '__main__':
    main()
