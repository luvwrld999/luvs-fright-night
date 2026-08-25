#ifndef LFN_BOSS_H
#define LFN_BOSS_H

#include "bn_camera_ptr.h"
#include "bn_fixed_point.h"
#include "bn_optional.h"
#include "bn_sprite_ptr.h"

#include "lfn_entities.h"
#include "lfn_level.h"
#include "lfn_luv.h"

namespace lfn
{
    /** How a boss carries itself around the arena. */
    enum class boss_move : uint8_t
    {
        hop,        // bounces along the floor
        drift,      // floats a figure of eight
        charge,     // rushes the floor wall to wall
        still,      // does not move at all
        stalk,      // mirrors the player from the far side
    };

    /** What it throws at you. */
    enum class boss_attack : uint8_t
    {
        rain,       // falls from above, aimed where you were
        lob,        // arcs across the room
        spread,     // a fan along the ground
        slam,       // a shockwave when it hits a wall
        charm,      // calls a demon to fight for it
    };

    struct boss_events
    {
        bool wounded = false;
        bool hurt_player = false;
        bool defeated = false;      // death animation finished
        bool phase = false;         // changed phase
    };

    /**
     * One of the seven sins, or the king behind them.
     *
     * All eight share a state machine - approach, attack, recover, die - and
     * differ by a movement kind, an attack kind and their numbers. Hades is
     * the exception that changes both as its health drops.
     */
    class boss
    {
    public:
        /** `floor_y` is the top of the arena floor; the boss rests on it. */
        void create(int which, bn::fixed x, bn::fixed floor_y,
                    bn::camera_ptr& camera);
        void clear();

        boss_events update(luv& player, level& lv, entities& ents);

        [[nodiscard]] bool active() const { return _which > 0; }
        [[nodiscard]] int health() const { return _health; }
        [[nodiscard]] int max_health() const { return _max_health; }
        [[nodiscard]] bool dying() const { return _dying; }
        [[nodiscard]] const char* name() const;

    private:
        bn::fixed_point _pos;
        bn::fixed_point _vel;
        bn::fixed_point _home;
        bn::optional<bn::sprite_ptr> _sprite;

        int _which = 0;
        int _health = 0;
        int _max_health = 0;
        int _timer = 0;
        int _invuln = 0;
        int _phase = 0;

        /** Attack interval and pace for the phase the fight is in. */
        [[nodiscard]] int _period() const;
        [[nodiscard]] bn::fixed _speed() const;
        int _frame = -1;
        bool _dying = false;
        int _death_timer = 0;
        bool _facing_right = false;
        bool _wall_hit = false;     // a charger just rebounded
        int _stagger = 0;           // dazed after slamming into a wall

        void _move(luv& player, level& lv);
        void _attack(luv& player, entities& ents);
        void _animate();
        [[nodiscard]] int _half() const;
    };
}

#endif
