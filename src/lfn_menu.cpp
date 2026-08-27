#include "lfn_menu.h"

#include "bn_core.h"
#include "bn_format.h"
#include "bn_keypad.h"
#include "bn_math.h"
#include "bn_optional.h"
#include "bn_regular_bg_ptr.h"
#include "bn_sprite_palette_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_sprite_tiles_ptr.h"
#include "bn_string_view.h"
#include "bn_vector.h"

#include "bn_sprite_items_logo.h"
#include "bn_sprite_items_luv.h"
#include "bn_sprite_items_soul_orb.h"
#include "bn_sprite_palette_items_text_cyan.h"
#include "bn_sprite_palette_items_text_gold.h"
#include "bn_sprite_palette_items_text_mag.h"

#include "lfn_audio.h"
#include "lfn_backdrop.h"
#include "lfn_cards.h"
#include "lfn_code.h"
#include "bn_core.h"
#include "lfn_hud.h"
#include "lfn_levels.h"
#include "lfn_tune.h"

namespace lfn
{
    namespace
    {
        enum class screen : uint8_t { main, stages, extras, confirm, controls };

        constexpr int stage_rows = 5;
        constexpr int drifters = 5;

        struct entry
        {
            const char* label;
            int action;                     // 0 continue, 1 new, 2 stages, 3 controls
        };

        /**
         * "I-1  CHAPEL OF THE MI" - the name is clipped because every glyph is
         * a sprite and the GBA runs out of sprite VRAM long before it runs out
         * of things to say.
         */
        /** Which slot a stage occupies inside its world, counting bosses. */
        int slot_of(int index)
        {
            int slot = 1;

            for(int i = 0; i < index; ++i)
            {
                if(levels[i].world == levels[index].world)
                {
                    ++slot;
                }
            }

            return slot;
        }

        bn::string<32> stage_label(int index)
        {
            bn::string<32> out = bn::format<32>("{}-{}  ", roman(levels[index].world),
                                                slot_of(index));

            // Short enough to leave the best time its own column on the right.
            for(const char* c = levels[index].name; *c && out.size() < 18; ++c)
            {
                out.push_back(*c);
            }

            return out;
        }

        void tint(bn::vector<bn::sprite_ptr, 112>& sprites, int from,
                  const bn::sprite_palette_item& palette)
        {
            for(int i = from; i < sprites.size(); ++i)
            {
                sprites[i].set_palette(palette);
            }
        }
    }

    namespace
    {
        // Survives a trip out to a sub-screen and back, but not a whole
        // session: a cheat arms one run.
        int cheat_lives = 0;
    }

    menu_result show_menu(bn::sprite_text_generator& text, save::file& file)
    {
        // A field, not a room: the room style draws a floor line across the
        // middle of the screen, and the option list sat on top of it.
        bn::regular_bg_ptr backdrop = make_backdrop(backdrop_front, backdrop_style::field);

        bn::vector<bn::sprite_ptr, 112> sprites;

        // Two halves of the 128x64 wordmark, side by side.
        constexpr bn::fixed logo_y = -52;
        bn::sprite_ptr logo_l = bn::sprite_items::logo.create_sprite(-32, logo_y);
        bn::sprite_ptr logo_r = bn::sprite_items::logo.create_sprite(32, logo_y);
        logo_r.set_tiles(bn::sprite_items::logo.tiles_item().create_tiles(1));

        // The title holds on its own before it becomes a list, the way a
        // cartridge of this era would. Once a boot: coming back from a game
        // should put the menu straight in front of you.
        static bool unseen = true;

        if(unseen)
        {
            unseen = false;
            audio::play_music(audio::track::title);

            bn::vector<bn::sprite_ptr, 24> gate;
            bn::sprite_ptr flier = bn::sprite_items::luv.create_sprite(-140, -8);
            bool asked = false;

            for(int frame = 0; ; ++frame)
            {
                // The wordmark drops in and settles, rather than simply being
                // there when the screen appears.
                const int fall = bn::min(frame, 26);
                const bn::fixed drop = (26 - fall) * (26 - fall) / bn::fixed(9);
                logo_l.set_y(logo_y - drop);
                logo_r.set_y(logo_y - drop);

                flier.set_position(-140 + (frame * 3),
                                   -8 + bn::lut_sin((frame * 22) & 2047) * 6);

                if((frame % 8) == 0)
                {
                    flier.set_tiles(bn::sprite_items::luv.tiles_item()
                                    .create_tiles(8 + ((frame / 8) & 1)));
                }

                if(!asked && frame > 40)
                {
                    asked = true;
                    text.set_center_alignment();
                    text.generate(0, 34, "PRESS START", gate);

                    for(bn::sprite_ptr& sprite : gate)
                    {
                        sprite.set_palette(bn::sprite_palette_items::text_gold);
                    }
                }

                // Blink it, so the screen never looks stalled.
                for(bn::sprite_ptr& sprite : gate)
                {
                    sprite.set_visible((frame >> 4) & 1);
                }

                if(frame > 20 && (bn::keypad::a_pressed() ||
                                  bn::keypad::start_pressed()))
                {
                    audio::sfx_menu();
                    break;
                }

                bn::core::update();
            }

            gate.clear();
            logo_l.set_y(logo_y);
            logo_r.set_y(logo_y);
            bn::core::update();
            bn::core::update();
        }

        bn::sprite_ptr cursor = bn::sprite_items::luv.create_sprite(0, 0);
        bn::sprite_ptr host = bn::sprite_items::luv.create_sprite(92, 44);

        // Souls drifting up through the scene.
        bn::vector<bn::sprite_ptr, drifters> souls;
        bn::fixed soul_y[drifters];

        for(int i = 0; i < drifters; ++i)
        {
            souls.push_back(bn::sprite_items::soul_orb.create_sprite(
                        -96 + (i * 46), 60 - (i * 21)));
            soul_y[i] = 60 - (i * 21);
        }

        const auto restore = [&]()
        {
            souls.clear();

            for(int i = 0; i < drifters; ++i)
            {
                souls.push_back(bn::sprite_items::soul_orb.create_sprite(
                            -96 + (i * 46), soul_y[i]));
            }

            cursor.set_visible(true);
            logo_l.set_visible(true);
            logo_r.set_visible(true);
        };

        // Twenty seconds of nobody touching anything and the cartridge starts
        // showing off, the way one in a shop window would.
        constexpr int attract_after = 20 * 60;
        int idle = 0;

        screen where = screen::main;
        int choice = 0;
        int stage_pick = 0;
        int stage_top = 0;
        bool dirty = true;
        int frame = 0;

        bn::vector<entry, 8> options;
        // Any slot with a game in it, not just the one last played, or a
        // second person's save would be unreachable from the front page.
        const bool has_save = save::slots_used(file) > 0;

        if(has_save)
        {
            options.push_back({"CONTINUE", 0});
        }

        options.push_back({"NEW GAME", 1});
        options.push_back({"2 PLAYER", 6});
        options.push_back({"LEVEL CODE", 7});

        if(has_save)
        {
            options.push_back({"STAGE SELECT", 2});
        }

        options.push_back({"EXTRAS", 8});

        // The second page. Six rows is all the front page can hold at a size
        // that stays readable, so the reference screens live one press deeper.
        bn::vector<entry, 8> extras;
        extras.push_back({"HIGH SCORES", 4});
        extras.push_back({"BOSS RUSH", 10});
        extras.push_back({"SOUND TEST", 9});
        extras.push_back({"CHEAT CODE", 11});
        extras.push_back({"CREDITS", 5});
        extras.push_back({"CONTROLS", 3});
        int extra_pick = 0;
        int erase_pick = 0;     // starts on NO: erasing should take two decisions

        // Test builds can reach the hidden rooms from stage select; the
        // shipping game only ever lists the story.
        const int listable = tune::test_invulnerable ? level_count : story_count;
        const int unlocked = bn::min<int>(save::slot(file).furthest_level + 1, listable);
        audio::play_music(audio::track::title);

        menu_result result;
        result.run.lives = tune::start_lives;

        // A cheat arms the next run to start, whatever it turns out to be, and
        // is spent doing so - it is not a permanent setting.
        const auto arm = [&]()
        {
            if(cheat_lives)
            {
                result.run.lives = cheat_lives;
                cheat_lives = 0;
            }
        };

        // Hand VRAM back before whatever comes next starts asking for it.
        // Butano reclaims a freed sprite's tiles on the following update, so
        // leaving that to the destructors means the next screen allocates on
        // top of everything this one was still holding.
        const auto release = [&]()
        {
            sprites.clear();
            souls.clear();
            cursor.set_visible(false);
            host.set_visible(false);
            logo_l.set_visible(false);
            logo_r.set_visible(false);
            bn::core::update();
            bn::core::update();
        };

        while(true)
        {
            ++frame;

            if(dirty)
            {
                sprites.clear();
                text.set_center_alignment();

                if(where == screen::main)
                {
                    // The name is a sprite now; only the tagline is text.
                    text.generate(0, -26, "a ghost in bad company", sprites);
                    tint(sprites, 0, bn::sprite_palette_items::text_mag);

                    // Centred, with the cursor to the left of the block, rather
                    // than a left-aligned list under a centred title.
                    for(int i = 0; i < options.size(); ++i)
                    {
                        text.generate(0, -8 + (i * 14), options[i].label, sprites);
                    }
                }
                else if(where == screen::confirm)
                {
                    text.generate(0, -60, "START AGAIN?", sprites);
                    tint(sprites, 0, bn::sprite_palette_items::text_gold);

                    int mark = sprites.size();
                    text.generate(0, -34, "THIS ERASES THE RUN", sprites);
                    text.generate(0, -18, "SAVED ON THE CARTRIDGE", sprites);
                    tint(sprites, mark, bn::sprite_palette_items::text_cyan);

                    text.set_left_alignment();
                    text.generate(-40, 14, "NO, GO BACK", sprites);
                    text.generate(-40, 38, "YES, ERASE IT", sprites);

                    text.set_center_alignment();
                    mark = sprites.size();
                    text.generate(0, 68, "HIGH SCORES ARE KEPT", sprites);
                    tint(sprites, mark, bn::sprite_palette_items::text_mag);
                }
                else if(where == screen::extras)
                {
                    text.generate(0, layout::title_y, "EXTRAS", sprites);
                    tint(sprites, 0, bn::sprite_palette_items::text_gold);

                    text.set_left_alignment();

                    for(int i = 0; i < extras.size(); ++i)
                    {
                        text.generate(-40, layout::body_top + (i * 18),
                                      extras[i].label, sprites);
                    }

                    text.set_center_alignment();
                    const int mark = sprites.size();
                    text.generate(0, layout::footer_y, "A PICK    B BACK", sprites);
                    tint(sprites, mark, bn::sprite_palette_items::text_mag);
                }
                else if(where == screen::stages)
                {
                    text.generate(0, layout::title_y, "STAGE SELECT", sprites);
                    tint(sprites, 0, bn::sprite_palette_items::text_gold);

                    for(int i = 0; i < stage_rows; ++i)
                    {
                        const int index = stage_top + i;

                        if(index >= unlocked)
                        {
                            break;
                        }

                        text.generate(-100, -40 + (i * 16), stage_label(index),
                                      sprites);

                        // Your fastest clear, in the same units the stage
                        // clock counts down. Blank until you have set one.
                        if(index < save::timed_stages && file.best_time[index])
                        {
                            const int mark = sprites.size();
                            text.generate(62, -40 + (i * 16),
                                          zero_pad(file.best_time[index], 3),
                                          sprites);
                            tint(sprites, mark, bn::sprite_palette_items::text_cyan);
                        }
                    }

                    const int mark = sprites.size();
                    text.generate(0, layout::footer_y,
                                  "A PLAY   B BACK   BEST TIME", sprites);
                    tint(sprites, mark, bn::sprite_palette_items::text_mag);
                }
                else
                {
                    text.generate(0, -70, "CONTROLS", sprites);
                    tint(sprites, 0, bn::sprite_palette_items::text_gold);

                    text.set_left_alignment();
                    text.generate(-92, -48, "PAD    RUN", sprites);
                    text.generate(-92, -32, "A      JUMP", sprites);
                    text.generate(-92, -18, "       HOLD IT TO HOVER", sprites);
                    text.generate(-92, 0,   "B      SOUL FLAME", sprites);
                    text.generate(-92, 14,  "       HOLD IT TO DASH", sprites);

                    // Nothing in the game said which power-ups a hit takes.
                    const int note = sprites.size();
                    text.generate(-92, 38, "A HIT TAKES THE SOUL,", sprites);
                    text.generate(-92, 52, "THEN THE FLAME. NOT DASH.", sprites);
                    tint(sprites, note, bn::sprite_palette_items::text_cyan);

                    text.set_center_alignment();
                    const int mark = sprites.size();
                    text.generate(0, layout::footer_y, "B BACK", sprites);
                    tint(sprites, mark, bn::sprite_palette_items::text_mag);
                }

                dirty = false;
            }

            if(bn::keypad::any_pressed() || bn::keypad::any_held())
            {
                idle = 0;
            }
            else if(where == screen::main && ++idle >= attract_after)
            {
                result.attract = true;
                release();
                return result;
            }

            logo_l.set_visible(where == screen::main);
            logo_r.set_visible(where == screen::main);

            const int bob = (frame >> 4) & 1;

            if(where == screen::main)
            {
                cursor.set_visible(true);
                cursor.set_position(-72, -6 + (choice * 14) + bob);
            }
            else if(where == screen::extras)
            {
                cursor.set_visible(true);
                cursor.set_position(-58, layout::body_top + 2 + (extra_pick * 18) + bob);
            }
            else if(where == screen::confirm)
            {
                cursor.set_visible(true);
                cursor.set_position(-58, 16 + (erase_pick * 24) + bob);
            }
            else if(where == screen::stages)
            {
                cursor.set_visible(true);
                cursor.set_position(-108, -42 + ((stage_pick - stage_top) * 16) + bob);
            }
            else
            {
                cursor.set_visible(false);
            }

            host.set_visible(false);

            if((frame % 24) == 0)
            {
                const int f = (frame / 24) & 1;
                cursor.set_tiles(bn::sprite_items::luv.tiles_item().create_tiles(f));
                host.set_tiles(bn::sprite_items::luv.tiles_item().create_tiles(8 + f));
            }

            // Souls rise and wrap, so the screen is never quite still.
            for(int i = 0; i < drifters; ++i)
            {
                soul_y[i] -= bn::fixed(0.25) + (i * bn::fixed(0.05));

                if(soul_y[i] < -76)
                {
                    soul_y[i] = 76;
                }

                souls[i].set_position(-96 + (i * 46) + bn::lut_sin((frame * 6 + i * 300) & 2047) * 5,
                                      soul_y[i]);
            }

            // Every other screen in the game ignores its first few frames of
            // input; this one never did, so anything that returned here still
            // holding a press could act on it before the player let go.
            if(frame <= 8)
            {
                bn::core::update();
                continue;
            }

            if(where == screen::main)
            {
                if(bn::keypad::up_pressed())
                {
                    choice = (choice + options.size() - 1) % options.size();
                    audio::sfx_menu();
                }
                else if(bn::keypad::down_pressed())
                {
                    choice = (choice + 1) % options.size();
                    audio::sfx_menu();
                }

                if(bn::keypad::a_pressed() || bn::keypad::start_pressed())
                {
                    const int action = options[choice].action;
                    audio::sfx_menu();

                    if(action == 0)
                    {
                        // One game on the cartridge continues itself; more
                        // than one has to be asked about.
                        if(save::slots_used(file) > 1)
                        {
                            release();
                            const int which = pick_file(text, file, false);

                            if(which < 0)
                            {
                                restore();
                                dirty = true;
                                // Take a frame before looping: `continue`
                                // skips the update at the foot of the loop,
                                // and without one the next pass would read the
                                // same keypad edges again.
                                bn::core::update();
                                continue;
                            }

                            save::choose(file, which);
                            save::store(file);
                        }

                        const save::progress& p = save::slot(file);
                        result.level_index = p.furthest_level;
                        result.run.lives = bn::max<int>(p.lives, 1);
                        result.run.souls = p.souls;
                        arm();
                        release();
                        return result;
                    }

                    if(action == 1)
                    {
                        // Always ask which file: starting a new game is how a
                        // second person gets one of their own.
                        release();
                        const int which = pick_file(text, file, true);

                        if(which < 0)
                        {
                            restore();
                            dirty = true;
                            bn::core::update();
                            continue;
                        }

                        save::choose(file, which);
                        save::store(file);

                        if(save::slot(file).used)
                        {
                            // There is a run on the cartridge. Erasing it
                            // should never be one button press away.
                            where = screen::confirm;
                            erase_pick = 0;
                            restore();
                            dirty = true;
                        }
                        else
                        {
                            save::wipe();
                            file = save::load();

                            // Claim the slot now rather than when a stage is
                            // first cleared, or a player who dies in 1-1 finds
                            // their file still reading EMPTY.
                            save::slot(file).used = 1;
                            save::store(file);
                            result.level_index = 0;
                            arm();
                            return result;
                        }
                    }
                    else

                    if(action == 6)
                    {
                        // Two seats, one pad, one life each side of the turn.
                        result.two_player = true;
                        result.level_index = 0;
                        arm();
                        release();
                        return result;
                    }

                    if(action == 7)
                    {
                        release();
                        const int opened = enter_code(text);

                        if(opened >= 0)
                        {
                            result.level_index = opened;
                            result.run.lives = tune::start_lives;

                            // A code is proof enough: stage select opens up to
                            // there too, so it need not be typed twice.
                            save::progress& p = save::slot(file);
                            p.furthest_level = uint16_t(bn::max<int>(
                                        p.furthest_level,
                                        bn::min(opened, story_count - 1)));
                            p.used = 1;
                            save::store(file);
                            arm();
                            return result;
                        }

                        restore();
                    }
                    else if(action == 2)
                    {
                        where = screen::stages;
                        stage_pick = save::slot(file).furthest_level;
                        stage_top = bn::clamp(stage_pick - (stage_rows / 2), 0,
                                              bn::max(unlocked - stage_rows, 0));
                    }
                    else if(action == 8)
                    {
                        where = screen::extras;
                        extra_pick = 0;
                    }

                    dirty = true;
                }
            }
            else if(where == screen::confirm)
            {
                if(bn::keypad::up_pressed() || bn::keypad::down_pressed())
                {
                    erase_pick ^= 1;
                    audio::sfx_menu();
                }

                if(bn::keypad::a_pressed() || bn::keypad::start_pressed())
                {
                    audio::sfx_menu();

                    if(erase_pick == 1)
                    {
                        save::wipe();
                        file = save::load();
                        save::slot(file).used = 1;
                        save::store(file);
                        result.level_index = 0;
                        result.run.lives = tune::start_lives;
                        arm();
                        release();
                        return result;
                    }

                    where = screen::main;
                    dirty = true;
                }

                if(bn::keypad::b_pressed())
                {
                    where = screen::main;
                    audio::sfx_menu();
                    dirty = true;
                }
            }
            else if(where == screen::extras)
            {
                if(bn::keypad::up_pressed())
                {
                    extra_pick = (extra_pick + extras.size() - 1) % extras.size();
                    audio::sfx_menu();
                }
                else if(bn::keypad::down_pressed())
                {
                    extra_pick = (extra_pick + 1) % extras.size();
                    audio::sfx_menu();
                }

                if(bn::keypad::a_pressed() || bn::keypad::start_pressed())
                {
                    const int action = extras[extra_pick].action;
                    audio::sfx_menu();

                    if(action == 11)
                    {
                        release();
                        const int lives = enter_cheat(text);

                        if(lives)
                        {
                            cheat_lives = lives;
                        }

                        restore();
                        dirty = true;
                    }
                    else if(action == 10)
                    {
                        // All eight sins, one after another, no continues.
                        result.boss_rush = true;
                        result.level_index = boss_rush_stages[0];
                        result.run.lives = tune::start_lives;
                        result.run.continues = 0;
                        arm();
                        release();
                        return result;
                    }
                    else if(action == 3)
                    {
                        where = screen::controls;
                    }
                    else
                    {
                        // These run their own screen and come straight back,
                        // so the menu just redraws itself afterwards.
                        release();

                        if(action == 4)
                        {
                            show_high_scores(text, file);
                        }
                        else if(action == 9)
                        {
                            show_sound_test(text);
                        }
                        else
                        {
                            show_credits(text);
                        }

                        restore();
                    }

                    dirty = true;
                }

                if(bn::keypad::b_pressed())
                {
                    where = screen::main;
                    audio::sfx_menu();
                    dirty = true;
                }
            }
            else if(where == screen::stages)
            {
                if(bn::keypad::up_pressed() && stage_pick > 0)
                {
                    --stage_pick;
                    audio::sfx_menu();
                }
                else if(bn::keypad::down_pressed() && stage_pick < unlocked - 1)
                {
                    ++stage_pick;
                    audio::sfx_menu();
                }

                // Only the list scrolling changes the text; the cursor is a
                // sprite and moves on its own.
                const int was_top = stage_top;
                stage_top = bn::clamp(stage_top, bn::max(stage_pick - stage_rows + 1, 0),
                                      stage_pick);
                dirty = dirty || stage_top != was_top;

                if(bn::keypad::a_pressed() || bn::keypad::start_pressed())
                {
                    audio::sfx_menu();
                    result.level_index = stage_pick;
                    result.run.lives = bn::max<int>(save::slot(file).lives,
                                                    tune::start_lives);
                    result.run.souls = save::slot(file).souls;
                    arm();
                    release();
                    return result;
                }

                if(bn::keypad::b_pressed())
                {
                    where = screen::main;
                    audio::sfx_menu();
                    dirty = true;
                }
            }
            else if(bn::keypad::b_pressed())
            {
                where = screen::extras;
                audio::sfx_menu();
                dirty = true;
            }

            bn::core::update();
        }
    }
}
