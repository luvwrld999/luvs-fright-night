#ifndef LFN_GAME_H
#define LFN_GAME_H

#include "bn_camera_ptr.h"
#include "bn_optional.h"
#include "bn_sprite_ptr.h"
#include "bn_sprite_text_generator.h"
#include "bn_vector.h"

#include "lfn_boss.h"
#include "lfn_entities.h"
#include "lfn_hud.h"
#include "lfn_level.h"
#include "lfn_luv.h"
#include "lfn_tune.h"

namespace lfn
{
    enum class game_result : uint8_t
    {
        running,
        level_cleared,
        game_over,
        // Only ever returned when the stage was told another player is
        // waiting: a lost life ends the turn instead of restarting it.
        handed_over,
    };

    /** What the player carries from one stage into the next. */
    struct run_state
    {
        int lives = tune::start_lives;
        int souls = 0;
        int score = 0;
        int continues = tune::start_continues;
        /**
         * What Luv is carrying. Kept in the run rather than the stage, so
         * finding a power-up late in a level is still worth something when the
         * gate takes you to the next one.
         */
        powers held;
    };

    /** One stage, played start to finish. */
    class game
    {
    public:
        /**
         * `player` is 0 for a solo game, else 1 or 2, and shows in the status
         * bar. `hand_off` makes a lost life end the turn rather than restart
         * the stage, for alternating two-player games.
         */
        game(int level_index, const run_state& carried, bn::sprite_text_generator& text,
             int player = 0, bool hand_off = false, bool demo = false);

        ~game();

        game_result update();

        [[nodiscard]] const run_state& carried() const { return _run; }
        /** Clock units the stage took, for the records table. */
        [[nodiscard]] int elapsed() const { return tune::stage_time - _status.time; }
        /** True when the stage was left through a warp door, not the gate. */
        [[nodiscard]] bool warped() const { return _warped; }

    private:
        level _level;
        luv _player;
        entities _entities;
        boss _boss;
        hud _hud;
        bn::sprite_text_generator& _text;
        bn::vector<bn::sprite_ptr, 40> _banner;
        bn::optional<bn::camera_ptr> _camera;
        bn::fixed_point _start;
        bn::fixed_point _boss_home;
        run_state _run;
        status _status;

        int _index;
        int _time_ticks = 0;
        int _combo = 0;                // consecutive stomps without landing
        int _hold = 0;                 // frames to sit on death / clear
        int _alive = 0;                // frames played, for the fragile test flag
        game_result _result = game_result::running;
        bool _warped = false;
        bool _hand_off = false;
        bool _demo = false;
        powers _powers_said;           // what the banner last announced
        bn::vector<bn::sprite_ptr, 32> _wall_text;

        void _restart();
        void _follow_camera();
        void _handle(const luv_events& le, const world_events& we);
        void _add_score(int points);
        void _die();
        void _refresh_hud();
        void _say(const char* line, int bonus);
    };
}

#endif
