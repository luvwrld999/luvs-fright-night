"""HTML/CSS/JS for the asset-review page. Kept apart from the data builder."""

import json

import palette as pal

ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']

WORLD_TITLES = [
    ('pride', 'Superbia', 'Pride', 'Mirrored cathedral spires'),
    ('greed', 'Avaritia', 'Greed', 'Collapsing treasure vaults'),
    ('lust', 'Luxuria', 'Lust', 'A garden of thorns and heart-lanterns'),
    ('envy', 'Invidia', 'Envy', 'The green mire'),
    ('gluttony', 'Gula', 'Gluttony', 'A feast hall, still warm'),
    ('wrath', 'Ira', 'Wrath', 'The volcanic faultline'),
    ('sloth', 'Acedia', 'Sloth', 'A manor under heavy gravity'),
    ('hades', 'Hades', 'the end of it', 'The throne below everything'),
]

# rate is the duration of the full cycle in ms, not of a single frame.
LUV_SKINS = [
    ('luv.idle', 'Ghost', 'the default'),
    ('luv_soul.idle', 'Purple Soul', 'carrying an extra hit'),
]

LUV_STATES = [
    ('idle', 'Idle', '2 frames, breathing', 700),
    ('run', 'Run', '4 frames', 420),
    ('jump', 'Jump', 'rising', 0),
    ('fall', 'Fall', 'descending', 0),
    ('hover', 'Hover', 'hold A; the meter drains', 320),
    ('dash', 'Devil Dash', 'horns first', 200),
    ('hurt', 'Hurt', 'one hit taken', 0),
]

DEMON_NOTES = [
    ('halo_imp', 'Halo Imp', 'Walks, turns at ledges. The first thing you stomp.'),
    ('cherub_fiend', 'Cherub Fiend', 'Flies a sine wave across the stage.'),
    ('gnasher', 'Gnasher', 'Winds up, then charges. Cannot stop.'),
    ('censer_wraith', 'Censer Wraith', 'Hovers and spits embers on an arc.'),
    ('bone_bat', 'Bone Bat', 'Hovers, telegraphs, then drops on you.'),
    ('spike_flame', 'Hellfire Jet', 'Static hazard. Breathes in and out.'),
]

ITEM_NOTES = [
    ('pu_soul_flame', 'Soul Flame', 'Halo ignites; throws bouncing flames.'),
    ('pu_purple_soul', 'Purple Soul', 'Turns Luv violet and absorbs one hit.'),
    ('pu_devil_dash', 'Devil Dash', 'Horns-first charge; breaks blocks.'),
    ('pu_wisp_wings', 'Wisp Wings', 'Triples the hover meter.'),
    ('one_up', '1-Up', 'A spare life.'),
    ('checkpoint', 'Checkpoint', 'Lights when Luv passes.'),
    ('soul_orb', 'Soul', 'The level currency.'),
    ('soul_flame', 'Flame shot', "Luv's projectile."),
    ('gate', 'Stage gate', 'The way out.'),
    ('hud_halo', 'Life icon', 'HUD.'),
    ('hud_meter', 'Hover meter', 'HUD, empty and full.'),
]

TRACK_ORDER = [
    ('title', 'Fright Night', 'Title'),
    ('w1_pride', 'Hall of Mirrors', 'World I'),
    ('w2_greed', 'The Counting Vault', 'World II'),
    ('w3_lust', 'Thornlight', 'World III'),
    ('w4_envy', 'The Green Mire', 'World IV'),
    ('w5_gluttony', 'Long Table', 'World V'),
    ('w6_wrath', 'Faultline', 'World VI'),
    ('w7_sloth', 'Nothing Stirs', 'World VII'),
    ('w8_hades', 'Below Everything', 'World VIII'),
    ('boss', 'Seven Ways Down', 'Boss'),
    ('victory', 'One Sin Down', 'Stage clear'),
    ('game_over', 'Claimed', 'Game over'),
]

SFX_ORDER = ['jump', 'hover', 'land', 'stomp', 'shot', 'flame_hit', 'dash',
             'hurt', 'death', 'pickup', 'power_up', 'one_up', 'checkpoint',
             'boss_hit', 'boss_die', 'menu', 'level_clear']


def _palette_strip():
    out = []
    for i, name in enumerate(pal.NAMES):
        r, g, b = pal.RGB[i]
        style = 'background:rgb(%d,%d,%d)' % (r, g, b)
        if i == 0:
            style += ';background-image:repeating-conic-gradient(#2a1d3a 0 25%,#1b1226 0 50%);background-size:8px 8px'
        out.append('<div class="sw"><i style="%s"></i><b>%s</b></div>' % (style, name.lower()))
    return ''.join(out)


def render(payload, themes):
    world_tabs = ''.join(
        '<button class="tab%s" data-world="%s">%s</button>'
        % (' on' if i == 0 else '', key, ROMAN[i])
        for i, (key, latin, sin, place) in enumerate(WORLD_TITLES))

    boss_cards = ''
    for i, (key, latin, sin, place) in enumerate(WORLD_TITLES):
        from gen_preview_page import BOSS_NOTES
        name, sin_en, arena, note = BOSS_NOTES[i]
        scale = 2 if _boss_size(i) > 32 else 3
        boss_cards += '''
        <article class="boss">
          <div class="boss-art"><div class="anim" data-set="bosses.%s" data-rate="2600" data-scale="%d" role="img" aria-label="%s"></div></div>
          <div class="boss-body">
            <div class="eyebrow"><span class="num">%s</span> %s</div>
            <h3>%s</h3>
            <p class="arena">%s</p>
            <p>%s</p>
          </div>
        </article>''' % (_boss_key(i), scale, name, ROMAN[i], sin_en.upper(),
                         name, arena, note)

    luv_cards = ''.join(
        '''<figure class="cell">
             <div class="stage tall"><div class="anim" data-set="luv.%s" data-rate="%d" data-scale="3" role="img" aria-label="%s"></div></div>
             <figcaption><b>%s</b><span>%s</span></figcaption>
           </figure>''' % (k, rate or 0, label, label, sub)
        for k, label, sub, rate in LUV_STATES)

    demon_cards = ''.join(
        '''<figure class="cell">
             <div class="stage"><div class="anim" data-set="demons.%s" data-rate="680" data-scale="3" role="img" aria-label="%s"></div></div>
             <figcaption><b>%s</b><span>%s</span></figcaption>
           </figure>''' % (k, label, label, note)
        for k, label, note in DEMON_NOTES)

    item_cards = ''.join(
        '''<figure class="cell">
             <div class="stage"><div class="anim" data-set="items.%s" data-rate="600" data-scale="3" role="img" aria-label="%s"></div></div>
             <figcaption><b>%s</b><span>%s</span></figcaption>
           </figure>''' % (k, label, label, note)
        for k, label, note in ITEM_NOTES)

    tile_rows = ''
    for i, (key, latin, sin, place) in enumerate(WORLD_TITLES):
        cells = ''.join('<div class="tile" data-set="tiles.%s" data-index="%d"></div>'
                        % (key, n) for n in range(16))
        tile_rows += '''
        <div class="tilerow">
          <div class="tilelabel"><span class="num">%s</span><b>%s</b><span>%s</span></div>
          <div class="tiles">%s</div>
        </div>''' % (ROMAN[i], latin, place, cells)

    track_rows = ''
    for key, name, role in TRACK_ORDER:
        t = themes.get(key, {})
        from gen_preview_page import TRACK_NOTES
        track_rows += '''
        <div class="track">
          <div class="t-role">%s</div>
          <div class="t-name">%s<span>%s</span></div>
          <div class="t-spec">%d BPM · %s</div>
          <audio controls preload="none" data-audio="music.%s"></audio>
        </div>''' % (role, name, TRACK_NOTES.get(key, ''), t.get('bpm', 0),
                     t.get('scale', '').replace('_', ' '), key)

    sfx_chips = ''.join('<button class="chip" data-sfx="%s">%s</button>'
                        % (k, k.replace('_', ' ')) for k in SFX_ORDER)

    return TEMPLATE.replace('__PAYLOAD__', payload) \
                   .replace('__PALETTE__', _palette_strip()) \
                   .replace('__WORLD_TABS__', world_tabs) \
                   .replace('__BOSS_CARDS__', boss_cards) \
                   .replace('__LUV__', luv_cards) \
                   .replace('__DEMONS__', demon_cards) \
                   .replace('__ITEMS__', item_cards) \
                   .replace('__TILES__', tile_rows) \
                   .replace('__TRACKS__', track_rows) \
                   .replace('__SFX__', sfx_chips) \
                   .replace('__WORLDS__', json.dumps(worlds_json()))


def worlds_json():
    return [{"key": k, "latin": l, "sin": s, "place": p}
            for k, l, s, p in WORLD_TITLES]


def _boss_key(i):
    import art_bosses
    return art_bosses.BOSSES[i][0]


def _boss_size(i):
    import art_bosses
    return art_bosses.BOSSES[i][2]


TEMPLATE = r"""<title>Luv's Fright Night</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Spectral:ital,wght@0,300;0,400;0,600;1,300&family=JetBrains+Mono:wght@400;600&display=swap">

<style>
/* A deliberately single-world page: this is a night game, and its own 16-colour
   cartridge palette is the design system. Every colour is painted explicitly so
   the page holds on any host background. */
:root{
  --ground:#0a0610; --panel:#150e1e; --panel-2:#1e142a; --line:#33234a;
  --ink:#ece2f6; --body:#c6b6d8; --muted:#8d7ba6;
  --mag:#ff30b0; --gold:#ffd838; --cyan:#68f0ff; --red:#ff3828; --green:#7cff38;
  --display:"Cinzel",Georgia,serif;
  --text:"Spectral",Georgia,serif;
  --mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  --grid:repeating-conic-gradient(#241834 0 25%,#1b1226 0 50%) 0 0/16px 16px;
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--ground); color:var(--body);
  font-family:var(--text); font-weight:300; font-size:17px; line-height:1.65;
  -webkit-font-smoothing:antialiased;
}
img{max-width:100%}
.wrap{max-width:1120px;margin:0 auto;padding:0 28px}
.prose{max-width:64ch}

/* ---- masthead ---- */
.mast{
  border-bottom:1px solid var(--line);
  background:
    radial-gradient(120% 90% at 50% -30%, rgba(255,48,176,.18), transparent 62%),
    linear-gradient(#120b1c,#0a0610);
  padding:64px 0 34px;
}
.eyebrow{
  font-family:var(--mono); font-size:11px; letter-spacing:.24em;
  text-transform:uppercase; color:var(--muted);
}
.eyebrow .num{color:var(--gold);font-weight:600}
h1{
  font-family:var(--display); font-weight:700; color:var(--ink);
  font-size:clamp(38px,7vw,74px); line-height:1.02; margin:14px 0 6px;
  letter-spacing:.01em; text-wrap:balance;
}
h1 em{font-style:normal;color:var(--mag)}
.dek{font-size:19px;color:var(--body);max-width:62ch;margin:0 0 26px}
.specs{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:28px}
.specs span{
  font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--body);border:1px solid var(--line);border-radius:2px;padding:5px 9px;
  background:var(--panel);
}
.palette{display:flex;flex-wrap:wrap;gap:2px}
.sw{width:62px}
.sw i{display:block;height:24px;border:1px solid rgba(0,0,0,.5)}
.sw b{
  display:block;font-family:var(--mono);font-weight:400;font-size:9px;
  letter-spacing:.06em;color:var(--muted);padding-top:4px;
}

/* ---- sections ---- */
section{padding:62px 0;border-bottom:1px solid var(--line)}
h2{
  font-family:var(--display);font-weight:700;color:var(--ink);
  font-size:clamp(25px,3.4vw,36px);margin:8px 0 10px;letter-spacing:.01em;
}
h3{font-family:var(--display);font-weight:700;color:var(--ink);font-size:22px;margin:2px 0 6px}
.lede{color:var(--muted);margin:0 0 30px;max-width:62ch;font-size:16px}
.num{
  font-family:var(--mono);font-weight:600;color:var(--gold);
  letter-spacing:.1em;margin-right:8px;
}

/* ---- pixel presentation ---- */
.anim,.tile,.shot{
  image-rendering:pixelated; image-rendering:crisp-edges;
  background-repeat:no-repeat; background-position:0 0;
}
@keyframes play{ to{ background-position-x: var(--sweep); } }
.stage{
  background:var(--grid);border:1px solid var(--line);
  display:flex;align-items:flex-end;justify-content:center;
  height:96px;padding:8px;
}
.stage.tall{height:132px}
.stage .anim{flex:0 0 auto}

.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}
.cell{margin:0}
figcaption{padding-top:9px}
figcaption b{
  display:block;font-family:var(--mono);font-size:12px;font-weight:600;
  letter-spacing:.08em;text-transform:uppercase;color:var(--ink);
}
figcaption span{display:block;font-size:14px;color:var(--muted);line-height:1.45}

/* ---- the screen viewer ---- */
.viewer{display:grid;gap:22px;grid-template-columns:minmax(0,1fr) 260px;align-items:start}
@media(max-width:820px){.viewer{grid-template-columns:1fr}}
.screen-frame{
  border:1px solid var(--line);background:#000;padding:10px;
  box-shadow:0 0 0 1px rgba(255,48,176,.12), 0 22px 60px rgba(0,0,0,.6);
}
.screen-frame .shot{display:block;width:100%;aspect-ratio:3/2;position:relative;overflow:hidden}
/* The strip is n screens wide and slides by whole screens, so the sweep is
   expressed in the strip's own width and stays correct at any page size. */
.screen-frame .strip{
  position:absolute;top:0;left:0;height:100%;
  background-repeat:no-repeat;background-size:100% 100%;
  image-rendering:pixelated;
}
@keyframes sweep{ to{ transform:translateX(-100%); } }
.tabs{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:14px}
.tab{
  font-family:var(--mono);font-size:12px;font-weight:600;letter-spacing:.12em;
  color:var(--muted);background:var(--panel);border:1px solid var(--line);
  padding:7px 12px;cursor:pointer;border-radius:0;
}
.tab:hover{color:var(--ink);border-color:var(--mag)}
.tab.on{color:var(--ground);background:var(--gold);border-color:var(--gold)}
.tab:focus-visible,.chip:focus-visible,.toggle:focus-visible{outline:2px solid var(--cyan);outline-offset:2px}
.side h3{margin-top:0}
.side .latin{font-family:var(--display);color:var(--mag);font-size:15px;letter-spacing:.08em;text-transform:uppercase}
.side p{font-size:15px;color:var(--body)}
.toggle{
  font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  background:transparent;color:var(--cyan);border:1px solid var(--line);
  padding:7px 12px;cursor:pointer;margin-top:6px;
}
.toggle:hover{border-color:var(--cyan)}
.caption{font-family:var(--mono);font-size:11px;color:var(--muted);letter-spacing:.1em;
  text-transform:uppercase;padding-top:10px}

/* ---- bosses ---- */
.bosses{display:grid;gap:2px}
.boss{
  display:grid;grid-template-columns:150px minmax(0,1fr);gap:22px;
  background:var(--panel);border:1px solid var(--line);padding:20px;align-items:start;
}
@media(max-width:680px){.boss{grid-template-columns:1fr}}
.boss-art{background:var(--grid);border:1px solid var(--line);height:150px;
  display:flex;align-items:center;justify-content:center}
.boss-art .anim{flex:0 0 auto}
.boss-body p{margin:0 0 10px;font-size:16px}
.arena{font-family:var(--mono);font-size:12px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--cyan)}

/* ---- tilesets ---- */
.tilerow{display:grid;grid-template-columns:180px minmax(0,1fr);gap:18px;
  padding:14px 0;border-top:1px solid var(--line);align-items:center}
@media(max-width:680px){.tilerow{grid-template-columns:1fr;gap:8px}}
.tilelabel b{display:block;font-family:var(--display);color:var(--ink);font-size:17px}
.tilelabel span{font-size:13px;color:var(--muted)}
.tiles{display:flex;flex-wrap:wrap;gap:3px}
.tiles .tile{width:34px;height:34px;border:1px solid var(--line);
  background-color:#1b1226;background-size:544px 32px}

/* ---- soundtrack, laid out like a tracker ---- */
.tracks{border-top:1px solid var(--line)}
.track{
  display:grid;grid-template-columns:92px minmax(0,1fr) 190px 260px;
  gap:18px;align-items:center;padding:12px 0;border-bottom:1px solid var(--line);
}
@media(max-width:900px){.track{grid-template-columns:1fr;gap:6px}}
.t-role{font-family:var(--mono);font-size:11px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--gold)}
.t-name{font-family:var(--display);color:var(--ink);font-size:19px}
.t-name span{display:block;font-family:var(--text);font-size:14px;color:var(--muted);
  letter-spacing:0;line-height:1.4}
.t-spec{font-family:var(--mono);font-size:12px;color:var(--cyan);
  font-variant-numeric:tabular-nums;letter-spacing:.04em}
.track audio{width:100%;height:34px}

/* ---- sfx ---- */
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{
  font-family:var(--mono);font-size:12px;letter-spacing:.06em;
  background:var(--panel);color:var(--body);border:1px solid var(--line);
  padding:9px 13px;cursor:pointer;
}
.chip:hover{color:var(--ground);background:var(--cyan);border-color:var(--cyan)}
.chip.hit{background:var(--mag);border-color:var(--mag);color:#fff}

/* ---- status ---- */
.status{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
.stat{border:1px solid var(--line);background:var(--panel);padding:18px}
.stat b{display:block;font-family:var(--mono);font-size:11px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--gold);margin-bottom:6px}
.stat p{margin:0;font-size:15px}
.done{color:var(--green)}
.next{color:var(--cyan)}
footer{padding:40px 0 70px;color:var(--muted);font-size:14px}
@media (prefers-reduced-motion:reduce){.anim{animation:none!important}}
</style>

<div class="mast">
  <div class="wrap">
    <div class="eyebrow"><span class="num">Build 001</span> Asset review — art and audio, before a line of gameplay code</div>
    <h1>Luv's <em>Fright Night</em></h1>
    <p class="dek">A Game Boy Advance platformer. Luv is a ghost with devil horns, an
      angel halo and a devil tail; the demons all wear halos they stole; the seven
      deadly sins are waiting, and Hades is behind them.</p>
    <div class="specs">
      <span>Game Boy Advance</span><span>240 × 160</span><span>4bpp · 16 colours</span>
      <span>Butano / devkitARM</span><span>264 sprite frames</span>
      <span>12 tracker modules</span><span>17 effects</span>
    </div>
    <div class="palette">__PALETTE__</div>
  </div>
</div>

<section>
  <div class="wrap">
    <div class="eyebrow">The game, running</div>
    <h2>Eight worlds, off the cartridge</h2>
    <p class="lede">Real frames, captured by driving the ROM headlessly under mGBA -
      not mock-ups. The status bar is live: lives, souls, the world you are in, the
      clock, and the score. The boss view is still a mock-up; the fights are
      designed but not yet built.</p>
    <div class="tabs">__WORLD_TABS__</div>
    <div class="viewer">
      <div>
        <div class="screen-frame"><div class="shot" role="img" aria-label="Mock stage"><div id="screen" class="strip"></div></div></div>
        <div class="caption" id="screen-caption"></div>
      </div>
      <div class="side">
        <div class="latin" id="side-latin"></div>
        <h3 id="side-sin"></h3>
        <p id="side-place"></p>
        <button class="toggle" id="boss-toggle">Show the boss</button>
      </div>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="eyebrow">Before and after</div>
    <h2>The card, and the way out</h2>
    <p class="lede">Every stage opens on a card in its own world's masonry - which
      world, which sin, and how many lives you are carrying in. START pauses at any
      point and stops the clock with it. Put Hades down and Luv goes up, through a
      column of souls going the same way, with the run totalled against your best.</p>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))">
      <figure class="cell">
        <div class="screen-frame"><div class="shot" id="card-shot" role="img" aria-label="World card"></div></div>
        <figcaption><b>World card</b><span>Shown before every stage.</span></figcaption>
      </figure>
      <figure class="cell">
        <div class="screen-frame"><div class="shot" id="ending-shot" role="img" aria-label="Ending"></div></div>
        <figcaption><b>Ending</b><span>After the last fight.</span></figcaption>
      </figure>
      <figure class="cell">
        <div class="screen-frame"><div class="shot" id="pause-shot" role="img" aria-label="Pause"></div></div>
        <figcaption><b>Pause</b><span>START, any time. The clock stops with it.</span></figcaption>
      </figure>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="eyebrow">The player character</div>
    <h2>Luv</h2>
    <p class="lede">One 16 &times; 32 sheet drives every state, so he costs a single
      sprite shape in VRAM. The four power-ups are palette swaps plus the two overlays
      at the end of the row - no second character sheet. He jumps four and a half
      metatiles, and holding A past the apex lets him hover on a meter that refills
      when he lands.</p>
    <div class="grid">
      <figure class="cell">
        <div class="stage tall"><div class="anim" data-set="luv_soul.run" data-rate="420" data-scale="3" role="img" aria-label="Purple Soul"></div></div>
        <figcaption><b>Purple Soul</b><span>Carrying an extra hit, and you can see it.</span></figcaption>
      </figure>__LUV__
      <figure class="cell">
        <div class="stage tall"><div class="anim" data-set="luv_extra.aura" data-rate="600" data-scale="3" role="img" aria-label="Blessed Halo aura"></div></div>
        <figcaption><b>Blessed Halo</b><span>Aura drawn behind Luv.</span></figcaption>
      </figure>
      <figure class="cell">
        <div class="stage tall"><div class="anim" data-set="luv_extra.wings" data-rate="480" data-scale="3" role="img" aria-label="Wisp Wings"></div></div>
        <figcaption><b>Wisp Wings</b><span>Overlay, mirrored for the other side.</span></figcaption>
      </figure>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="eyebrow">The opposition</div>
    <h2>Demons, in halos they did not earn</h2>
    <p class="lede">All 16 × 16 and built on one shared anatomy — halo, horns, sunken
      sockets — so they read as one species however they behave.</p>
    <div class="grid">__DEMONS__</div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="eyebrow">Bosses</div>
    <h2>The seven sins, and Hades</h2>
    <p class="lede">Seven 32 &times; 32 sins and a 64 &times; 64 king, and all eight
      fights are playable. Each has its own way of moving and its own attack; every one
      of them commits to a run at you around its attack, which is the opening you answer.
      Use the toggle in the viewer above to watch any of them in their arena.</p>
    <div class="bosses">__BOSS_CARDS__</div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="eyebrow">Power-ups and pickups</div>
    <h2>What Luv can pick up</h2>
    <p class="lede">Break a block open and what was sealed inside drops to the floor
      where you can walk into it. Losing a hit costs the Purple Soul first, then the
      Soul Flame, then a life.</p>
    <div class="grid">__ITEMS__</div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="eyebrow">Level building blocks</div>
    <h2>Sixteen metatiles, eight ways</h2>
    <p class="lede">Every world uses the same sixteen slots in the same order, so one
      level file can be re-skinned into any world. Left to right: empty, ground top,
      ground fill, block, breakable, platform, spikes, two ledges, pillar, lamp, two
      backdrops, door, chain, lava.</p>
    __TILES__
  </div>
</section>

<section>
  <div class="wrap">
    <div class="eyebrow">Soundtrack</div>
    <h2>Twelve modules, all in dark modes</h2>
    <p class="lede">Synthesised from scratch and written straight to Maxmod tracker
      modules — nothing sampled. Eight channels: sub, heartbeat, two pads, a
      sixteenth-note arpeggio, a glass-bell motif, room tone and offbeat ash. These
      previews are normalised for headphones; in the game the music is capped at about
      a third of full so it stays under the action.</p>
    <div class="tracks">__TRACKS__</div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="eyebrow">Effects</div>
    <h2>Seventeen sounds</h2>
    <p class="lede">Click to hear one.</p>
    <div class="chips">__SFX__</div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="eyebrow">Where the build stands</div>
    <h2>Done, and next</h2>
    <div class="status">
      <div class="stat"><b class="done">Toolchain</b><p>devkitARM in Docker, Butano
        pinned, one-command build. A ROM with these assets compiles and boots headlessly.</p></div>
      <div class="stat"><b class="done">Art</b><p>264 frames: Luv, six demons, eight
        bosses, pickups, HUD and eight tilesets — all generated from code, so any of it
        can be re-rolled by changing a number.</p></div>
      <div class="stat"><b class="done">Audio</b><p>12 modules and 17 effects. Every
        module passes mmutil, the real GBA converter.</p></div>
      <div class="stat"><b class="done">Engine</b><p>Physics, hover, metatile collision,
        scrolling camera, pooled enemies, power-ups, checkpoints, lives and a battery
        save. Break a block open and whatever was sealed inside drops out.</p></div>
      <div class="stat"><b class="done">Front end</b><p>Continue, new game, stage select
        and a controls screen, with the high score kept on the cartridge.</p></div>
      <div class="stat"><b class="done">Scoring</b><p>Souls, blocks, power-ups and
        chained stomps that double in value, a stage clock, and whatever is left on it
        paid out as a bonus at the exit.</p></div>
      <div class="stat"><b class="done">Stage shapes</b><p>Six of them - open ground,
        ledges, pillared halls, crossings, low cellars and climbs - dealt out so the
        two halves of a world never play the same way.</p></div>
      <div class="stat"><b class="done">Controls</b><p>D-pad runs. A jumps, and holding
        it past the apex hovers. B throws a soul flame; holding B is the Devil Dash -
        one button, the way Mario Land does it.</p></div>
      <div class="stat"><b class="done">Bosses</b><p>All eight arenas and fights are in:
        five ways of moving, five attacks, a health bar, and a run at you around every
        attack. Every one has been beaten under an automated test.</p></div>
      <div class="stat"><b class="done">Front matter</b><p>A world card before every
        stage, and an ending after the last fight that totals your run against the
        high score on the cartridge.</p></div>
      <div class="stat"><b class="done">Difficulty curve</b><p>Measured rather than
        guessed: enemies, holes and hazards per screen, world by world. It now climbs
        from 0.80 to 2.09 with no world easier than the one before it.</p></div>
      <div class="stat"><b class="next">Next</b><p>Whatever you find wrong with it
        now that it plays start to finish.</p></div>
    </div>
  </div>
</section>

<footer><div class="wrap prose">Every sprite, tile, note and sound on this page was
  generated by the project's own tools in <code>tools/</code>. Nothing here is sampled
  or borrowed.</div></footer>

<script id="assets" type="application/json">__PAYLOAD__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('assets').textContent);
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function pick(path){
    return path.split('.').reduce(function(o,k){ return o && o[k]; }, D);
  }

  // Each sprite is one strip painted as a background and swept with a CSS
  // steps() animation - the browser decodes the image once and the rest is
  // compositor work.
  function paintStrip(el, set, scale, durationMs){
    if(!set){ return; }
    var w = set.w * scale, h = set.h * scale;
    el.style.width = w + 'px';
    el.style.height = h + 'px';
    el.style.backgroundImage = 'url("' + set.uri + '")';
    el.style.backgroundSize = (set.w * set.n * scale) + 'px ' + h + 'px';
    el.style.backgroundPositionX = '0px';
    if(set.n > 1 && durationMs && !reduce){
      el.style.setProperty('--sweep', '-' + (set.w * set.n * scale) + 'px');
      el.style.animation = 'play ' + (durationMs / 1000) + 's steps(' + set.n + ') infinite';
    }
  }

  document.querySelectorAll('.anim').forEach(function(el){
    paintStrip(el, pick(el.dataset.set), parseInt(el.dataset.scale, 10) || 3,
               parseInt(el.dataset.rate, 10) || 0);
  });

  document.querySelectorAll('.tile').forEach(function(el){
    var set = pick(el.dataset.set);
    if(!set){ return; }
    var idx = parseInt(el.dataset.index, 10);
    el.style.backgroundImage = 'url("' + set.uri + '")';
    el.style.backgroundSize = (set.w * set.n * 2) + 'px ' + (set.h * 2) + 'px';
    el.style.backgroundPosition = (-idx * set.w * 2) + 'px 0';
  });

  // ---- world viewer
  var WORLDS = __WORLDS__;
  var screen = document.getElementById('screen');
  var cap = document.getElementById('screen-caption');
  var latin = document.getElementById('side-latin');
  var sinEl = document.getElementById('side-sin');
  var placeEl = document.getElementById('side-place');
  var toggle = document.getElementById('boss-toggle');
  var current = 0, showBoss = false;

  function paintScreen(set){
    if(!set){ return; }
    screen.style.width = (set.n * 100) + '%';
    screen.style.backgroundImage = 'url("' + set.uri + '")';
    screen.style.transform = 'translateX(0)';
    if(set.n > 1 && !reduce){
      screen.style.animation = 'sweep ' + (set.n * 0.19) + 's steps(' + set.n + ') infinite';
    }
  }

  function refresh(){
    var w = WORLDS[current];
    screen.style.animation = 'none';
    void screen.offsetWidth;                       // restart the sweep cleanly
    paintScreen(showBoss ? (FIGHTS[w.key] || D.boss_screens[w.key])
                         : (CAPS[w.key] || D.screens[w.key]));
    latin.textContent = w.latin;
    sinEl.textContent = w.sin;
    placeEl.textContent = w.place;
    cap.textContent = 'Captured from the ROM \u2014 ' +
                      (showBoss ? w.latin + ', the fight' : w.latin) +
                      ' \u00b7 240 \u00d7 160';
    toggle.textContent = showBoss ? 'Show the stage' : 'Show the boss';
  }
  document.querySelectorAll('.tab').forEach(function(btn, idx){
    btn.addEventListener('click', function(){
      document.querySelectorAll('.tab').forEach(function(b){ b.classList.remove('on'); });
      btn.classList.add('on');
      current = idx; refresh();
    });
  });
  toggle.addEventListener('click', function(){ showBoss = !showBoss; refresh(); });
  refresh();

  // ---- the two still captures
  [['card-shot', 'card'], ['ending-shot', 'ending'],
   ['pause-shot', 'pause']].forEach(function(pair){
    var el = document.getElementById(pair[0]);
    var set = D[pair[1]];

    if(el && set){
      el.style.backgroundImage = 'url("' + set.uri + '")';
      el.style.backgroundSize = '100% 100%';
      el.style.width = '100%';
    }
  });

  // ---- effects
  document.querySelectorAll('.chip').forEach(function(btn){
    btn.addEventListener('click', function(){
      var uri = D.sfx[btn.dataset.sfx];
      if(!uri){ return; }
      var a = new Audio(uri); a.volume = 0.85; a.play();
      btn.classList.add('hit');
      setTimeout(function(){ btn.classList.remove('hit'); }, 220);
    });
  });

  // ---- music: one track at a time
  var players = [];
  document.querySelectorAll('audio[data-audio]').forEach(function(el){
    el.src = pick(el.dataset.audio) || '';
    el.loop = true;
    players.push(el);
    el.addEventListener('play', function(){
      players.forEach(function(o){ if(o !== el){ o.pause(); } });
    });
  });
})();
</script>
"""
