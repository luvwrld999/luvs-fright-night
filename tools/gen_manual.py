#!/usr/bin/env python3
"""
Build the instruction booklet that ships beside the box art.

One self-contained HTML file: every sprite is cropped straight out of the
graphics the ROM is built from and embedded, so the manual cannot drift away
from the game it documents. If a sprite changes, so does this.

    python3 tools/gen_manual.py
"""

import base64
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image

import gen_music
import palette as pal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GFX = os.path.join(ROOT, 'graphics')
OUT = os.path.join(ROOT, 'scrape', 'manual.html')
SCALE = 4


def icon(name, frame=0, height=None, scale=SCALE):
    """
    One frame of a sheet, scaled up, as a transparent PNG data URI.

    Palette index 0 is the transparency key everywhere in this game, so it can
    be knocked out by index rather than by guessing at a colour.
    """
    sheet = Image.open(os.path.join(GFX, name + '.bmp'))
    width = sheet.width
    height = height or width
    tile = sheet.crop((0, frame * height, width, frame * height + height))

    if tile.mode == 'P':
        tile = tile.convert('RGBA')
        source = Image.open(os.path.join(GFX, name + '.bmp')).crop(
                    (0, frame * height, width, frame * height + height))
        pixels = list(source.getdata())
        out = list(tile.getdata())
        tile.putdata([(r, g, b, 0) if pixels[i] == 0 else (r, g, b, 255)
                      for i, (r, g, b, _a) in enumerate(out)])
    else:
        tile = tile.convert('RGBA')

    tile = tile.resize((tile.width * scale, tile.height * scale), Image.NEAREST)
    buf = io.BytesIO()
    tile.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def rgb(index):
    return '#%02x%02x%02x' % pal.RGB[index]


ENEMIES = [
    ('halo_imp', 16, 'Halo Imp',
     'Walks its patch and turns at the edge. Stamp on it.'),
    ('cherub_fiend', 16, 'Cherub Fiend',
     'Flies a slow wave. It will not come down to you; go up to it.'),
    ('gnasher', 16, 'Gnasher',
     'Charges once it sees you. Its rush is faster than your run.'),
    ('censer_wraith', 16, 'Censer Wraith',
     'Stands off and spits. Close the distance or burn it from range.'),
    ('bone_bat', 16, 'Bone Bat',
     'Hangs, drops, and climbs back up. Wait for the top of its rise.'),
]

POWERS = [
    ('pu_soul_flame', 'Soul Flame',
     'Tap B to throw a flame. Lost first when you are hit.'),
    ('pu_devil_dash', 'Devil Dash',
     'Hold B to run horns-first, fast enough to break blocks.'),
    ('pu_wisp_wings', 'Wisp Wings',
     'Triples the hover meter. Held until the run ends.'),
    ('pu_purple_soul', 'Purple Soul',
     'Turns Luv violet and takes one hit for him.'),
]

SINS = [
    ('boss_superbia', 'I', 'Superbia', 'Pride',
     'Holds station and rains from above, then runs at you.'),
    ('boss_avaritia', 'II', 'Avaritia', 'Greed',
     'Hops and lobs its hoard in two arcs at once.'),
    ('boss_luxuria', 'III', 'Luxuria', 'Lust',
     'Drifts, and charms whatever else is in the room.'),
    ('boss_invidia', 'IV', 'Invidia', 'Envy',
     'Charges wall to wall. It is dazed for a moment when it hits one.'),
    ('boss_gula', 'V', 'Gula', 'Gluttony',
     'Slow and enormous, and it fills the room with what it spits.'),
    ('boss_ira', 'VI', 'Ira', 'Wrath',
     'The fastest of them, and it slams the floor.'),
    ('boss_acedia', 'VII', 'Acedia', 'Sloth',
     'Never moves. The ceiling does the work.'),
    ('boss_hades', 'VIII', 'Hades', 'The end of it',
     'Three phases, and it gets quicker with every one you take.'),
]


def page(title, body, index=None):
    label = ('<div class="folio">%s</div>' % index) if index else ''
    return ('<section class="page">%s<h2>%s</h2>%s</section>'
            % (label, title, body))


def build():
    tracks = [t for t in gen_music.THEMES if t['key'].startswith('w')]

    enemies = ''.join(
        '<li><img src="%s" alt=""><div><h3>%s</h3><p>%s</p></div></li>'
        % (icon(name, 0, size), title, text)
        for name, size, title, text in ENEMIES)

    powers = ''.join(
        '<li><img src="%s" alt=""><div><h3>%s</h3><p>%s</p></div></li>'
        % (icon(name, 0, 16), title, text)
        for name, title, text in POWERS)

    sins = ''.join(
        '<li><img src="%s" alt=""><div><h3>%s &middot; %s</h3>'
        '<p class="sub">the sin of %s</p><p>%s</p></div></li>'
        % (icon(name, 0, 32, scale=3), numeral, title, plain, text)
        for name, numeral, title, plain, text in SINS)

    worlds = ''.join(
        '<tr><td>%s</td><td>%s</td><td>%s</td><td>%d BPM</td></tr>'
        % (['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'][i],
           t['name'], t['scale'].replace('_', ' '), t['bpm'])
        for i, t in enumerate(tracks))

    html = """<!doctype html>
<meta charset="utf-8">
<title>Luv's Fright Night &mdash; Instruction Booklet</title>
<style>
  :root {
    --ink: %(ink)s; --paper: #f4eee2; --gold: %(gold)s; --mag: %(mag)s;
    --cyan: %(cyan)s; --purple: %(purple)s;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--ink); color: #1a1220;
    font: 16px/1.55 "Iowan Old Style", "Palatino Linotype", Georgia, serif;
    padding: 32px 16px;
  }
  .book { max-width: 820px; margin: 0 auto; }
  .page {
    background: var(--paper); border-radius: 3px; padding: 40px 44px 48px;
    margin: 0 0 26px; position: relative;
    box-shadow: 0 1px 0 #fff inset, 0 18px 40px rgba(0,0,0,.45);
  }
  .folio {
    position: absolute; top: 18px; right: 22px; font-size: 12px;
    letter-spacing: .18em; color: #9a8ea6; text-transform: uppercase;
  }
  .cover { text-align: center; padding: 64px 44px 72px; }
  .cover h1 {
    font-size: 40px; line-height: 1.1; margin: 0 0 6px; letter-spacing: .02em;
  }
  .cover .tag { font-style: italic; color: #6c5f78; margin: 0 0 28px; }
  .cover img { image-rendering: pixelated; }
  .cover .plate { margin: 26px 0 10px; }
  .stamp {
    display: inline-block; margin-top: 30px; padding: 7px 16px;
    border: 2px solid var(--ink); border-radius: 2px; font-size: 12px;
    letter-spacing: .22em; text-transform: uppercase;
  }
  h2 {
    font-size: 13px; letter-spacing: .24em; text-transform: uppercase;
    color: #6c5f78; margin: 0 0 20px; padding-bottom: 9px;
    border-bottom: 1px solid #d8cebe;
  }
  h3 { font-size: 17px; margin: 0 0 3px; }
  p { margin: 0 0 12px; }
  p.sub { font-style: italic; color: #6c5f78; margin: 0 0 5px; }
  ul.cards { list-style: none; margin: 0; padding: 0; }
  ul.cards li {
    display: flex; gap: 20px; align-items: flex-start;
    padding: 15px 0; border-bottom: 1px solid #e6ddcf;
  }
  ul.cards li:last-child { border-bottom: 0; }
  ul.cards img { image-rendering: pixelated; flex: none; }
  table { border-collapse: collapse; width: 100%%; }
  th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid #e6ddcf; }
  th {
    font-size: 11px; letter-spacing: .16em; text-transform: uppercase;
    color: #6c5f78;
  }
  kbd {
    font: 600 13px/1 ui-monospace, "SF Mono", Menlo, monospace;
    background: #1a1220; color: var(--paper); border-radius: 3px;
    padding: 4px 8px; display: inline-block;
  }
  .note {
    background: #ece2d2; border-left: 3px solid var(--mag);
    padding: 12px 16px; margin: 20px 0 0; font-size: 15px;
  }
  .colophon { text-align: center; color: #6c5f78; font-size: 13px; }
  @media print {
    body { background: #fff; padding: 0; }
    .page { box-shadow: none; margin: 0; page-break-after: always; }
  }
</style>
<div class="book">

<section class="page cover">
  <h1>Luv's Fright Night</h1>
  <p class="tag">a ghost in bad company</p>
  <div class="plate"><img src="%(luv)s" alt="Luv"></div>
  <p>Instruction Booklet</p>
  <div class="stamp">Retro Rumble &middot; LuvWrld</div>
</section>

%(story)s
%(controls)s
%(enemies)s
%(powers)s
%(sins)s
%(reference)s

<section class="page colophon">
  <p>Every sprite, tile, note and sound effect in this game was generated by
     the scripts that build it. Nothing here was sampled or borrowed.</p>
  <p>Published by Retro Rumble &middot; Developed by LuvWrld &middot; 999</p>
</section>

</div>
""" % dict(
        ink=rgb(pal.INK), gold=rgb(pal.GOLD), mag=rgb(pal.MAG),
        cyan=rgb(pal.CYAN), purple=rgb(pal.PURPLE),
        luv=icon('luv', 0, 32, scale=6),
        story=page('The story', """
<p>Luv is a ghost, which is the least of it. He has devil horns he did not ask
   for, an angel halo that will not sit straight, and a tail with opinions of
   its own. None of the three agree about where he belongs.</p>
<p>Below him are eight worlds and everything that lives in them: demons wearing
   halos they stole, and at the bottom of each world one of the seven deadly
   sins, waiting. Past the seventh is Hades, and past Hades is the way out.</p>
<p>Nobody is coming to help. Go down.</p>""", 'One'),
        controls=page('Controls', """
<table>
  <tr><th>Button</th><th>Does</th></tr>
  <tr><td><kbd>&#9664; &#9654;</kbd></td><td>Run</td></tr>
  <tr><td><kbd>A</kbd></td><td>Jump. Hold it past the top and Luv hovers
      while the meter lasts.</td></tr>
  <tr><td><kbd>B</kbd></td><td>Tap to throw a soul flame. Hold to Devil Dash.
      One button covers both, the way it did on the Game Boy.</td></tr>
  <tr><td><kbd>START</kbd></td><td>Pause, or quit back to the menu.</td></tr>
</table>
<div class="note"><strong>Stomping always works.</strong> The flame and the dash
  both need their power-up; landing on something's head never does.</div>""",
                       'Two'),
        enemies=page('What lives down there',
                     '<ul class="cards">%s</ul>' % enemies, 'Three'),
        powers=page('What you can carry', """
<ul class="cards">%s</ul>
<div class="note">A hit takes the Purple Soul first, then the Soul Flame, and
  only then a life. The status bar shows what you are holding.</div>""" % powers,
                    'Four'),
        sins=page('The seven, and the eighth',
                  '<ul class="cards">%s</ul>' % sins, 'Five'),
        reference=page('Souls, codes and the rest', """
<p><strong>Souls.</strong> The small ones are worth one. The large gold ones
   are worth ten, and there are nine of those hidden in every stage.
   Ninety-nine souls is an extra life, and the counter starts again.</p>
<p><strong>Stage select.</strong> Every stage you reach is listed on the
   title screen by name, with your best time beside it. Pick one and play it
   again.</p>
<p><strong>Continues.</strong> Three a run, offered on a countdown when the
   lives are gone. Your score survives them.</p>
<p><strong>Two players.</strong> Two people, one pad, alternating on death.
   Each keeps their own lives, score and place in the game.</p>
<p><strong>Three files.</strong> The cartridge holds three separate games,
   plus the high score boards and the best times, which belong to everyone.</p>
<h3 style="margin-top:22px">The music</h3>
<table>
  <tr><th>World</th><th>Track</th><th>Mode</th><th>Tempo</th></tr>
  %s
</table>""" % worlds, 'Six'))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    with open(OUT, 'w') as f:
        f.write(html)

    print('%s  (%.1f KB)' % (OUT, os.path.getsize(OUT) / 1024.0))


if __name__ == '__main__':
    build()
