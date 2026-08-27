#ifndef LFN_CARDS_H
#define LFN_CARDS_H

#include "bn_sprite_text_generator.h"

#include "lfn_game.h"
#include "lfn_save.h"

namespace lfn
{
    /**
     * Shared furniture for every full-screen panel.
     *
     * These used to be written out per screen, so titles sat at -66 on one and
     * -70 on the next, footers at 62 or 70, and lists started at -64, -80 or
     * -92 depending on which screen you were looking at. Flicking between them
     * the furniture moved. One set of numbers, used everywhere.
     */
    namespace layout
    {
        constexpr int title_y = -70;    // the gold heading
        constexpr int footer_y = 70;    // "A PICK   B BACK" and friends
        constexpr int body_top = -46;   // first row of a list
        constexpr int list_x = -80;     // left edge of a left-aligned list
        constexpr int cursor_x = -100;  // clear of the widest list row
    }

    enum class pause_result : uint8_t { resume, restart, quit };

    /** START during play. Freezes the scene and puts a choice over it. */
    [[nodiscard]] pause_result run_pause(bn::sprite_text_generator& text);

    /** Out of lives. Shows the damage, then hands back to the menu. */
    void show_game_over(bn::sprite_text_generator& text, const run_state& run,
                        const save::file& file);

    /**
     * The boards. A flips between the story ladder and the boss rush one.
     *
     * In `attract` the screen belongs to nobody: it times out on its own and
     * any button at all leaves, because the whole point of an attract loop is
     * that touching the pad gets you out of it.
     */
    void show_high_scores(bn::sprite_text_generator& text, const save::file& file,
                          int highlight = -1,
                          save::board which = save::board::story,
                          bool attract = false);

    /**
     * Which of the three games on the cartridge. Returns the slot, or -1 if
     * the player backed out. `for_new` lets an empty slot be picked.
     */
    [[nodiscard]] int pick_file(bn::sprite_text_generator& text,
                                const save::file& data, bool for_new);

    /** Who made it. */
    void show_credits(bn::sprite_text_generator& text);

    /** Every track in the game, on demand. */
    void show_sound_test(bn::sprite_text_generator& text);

    /**
     * The cheat screen. Returns the number of lives the next run starts with,
     * or 0 if nothing was entered. Closes itself after ten seconds.
     */
    [[nodiscard]] int enter_cheat(bn::sprite_text_generator& text);

    /**
     * Three letters, arcade style. Returns the slot the score landed in so the
     * board can point at it afterwards.
     */
    int enter_initials(bn::sprite_text_generator& text, save::file& file, int score,
                       int player = 0, save::board which = save::board::story);

    /** Who Luv is and why he is going down. Once, at the top of a run. */
    void show_opening(bn::sprite_text_generator& text);

    /** What the sin has to say, once, on the way into its world. */
    void show_world_story(bn::sprite_text_generator& text, int world);

    /**
     * The card before a stage: which world, which sin, how many lives left,
     * and the code that comes back here. Holds for a beat, or until the player
     * presses something. `player` is 0 for a solo game, else 1 or 2.
     */
    void show_world_card(bn::sprite_text_generator& text, int stage_index,
                         const run_state& run, int player = 0);

    /**
     * Out of lives with a continue still in hand. Counts down; A takes it, B
     * or the clock running out ends the run.
     */
    [[nodiscard]] bool offer_continue(bn::sprite_text_generator& text,
                                      const run_state& run, int player = 0);

    /** Handing the pad over: who is up, and what they are carrying. */
    void show_player_card(bn::sprite_text_generator& text, int player,
                          const run_state& run);

    /** Four letters. Returns the level the code opens, or -1 if backed out. */
    [[nodiscard]] int enter_code(bn::sprite_text_generator& text);

    /** Both seats are empty. Shows the two scores side by side. */
    void show_two_player_result(bn::sprite_text_generator& text,
                                const run_state& one, const run_state& two);

    /** Hades is down. Luv goes up. */
    void show_ending(bn::sprite_text_generator& text, const run_state& run,
                     const save::file& file);
}

#endif
