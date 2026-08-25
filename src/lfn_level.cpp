#include "lfn_level.h"

#include "bn_bg_palette_items_lfn_palette.h"
#include "bn_bg_tiles.h"
#include "bn_memory.h"
#include "bn_regular_bg_item.h"
#include "bn_regular_bg_map_cell_info.h"
#include "bn_regular_bg_tiles_item.h"
#include "bn_size.h"

#include "bn_regular_bg_tiles_items_tiles_envy.h"
#include "bn_regular_bg_tiles_items_tiles_gluttony.h"
#include "bn_regular_bg_tiles_items_tiles_greed.h"
#include "bn_regular_bg_tiles_items_tiles_hades.h"
#include "bn_regular_bg_tiles_items_tiles_lust.h"
#include "bn_regular_bg_tiles_items_tiles_pride.h"
#include "bn_regular_bg_tiles_items_tiles_sloth.h"
#include "bn_regular_bg_tiles_items_tiles_wrath.h"

namespace lfn
{
    namespace
    {
        // Widest level, rounded up. One metatile is 2x2 cells.
        constexpr int max_columns = 224;
        constexpr int map_cols = max_columns * 2;
        constexpr int map_rows = level_rows * 2;

        // Big enough for any single stage; only one is loaded at a time.
        // ~28KB, so it lives in EWRAM - IWRAM is only 32KB in total.
        alignas(int) BN_DATA_EWRAM_BSS bn::regular_bg_map_cell cells[map_cols * map_rows];

        // The compiled tiles live in ROM, so smashing a block needs a working
        // copy in RAM. Collision reads this, never the ROM array.
        BN_DATA_EWRAM_BSS uint8_t live_tiles[max_columns * level_rows];

        // Live map dimensions, set per level.
        bn::regular_bg_map_item map_item(cells[0], bn::size(map_cols, map_rows));

        const bn::regular_bg_tiles_item& tiles_for(int world)
        {
            switch(world)
            {
            case 0:  return bn::regular_bg_tiles_items::tiles_pride;
            case 1:  return bn::regular_bg_tiles_items::tiles_greed;
            case 2:  return bn::regular_bg_tiles_items::tiles_lust;
            case 3:  return bn::regular_bg_tiles_items::tiles_envy;
            case 4:  return bn::regular_bg_tiles_items::tiles_gluttony;
            case 5:  return bn::regular_bg_tiles_items::tiles_wrath;
            case 6:  return bn::regular_bg_tiles_items::tiles_sloth;
            default: return bn::regular_bg_tiles_items::tiles_hades;
            }
        }
    }

    surface surface_of(int metatile)
    {
        switch(metatile)
        {
        case tile::ground_top:
        case tile::ground_fill:
        case tile::block:
        case tile::ledge_l:
        case tile::ledge_r:
            return surface::solid;

        // Pillars run floor to ceiling, so a solid one would wall the stage
        // off completely. They are scenery Luv passes in front of.
        case tile::pillar:
            return surface::open;

        case tile::breakable:
            return surface::breakable;

        case tile::platform:
            return surface::platform;

        case tile::spikes:
        case tile::hazard:
            return surface::hazard;

        default:
            return surface::open;
        }
    }

    void level::load(int index, bn::camera_ptr& camera)
    {
        unload();
        _data = &levels[index];

        const int cols = _data->columns;
        BN_ASSERT(cols <= max_columns, "Level too wide: ", cols);

        map_item = bn::regular_bg_map_item(cells[0], bn::size(cols * 2, map_rows));

        bn::memory::copy(_data->tiles[0], cols * level_rows, live_tiles[0]);

        for(int row = 0; row < level_rows; ++row)
        {
            for(int col = 0; col < cols; ++col)
            {
                _write_cell(col, row, live_tiles[(row * cols) + col]);
            }
        }

        // Tile indices in the cells are absolute positions in our tileset, so
        // Butano must not shift them when it uploads the tiles.
        bn::bg_tiles::set_allow_offset(false);

        bn::regular_bg_item item(tiles_for(_data->world),
                                 bn::bg_palette_items::lfn_palette, map_item);

        // Butano places a background by its centre, but every world coordinate
        // in the engine is measured from the level's top-left corner, so the
        // background is offset by half the map to line the two up.
        _bg = item.create_bg(pixel_width() / 2, pixel_height() / 2);
        _map = _bg->map();
        _bg->set_camera(camera);

        bn::bg_tiles::set_allow_offset(true);
    }

    void level::unload()
    {
        _map.reset();
        _bg.reset();
        _data = nullptr;
    }

    void level::_write_cell(int col, int row, int metatile_index)
    {
        // grit emits our 16px-wide tileset as TL, TR, BL, BR per metatile.
        const int base = metatile_index * 4;
        const int cx = col * 2;
        const int cy = row * 2;

        for(int i = 0; i < 4; ++i)
        {
            bn::regular_bg_map_cell_info info;
            info.set_tile_index(base + i);
            info.set_palette_id(0);
            cells[map_item.cell_index(cx + (i & 1), cy + (i >> 1))] = info.cell();
        }
    }

    int level::metatile(int col, int row) const
    {
        // Outside the stage reads as open air; the side walls are handled by
        // blocks(), and falling off the bottom is meant to kill.
        if(col < 0 || row < 0 || col >= _data->columns || row >= level_rows)
        {
            return tile::empty;
        }

        return live_tiles[(row * _data->columns) + col];
    }

    surface level::at_pixel(int px, int py) const
    {
        return surface_of(metatile(px / tune::tile, py / tune::tile));
    }

    bool level::blocks(int px, int py) const
    {
        if(px < 0 || px >= pixel_width())
        {
            return true;                       // the stage edges are walls
        }

        const surface s = at_pixel(px, py);
        return s == surface::solid || s == surface::breakable;
    }

    bool level::hurts(int px, int py) const
    {
        return px >= 0 && px < pixel_width() && at_pixel(px, py) == surface::hazard;
    }

    bool level::lands_on(int px, int py, int prev_py, bn::fixed vy) const
    {
        if(blocks(px, py))
        {
            return true;
        }

        if(vy <= 0 || at_pixel(px, py) != surface::platform)
        {
            return false;
        }

        // One-way: catch him only if his foot came down through the surface,
        // so he still rises straight through from below.
        return prev_py <= (py / tune::tile) * tune::tile;
    }

    bool level::smash(int col, int row)
    {
        if(surface_of(metatile(col, row)) != surface::breakable)
        {
            return false;
        }

        live_tiles[(row * _data->columns) + col] = tile::empty;
        _write_cell(col, row, tile::empty);
        _map->reload_cells_ref();
        return true;
    }
}
