"""
Luv - a ghost with devil horns, an angel halo and a devil tail.

Drawn parametrically into a 16x32 sprite frame (the GBA has no 16x24 sprite
size, so the art lives in the top ~26 rows and the slack below is used by the
bob and hover animations).
"""

import math

import palette as pal
from pixel import Canvas

W, H = 16, 32
CX = 8.0            # horizontal centre of the body

# vertical anatomy
HALO_Y = 3.2

# A skin is the small set of colours that change when Luv is powered up. The
# Purple Soul turns the whole sheet violet with a lime outline, so at a glance
# you can see you are carrying an extra hit.
SKIN_GHOST = dict(body=pal.WHITE, ink=pal.INK, rim=pal.CYAN, rim_low=pal.TEAL,
                  face=pal.INK, glint=pal.CYAN)
SKIN_SOUL = dict(body=pal.PURPLE, ink=pal.GREEN, rim=pal.DGREEN, rim_low=pal.SHADOW,
                 face=pal.GREEN, glint=pal.WHITE)
HORN_TOP = 5.2
BODY_TOP = 8.0
HEAD_CY = 14.0
BODY_BOT = 24.0
HALF_W = 4.6


def _body(c, top, head_cy, bot, halfw, wave_phase, wave_amp, flare, color):
    """Classic ghost silhouette: domed head, straight sides, scalloped hem."""
    dome = head_cy - top
    for y in range(int(top), int(bot + wave_amp) + 2):
        if y < head_cy:
            t = (head_cy - y) / dome
            hw = halfw * math.sqrt(max(0.0, 1.0 - t * t))
        else:
            hw = halfw * (1.0 + flare * (y - head_cy))
        limit = bot + wave_amp * math.sin(wave_phase + y * 0.0)
        for x in range(W):
            dx = x + 0.5 - CX
            if abs(dx) > hw:
                continue
            hem = bot + wave_amp * math.sin(wave_phase + (x + 0.5) * 1.15)
            if y > hem:
                continue
            c.set(x, y, color)


def _horn(c, path, color):
    """
    Tapered devil horn: a continuous stroke, thick at the base, sharp at the
    tip.

    Wider than it looks like it needs to be on paper. At 16 pixels a horn that
    tapers below one pixel simply is not there, and these were drawn behind the
    body as well - half the character brief was invisible on screen.
    """
    total = len(path) - 1
    for i in range(total):
        (ax, ay), (bx, by) = path[i], path[i + 1]
        steps = 10
        for k in range(steps + 1):
            t = k / float(steps)
            seg = (i + t) / float(total)
            r = 0.95 * (1.0 - seg) + 0.40
            c.disc(ax + (bx - ax) * t, ay + (by - ay) * t, r, color)


def _halo(c, cy, color):
    c.ellipse(CX, cy, 5.0, 2.0, color, fill=False)


# The tail is authored pixel by pixel. Three columns beside a body this wide is
# not enough room for a curve to survive rasterising - what reads as a devil
# tail at 16px is a thin stalk, a clear gap from the sheet, and a barbed spade.
# Read top to bottom: the forked tip is up and away from the body, the stalk
# curls out and back, and the root tucks under the hem. The old one was eight
# rows of mostly-straight stalk with a blob on the end, which is why it read as
# a squiggle rather than a tail.
_TAIL_ROWS = [
    '.R.R.',    # forked spade, tip held high
    '.RRR.',
    '..R..',
    '..R..',    # stalk, curling out from under him
    '.R...',
    'R....',
    'R....',
    '.R...',    # and back in toward the hem
    '..R..',
    '..r..',
    '...r.',    # root
]


def _tail(c, phase, color):
    """Devil tail, swaying with `phase`. Drawn to the left of the body."""
    sway = 1 if math.sin(phase) > 0.35 else 0
    top = 14

    for row, line in enumerate(_TAIL_ROWS):
        # Only the spade end swings; the root stays anchored to the body.
        shift = sway if row < 3 else 0

        for col, ch in enumerate(line):
            if ch == '.':
                continue

            # Shifted a column right so the root meets the hem: drawn hard
            # against the frame edge it read as a separate object floating
            # beside him rather than something attached.
            c.set(col + shift + 1, top + row, color if ch == 'R' else pal.DRED)


def _face(c, dy, look, eyes='open', mouth='o', ink=pal.INK, glint=pal.CYAN):
    """Hollow glowing eye sockets and a small ghostly mouth."""
    ex = [5 + look, 9 + look]
    ey = int(12 + dy)
    if eyes == 'closed':
        for x0 in ex:
            c.rect(x0, ey + 1, x0 + 1, ey + 1, ink)
    elif eyes == 'hurt':
        for x0 in ex:
            c.line(x0, ey, x0 + 1, ey + 2, ink)
            c.line(x0 + 1, ey, x0, ey + 2, ink)
    else:
        wide = 1 if eyes == 'wide' else 0
        for x0 in ex:
            c.rect(x0, ey - wide, x0 + 1, ey + 2, ink)
            c.set(x0, ey - wide, glint)

    my = int(17 + dy)
    mx = int(7 + look)
    if mouth == 'o':
        c.rect(mx, my, mx + 1, my + 1, ink)
    elif mouth == 'wide':
        c.rect(mx - 1, my, mx + 2, my + 2, ink)
        c.rect(mx, my + 1, mx + 1, my + 1, pal.DMAG)
    elif mouth == 'grin':
        c.rect(mx - 1, my, mx + 2, my, ink)
        c.set(mx - 1, my + 1, ink)
        c.set(mx + 2, my + 1, ink)


def frame(bob=0.0, halo_bob=0.0, tail_phase=0.0, wave_phase=0.0,
          halfw=HALF_W, stretch=0.0, look=1, eyes='open', mouth='o',
          horns=True, halo=True, tail=True, body_color=None,
          halo_color=pal.GOLD, horn_color=pal.RED, aura=None, wisps=False,
          skin=None):
    """Build one 16x32 frame of Luv."""
    skin = skin or SKIN_GHOST
    body_color = body_color or skin['body']
    c = Canvas(W, H)

    top = BODY_TOP + bob - stretch
    head_cy = HEAD_CY + bob - stretch * 0.5
    bot = BODY_BOT + bob + stretch * 0.5

    # aura sits behind everything (power-up states)
    if aura is not None:
        a = Canvas(W, H)
        _body(a, top - 1, head_cy - 1, bot + 1, halfw + 1.1, wave_phase, 1.6, 0.012, aura)
        c.paste(a)

    if halo:
        # A row higher than it used to sit, so there is clear air between the
        # ring and the horn tips instead of the three of them touching.
        _halo(c, max(0.8, top - 6.0 + halo_bob), halo_color)

    _body(c, top, head_cy, bot, halfw, wave_phase, 1.7, 0.012, body_color)

    if horns:
        # Drawn after the body, not before it. They used to go down first and
        # the body painted over their bases, leaving two red specks tucked
        # behind the halo. They now sweep outward and finish just under the
        # halo, where there is clear air to read against.
        # From the crown, rising and curving outward. They used to start at
        # eye level and sweep sideways, which at this size reads as a pair of
        # angry eyebrows rather than horns.
        # Short enough to stop under the halo rather than growing into it -
        # at full height the two of them and the ring merged into one red mass
        # across the top of his head.
        hy = top
        _horn(c, [(5.8, hy + 1.0), (5.0, hy - 0.4), (4.3, hy - 1.7),
                  (3.9, hy - 2.8)], horn_color)
        _horn(c, [(10.2, hy + 1.0), (11.0, hy - 0.4), (11.7, hy - 1.7),
                  (12.1, hy - 2.8)], horn_color)

    if tail:
        t = Canvas(W, H)
        _tail(t, tail_phase, horn_color)
        t.outline(skin['ink'])
        c.paste(t.shifted(0, int(round(bob))))

    if wisps:
        for i, x in enumerate((2, 13)):
            c.disc(x, 21 + bob + 2 * math.sin(tail_phase + i * 2.1), 1.3, pal.CYAN)
            c.disc(x, 24 + bob + 2 * math.sin(tail_phase + i * 2.1), 0.9, pal.TEAL)

    _face(c, bob - stretch * 0.5, look, eyes, mouth, skin['face'], skin['glint'])

    # finishing passes: shade away from the light, spectral rim, then outline
    c.shade(light=(-1, -1),
            colors={body_color, pal.RED, pal.GOLD, pal.MAG})
    c.rim(skin['rim_low'], direction=(-1, 0), over={body_color},
          region=lambda x, y: x < CX and y > BODY_TOP)
    c.rim(skin['rim'], direction=(-1, 0), over={body_color, skin['rim_low']},
          region=lambda x, y: x < CX and BODY_TOP < y < HEAD_CY + 5 + bob)
    c.outline(skin['ink'])
    return c


# ---------------------------------------------------------------------------
# The animation table the engine indexes into. One sheet covers every state;
# the power-ups are expressed with palette swaps and the overlay sprites below,
# which keeps Luv down to a single 16x32 tile budget in VRAM.
FRAME_NAMES = ['idle0', 'idle1', 'run0', 'run1', 'run2', 'run3', 'jump', 'fall',
               'hover0', 'hover1', 'dash0', 'dash1', 'hurt']


def sheet_frames(skin=None):
    skin = skin or SKIN_GHOST
    return [
        frame(bob=0, halo_bob=0.0, tail_phase=0.0, wave_phase=0.0, skin=skin),
        frame(bob=1, halo_bob=-0.6, tail_phase=1.6, wave_phase=1.1, skin=skin),
        frame(bob=0, halo_bob=-0.3, tail_phase=0.0, wave_phase=0.0, look=2, skin=skin),
        frame(bob=1, halo_bob=0.4, tail_phase=1.6, wave_phase=1.6, look=2, skin=skin),
        frame(bob=0, halo_bob=0.6, tail_phase=3.1, wave_phase=3.1, look=2, skin=skin),
        frame(bob=1, halo_bob=-0.4, tail_phase=4.7, wave_phase=4.7, look=2, skin=skin),
        frame(bob=-1, stretch=1.6, tail_phase=2.4, wave_phase=2.0,
              eyes='wide', mouth='wide', look=1, skin=skin),
        frame(bob=1, stretch=-1.2, tail_phase=4.2, wave_phase=5.0,
              eyes='wide', mouth='o', look=1, skin=skin),
        frame(bob=0, halfw=5.6, tail_phase=3.0, wave_phase=1.0,
              eyes='open', mouth='grin', wisps=True, skin=skin),
        frame(bob=1, halfw=5.6, tail_phase=4.6, wave_phase=2.6,
              eyes='open', mouth='grin', wisps=True, skin=skin),
        frame(bob=1, halfw=5.8, stretch=-1.6, tail_phase=5.4, wave_phase=3.0,
              eyes='wide', mouth='grin', look=2, skin=skin),
        frame(bob=1, halfw=6.0, stretch=-2.0, tail_phase=2.2, wave_phase=4.4,
              eyes='wide', mouth='grin', look=2, skin=skin),
        frame(bob=1, tail_phase=5.0, wave_phase=2.2, eyes='hurt', mouth='wide', look=0, skin=skin),
    ]


def aura_frames():
    """Behind-Luv glow used by Blessed Halo and Devil Dash. 16x32."""
    out = []
    for i in range(4):
        c = Canvas(W, H)
        _body(c, BODY_TOP - 1.5, HEAD_CY - 1, BODY_BOT + 1.5, HALF_W + 1.6 + (i % 2) * 0.4,
              i * 1.6, 1.8, 0.012, pal.GOLD)
        inner = Canvas(W, H)
        _body(inner, BODY_TOP - 0.2, HEAD_CY, BODY_BOT + 0.2, HALF_W + 0.4,
              i * 1.6, 1.7, 0.012, pal.WHITE)
        for y in range(H):
            for x in range(W):
                if inner.px[y][x] != pal.KEY:
                    c.px[y][x] = pal.KEY
        out.append(c)
    return out


def wing_frames():
    """Wisp Wings overlay, mirrored by the engine for the other side. 16x16."""
    out = []
    for i in range(4):
        c = Canvas(16, 16)
        spread = [0.0, 1.2, 2.2, 1.2][i]
        c.poly([(14, 9), (5 - spread, 3 - spread), (2 - spread, 9),
                (6, 13)], pal.CYAN)
        c.poly([(13, 9), (7 - spread * 0.7, 5 - spread * 0.7), (5 - spread, 9)], pal.WHITE)
        c.outline(pal.INK)
        out.append(c)
    return out
