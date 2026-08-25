#ifndef LFN_CARDS_H
#define LFN_CARDS_H

#include "bn_sprite_text_generator.h"

#include "lfn_game.h"
#include "lfn_save.h"

namespace lfn
{
    enum class pause_result : uint8_t { resume, quit };

    /** START during play. Freezes the scene and puts a choice over it. */
    [[nodiscard]] pause_result run_pause(bn::sprite_text_generator& text);

    /** Out of lives. Shows the damage, then hands back to the menu. */
    void show_game_over(bn::sprite_text_generator& text, const run_state& run,
                        const save::file& file);

    /** The board. */
    void show_high_scores(bn::sprite_text_generator& text, const save::file& file,
                          int highlight = -1);

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
                       int player = 0);

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
