#ifndef LFN_BACKDROP_H
#define LFN_BACKDROP_H

#include "bn_regular_bg_ptr.h"

namespace lfn
{
    /** How much of a room to build behind a screen. */
    enum class backdrop_style : uint8_t
    {
        room,       // masonry, pillars with lamps, and a floor
        field,      // masonry only, for a card with nothing standing on it
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
