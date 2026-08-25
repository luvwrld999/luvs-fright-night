# Luv's Fright Night — scrape package

Everything a front end needs to show the game: the ROM, the metadata, and the
media. Nothing here is fetched from a scraper service — the screenshots are
frames captured out of the emulator running this exact build, and the box art
is composed from the game's own sprite sheets, so the art cannot drift away
from what the ROM actually looks like.

```
scrape/
├── LuvsFrightNight.gba      the ROM the metadata points at
├── gamelist.xml             EmulationStation / Batocera / RetroBat metadata
└── media/
    ├── box/box-front.png            900x1200  cover art
    ├── marquee/logo.png            1200x380   wordmark, transparent
    ├── fanart/fanart.png           1920x1080  wallpaper
    ├── titlescreen/title.png        240x160   the front end, native res
    └── screenshot/*.png             240x160   gameplay, native res
```

## Installing it

Copy the ROM and `gamelist.xml` into your GBA roms folder, and `media/` next to
them:

```
roms/gba/LuvsFrightNight.gba
roms/gba/gamelist.xml
roms/gba/media/...
```

The paths inside `gamelist.xml` are relative (`./media/...`), so the folder can
live anywhere as long as the pieces stay together. If your front end keeps
media in a shared `downloaded_media/` tree instead, point it at these files or
copy them into the matching subfolders — the filenames already follow the usual
`box`, `marquee`, `screenshot`, `titlescreen`, `fanart` convention.

## Screenshots

| File | What it shows |
|---|---|
| `titlescreen/title.png` | Front end: continue, new game, stage select, scores, credits |
| `screenshot/world-card.png` | World intro card — the sin, the stage name, lives |
| `screenshot/gameplay-world-1.png` | World I, Chapel of the Mirror |
| `screenshot/gameplay-world-1b.png` | World I, further in |
| `screenshot/gameplay-world-5.png` | World V, the rotting feast hall |
| `screenshot/gameplay-world-7.png` | World VII, the decaying manor |
| `screenshot/boss-*.png` | Three of the eight boss arenas |

Screenshots are stored at the GBA's native 240x160 so front ends can scale them
with whatever filtering they prefer. Do not pre-scale them with a smooth
filter — nearest-neighbour only, or the pixel art turns to mush.

## Regenerating

```bash
python3 tools/gen_scrape.py
```

That rebuilds every file in `media/` and rewrites `gamelist.xml` from the
frames sitting in `tools/emu/shots` and `tools/emu/shots2`. To recapture those
frames first:

```bash
./build.sh clean && ./build.sh "USERFLAGS=-DLFN_TEST_INVULNERABLE=1"
```

then run `tools/emu/scrape.txt` and `tools/emu/bossshots.txt` through the
headless runner (see `test.sh` for the docker invocation).

## Credits

Published by **Retro Rumble**. Developed by **LuvWrld**.
