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
    };

    /**
     * The front end. Runs its own loop until the player picks something to
     * play, and hands back the stage to start and the run to start it with.
     */
    menu_result show_menu(bn::sprite_text_generator& text, save::file& file);
}

#endif
