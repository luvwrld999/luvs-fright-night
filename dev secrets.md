# Dev Secrets

Everything hidden in Luv's Fright Night, and exactly how to reach it.

Not for the box. This is the file you keep.

---

## How a secret works

A secret is three pieces of data, all of them in the level format:

| Piece | Where it lives | What it does |
|---|---|---|
| A **warp door** | a `O` in the stage's ASCII map | Touch it and the stage ends through the door instead of the gate |
| The stage's **`! warp:`** | the level's metadata | Which room that door opens onto |
| The room's **`! exit_to:`** | the room's metadata | Where the game continues when you leave the room |

Hidden rooms carry `! hidden: 1`. They sit after the 24 story stages in the
compiled list, so they are never reached by ordinary progression and never
appear in Stage Select. `story_count` (24) is what the game counts to; the
ending fires when the index passes it, not `level_count` (27).

Writing on a wall is a `S` marker plus the room's `! secret:` line. The engine
draws that text at the marker, pinned to the world rather than the screen, so
it scrolls with the room like part of the masonry.

---

## The three rooms

### 1. Nine Nine Nine — the tribute

| | |
|---|---|
| **Stage index** | 24 |
| **Reached from** | World I-2, *The Long Gallery* (stage 1) |
| **Lets you out at** | Stage 2, the Superbia arena - you rejoin the story where you left it |
| **On the wall** | `999  RIP JUICE WRLD` |
| **Also inside** | A 1-Up and four souls |

**How to find it.** Near the end of I-2, past the last of the gallery, the
ground runs on a little longer than it needs to. There is a platform four
tiles up with a soul on it, and above that a second platform eight tiles up
with another soul. The door is on the top one.

You cannot reach it with a jump. You have to jump and then *hover* - hold A
past the apex - which is why the room is behind World I's second stage and not
its first. By then the game has taught you the only mechanic that opens it.

The room lets you out into the boss arena, so taking it costs you nothing.

### 2. The Long Way Round — the date

| | |
|---|---|
| **Stage index** | 25 |
| **Reached from** | World III-2, *The Lantern Beds* (stage 7) |
| **Lets you out at** | Stage 15, World VI-1 - **skips worlds IV and V entirely** |
| **On the wall** | `06/15` |

**How to find it.** Same shape as the first: a soul on a high platform late in
the stage, and the door above it.

This is the game's real warp. Taking it jumps you from the end of World III to
the start of World VI, past four stages and two bosses. Your score comes with
you; the stages you skipped are simply never played, so the run is faster and
worth less.

`06/15` is on the back wall of the room, above the block course. It is not
explained anywhere in the game and nothing acknowledges it.

### 3. Straight Down — the deep warp

| | |
|---|---|
| **Stage index** | 26 |
| **Reached from** | World VI-2, *The Faultline* (stage 16) |
| **Lets you out at** | Stage 21, World VIII-1 |
| **On the wall** | `WE ALL FLOAT DOWN HERE` |

**How to find it.** As above.

Chaining warp 2 and warp 3 takes a run from the end of World III to the start
of World VIII: eight stages and three bosses skipped. That is the speedrun
route, and it is deliberately available.

---

## Stage select

Every stage the save has reached is listed on the title screen by name, with
its best time beside it. The cursor opens on the furthest level, so continuing
is one button.

This replaced a four-letter level code system. Codes did the same job with
more keystrokes and a screen of their own, and once stage select existed there
was nothing left for them to do. The test harnesses used to drive that screen
to reach a stage; they seed the cartridge instead - see `tools/make_save.py`,
which writes a save positioned exactly on the stage under test.

---

## Verifying them

Build with the test flags and every room appears in Stage Select, listed after
the story:

```bash
./build.sh clean && ./build.sh "USERFLAGS=-DBN_CFG_ASSERT_ENABLED=true -DLFN_TEST_INVULNERABLE=1"
```

`src/lfn_menu.cpp` only lists hidden rooms when `tune::test_invulnerable` is
set, so a shipping build cannot reach them from the menu no matter what.
