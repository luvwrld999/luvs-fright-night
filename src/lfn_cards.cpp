#include "lfn_cards.h"

#include "lfn_code.h"

#include "bn_bg_palettes.h"
#include "bn_core.h"
#include "bn_format.h"
#include "bn_keypad.h"
#include "bn_math.h"
#include "bn_optional.h"
#include "bn_regular_bg_ptr.h"
#include "bn_sprite_palette_ptr.h"
#include "bn_sprite_palettes.h"
#include "bn_sprite_ptr.h"
#include "bn_sprite_tiles_ptr.h"
#include "bn_string.h"
#include "bn_string_view.h"
#include "bn_vector.h"

#include "bn_sprite_items_hud_halo.h"
#include "bn_sprite_items_luv.h"
#include "bn_sprite_items_soul_orb.h"
#include "bn_sprite_palette_items_text_cyan.h"
#include "bn_sprite_palette_items_text_gold.h"
#include "bn_sprite_palette_items_text_mag.h"

#include "lfn_audio.h"
#include "lfn_backdrop.h"
#include "lfn_hud.h"
#include "lfn_levels.h"
#include "lfn_tune.h"

namespace lfn
{
    namespace
    {
        constexpr int card_frames = 190;
        constexpr int drifters = 6;

        // The sin each world belongs to, and what it is called in English.
        struct sin_name
        {
            const char* latin;
            const char* plain;
        };

        constexpr sin_name sins[] = {
            {"SUPERBIA", "PRIDE"},   {"AVARITIA", "GREED"},
            {"LUXURIA",  "LUST"},    {"INVIDIA",  "ENVY"},
            {"GULA",     "GLUTTONY"},{"IRA",      "WRATH"},
            {"ACEDIA",   "SLOTH"},   {"HADES",    "THE END OF IT"},
        };

        /**
         * What each sin has to say for itself, shown once on the way into its
         * world. Three short lines: a GBA screen at this font size holds about
         * twenty-six characters, and nobody reads a wall of text on a card
         * that dismisses itself.
         */
        struct sin_words { const char* a; const char* b; const char* c; };

        constexpr sin_words words[] = {
            {"IT BUILT A MIRROR",     "FOR EVERY WALL, AND CALLED",
             "THE REFLECTION WORSHIP"},
            {"IT COUNTED EVERYTHING",  "IT HAD. TWICE.",
             "THEN IT ASKED FOR YOURS"},
            {"EVERY LANTERN HERE",     "IS A HEART, STILL WARM,",
             "STILL ASKING"},
            {"THE WATER IS GREEN",     "BECAUSE IT HAS BEEN",
             "LOOKING AT YOU"},
            {"THE TABLE WAS SET",      "FOR ONE.",
             "IT ATE THE TABLE"},
            {"IT HAS BEEN SHOUTING",   "SO LONG THAT THE ROCK",
             "LEARNED THE WORDS"},
            {"NOTHING MOVES HERE.",    "NOTHING HAS TO.",
             "YOU WILL STOP TOO"},
            {"THE LAST DOOR",          "IS NOT LOCKED.",
             "THAT IS THE TRICK OF IT"},
        };

        /** Recolour everything generated after `from`, whatever the vector size. */
        template<int Size>
        void tint(bn::vector<bn::sprite_ptr, Size>& sprites, int from,
                  const bn::sprite_palette_item& palette)
        {
            for(int i = from; i < sprites.size(); ++i)
            {
                sprites[i].set_palette(palette);
            }
        }

        /**
         * Let go of everything a screen just used.
         *
         * Butano reclaims sprite tiles on the next update, not the moment a
         * sprite is destroyed. Without a frame in between, whatever is built
         * next is allocated on top of the screen that has only just left.
         */
        void settle()
        {
            // Two frames: one to commit the destruction, one for the free list
            // to actually give the VRAM back.
            bn::core::update();
            bn::core::update();
        }

        [[nodiscard]] bool skipped()
        {
            return bn::keypad::a_pressed() || bn::keypad::start_pressed() ||
                   bn::keypad::b_pressed();
        }
    }

    pause_result run_pause(bn::sprite_text_generator& text)
    {
        // Sink the whole scene into the dark so the menu reads over it, then
        // pull the menu's own palettes back out of the fade.
        constexpr bn::fixed dim = 0.62;
        bn::bg_palettes::set_fade(bn::color(0, 0, 0), dim);
        bn::sprite_palettes::set_fade(bn::color(0, 0, 0), dim);

        bn::vector<bn::sprite_ptr, 40> sprites;
        int choice = 0;
        bool dirty = true;
        int frame = 0;

        audio::sfx_menu();

        while(true)
        {
            ++frame;

            if(dirty)
            {
                sprites.clear();
                text.set_center_alignment();
                text.generate(0, -34, "PAUSED", sprites);
                tint(sprites, 0, bn::sprite_palette_items::text_gold);

                const int mark = sprites.size();
                text.generate(0, -4, choice == 0 ? "> RESUME" : "  RESUME", sprites);
                text.generate(0, 16, choice == 1 ? "> QUIT TO MENU"
                                                 : "  QUIT TO MENU", sprites);
                tint(sprites, mark, bn::sprite_palette_items::text_cyan);

                for(bn::sprite_ptr& sprite : sprites)
                {
                    bn::sprite_palette_ptr palette = sprite.palette();
                    palette.set_fade_intensity(0);
                }

                dirty = false;
            }

            if(bn::keypad::up_pressed() || bn::keypad::down_pressed())
            {
                choice = 1 - choice;
                audio::sfx_menu();
                dirty = true;      // this menu marks its choice in the text
            }

            // The button that opened the pause is still down on the first
            // frames; without this the menu closes the instant it appears.
            const bool listening = frame > 8;

            const auto leave = [&](pause_result r)
            {
                bn::bg_palettes::set_fade_intensity(0);
                bn::sprite_palettes::set_fade_intensity(0);
                audio::sfx_menu();
                return r;
            };

            if(listening && (bn::keypad::b_pressed() || bn::keypad::start_pressed()))
            {
                return leave(pause_result::resume);
            }

            if(listening && bn::keypad::a_pressed())
            {
                return leave(choice == 0 ? pause_result::resume : pause_result::quit);
            }

            bn::core::update();
        }
    }

    void show_game_over(bn::sprite_text_generator& text, const run_state& run,
                        const save::file& file)
    {
        bn::regular_bg_ptr backdrop = make_backdrop(7, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 48> sprites;

        text.set_center_alignment();
        text.generate(0, -40, "GAME OVER", sprites);
        tint(sprites, 0, bn::sprite_palette_items::text_mag);

        int mark = sprites.size();
        text.generate(0, -10, "THE DARK KEPT YOU", sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_cyan);

        mark = sprites.size();
        text.generate(0, 20, bn::format<28>("SCORE {}", zero_pad(run.score, 6)),
                      sprites);
        text.generate(0, 38, bn::format<28>("BEST  {}",
                      zero_pad(int(save::best(file)), 6)), sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_gold);

        // Luv, drifting down and out.
        bn::sprite_ptr luv = bn::sprite_items::luv.create_sprite(-84, 30);
        bn::fixed y = 30;

        for(int frame = 0; frame < 420; ++frame)
        {
            y += bn::fixed(0.12);
            luv.set_position(-84, y);

            if((frame % 24) == 0)
            {
                luv.set_tiles(bn::sprite_items::luv.tiles_item()
                              .create_tiles(frame & 16 ? 12 : 7));
            }

            if(frame > 90 && skipped())
            {
                break;
            }

            bn::core::update();
        }
    }

    void show_high_scores(bn::sprite_text_generator& text, const save::file& file,
                          int highlight)
    {
        settle();

        {
        bn::regular_bg_ptr backdrop = make_backdrop(7, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 96> sprites;

        text.set_center_alignment();
        text.generate(0, -70, "HIGH SCORES", sprites);
        tint(sprites, 0, bn::sprite_palette_items::text_gold);

        text.set_left_alignment();

        for(int i = 0; i < save::table_size; ++i)
        {
            const save::entry& row = file.table[i];
            const int mark = sprites.size();
            const bn::string<4> name = bn::string<4>(row.name, save::name_length);

            text.generate(-64, -48 + (i * 15),
                          bn::format<24>("{} {}  {}", i + 1, name,
                                         zero_pad(int(row.score), 6)), sprites);

            // The row you just earned is the one worth looking at.
            tint(sprites, mark, i == highlight ? bn::sprite_palette_items::text_mag
                                               : bn::sprite_palette_items::text_cyan);
        }

        text.set_center_alignment();
        const int mark = sprites.size();
        text.generate(0, 70, "B BACK", sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_mag);

        for(int frame = 0; frame < 1200; ++frame)
        {
            if(frame > 12 && skipped())
            {
                break;
            }

            bn::core::update();
        }
        }

        settle();
    }

    void show_credits(bn::sprite_text_generator& text)
    {
        settle();

        {
        bn::regular_bg_ptr backdrop = make_backdrop(0, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 96> sprites;

        text.set_center_alignment();
        text.generate(0, -68, "CREDITS", sprites);
        tint(sprites, 0, bn::sprite_palette_items::text_gold);

        int mark = sprites.size();
        text.generate(0, -44, "PUBLISHER", sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_cyan);

        mark = sprites.size();
        text.generate(0, -28, "RETRO RUMBLE", sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_gold);

        mark = sprites.size();
        text.generate(0, -4, "DEVELOPER", sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_cyan);

        mark = sprites.size();
        text.generate(0, 12, "LUVWRLD", sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_gold);

        mark = sprites.size();
        text.generate(0, 38, "999", sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_mag);

        mark = sprites.size();
        text.generate(0, 70, "B BACK", sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_mag);

        bn::sprite_ptr luv = bn::sprite_items::luv.create_sprite(-88, 20);

        for(int frame = 0; frame < 1800; ++frame)
        {
            luv.set_position(-88, 20 - ((frame >> 4) & 1));

            if((frame % 26) == 0)
            {
                luv.set_tiles(bn::sprite_items::luv.tiles_item()
                              .create_tiles((frame / 26) & 1));
            }

            if(frame > 12 && skipped())
            {
                break;
            }

            bn::core::update();
        }
        }

        settle();
    }

    int enter_initials(bn::sprite_text_generator& text, save::file& file, int score,
                       int player)
    {
        settle();

        char name[save::name_length] = {'A', 'A', 'A'};
        int slot = 0;

        {
        bn::regular_bg_ptr backdrop = make_backdrop(7, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 64> fixed_text;
        bn::vector<bn::sprite_ptr, 32> entry_text;

        text.set_center_alignment();

        if(player)
        {
            text.generate(0, -74, bn::format<16>("PLAYER {}", player), fixed_text);
            tint(fixed_text, 0, bn::sprite_palette_items::text_mag);
        }

        int head = fixed_text.size();
        text.generate(0, -56, "YOU MADE THE BOARD", fixed_text);
        tint(fixed_text, head, bn::sprite_palette_items::text_gold);

        int mark = fixed_text.size();
        text.generate(0, -36, bn::format<24>("SCORE {}", zero_pad(score, 6)),
                      fixed_text);
        tint(fixed_text, mark, bn::sprite_palette_items::text_cyan);

        mark = fixed_text.size();
        text.generate(0, 46, "PAD PICK    A DONE", fixed_text);
        tint(fixed_text, mark, bn::sprite_palette_items::text_mag);

        bool dirty = true;
        int frame = 0;

        while(true)
        {
            ++frame;

            if(dirty)
            {
                entry_text.clear();
                text.set_center_alignment();

                // The slot being edited is bracketed, so it reads without a
                // blinking cursor to animate.
                bn::string<16> line;

                for(int i = 0; i < save::name_length; ++i)
                {
                    line.push_back(i == slot ? '[' : ' ');
                    line.push_back(name[i]);
                    line.push_back(i == slot ? ']' : ' ');
                }

                text.generate(0, 4, line, entry_text);

                for(bn::sprite_ptr& sprite : entry_text)
                {
                    sprite.set_palette(bn::sprite_palette_items::text_gold);
                }

                dirty = false;
            }

            if(frame > 10)
            {
                if(bn::keypad::up_pressed())
                {
                    name[slot] = name[slot] == 'Z' ? '0'
                               : (name[slot] == '9' ? 'A' : char(name[slot] + 1));
                    audio::sfx_menu();
                    dirty = true;
                }
                else if(bn::keypad::down_pressed())
                {
                    name[slot] = name[slot] == 'A' ? '9'
                               : (name[slot] == '0' ? 'Z' : char(name[slot] - 1));
                    audio::sfx_menu();
                    dirty = true;
                }

                if(bn::keypad::right_pressed() && slot < save::name_length - 1)
                {
                    ++slot;
                    audio::sfx_menu();
                    dirty = true;
                }
                else if(bn::keypad::left_pressed() && slot > 0)
                {
                    --slot;
                    audio::sfx_menu();
                    dirty = true;
                }

                if(bn::keypad::a_pressed() || bn::keypad::start_pressed())
                {
                    audio::sfx_one_up();
                    break;
                }
            }

            bn::core::update();
        }
        }

        settle();
        save::submit(file, name, score);

        for(int i = 0; i < save::table_size; ++i)
        {
            if(uint32_t(score) == file.table[i].score &&
               file.table[i].name[0] == name[0] && file.table[i].name[1] == name[1])
            {
                return i;
            }
        }

        return 0;
    }

    void show_sound_test(bn::sprite_text_generator& text)
    {
        settle();

        // Indices match tools/build_levels.py's MUSIC table.
        static const char* const names[] = {
            "TITLE", "I    SUPERBIA", "II   AVARITIA", "III  LUXURIA",
            "IV   INVIDIA", "V    GULA", "VI   IRA", "VII  ACEDIA",
            "VIII HADES", "BOSS", "VICTORY", "GAME OVER",
        };
        constexpr int count = int(sizeof(names) / sizeof(names[0]));
        constexpr int rows = 6;

        {
        bn::regular_bg_ptr backdrop = make_backdrop(7, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 96> sprites;

        int pick = 0;
        int top = 0;
        int playing = -1;
        bool dirty = true;
        int frame = 0;

        bn::sprite_ptr cursor = bn::sprite_items::luv.create_sprite(-96, 0);

        while(true)
        {
            ++frame;

            if(dirty)
            {
                sprites.clear();
                text.set_center_alignment();
                text.generate(0, -70, "SOUND TEST", sprites);
                tint(sprites, 0, bn::sprite_palette_items::text_gold);

                text.set_left_alignment();

                for(int i = 0; i < rows && top + i < count; ++i)
                {
                    const int index = top + i;
                    const int mark = sprites.size();
                    text.generate(-80, -44 + (i * 18), names[index], sprites);

                    // The one you are hearing stays lit while you browse past it.
                    tint(sprites, mark, index == playing
                                        ? bn::sprite_palette_items::text_gold
                                        : bn::sprite_palette_items::text_cyan);
                }

                text.set_center_alignment();
                const int mark = sprites.size();
                text.generate(0, 68, "A PLAY   B BACK", sprites);
                tint(sprites, mark, bn::sprite_palette_items::text_mag);
                dirty = false;
            }

            cursor.set_position(-96, -42 + ((pick - top) * 18) + ((frame >> 4) & 1));

            if((frame % 26) == 0)
            {
                cursor.set_tiles(bn::sprite_items::luv.tiles_item()
                                 .create_tiles((frame / 26) & 1));
            }

            if(frame > 10)
            {
                if(bn::keypad::up_pressed() && pick > 0)
                {
                    --pick;
                    audio::sfx_menu();
                }
                else if(bn::keypad::down_pressed() && pick < count - 1)
                {
                    ++pick;
                    audio::sfx_menu();
                }

                const int was = top;
                top = bn::clamp(top, bn::max(pick - rows + 1, 0), pick);
                dirty = dirty || top != was;

                if(bn::keypad::a_pressed())
                {
                    playing = pick;
                    audio::play_music(pick);
                    dirty = true;
                }

                if(bn::keypad::b_pressed())
                {
                    break;
                }
            }

            bn::core::update();
        }
        }

        settle();
        audio::play_music(audio::track::title);
    }

    bool offer_continue(bn::sprite_text_generator& text, const run_state& run,
                        int player)
    {
        settle();
        bool taken = false;

        {
        bn::regular_bg_ptr backdrop = make_backdrop(7, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 48> sprites;
        bn::vector<bn::sprite_ptr, 8> clock;

        text.set_center_alignment();

        if(player)
        {
            text.generate(0, -70, bn::format<16>("PLAYER {}", player), sprites);
            tint(sprites, 0, bn::sprite_palette_items::text_mag);
        }

        int mark = sprites.size();
        text.generate(0, -46, "CONTINUE?", sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_gold);

        mark = sprites.size();
        text.generate(0, -20, bn::format<24>("{} LEFT AFTER THIS",
                                             run.continues - 1), sprites);
        text.generate(0, 44, "A YES     B NO", sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_cyan);

        bn::sprite_ptr luv = bn::sprite_items::luv.create_sprite(0, 68);
        int shown = -1;

        for(int frame = 0; frame < tune::continue_seconds * 60; ++frame)
        {
            const int left = tune::continue_seconds - (frame / 60);

            if(left != shown)
            {
                // The count is the whole tension of the screen, so it gets
                // rebuilt only when the digit actually changes.
                shown = left;
                clock.clear();
                text.set_center_alignment();
                text.generate(0, 12, bn::format<4>("{}", left), clock);

                for(bn::sprite_ptr& sprite : clock)
                {
                    sprite.set_palette(left <= 3
                                       ? bn::sprite_palette_items::text_mag
                                       : bn::sprite_palette_items::text_gold);
                }

                audio::sfx_menu();
            }

            luv.set_position(0, 68 - ((frame >> 4) & 1));

            if(frame > 12)
            {
                if(bn::keypad::a_pressed() || bn::keypad::start_pressed())
                {
                    audio::sfx_one_up();
                    taken = true;
                    break;
                }

                if(bn::keypad::b_pressed())
                {
                    break;
                }
            }

            bn::core::update();
        }
        }

        settle();
        return taken;
    }

    void show_player_card(bn::sprite_text_generator& text, int player,
                          const run_state& run)
    {
        settle();

        {
        bn::regular_bg_ptr backdrop = make_backdrop(0, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 32> sprites;

        text.set_center_alignment();
        text.generate(0, -24, bn::format<16>("PLAYER {}", player), sprites);
        tint(sprites, 0, bn::sprite_palette_items::text_gold);

        int mark = sprites.size();
        text.generate(0, 0, bn::format<24>("{} LIVES LEFT", bn::max(run.lives, 0)),
                      sprites);
        text.generate(0, 20, bn::format<24>("SCORE {}", zero_pad(run.score, 6)),
                      sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_cyan);

        bn::sprite_ptr luv = bn::sprite_items::luv.create_sprite(0, 52);

        for(int frame = 0; frame < 150; ++frame)
        {
            luv.set_position(0, 52 - ((frame >> 4) & 1));

            if(frame > 20 && skipped())
            {
                break;
            }

            bn::core::update();
        }
        }

        settle();
    }

    int enter_code(bn::sprite_text_generator& text)
    {
        settle();

        const char* letters = code::alphabet();
        int pick[code::length] = {0, 0, 0, 0};
        int slot = 0;
        int found = -1;

        {
        bn::regular_bg_ptr backdrop = make_backdrop(7, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 64> fixed_text;
        bn::vector<bn::sprite_ptr, 32> entry_text;

        text.set_center_alignment();
        text.generate(0, -60, "LEVEL CODE", fixed_text);
        tint(fixed_text, 0, bn::sprite_palette_items::text_gold);

        int mark = fixed_text.size();
        text.generate(0, 42, "PAD PICK    A ENTER", fixed_text);
        text.generate(0, 60, "B BACK", fixed_text);
        tint(fixed_text, mark, bn::sprite_palette_items::text_mag);

        bn::vector<bn::sprite_ptr, 16> answer;
        bool dirty = true;
        int shout = 0;
        int frame = 0;

        while(true)
        {
            ++frame;

            if(dirty)
            {
                entry_text.clear();
                text.set_center_alignment();

                bn::string<20> line;

                for(int i = 0; i < code::length; ++i)
                {
                    line.push_back(i == slot ? '[' : ' ');
                    line.push_back(letters[pick[i]]);
                    line.push_back(i == slot ? ']' : ' ');
                }

                text.generate(0, -14, line, entry_text);

                for(bn::sprite_ptr& sprite : entry_text)
                {
                    sprite.set_palette(bn::sprite_palette_items::text_gold);
                }

                dirty = false;
            }

            if(shout > 0 && --shout == 0)
            {
                answer.clear();
            }

            if(frame > 10)
            {
                if(bn::keypad::up_pressed())
                {
                    pick[slot] = (pick[slot] + 1) & 0xF;
                    audio::sfx_menu();
                    dirty = true;
                }
                else if(bn::keypad::down_pressed())
                {
                    pick[slot] = (pick[slot] + 15) & 0xF;
                    audio::sfx_menu();
                    dirty = true;
                }

                if(bn::keypad::right_pressed() && slot < code::length - 1)
                {
                    ++slot;
                    audio::sfx_menu();
                    dirty = true;
                }
                else if(bn::keypad::left_pressed() && slot > 0)
                {
                    --slot;
                    audio::sfx_menu();
                    dirty = true;
                }

                if(bn::keypad::b_pressed())
                {
                    break;
                }

                if(bn::keypad::a_pressed() || bn::keypad::start_pressed())
                {
                    char typed[code::length];

                    for(int i = 0; i < code::length; ++i)
                    {
                        typed[i] = letters[pick[i]];
                    }

                    const int level = code::to_level(typed);
                    answer.clear();
                    text.set_center_alignment();

                    if(level >= 0)
                    {
                        audio::sfx_one_up();
                        text.generate(0, 14, levels[level].name, answer);

                        for(bn::sprite_ptr& sprite : answer)
                        {
                            sprite.set_palette(bn::sprite_palette_items::text_cyan);
                        }

                        // Let the name land before the stage takes over.
                        for(int hold = 0; hold < 90; ++hold)
                        {
                            bn::core::update();
                        }

                        found = level;
                        break;
                    }

                    audio::sfx_hurt();
                    text.generate(0, 14, "NO SUCH PLACE", answer);

                    for(bn::sprite_ptr& sprite : answer)
                    {
                        sprite.set_palette(bn::sprite_palette_items::text_mag);
                    }

                    shout = 90;
                }
            }

            bn::core::update();
        }
        }

        settle();
        return found;
    }

    void show_two_player_result(bn::sprite_text_generator& text,
                                const run_state& one, const run_state& two)
    {
        settle();

        {
        bn::regular_bg_ptr backdrop = make_backdrop(7, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 64> sprites;

        text.set_center_alignment();
        text.generate(0, -56, "GAME OVER", sprites);
        tint(sprites, 0, bn::sprite_palette_items::text_gold);

        int mark = sprites.size();
        text.generate(0, -20, bn::format<24>("PLAYER 1  {}", zero_pad(one.score, 6)),
                      sprites);
        tint(sprites, mark, one.score >= two.score
                          ? bn::sprite_palette_items::text_gold
                          : bn::sprite_palette_items::text_cyan);

        mark = sprites.size();
        text.generate(0, 2, bn::format<24>("PLAYER 2  {}", zero_pad(two.score, 6)),
                      sprites);
        tint(sprites, mark, two.score >= one.score
                          ? bn::sprite_palette_items::text_gold
                          : bn::sprite_palette_items::text_cyan);

        mark = sprites.size();
        text.generate(0, 34, one.score == two.score ? "A DEAD HEAT"
                     : (one.score > two.score ? "PLAYER 1 WINS" : "PLAYER 2 WINS"),
                     sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_mag);

        for(int frame = 0; frame < 600; ++frame)
        {
            if(frame > 20 && skipped())
            {
                break;
            }

            bn::core::update();
        }
        }

        settle();
    }

    void show_world_story(bn::sprite_text_generator& text, int world)
    {
        settle();
        const int which = bn::clamp(world, 0, 7);

        {
        bn::regular_bg_ptr backdrop = make_backdrop(which, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 64> sprites;

        text.set_center_alignment();
        text.generate(0, -60, sins[which].latin, sprites);
        tint(sprites, 0, bn::sprite_palette_items::text_mag);

        // The lines arrive one at a time. Read at the speed it is spoken.
        const char* const lines[] = {
            words[which].a, words[which].b, words[which].c,
        };

        int shown = 0;

        for(int frame = 0; frame < 400; ++frame)
        {
            if(shown < 3 && frame == 30 + (shown * 55))
            {
                const int mark = sprites.size();
                text.generate(0, -16 + (shown * 20), lines[shown], sprites);
                tint(sprites, mark, bn::sprite_palette_items::text_cyan);
                ++shown;
                audio::sfx_menu();
            }

            if(frame > 20 && skipped())
            {
                break;
            }

            bn::core::update();
        }
        }

        settle();
    }

    void show_world_card(bn::sprite_text_generator& text, int stage_index,
                         const run_state& run, int player)
    {
        settle();

        const level_data& data = levels[stage_index];
        const int world = data.world;

        {
        bn::regular_bg_ptr backdrop = make_backdrop(world, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 64> sprites;

        text.set_center_alignment();

        if(player)
        {
            text.generate(0, -68, bn::format<16>("PLAYER {}", player), sprites);
            tint(sprites, 0, bn::sprite_palette_items::text_mag);
        }

        int head = sprites.size();
        text.generate(0, -50, bn::format<24>("WORLD {}", roman(world)), sprites);
        tint(sprites, head, bn::sprite_palette_items::text_gold);

        int mark = sprites.size();
        text.generate(0, -30, sins[world].latin, sprites);
        text.generate(0, -14, bn::format<24>("the sin of {}", sins[world].plain),
                      sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_mag);

        mark = sprites.size();

        if(data.boss)
        {
            text.generate(0, 16, "IT IS WAITING FOR YOU", sprites);
        }
        else
        {
            text.generate(0, 16, data.name, sprites);
        }

        tint(sprites, mark, bn::sprite_palette_items::text_cyan);

        // The code that comes back here, so progress survives a dead battery.
        mark = sprites.size();
        text.generate(0, 70, bn::format<16>("CODE {}", code::for_level(stage_index)),
                      sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_gold);

        // Luv, with the lives he is carrying in.
        bn::sprite_ptr luv = bn::sprite_items::luv.create_sprite(-24, 48);
        bn::vector<bn::sprite_ptr, 8> tally;
        text.generate(6, 46, bn::format<8>("x {}", bn::max(run.lives, 0)), tally);

        for(int frame = 0; frame < card_frames; ++frame)
        {
            if(frame > 20 && skipped())
            {
                break;
            }

            luv.set_position(-24, 48 - ((frame >> 4) & 1));

            if((frame % 26) == 0)
            {
                luv.set_tiles(bn::sprite_items::luv.tiles_item()
                              .create_tiles((frame / 26) & 1));
            }

            bn::core::update();
        }
        }

        settle();
    }

    void show_ending(bn::sprite_text_generator& text, const run_state& run,
                     const save::file& file)
    {
        bn::regular_bg_ptr backdrop = make_backdrop(0, backdrop_style::field);
        audio::play_music(audio::track::victory);

        // Luv rises through a column of souls going the same way.
        bn::sprite_ptr luv = bn::sprite_items::luv.create_sprite(-78, 70);
        bn::vector<bn::sprite_ptr, drifters> souls;
        bn::fixed soul_y[drifters];

        for(int i = 0; i < drifters; ++i)
        {
            souls.push_back(bn::sprite_items::soul_orb.create_sprite(
                        -50 + (i * 30), 80 - (i * 26)));
            soul_y[i] = 80 - (i * 26);
        }

        struct panel
        {
            int at;
            int y;
            const char* line;
        };

        constexpr panel panels[] = {
            {40,  -60, "THE SEVEN ARE UNDONE"},
            {150, -42, "AND HADES KEPT NOTHING"},
            {270, -18, "LUV GOES UP"},
            {390,   6, "HORNS AND ALL"},
        };

        bn::vector<bn::sprite_ptr, 64> sprites;
        bn::vector<bn::sprite_ptr, 32> tail;
        bn::fixed luv_y = 70;
        int shown = 0;

        text.set_center_alignment();

        for(int frame = 0; frame < 900; ++frame)
        {
            if(shown < 4 && frame >= panels[shown].at)
            {
                const int mark = sprites.size();
                text.generate(0, panels[shown].y, panels[shown].line, sprites);
                tint(sprites, mark, shown < 2 ? bn::sprite_palette_items::text_mag
                                              : bn::sprite_palette_items::text_gold);
                ++shown;
                audio::sfx_menu();
            }

            if(frame == 560)
            {
                text.generate(0, 34, bn::format<28>("SCORE {}", zero_pad(run.score, 6)),
                              tail);
                text.generate(0, 52, int(save::best(file)) <= run.score
                                   ? "A NEW BEST" : "THANKS FOR PLAYING", tail);

                for(bn::sprite_ptr& sprite : tail)
                {
                    sprite.set_palette(bn::sprite_palette_items::text_cyan);
                }
            }

            // Everything drifts upward, Luv slowest of all.
            luv_y -= bn::fixed(0.06);
            // Up the left-hand side, so he never crosses the writing.
            luv.set_position(-78 + bn::lut_sin((frame * 5) & 2047) * 5, luv_y);

            if((frame % 22) == 0)
            {
                luv.set_tiles(bn::sprite_items::luv.tiles_item()
                              .create_tiles(8 + ((frame / 22) & 1)));
            }

            for(int i = 0; i < drifters; ++i)
            {
                soul_y[i] -= bn::fixed(0.3) + (i * bn::fixed(0.04));

                if(soul_y[i] < -80)
                {
                    soul_y[i] = 80;
                }

                souls[i].set_position(-50 + (i * 30) +
                                      bn::lut_sin((frame * 7 + i * 280) & 2047) * 4,
                                      soul_y[i]);
            }

            if(frame > 620 && skipped())
            {
                break;
            }

            bn::core::update();
        }

        audio::stop_music();
    }
}
