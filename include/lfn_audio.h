#ifndef LFN_AUDIO_H
#define LFN_AUDIO_H

namespace lfn::audio
{
    // Indices match tools/build_levels.py's MUSIC table.
    namespace track
    {
        constexpr int title = 0, boss = 9, victory = 10, game_over = 11;
    }

    /**
     * Opens a new frame's effect budget.
     *
     * Butano allows only a handful of audio commands per frame and asserts on
     * the one that overflows. A single game frame can easily want a dozen -
     * land, collect, one-up, get hit - so the budget drops the surplus instead
     * of taking the game down with it.
     */
    void new_frame();

    /** Starts a track only if it is not the one already playing. */
    void play_music(int track_index);
    void stop_music();

    void sfx_jump();
    void sfx_land();
    void sfx_stomp();
    void sfx_shot();
    void sfx_dash();
    void sfx_hurt();
    void sfx_death();
    void sfx_pickup();
    void sfx_power_up();
    void sfx_one_up();
    void sfx_checkpoint();
    void sfx_smash();
    void sfx_boss_hit();
    void sfx_boss_die();
    void sfx_menu();
    void sfx_level_clear();
    /** A boss is about to commit to something. */
    void sfx_boss_tell();
    /** The floor gives way and somewhere else takes over. */
    void sfx_warp();
}

#endif
