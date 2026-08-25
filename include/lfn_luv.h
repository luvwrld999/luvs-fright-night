#ifndef LFN_LUV_H
#define LFN_LUV_H

#include "bn_camera_ptr.h"
#include "bn_fixed_point.h"
#include "bn_optional.h"
#include "bn_sprite_ptr.h"

#include "lfn_level.h"
#include "lfn_tune.h"

namespace lfn
{
    /** What Luv is carrying. Lost from the top down when he takes a hit. */
    struct powers
    {
        bool soul = false;      // Purple Soul: absorbs one hit
        bool flame = false;     // soul flame shot
        bool wings = false;     // longer hover
        bool dash = false;      // horns-first charge

        void clear() { soul = flame = wings = dash = false; }
    };

    /** Things that happened this frame, for the scene to react to. */
    struct luv_events
    {
        bool jumped = false;
        bool landed = false;
        bool hurt = false;
        bool died = false;
        bool dashed = false;
        bool shot = false;
        bool smashed = false;
        int smash_col = -1;      // the cell Luv opened, for whatever was inside
        int smash_row = -1;
    };

    class luv
    {
    public:
        void create(bn::fixed x, bn::fixed y, bn::camera_ptr& camera);
        void respawn(bn::fixed x, bn::fixed y);

        luv_events update(level& lv);

        [[nodiscard]] const bn::fixed_point& position() const { return _pos; }
        [[nodiscard]] bn::fixed x() const { return _pos.x(); }
        [[nodiscard]] bn::fixed y() const { return _pos.y(); }
        [[nodiscard]] bool facing_right() const { return _facing_right; }
        [[nodiscard]] bool grounded() const { return _grounded; }
        [[nodiscard]] bool dashing() const { return _dash_timer >= tune::dash_windup; }
        [[nodiscard]] bool invulnerable() const { return _invuln > 0; }
        [[nodiscard]] bool dead() const { return _dead; }
        [[nodiscard]] powers& carrying() { return _powers; }
        [[nodiscard]] int hover_left() const { return _hover; }
        [[nodiscard]] int hover_max() const;
        [[nodiscard]] bn::fixed velocity_y() const { return _vel.y(); }

        /** Returns false if the hit was absorbed by a power-up. */
        bool take_hit();
        void bounce();                       // after stomping something
        void set_visible(bool visible);

        [[nodiscard]] bool overlaps(bn::fixed ox, bn::fixed oy, int half) const;

    private:
        bn::fixed_point _pos;
        bn::fixed_point _vel;
        bn::optional<bn::sprite_ptr> _sprite;
        powers _powers;

        bool _facing_right = true;
        bool _grounded = false;
        bool _dead = false;
        bool _jump_held = false;
        int _coyote = 0;
        int _buffer = 0;
        int _invuln = 0;
        int _hover = tune::hover_frames;
        int _dash_timer = 0;
        int _anim = 0;
        int _frame = 0;
        bool _soul_shown = false;

        void _read_input(level& lv, luv_events& ev);
        void _apply_gravity(bool hover_wanted);
        void _move_x(level& lv);
        void _move_y(level& lv, luv_events& ev);
        void _animate();
    };
}

#endif
