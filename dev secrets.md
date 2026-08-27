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

## Level codes

Every stage prints its own code on the world intro card, and `LEVEL CODE` on
the title screen takes four letters back. Codes use a sixteen-letter alphabet
with no vowels and nothing that reads as a digit —
`B C D F G H J K L M N P R S T V` — so a code written on paper always types
back cleanly. A code that answers to nothing says **NO SUCH PLACE**; there is
no way to typo your way into the wrong stage, because entry compares against
every generated code rather than decoding the letters.

Entering a code also unlocks stage select up to that point, so it never has to
be typed twice.

| Code | Stage | Name |
|---|---|---|
| `FJTK` | I-1 | Chapel of the Mirror |
| `DMDB` | I-2 | The Long Gallery |
| `CRJS` | I-3 | Superbia |
| `CJNT` | II-1 | The Counting Floor |
| `BMTP` | II-2 | Vault of Small Coins |
| `KRFG` | II-3 | Avaritia |
| `KKKC` | III-1 | Thorn Walk |
| `JMPD` | III-2 | The Lantern Beds |
| `HRVV` | III-3 | Luxuria |
| `HKFL` | IV-1 | Green Water |
| `GNGH` | IV-2 | What He Has |
| `PRLJ` | IV-3 | Invidia |
| `PKRF` | V-1 | The Larder |
| `NNBR` | V-2 | Second Helpings |
| `MSGM` | V-3 | Gula |
| `MKLN` | VI-1 | Cinderpath |
| `LNSK` | VI-2 | The Faultline |
| `VSCB` | VI-3 | Ira |
| `VBHS` | VII-1 | Dust Rooms |
| `TNMT` | VII-2 | Nothing Stirs |
| `SSSP` | VII-3 | Acedia |
| `SBJG` | VIII-1 | The Descent |
| `RNNC` | VIII-2 | Below Everything |
| `FSTD` | VIII-3 | Hades |

### The three hidden rooms have codes too

A hidden room shows its own intro card once you warp into it, code and all —
so a player who finds the door the honest way keeps the shortcut. Until then
these three are the only codes with nothing in the game pointing at them.
Typing one drops you straight into the room, wall writing and all.

| Code | Room |
|---|---|
| `FBDV` | Nine Nine Nine |
| `DPJL` | The Long Way Round |
| `CSPH` | Straight Down |

The generator is one line in `src/lfn_code.cpp`: `((index + 1) * 2749) ^ 0x3C5A`,
taken as four hex nibbles indexed into the alphabet. The multiplier is odd, so
no two stages can ever collide.

## Cheat codes

`EXTRAS` > `CHEAT CODE` opens a screen that listens for ten seconds and then
closes itself, so nobody who wandered in is stuck holding a pad they do not
know what to do with. A row of marks shows how far into a sequence you are,
without ever showing the sequence back - that would stop it being something
you have to know. A correct entry plays a rising major arpeggio, the only
major-key sound in the game.

| Input | Effect |
|---|---|
| Up Up Down Down Left Right A B Select Start | Start the next run with **99 lives** |
| B pressed ten times | Start the next run with **10 lives** |

B is both the eighth key of the long sequence and a cheat in its own right, so
its tally runs alongside the sequence check rather than inside it. A wrong key
restarts the sequence - at the first key if that is what you pressed, which
means `Up Up Up Down...` still works.

A cheat arms **the next run to start**, whichever mode it turns out to be, and
is spent doing so. It is not a setting, it does not persist to the cartridge,
and it never touches the high score board's rules.

## Depth

The wall behind a stage is its own background layer, moving at half the
camera's pace. The stage layer draws terrain only and leaves its background
transparent - an opaque wall in front of the far layer is why the first
attempt at depth did nothing visible at all.

Priorities, because they are easy to get wrong: wall 3, stage 2, everything
that moves at sprite bg_priority 1, status bar at 0 with z_order -100. Butano
starts sprites at bg_priority 3, so a stage layer at 2 puts the player behind
the floor, and bg_priority alone will not stop a bonus soul drawing over the
clock - between two sprites it is z_order that decides.

## Boss arenas

Every sin's room is shaped for the thing that lives in it. All eight used to be
the same sixteen columns with the same two ledges, so eight different fights
happened in one room.

| Sin | Room |
|---|---|
| I Superbia | two ledges clear of the middle |
| II Avaritia | a stepped floor, so its hops land somewhere different |
| III Luxuria | pillars for cover, for something that drifts and charms |
| IV Invidia | bare - a charger rebounding off walls is the whole fight |
| V Gula | a hole in the floor, because it eats the floor |
| VI Ira | a lid on the room, so a slam leaves nowhere to jump |
| VII Acedia | a ceiling with teeth; it never moves, the room attacks |
| VIII Hades | three tiers, for a fight with three phases |

Hades also has its own music - `hades_boss`, *The King Below* - rather than
sharing the boss theme with the other seven.

## The air in each world

Each world's air pushes differently, which is the one thing that makes a world
play rather than merely look different. `world_drift` is a horizontal push
applied while airborne; `world_gravity` scales the fall. Both live in
`include/lfn_tune.h`, and `tools/check_levels.py` reads that same table so
every gap is proved crossable in the wind it will actually be jumped in.

| World | Air | Jump reach |
|---|---|---|
| I Pride, II Greed | still | 70 px |
| III Lust | a draught at your back | 80 px |
| IV Envy | the green water pushes back | 58 px |
| V Gluttony | thick, a slower fall | 75 px |
| VI Wrath | it blows out from the fault | 82 px |
| VII Sloth | everything takes its time | 82 px |
| VIII Hades | something is inhaling | 61 px |

## Souls

Nine bonus souls per stage are placed by reading the finished level for the
lowest solid cell with air above it - the floor the player actually stands on.
Scanning from the top instead finds the ceiling wherever a column has one, and
puts the soul above it where nobody can reach it. check_levels.py now fails on
a bonus soul with no floor within a jump beneath it, and on a ground enemy
hung in the air with nothing to walk on.

A plain soul is worth one. A **bonus soul** - larger, gold rather than cyan -
is worth ten, and nine of them are scattered through every stage, placed by
reading the finished level rather than by any one beat, so they land above the
local surface wherever that happens to be.

Ninety-nine souls is an extra life, and the counter rolls back to zero. A run
that collects everything is worth about sixteen extra lives.

Souls cost nothing on the balance sheet: pressure counts enemies, holes and
hazard regions per screen, so a stage can be as generous with them as it likes
without getting harder.

## Endings

The last line of the ending changes with what the run was. The rest does not -
the point is the run, not a different story.

| Condition | Last line |
|---|---|
| All three hidden rooms, and no continues spent | `NOTHING DOWN THERE KEPT HIM` |
| All three hidden rooms | `HE SAW EVERY ROOM` |
| No continues spent | `AND NEVER ONCE TURNED BACK` |
| Otherwise | `HORNS AND ALL` |

The run carries a three-bit mask of which hidden rooms it has been inside, set
by the stage itself: hidden rooms sit after the story in the level list, so
their index doubles as the bit. The ending also prints `SECRETS n OF 3`.

## Save files and boards

The cartridge holds **three separate games**. NEW GAME always asks which file,
so a second person can take an empty one; CONTINUE only asks when more than
one file has something in it. Erasing a file clears that file alone.

The **high score boards and the best times are not part of a save file** -
they belong to the cartridge. NEW GAME does not touch them.

There are two boards. A five minute boss rush and a forty minute run do not
belong on the same ladder, so the rush has its own, seeded lower. `A` on the
board screen flips between them.

## Modes and records

`EXTRAS` on the title screen holds **BOSS RUSH**: the eight sins back to back,
following its own list rather than the story order, with no continues. It does
not touch saved progress.

Leaving the pad alone for twenty seconds on the title screen starts the
**attract loop** - the high score board, then the autopilot playing a stage
with DEMO across the bottom. It cycles through stages 1-1, 3-1, 5-1 and 7-1,
one per turn, and any button drops straight back to the menu. The autopilot is
the same driver the headless test harness uses.

**Continues**: three per run, offered on a nine second countdown when the lives
run out. Taking one restores three lives and restarts the current stage. The
score stands.

**Best times** are kept per stage in SRAM, in the same clock units the status
bar counts down, and shown as a column on stage select. They survive NEW GAME,
because they are records rather than progress - the same reasoning that keeps
the high score board.

## Two player

`2 PLAYER` runs two seats on one pad, alternating on death — the classic
arcade turn. Each seat keeps its own lives, score and place in the game; losing
a life ends your turn and the other player resumes their own stage from the
start of it. A seat that runs out of lives is skipped, and the last one
standing plays on alone. When both are done the two scores go up side by side,
and each one that earns a place gets its own turn at the initials screen.

Two-player games deliberately do **not** touch the saved file's progress — two
people sharing a cartridge should not overwrite the single-player game. Scores
still go to the board.

## Where the data lives

| Thing | File |
|---|---|
| Which stage hides which door | `SECRET_DOORS` in `tools/gen_levels.py` |
| The rooms themselves | `SECRET_ROOMS` in `tools/gen_levels.py` |
| The door beat | `Builder.secret_door()` in `tools/gen_levels.py` |
| Warp and sign handling | `src/lfn_entities.cpp`, `ent_kind::warp` and `spawn_type::sign` |
| Wall writing | `game::game()` in `src/lfn_game.cpp` |
| Where a cleared stage sends you | `src/main.cpp`, the block after `stage->warped()` |

To add another: put a `warp` spawn in a stage, set that stage's `! warp:` to the
new room's index, and give the room `! hidden: 1` and an `! exit_to:`. The
linter (`tools/check_levels.py`) and the compiler will tell you if you have
made a room nobody can cross or a stage with no way out.

---

## Verifying them

Build with the test flags and every room appears in Stage Select, listed after
the story:

```bash
./build.sh clean && ./build.sh "USERFLAGS=-DBN_CFG_ASSERT_ENABLED=true -DLFN_TEST_INVULNERABLE=1"
```

`src/lfn_menu.cpp` only lists hidden rooms when `tune::test_invulnerable` is
set, so a shipping build cannot reach them from the menu no matter what.
