#ifndef LFN_BACKDROP_H
#define LFN_BACKDROP_H

#include "bn_fixed.h"
#include "bn_regular_bg_ptr.h"

namespace lfn
{
    /**
     * Not a world: the front end's own masonry.
     *
     * The menu, the boards, the code screen and the system cards all used to
     * ask for world 7 and get the Hades tileset. That tied how readable a
     * screen of text was to how readable the last world was to play in, and
     * the two want opposite things. They ask for this instead.
     */
    constexpr int backdrop_front = -1;

    /** How far the menu and card backdrops are pushed toward black. */
    constexpr bn::fixed backdrop_dim = 0.45;

    /** How much of a room to build behind a screen. */
    enum class backdrop_style : uint8_t
    {
        room,       // masonry, pillars with lamps, and a floor
        field,      // masonry only, for a card with nothing standing on it
        panel,      // masonry with a framed dark box for a list to sit in
    };

    /**
     * A full-screen background built from a world's own tileset.
     *
     * The menu and the world cards both want to sit in front of somewhere that
     * looks like the game rather than a flat colour, and they want it in the
     * palette of whichever world they are talking about.
     */
    [[nodiscard]] bn::regular_bg_ptr make_backdrop(int world, backdrop_style style);
}

#endif
