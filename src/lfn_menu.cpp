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

#include "bn_sprite_items_luv.h"
#include "bn_sprite_items_soul_orb.h"
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
        enum class screen : uint8_t { main, stages, extras, controls };

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
        bn::string<32> stage_label(int index)
        {
            bn::string<32> out = bn::format<32>("{}-{}  ", roman(levels[index].world),
                                                (index & 1) + 1);

            for(const char* c = levels[index].name; *c && out.size() < 22; ++c)
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

    menu_result show_menu(bn::sprite_text_generator& text, save::file& file)
    {
        bn::regular_bg_ptr backdrop = make_backdrop(7, backdrop_style::room);

        bn::vector<bn::sprite_ptr, 112> sprites;
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
            host.set_visible(true);
        };

        screen where = screen::main;
        int choice = 0;
        int stage_pick = 0;
        int stage_top = 0;
        bool dirty = true;
        int frame = 0;

        bn::vector<entry, 8> options;
        const bool has_save = file.furthest_level > 0;

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
        bn::vector<entry, 4> extras;
        extras.push_back({"HIGH SCORES", 4});
        extras.push_back({"CREDITS", 5});
        extras.push_back({"CONTROLS", 3});
        int extra_pick = 0;

        // Test builds can reach the hidden rooms from stage select; the
        // shipping game only ever lists the story.
        const int listable = tune::test_invulnerable ? level_count : story_count;
        const int unlocked = bn::min<int>(file.furthest_level + 1, listable);
        audio::play_music(audio::track::title);

        menu_result result;
        result.run.lives = tune::start_lives;

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
                    text.generate(0, -66, "LUV'S FRIGHT NIGHT", sprites);
                    tint(sprites, 0, bn::sprite_palette_items::text_gold);
                    int mark = sprites.size();
                    text.generate(0, -50, "a ghost in bad company", sprites);
                    tint(sprites, mark, bn::sprite_palette_items::text_mag);

                    text.set_left_alignment();

                    for(int i = 0; i < options.size(); ++i)
                    {
                        text.generate(-40, -30 + (i * 16), options[i].label, sprites);
                    }

                    text.set_center_alignment();
                    mark = sprites.size();
                    text.generate(0, 66, bn::format<24>("BEST {}",
                                  zero_pad(int(save::best(file)), 6)), sprites);
                    tint(sprites, mark, bn::sprite_palette_items::text_gold);
                }
                else if(where == screen::extras)
                {
                    text.generate(0, -66, "EXTRAS", sprites);
                    tint(sprites, 0, bn::sprite_palette_items::text_gold);

                    text.set_left_alignment();

                    for(int i = 0; i < extras.size(); ++i)
                    {
                        text.generate(-40, -22 + (i * 20), extras[i].label, sprites);
                    }

                    text.set_center_alignment();
                    const int mark = sprites.size();
                    text.generate(0, 62, "A PICK    B BACK", sprites);
                    tint(sprites, mark, bn::sprite_palette_items::text_mag);
                }
                else if(where == screen::stages)
                {
                    text.generate(0, -66, "STAGE SELECT", sprites);
                    tint(sprites, 0, bn::sprite_palette_items::text_gold);

                    for(int i = 0; i < stage_rows; ++i)
                    {
                        const int index = stage_top + i;

                        if(index >= unlocked)
                        {
                            break;
                        }

                        text.generate(4, -40 + (i * 16), stage_label(index), sprites);
                    }

                    const int mark = sprites.size();
                    text.generate(0, 62, "A PLAY    B BACK", sprites);
                    tint(sprites, mark, bn::sprite_palette_items::text_mag);
                }
                else
                {
                    text.generate(0, -66, "CONTROLS", sprites);
                    tint(sprites, 0, bn::sprite_palette_items::text_gold);

                    text.set_left_alignment();
                    text.generate(-92, -40, "PAD    RUN", sprites);
                    text.generate(-92, -22, "A      JUMP", sprites);
                    text.generate(-92, -6,  "       HOLD IT TO HOVER", sprites);
                    text.generate(-92, 14,  "B      SOUL FLAME", sprites);
                    text.generate(-92, 30,  "       HOLD IT TO DASH", sprites);

                    text.set_center_alignment();
                    const int mark = sprites.size();
                    text.generate(0, 62, "B BACK", sprites);
                    tint(sprites, mark, bn::sprite_palette_items::text_mag);
                }

                dirty = false;
            }

            const int bob = (frame >> 4) & 1;

            if(where == screen::main)
            {
                cursor.set_visible(true);
                cursor.set_position(-58, -32 + (choice * 16) + bob);
            }
            else if(where == screen::extras)
            {
                cursor.set_visible(true);
                cursor.set_position(-58, -24 + (extra_pick * 20) + bob);
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

            host.set_visible(where == screen::main);
            host.set_position(92, 44 - ((frame >> 5) & 1));

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
                        result.level_index = file.furthest_level;
                        result.run.lives = bn::max<int>(file.lives, 1);
                        result.run.souls = file.souls;
                        release();
                        return result;
                    }

                    if(action == 1)
                    {
                        save::wipe();
                        file = save::load();
                        result.level_index = 0;
                        release();
                        return result;
                    }

                    if(action == 6)
                    {
                        // Two seats, one pad, one life each side of the turn.
                        result.two_player = true;
                        result.level_index = 0;
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
                            file.furthest_level = uint16_t(bn::max<int>(
                                        file.furthest_level,
                                        bn::min(opened, story_count - 1)));
                            save::store(file);
                            return result;
                        }

                        restore();
                    }
                    else if(action == 2)
                    {
                        where = screen::stages;
                        stage_pick = file.furthest_level;
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

                    if(action == 3)
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
                    result.run.lives = bn::max<int>(file.lives, tune::start_lives);
                    result.run.souls = file.souls;
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
