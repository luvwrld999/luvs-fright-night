// Every number that decides how the game feels, in one place.
#ifndef LFN_TUNE_H
#define LFN_TUNE_H

#include "bn_fixed.h"

namespace lfn::tune
{
    // -- world --------------------------------------------------------------
    constexpr int tile = 16;                        // metatile size in pixels
    constexpr int screen_w = 240;
    constexpr int screen_h = 160;

    // -- Luv ----------------------------------------------------------------
    constexpr bn::fixed run_accel      = 0.14;
    constexpr bn::fixed air_accel      = 0.09;
    constexpr bn::fixed run_max        = 1.7;
    constexpr bn::fixed dash_max       = 3.1;
    constexpr bn::fixed friction       = 0.20;
    constexpr bn::fixed gravity        = 0.36;
    constexpr bn::fixed fall_max       = 6.0;
    // Rises 72px - four and a half metatiles. That clears an overhead block row
    // by half a tile, so landing on top of one is comfortable rather than
    // pixel-perfect, and there is airtime left to hover up there.
    constexpr bn::fixed jump_speed     = -7.4;
    constexpr bn::fixed jump_cut       = -1.6;      // vy kept when A released
    constexpr bn::fixed stomp_bounce   = -5.0;

    // Hover: hold A past the apex and Luv stops falling while the meter drains.
    constexpr bn::fixed hover_gravity  = 0.055;
    constexpr bn::fixed hover_fall_max = 0.9;
    constexpr int hover_frames         = 90;
    constexpr int hover_frames_winged  = 270;       // Wisp Wings
    constexpr int hover_regen          = 3;         // per grounded frame

    constexpr int coyote_frames        = 6;
    constexpr int jump_buffer_frames   = 6;
    constexpr int invuln_frames        = 90;
    // Devil Dash is held, not triggered: B raises the speed cap, and once Luv
    // is actually at that speed he is going horns-first and goes through things.
    constexpr bn::fixed dash_threshold = 2.8;
    constexpr int dash_windup          = 10;        // frames at speed before it bites

    // Hitboxes are narrower than the art so corners forgive.
    constexpr int luv_half_w           = 5;
    constexpr int luv_half_h           = 11;
    constexpr int luv_sprite_dy        = 2;

    // -- enemies ------------------------------------------------------------
    constexpr bn::fixed imp_speed      = 0.42;
    constexpr bn::fixed gnasher_speed  = 0.35;
    constexpr bn::fixed gnasher_charge = 1.55;
    constexpr bn::fixed cherub_speed   = 0.5;
    constexpr bn::fixed cherub_amp     = 26;        // a wider, lazier float
    // The drop enemy hangs, telegraphs, falls, then floats back up. It should
    // spend most of its time in the air, not on the floor.
    constexpr bn::fixed bat_dive       = 2.3;
    constexpr bn::fixed bat_rise       = 0.34;
    constexpr bn::fixed bat_bob        = 3.5;
    constexpr int bat_windup           = 22;
    constexpr int bat_rest             = 34;
    constexpr bn::fixed ember_speed    = 1.1;
    constexpr bn::fixed flame_speed    = 2.6;
    constexpr bn::fixed flame_bounce   = -2.2;
    constexpr int flame_life           = 150;
    constexpr int enemy_half           = 7;

    // -- camera -------------------------------------------------------------
    constexpr int cam_deadzone_x       = 18;
    constexpr int cam_look_ahead       = 26;
    constexpr bn::fixed cam_lerp       = 0.12;

    // Build with -DLFN_TEST_INVULNERABLE=1 to let the headless test harness
    // walk a whole stage without dying. Never set in a shipping build.
#ifndef LFN_TEST_POWERS
    #define LFN_TEST_POWERS 0
#endif

#ifndef LFN_TEST_FRAGILE
    #define LFN_TEST_FRAGILE 0
#endif

#ifndef LFN_TEST_INITIALS
    #define LFN_TEST_INITIALS 0
#endif

#ifndef LFN_TEST_INVULNERABLE
    #define LFN_TEST_INVULNERABLE 0
#endif
    constexpr bool test_invulnerable = LFN_TEST_INVULNERABLE != 0;
    // Frames of play before the harness kills the player outright; 0 is off.
    constexpr int test_fragile = LFN_TEST_FRAGILE;
    // Start every stage holding everything, to check the HUD shows it.
    constexpr bool test_powers = LFN_TEST_POWERS != 0;

    // Build with -DLFN_TEST_AUTOPILOT=1 and Luv drives himself to the right,
    // jumping when the floor runs out. It reads the same collision data the
    // game does, so "every stage is completable" becomes a check we can run.
#ifndef LFN_TEST_AUTOPILOT
    #define LFN_TEST_AUTOPILOT 0
#endif
    constexpr bool test_autopilot = LFN_TEST_AUTOPILOT != 0;

    // -- rules --------------------------------------------------------------
    constexpr int start_lives          = 3;
    // Running out of lives is not the end while you still have one of these.
    constexpr int start_continues      = 3;
    constexpr int continue_seconds     = 9;
    constexpr int souls_per_life       = 99;
    // What a bonus soul is worth. Nine of them sit in every stage.
    constexpr int bonus_soul_worth     = 10;

    // -- scoring ------------------------------------------------------------
    constexpr int stage_time           = 300;       // counts down to zero
    constexpr int time_frames          = 20;        // frames per time unit
    constexpr int score_soul           = 10;
    constexpr int score_block          = 20;
    constexpr int score_checkpoint     = 200;
    constexpr int score_power_up       = 500;
    constexpr int score_one_up         = 1000;
    constexpr int score_stomp          = 100;       // doubles per air combo
    constexpr int score_combo_cap      = 8;         // ...up to 800
    constexpr int score_time_bonus     = 20;        // per unit left at the exit
    constexpr int score_boss_hit       = 300;
    constexpr int score_boss           = 5000;
    constexpr int score_max            = 999999;
    constexpr bn::fixed music_volume    = 0.35;     // ambience, not performance
}

#endif
