#ifndef LFN_LEVEL_H
#define LFN_LEVEL_H

#include "bn_camera_ptr.h"
#include "bn_optional.h"
#include "bn_regular_bg_map_ptr.h"
#include "bn_regular_bg_ptr.h"

#include "lfn_levels.h"
#include "lfn_tiles.h"
#include "lfn_tune.h"

namespace lfn
{
    // What a metatile does to anything that touches it.
    enum class surface : uint8_t
    {
        open,       // walk straight through
        solid,      // blocks from every side
        platform,   // solid only when landing on it from above
        hazard,     // hurts
        breakable,  // solid, but a Devil Dash or a stomp from below opens it
    };

    [[nodiscard]] surface surface_of(int metatile);

    /**
     * A loaded stage: the background it draws with, and the queries the rest of
     * the engine asks about the world.
     *
     * Tile lookups take world pixels, because everything else in the engine
     * works in pixels and converting at the boundary keeps the callers honest.
     */
    class level
    {
    public:
        void load(int index, bn::camera_ptr& camera);
        void unload();

        [[nodiscard]] const level_data& data() const { return *_data; }
        /** The background the stage draws with, for windowing and effects. */
        [[nodiscard]] const bn::regular_bg_ptr& bg() const { return *_bg; }
        /** The slower layer behind the stage, if this level has one. */
        [[nodiscard]] const bn::optional<bn::regular_bg_ptr>& far_bg() const
        { return _far; }

        /**
         * Slide the far layer at half the camera's pace.
         *
         * Called once a frame from the stage. Depth on a machine with no
         * hardware for it is just this: a second map moving slower.
         */
        void parallax(const bn::camera_ptr& camera);
        [[nodiscard]] int columns() const { return _data->columns; }
        [[nodiscard]] int pixel_width() const { return _data->columns * tune::tile; }
        [[nodiscard]] int pixel_height() const { return level_rows * tune::tile; }

        [[nodiscard]] int metatile(int col, int row) const;
        [[nodiscard]] surface at_pixel(int px, int py) const;

        [[nodiscard]] bool blocks(int px, int py) const;
        [[nodiscard]] bool hurts(int px, int py) const;
        /**
         * Would a foot at `py`, which was at `prev_py` last frame, come to rest
         * here? One-way platforms catch a foot that *crossed* their surface this
         * frame - testing only where the foot ended up lets a fast fall skip
         * straight through them.
         */
        [[nodiscard]] bool lands_on(int px, int py, int prev_py, bn::fixed vy) const;

        /** Turn a breakable metatile into open air, and redraw it. */
        bool smash(int col, int row);

    private:
        const level_data* _data = nullptr;
        bn::optional<bn::regular_bg_ptr> _bg;
        bn::optional<bn::regular_bg_ptr> _far;
        bn::optional<bn::regular_bg_map_ptr> _map;

        void _write_cell(int col, int row, int metatile_index);
    };
}

#endif
