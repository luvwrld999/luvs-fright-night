#include "lfn_cards.h"


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
#include "bn_sprite_palette_items_text_green.h"
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

        /**
         * What Luv says back.
         *
         * Every sin addresses him and he had never once answered - described
         * in the opening, then silent for eight worlds. One dry line each, on
         * the card where he is being spoken to.
         */
        constexpr const char* answers[] = {
            "IT CAN KEEP LOOKING",
            "I HAVE NOTHING IT WANTS",
            "I AM NOT WARM ENOUGH",
            "IT CAN HAVE THE HORNS",
            "I AM NOT ON THE MENU",
            "SHOUT AT THE ROCK THEN",
            "I HAVE SOMEWHERE TO BE",
            "THEN SHOW ME IN",
        };

        /** How far down he is, so the descent reads as one. */
        constexpr const char* depth[] = {
            "ONE FLOOR DOWN",   "TWO FLOORS DOWN",  "THREE FLOORS DOWN",
            "FOUR FLOORS DOWN", "FIVE FLOORS DOWN", "SIX FLOORS DOWN",
            "SEVEN FLOORS DOWN", "THE BOTTOM",
        };

        constexpr sin_words words[] = {
            // Three of the eight now answer what Luv is carrying: the halo,
            // both, and the horns. A ghost wearing one of each walks past
            // seven things that only ever managed one.
            {"IT BUILT A MIRROR",     "FOR EVERY WALL, AND IT",
             "LIKES YOUR HALO BEST"},
            {"IT COUNTED EVERYTHING",  "IT HAD. TWICE.",
             "THEN IT ASKED FOR YOURS"},
            {"EVERY LANTERN HERE",     "IS A HEART, STILL WARM,",
             "STILL ASKING"},
            {"THE WATER IS GREEN",     "BECAUSE IT HAS BEEN",
             "LOOKING AT WHAT YOU HAVE"},
            {"THE TABLE WAS SET",      "FOR ONE.",
             "IT ATE THE TABLE"},
            {"IT HAS BEEN SHOUTING",   "SO LONG THAT THE ROCK",
             "LEARNED THE WORDS"},
            {"NOTHING MOVES HERE.",    "NOTHING HAS TO.",
             "YOU WILL STOP TOO"},
            {"THE LAST DOOR IS NOT",   "LOCKED, AND NEVER WAS.",
             "NOT FOR SOMETHING LIKE YOU"},
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

        bn::vector<bn::sprite_ptr, 48> sprites;
        int choice = 0;
        bool dirty = true;
        int frame = 0;
        constexpr int options = 3;

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
                text.generate(0, -10, choice == 0 ? "> RESUME" : "  RESUME",
                              sprites);
                text.generate(0, 8, choice == 1 ? "> RESTART STAGE"
                                                : "  RESTART STAGE", sprites);
                text.generate(0, 26, choice == 2 ? "> QUIT TO MENU"
                                                 : "  QUIT TO MENU", sprites);
                tint(sprites, mark, bn::sprite_palette_items::text_cyan);

                for(bn::sprite_ptr& sprite : sprites)
                {
                    bn::sprite_palette_ptr palette = sprite.palette();
                    palette.set_fade_intensity(0);

                    // In front of the stage, not behind it. Without this the
                    // menu draws at Butano's default priority 3 and the level
                    // layer at 2 covers it, so the words vanished wherever
                    // there happened to be a platform behind them.
                    sprite.set_bg_priority(0);
                    sprite.set_z_order(-200);
                }

                dirty = false;
            }

            if(bn::keypad::up_pressed())
            {
                choice = (choice + options - 1) % options;
                audio::sfx_menu();
                dirty = true;      // this menu marks its choice in the text
            }
            else if(bn::keypad::down_pressed())
            {
                choice = (choice + 1) % options;
                audio::sfx_menu();
                dirty = true;
            }

            // The button that opened the pause is still down on the first
            // frames; without this the menu closes the instant it appears.
            const bool listening = frame > 8;

            const auto leave = [&](pause_result r)
            {
                bn::bg_palettes::set_fade_intensity(0);
                bn::sprite_palettes::set_fade_intensity(0);
                audio::sfx_menu();

                // Spend the frame that carried the press. Returning on the
                // same frame hands the caller a keypad edge that is still
                // live, and quitting to the menu was landing that A on the
                // menu's first row - which is CONTINUE, so the level appeared
                // to restart instead of quitting.
                bn::core::update();
                return r;
            };

            if(listening && (bn::keypad::b_pressed() || bn::keypad::start_pressed()))
            {
                return leave(pause_result::resume);
            }

            if(listening && bn::keypad::a_pressed())
            {
                return leave(choice == 0 ? pause_result::resume
                             : (choice == 1 ? pause_result::restart
                                            : pause_result::quit));
            }

            bn::core::update();
        }
    }

    void show_game_over(bn::sprite_text_generator& text, const run_state& run,
                        const save::file& file)
    {
        bn::regular_bg_ptr backdrop = make_backdrop(backdrop_front, backdrop_style::field);
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
                          int highlight, save::board which, bool attract)
    {
        settle();

        {
        bn::regular_bg_ptr backdrop = make_backdrop(backdrop_front, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 96> sprites;

        save::board showing = which;
        bool dirty = true;

        for(int frame = 0; frame < (attract ? 360 : 2400); ++frame)
        {
            if(dirty)
            {
                sprites.clear();
                text.set_center_alignment();
                text.generate(0, -70, showing == save::board::rush
                              ? "BOSS RUSH SCORES" : "HIGH SCORES", sprites);
                tint(sprites, 0, bn::sprite_palette_items::text_gold);

                text.set_left_alignment();
                const save::entry* table = save::rows(file, showing);

                for(int i = 0; i < save::table_size; ++i)
                {
                    const int mark = sprites.size();
                    const bn::string<4> name = bn::string<4>(table[i].name,
                                                             save::name_length);

                    text.generate(-64, -48 + (i * 15),
                                  bn::format<24>("{} {}  {}", i + 1, name,
                                                 zero_pad(int(table[i].score), 6)),
                                  sprites);

                    // The row you just earned is the one worth looking at, and
                    // only on the board it landed on.
                    const bool lit = i == highlight && showing == which;
                    tint(sprites, mark, lit
                         ? bn::sprite_palette_items::text_mag
                         : bn::sprite_palette_items::text_cyan);
                }

                text.set_center_alignment();
                const int mark = sprites.size();
                text.generate(0, 70, attract ? "PRESS ANYTHING"
                                             : "A OTHER BOARD   B BACK", sprites);
                tint(sprites, mark, bn::sprite_palette_items::text_mag);
                dirty = false;
            }

            if(frame > 12)
            {
                if(attract)
                {
                    if(bn::keypad::any_pressed())
                    {
                        break;
                    }
                }
                else if(bn::keypad::a_pressed() || bn::keypad::left_pressed() ||
                        bn::keypad::right_pressed())
                {
                    showing = showing == save::board::rush ? save::board::story
                                                           : save::board::rush;
                    audio::sfx_menu();
                    dirty = true;
                }
                else if(bn::keypad::b_pressed() || bn::keypad::start_pressed())
                {
                    break;
                }
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
                       int player, save::board which)
    {
        settle();

        char name[save::name_length] = {'A', 'A', 'A'};
        int slot = 0;

        {
        bn::regular_bg_ptr backdrop = make_backdrop(backdrop_front, backdrop_style::field);
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
        save::submit(file, name, score, which);
        const save::entry* table = save::rows(file, which);

        for(int i = 0; i < save::table_size; ++i)
        {
            if(uint32_t(score) == table[i].score &&
               table[i].name[0] == name[0] && table[i].name[1] == name[1])
            {
                return i;
            }
        }

        return 0;
    }

    int pick_file(bn::sprite_text_generator& text, const save::file& data,
                  bool for_new)
    {
        settle();
        int pick = data.active < save::slot_count ? data.active : 0;
        int chosen = -1;

        {
        bn::regular_bg_ptr backdrop = make_backdrop(backdrop_front, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 64> sprites;
        bn::sprite_ptr cursor = bn::sprite_items::luv.create_sprite(-108, 0);

        bool dirty = true;
        int frame = 0;

        while(true)
        {
            ++frame;

            if(dirty)
            {
                sprites.clear();
                text.set_center_alignment();
                text.generate(0, -68, for_new ? "START WHICH FILE" : "WHICH FILE",
                              sprites);
                tint(sprites, 0, bn::sprite_palette_items::text_gold);

                text.set_left_alignment();

                for(int i = 0; i < save::slot_count; ++i)
                {
                    const save::progress& p = data.slots[i];
                    const int mark = sprites.size();

                    const int row = -34 + (i * 24);

                    if(p.used)
                    {
                        // Where they got to, what they are carrying, and how
                        // far through the eight worlds they are - enough for
                        // someone to recognise their own game at a glance.
                        const level_data& where = levels[bn::min<int>(
                                    p.furthest_level, story_count - 1)];
                        text.generate(-92, row,
                                      bn::format<16>("{}  {}-{}", i + 1,
                                                     roman(where.world),
                                                     (p.furthest_level % 3) + 1),
                                      sprites);
                        tint(sprites, mark, bn::sprite_palette_items::text_cyan);

                        const int stat = sprites.size();
                        text.generate(-16, row,
                                      bn::format<24>("x{}   {} SOULS",
                                                     int(p.lives), int(p.souls)),
                                      sprites);
                        tint(sprites, stat, bn::sprite_palette_items::text_gold);

                    }
                    else
                    {
                        text.generate(-92, row,
                                      bn::format<16>("{}  EMPTY", i + 1), sprites);
                        tint(sprites, mark, bn::sprite_palette_items::text_mag);
                    }
                }

                text.set_center_alignment();
                const int mark = sprites.size();
                text.generate(0, 62, "A PICK    B BACK", sprites);
                tint(sprites, mark, bn::sprite_palette_items::text_mag);
                dirty = false;
            }

            cursor.set_position(-108, -32 + (pick * 24) + ((frame >> 4) & 1));

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
                else if(bn::keypad::down_pressed() && pick < save::slot_count - 1)
                {
                    ++pick;
                    audio::sfx_menu();
                }

                if(bn::keypad::a_pressed() || bn::keypad::start_pressed())
                {
                    // Continuing needs a game to continue; starting one does not.
                    if(for_new || data.slots[pick].used)
                    {
                        audio::sfx_menu();
                        chosen = pick;
                        break;
                    }

                    audio::sfx_hurt();
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
        return chosen;
    }

    int enter_cheat(bn::sprite_text_generator& text)
    {
        settle();

        // Up up down down left right A B select start. The screen closes
        // itself after ten seconds either way, so nobody who wandered in by
        // accident is stuck holding a pad they do not know what to do with.
        enum key : uint8_t { k_up, k_down, k_left, k_right, k_a, k_b,
                             k_select, k_start };
        static constexpr uint8_t wanted[] = {
            k_up, k_up, k_down, k_down, k_left, k_right, k_a, k_b,
            k_select, k_start,
        };
        constexpr int wanted_len = int(sizeof(wanted));
        constexpr int timeout = 10 * 60;
        constexpr int b_target = 10;

        int granted = 0;

        {
        bn::regular_bg_ptr backdrop = make_backdrop(backdrop_front, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 64> fixed_text;
        bn::vector<bn::sprite_ptr, 24> progress;
        bn::vector<bn::sprite_ptr, 16> clock;

        text.set_center_alignment();
        text.generate(0, layout::title_y, "CHEAT CODE", fixed_text);
        tint(fixed_text, 0, bn::sprite_palette_items::text_gold);

        int mark = fixed_text.size();
        text.generate(0, -40, "IF YOU KNOW IT,", fixed_text);
        text.generate(0, -22, "PUT IT IN", fixed_text);
        tint(fixed_text, mark, bn::sprite_palette_items::text_cyan);

        int step = 0;
        int b_count = 0;
        int shown_step = -1;
        int shown_left = -1;

        for(int frame = 0; frame < timeout; ++frame)
        {
            const int left = (timeout - frame + 59) / 60;

            if(left != shown_left)
            {
                shown_left = left;
                clock.clear();
                text.set_center_alignment();
                text.generate(0, 44, bn::format<16>("{}", left), clock);

                for(bn::sprite_ptr& sprite : clock)
                {
                    sprite.set_palette(left <= 3
                                       ? bn::sprite_palette_items::text_mag
                                       : bn::sprite_palette_items::text_cyan);
                }
            }

            if(step != shown_step)
            {
                // A row of marks rather than the keys themselves: showing the
                // sequence back would stop it being a thing you have to know.
                shown_step = step;
                progress.clear();
                bn::string<24> bar;

                for(int i = 0; i < wanted_len; ++i)
                {
                    bar.push_back(i < step ? '*' : '.');
                }

                text.set_center_alignment();
                text.generate(0, 12, bar, progress);

                for(bn::sprite_ptr& sprite : progress)
                {
                    sprite.set_palette(bn::sprite_palette_items::text_gold);
                }
            }

            if(frame > 8)
            {
                int pressed = -1;

                if(bn::keypad::up_pressed())          { pressed = k_up; }
                else if(bn::keypad::down_pressed())   { pressed = k_down; }
                else if(bn::keypad::left_pressed())   { pressed = k_left; }
                else if(bn::keypad::right_pressed())  { pressed = k_right; }
                else if(bn::keypad::a_pressed())      { pressed = k_a; }
                else if(bn::keypad::b_pressed())      { pressed = k_b; }
                else if(bn::keypad::select_pressed()) { pressed = k_select; }
                else if(bn::keypad::start_pressed())  { pressed = k_start; }

                if(pressed >= 0)
                {
                    // B is both the eighth key of the sequence and a cheat of
                    // its own, so its tally runs alongside rather than inside
                    // the sequence check.
                    if(pressed == k_b && ++b_count >= b_target)
                    {
                        audio::sfx_cheat();
                        granted = 10;
                        break;
                    }

                    if(pressed == wanted[step])
                    {
                        ++step;
                        audio::sfx_menu();

                        if(step == wanted_len)
                        {
                            audio::sfx_cheat();
                            granted = 99;
                            break;
                        }
                    }
                    else
                    {
                        // Start again from whatever this key could begin.
                        step = pressed == wanted[0] ? 1 : 0;
                        audio::sfx_hurt();
                    }
                }
            }

            bn::core::update();
        }

        if(granted)
        {
            bn::vector<bn::sprite_ptr, 24> said;
            text.set_center_alignment();
            text.generate(0, layout::footer_y, bn::format<24>("{} LIVES", granted),
                          said);

            for(bn::sprite_ptr& sprite : said)
            {
                sprite.set_palette(bn::sprite_palette_items::text_gold);
            }

            for(int hold = 0; hold < 120; ++hold)
            {
                bn::core::update();
            }
        }
        }

        settle();
        return granted;
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
        constexpr int rows = 7;

        {
        bn::regular_bg_ptr backdrop = make_backdrop(backdrop_front, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 96> sprites;

        int pick = 0;
        int top = 0;
        int playing = -1;
        bool dirty = true;
        int frame = 0;

        bn::sprite_ptr cursor = bn::sprite_items::luv.create_sprite(
                    layout::cursor_x, 0);

        while(true)
        {
            ++frame;

            if(dirty)
            {
                sprites.clear();
                text.set_center_alignment();
                text.generate(0, layout::title_y, "SOUND TEST", sprites);
                tint(sprites, 0, bn::sprite_palette_items::text_gold);

                text.set_left_alignment();

                for(int i = 0; i < rows && top + i < count; ++i)
                {
                    const int index = top + i;
                    const int mark = sprites.size();
                    // A mark rather than only a colour: which track is
                    // playing should survive being glanced at.
                    text.generate(layout::list_x, layout::body_top + (i * 17),
                                  bn::format<24>("{} {}",
                                                 index == playing ? '>' : ' ',
                                                 names[index]), sprites);
                    tint(sprites, mark, index == playing
                                        ? bn::sprite_palette_items::text_gold
                                        : bn::sprite_palette_items::text_cyan);
                }

                text.set_center_alignment();
                const int mark = sprites.size();
                text.generate(0, layout::footer_y, "A PLAY   B BACK", sprites);
                tint(sprites, mark, bn::sprite_palette_items::text_mag);
                dirty = false;
            }

            cursor.set_position(layout::cursor_x,
                               layout::body_top + 2 + ((pick - top) * 17)
                               + ((frame >> 4) & 1));

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
        bn::regular_bg_ptr backdrop = make_backdrop(backdrop_front, backdrop_style::field);
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

    void show_two_player_result(bn::sprite_text_generator& text,
                                const run_state& one, const run_state& two)
    {
        settle();

        {
        bn::regular_bg_ptr backdrop = make_backdrop(backdrop_front, backdrop_style::field);
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

    void show_opening(bn::sprite_text_generator& text)
    {
        settle();

        {
        bn::regular_bg_ptr backdrop = make_backdrop(0, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 64> sprites;

        // Who he is and why he is going down. The game said neither before,
        // and it is the one thing the sins are all reacting to.
        static const char* const lines[] = {
            "HORNS HE DID NOT ASK FOR",
            "A HALO THAT WILL NOT SIT",
            "NEITHER SIDE WILL HAVE HIM",
            "SO HE IS GOING DOWN TO ASK",
        };

        text.set_center_alignment();
        bn::sprite_ptr luv = bn::sprite_items::luv.create_sprite(0, 52);
        int shown = 0;

        for(int frame = 0; frame < 560; ++frame)
        {
            if(shown < 4 && frame == 30 + (shown * 62))
            {
                const int mark = sprites.size();
                text.generate(0, -56 + (shown * 20), lines[shown], sprites);
                tint(sprites, mark, shown < 2 ? bn::sprite_palette_items::text_cyan
                                              : bn::sprite_palette_items::text_gold);
                ++shown;
                audio::sfx_menu();
            }

            luv.set_position(0, 52 - ((frame >> 4) & 1));

            if((frame % 26) == 0)
            {
                luv.set_tiles(bn::sprite_items::luv.tiles_item()
                              .create_tiles((frame / 26) & 1));
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

    void show_world_story(bn::sprite_text_generator& text, int world)
    {
        settle();
        const int which = bn::clamp(world, 0, 7);

        {
        bn::regular_bg_ptr backdrop = make_backdrop(which, backdrop_style::field);
        bn::vector<bn::sprite_ptr, 64> sprites;

        text.set_center_alignment();
        text.generate(0, -68, sins[which].latin, sprites);
        tint(sprites, 0, bn::sprite_palette_items::text_mag);

        int mark = sprites.size();
        text.generate(0, -50, depth[which], sprites);
        tint(sprites, mark, bn::sprite_palette_items::text_gold);

        // The sin speaks, a line at a time, and then he answers it.
        const char* const lines[] = {
            words[which].a, words[which].b, words[which].c,
        };

        bn::sprite_ptr luv = bn::sprite_items::luv.create_sprite(-84, 44);
        luv.set_visible(false);
        int shown = 0;
        bool answered = false;

        for(int frame = 0; frame < 560; ++frame)
        {
            if(shown < 3 && frame == 30 + (shown * 55))
            {
                mark = sprites.size();
                text.generate(0, -24 + (shown * 20), lines[shown], sprites);
                tint(sprites, mark, bn::sprite_palette_items::text_cyan);
                ++shown;
                audio::sfx_menu();
            }

            if(!answered && frame == 250)
            {
                answered = true;
                luv.set_visible(true);
                mark = sprites.size();
                text.generate(8, 46, answers[which], sprites);
                tint(sprites, mark, bn::sprite_palette_items::text_green);
                audio::sfx_menu();
            }

            if(answered)
            {
                luv.set_position(-84, 44 - ((frame >> 4) & 1));

                if((frame % 26) == 0)
                {
                    luv.set_tiles(bn::sprite_items::luv.tiles_item()
                                  .create_tiles((frame / 26) & 1));
                }
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

        // Three endings. The last line is the only one that changes, because
        // the point is what the run was, not a different story.
        const int found = secrets_found(run);
        const bool clean = run.continues >= tune::start_continues;

        // The opening asks whether either side will have him. The close has to
        // answer that, not gesture at it.
        const char* last = "HE WENT WHERE HE LIKED";

        if(found >= 3 && clean)
        {
            last = "HE HAD SEEN EVERYTHING";
        }
        else if(found >= 3)
        {
            last = "HE HAD SEEN EVERY ROOM";
        }
        else if(clean)
        {
            last = "HE NEVER ONCE TURNED BACK";
        }

        const panel panels[] = {
            {40,  -62, "THE SEVEN ARE UNDONE"},
            {150, -44, "AND HADES KEPT NOTHING"},
            {270, -20, "BOTH SIDES SENT FOR HIM"},
            {390,   2, last},
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
                text.generate(0, 68, bn::format<28>("SECRETS {} OF 3", found), tail);

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
