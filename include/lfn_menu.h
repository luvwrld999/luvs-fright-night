#ifndef LFN_MENU_H
#define LFN_MENU_H

#include "bn_sprite_text_generator.h"

#include "lfn_game.h"
#include "lfn_save.h"

namespace lfn
{
    struct menu_result
    {
        int level_index = 0;
        run_state run;
        /** Two seats taking alternating turns on the one pad. */
        bool two_player = false;
        /** The eight sins back to back, nothing in between. */
        bool boss_rush = false;
        /**
         * Nobody touched the pad. Not a choice: the caller should run the
         * attract loop and come straight back to the menu.
         */
        bool attract = false;
    };

    /** Stages the boss rush visits, in order. */
    constexpr int boss_rush_stages[] = {2, 5, 8, 11, 14, 17, 20, 23};
    constexpr int boss_rush_count = int(sizeof(boss_rush_stages) / sizeof(int));

    /**
     * The front end. Runs its own loop until the player picks something to
     * play, and hands back the stage to start and the run to start it with.
     */
    menu_result show_menu(bn::sprite_text_generator& text, save::file& file);
}

#endif
