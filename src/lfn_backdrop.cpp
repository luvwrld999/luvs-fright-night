#include "lfn_backdrop.h"

#include "bn_bg_palette_items_lfn_palette.h"
#include "bn_bg_tiles.h"
#include "bn_regular_bg_item.h"
#include "bn_regular_bg_map_cell_info.h"
#include "bn_regular_bg_map_item.h"
#include "bn_size.h"

#include "bn_regular_bg_tiles_items_tiles_envy.h"
#include "bn_regular_bg_tiles_items_tiles_gluttony.h"
#include "bn_regular_bg_tiles_items_tiles_greed.h"
#include "bn_regular_bg_tiles_items_tiles_hades.h"
#include "bn_regular_bg_tiles_items_tiles_lust.h"
#include "bn_regular_bg_tiles_items_tiles_pride.h"
#include "bn_regular_bg_tiles_items_tiles_sloth.h"
#include "bn_regular_bg_tiles_items_tiles_wrath.h"

#include "lfn_tiles.h"

namespace lfn
{
    namespace
    {
        constexpr int map_cols = 32;
        constexpr int map_rows = 32;

        alignas(int) BN_DATA_EWRAM_BSS bn::regular_bg_map_cell cells[map_cols * map_rows];
        bn::regular_bg_map_item map_item(cells[0], bn::size(map_cols, map_rows));

        void put(int col, int row, int metatile)
        {
            const int base = metatile * 4;

            for(int i = 0; i < 4; ++i)
            {
                bn::regular_bg_map_cell_info info;
                info.set_tile_index(base + i);
                info.set_palette_id(0);
                cells[map_item.cell_index((col * 2) + (i & 1),
                                          (row * 2) + (i >> 1))] = info.cell();
            }
        }

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

    bn::regular_bg_ptr make_backdrop(int world, backdrop_style style)
    {
        const bool floored = style == backdrop_style::room;

        for(int row = 0; row < map_rows / 2; ++row)
        {
            for(int col = 0; col < map_cols / 2; ++col)
            {
                int metatile = tile::bg_a;

                if(floored && row >= 9)
                {
                    metatile = row == 9 ? tile::ground_top : tile::ground_fill;
                }
                else if(((col + row) % 7) == 0)
                {
                    metatile = tile::bg_b;      // a little masonry variation
                }

                put(col, row, metatile);
            }
        }

        if(floored)
        {
            for(int row = 1; row < 9; ++row)
            {
                put(1, row, tile::pillar);
                put(13, row, tile::pillar);
            }

            put(1, 4, tile::decor);
            put(13, 4, tile::decor);
        }

        // Tile indices here are absolute, so Butano must not renumber them.
        bn::bg_tiles::set_allow_offset(false);
        bn::regular_bg_item item(tiles_for(world), bn::bg_palette_items::lfn_palette,
                                 map_item);
        bn::regular_bg_ptr bg = item.create_bg(0, 0);
        bn::bg_tiles::set_allow_offset(true);
        bg.set_priority(3);
        return bg;
    }
}
