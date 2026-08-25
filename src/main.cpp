#include "bn_bg_palettes.h"
#include "bn_color.h"
#include "bn_core.h"
#include "bn_keypad.h"
#include "bn_sprite_text_generator.h"
#include "bn_unique_ptr.h"

#include "common_variable_8x16_sprite_font.h"
#include "common_variable_8x8_sprite_font.h"

#include "lfn_audio.h"
#include "lfn_cards.h"
#include "lfn_game.h"
#include "lfn_levels.h"
#include "lfn_menu.h"
#include "lfn_save.h"
#include "lfn_trace.h"
#include "lfn_tune.h"

namespace
{
    constexpr bn::color night(4, 2, 8);

    /** One player's whole game: where they are, and what they are carrying. */
    struct seat
    {
        lfn::run_state run;
        int index = 0;
        bool out = false;
    };

    /**
     * Offer the board to one finished run. Returns the row it landed on, or
     * -1 if the score was not good enough. The cartridge is written either
     * way, so a run always leaves something behind.
     */
    int claim(bn::sprite_text_generator& text, lfn::save::file& file,
              const lfn::run_state& run, int player)
    {
        int slot = -1;

        if(lfn::save::qualifies(file, run.score))
        {
            slot = lfn::enter_initials(text, file, run.score, player);
        }

        lfn::save::store(file);
        return slot;
    }
}

int main()
{
    bn::core::init();
    bn::bg_palettes::set_transparent_color(night);

    bn::sprite_text_generator text(common::variable_8x16_sprite_font);
    // Half the sprite VRAM per character, for everything that has to
    // coexist with a stage full of sprites.
    bn::sprite_text_generator small(common::variable_8x8_sprite_font);

#if LFN_TEST_INITIALS
    {
        // Test build only: drop straight into the name entry with a score that
        // lands mid-table, so the screen can be driven without a full run.
        lfn::save::file probe = lfn::save::load();
        lfn::run_state fake;
        fake.score = 40000;

        if(claim(text, probe, fake, 0) >= 0)
        {
            lfn::show_high_scores(text, probe, 0);
        }
    }
#endif

    while(true)
    {
        lfn::save::file file = lfn::save::load();
        lfn::menu_result picked = lfn::show_menu(text, file);

        const int seats_taken = picked.two_player ? 2 : 1;
        seat seats[2];

        for(int i = 0; i < seats_taken; ++i)
        {
            seats[i].run = picked.run;
            seats[i].index = picked.level_index;
        }

        int turn = 0;
        // The first turn of a two-player game gets its own card too, so the
        // pad is never handed over without saying whose it is.
        bool announce = picked.two_player;
        bool abandoned = false;
        bool won = false;

        while(!seats[0].out || (seats_taken > 1 && !seats[1].out))
        {
            if(seats[turn].out)
            {
                turn ^= 1;
                continue;
            }

            seat& me = seats[turn];
            const bool alone = seats_taken == 1 || seats[turn ^ 1].out;
            const int label = seats_taken > 1 ? turn + 1 : 0;

            if(announce)
            {
                lfn::show_player_card(text, label, me.run);
                announce = false;
            }

            LFN_TRACE("main: starting stage ", me.index);
            lfn::show_world_card(text, me.index, me.run, label);

            // The stage owns the whole entity pool, which is far too big to
            // sit on the GBA's small stack.
            bn::unique_ptr<lfn::game> stage(
                        new lfn::game(me.index, me.run, small, label, !alone));
            lfn::game_result result = lfn::game_result::running;

            while(result == lfn::game_result::running)
            {
                if(bn::keypad::start_pressed() &&
                   lfn::run_pause(text) == lfn::pause_result::quit)
                {
                    abandoned = true;
                    break;
                }

                result = stage->update();
                bn::core::update();
            }

            me.run = stage->carried();
            const bool stage_warped = stage->warped();
            stage.reset();

            if(abandoned)
            {
                lfn::audio::stop_music();
                break;
            }

            if(result == lfn::game_result::handed_over)
            {
                // A life lost with someone waiting. They keep their stage and
                // start it again when the pad comes back to them.
                turn ^= 1;
                announce = true;
                continue;
            }

            if(result == lfn::game_result::game_over)
            {
                me.out = true;

                if(seats_taken == 1)
                {
                    lfn::show_game_over(text, me.run, file);
                }
                else if(!seats[turn ^ 1].out)
                {
                    turn ^= 1;
                    announce = true;
                    continue;
                }

                break;
            }

            // A warp door, an explicit exit, or simply the next stage.
            const lfn::level_data& done = lfn::levels[me.index];

            if(stage_warped && done.warp >= 0)
            {
                me.index = done.warp;
            }
            else if(done.exit_to >= 0)
            {
                me.index = done.exit_to;
            }
            else
            {
                ++me.index;
            }

            // Two seats share one cartridge slot, so only a solo run is
            // allowed to move the saved progress.
            if(seats_taken == 1)
            {
                file.furthest_level = uint16_t(bn::clamp(me.index, 0,
                                                         lfn::story_count - 1));
                file.lives = uint8_t(bn::clamp(me.run.lives, 1, 99));
                file.souls = uint16_t(me.run.souls);
                lfn::save::store(file);
            }

            if(me.index >= lfn::story_count)
            {
                // Hades is down: the run is over however many seats are taken.
                lfn::show_ending(text, me.run, file);
                won = true;
                seats[0].out = true;
                seats[1].out = true;
                break;
            }
        }

        lfn::audio::stop_music();

        if(!abandoned)
        {
            if(seats_taken > 1)
            {
                if(!won)
                {
                    lfn::show_two_player_result(text, seats[0].run, seats[1].run);
                }

                const int first = claim(text, file, seats[0].run, 1);
                const int second = claim(text, file, seats[1].run, 2);

                if(first >= 0 || second >= 0)
                {
                    lfn::show_high_scores(text, file, second >= 0 ? second : first);
                }
            }
            else
            {
                const int slot = claim(text, file, seats[0].run, 0);

                if(slot >= 0)
                {
                    lfn::show_high_scores(text, file, slot);
                }
            }
        }
    }
}
