#include "lfn_luv.h"

#include "bn_sprite_tiles_ptr.h"

#include "bn_keypad.h"
#include "bn_sprite_items_luv.h"
#include "bn_sprite_items_luv_soul.h"

namespace lfn
{
    namespace
    {
        // Frame indices into the luv sprite sheet.
        constexpr int f_idle = 0, f_run = 2, f_jump = 6, f_fall = 7;
        constexpr int f_hover = 8, f_dash = 10, f_hurt = 12;

        constexpr bn::fixed sign_of(bn::fixed v)
        {
            return v < 0 ? bn::fixed(-1) : bn::fixed(1);
        }
    }

    void luv::create(bn::fixed x, bn::fixed y, bn::camera_ptr& camera)
    {
        _sprite = bn::sprite_items::luv.create_sprite(x, y + tune::luv_sprite_dy);
        _sprite->set_camera(camera);
        _sprite->set_z_order(-10);
        respawn(x, y);
    }

    void luv::respawn(bn::fixed x, bn::fixed y)
    {
        _pos = bn::fixed_point(x, y);
        _vel = bn::fixed_point(0, 0);
        _grounded = false;
        _dead = false;
        _invuln = 0;
        _hover = hover_max();
        _dash_timer = 0;
        _facing_right = true;
        set_visible(true);
    }

    int luv::hover_max() const
    {
        return _powers.wings ? tune::hover_frames_winged : tune::hover_frames;
    }

    void luv::set_visible(bool visible)
    {
        if(_sprite)
        {
            _sprite->set_visible(visible);
        }
    }

    bool luv::overlaps(bn::fixed ox, bn::fixed oy, int half) const
    {
        const bn::fixed dx = ox - _pos.x();
        const bn::fixed dy = oy - _pos.y();
        return dx > -(tune::luv_half_w + half) && dx < (tune::luv_half_w + half) &&
               dy > -(tune::luv_half_h + half) && dy < (tune::luv_half_h + half);
    }

    void luv::bounce()
    {
        _vel.set_y(tune::stomp_bounce);
        _grounded = false;
        _coyote = 0;
    }

    bool luv::take_hit()
    {
        if(_invuln > 0 || _dead || tune::test_invulnerable)
        {
            return false;
        }

        _invuln = tune::invuln_frames;

        // Power-ups are shed from the top down before a life is spent.
        if(_powers.soul)
        {
            _powers.soul = false;
            return false;
        }

        if(_powers.flame)
        {
            _powers.flame = false;
            return false;
        }

        _dead = true;
        _vel = bn::fixed_point(0, -3.2);
        return true;
    }

    namespace
    {
        /** Test-only driver: run right, jump when the ground ahead runs out. */
        struct pilot
        {
            bool press = false;
            bool hold = false;
        };

        pilot autopilot(level& lv, bool grounded, int px, int py)
        {
            pilot out;
            const int col = px / tune::tile;
            const int row = (py + tune::luv_half_h) / tune::tile;

            if(grounded)
            {
                const int probe = py + tune::luv_half_h + 4;

                for(int d = 10; d <= 26; d += 8)
                {
                    if(!lv.blocks(px + d, probe) &&
                       lv.at_pixel(px + d, probe) != surface::platform)
                    {
                        out.press = true;
                        break;
                    }

                    if(lv.hurts(px + d, probe - 8))
                    {
                        out.press = true;
                        break;
                    }
                }

                if(lv.blocks(px + tune::luv_half_w + 3, py))
                {
                    out.press = true;                 // something in the way
                }
            }
            else
            {
                // Full height, and keep hovering on the way down. Aiming for a
                // specific ledge needs a real planner; this is a smoke test.
                out.hold = true;
                (void) col;
                (void) row;
            }

            out.hold = out.hold || out.press;
            return out;
        }
    }

    void luv::_read_input(level& lv, luv_events& ev)
    {
        const int px_now = _pos.x().right_shift_integer();
        const int py_now = _pos.y().right_shift_integer();
        // The harness flag and the attract demo want the same thing: nobody
        // is holding the pad, so something has to hold it for them.
        const bool driven = tune::test_autopilot || _demo;
        const pilot ai = driven ? autopilot(lv, _grounded, px_now, py_now)
                                : pilot();

        const bool left = driven ? false : bn::keypad::left_held();
        const bool right = driven ? true : bn::keypad::right_held();
        const bn::fixed accel = _grounded ? tune::run_accel : tune::air_accel;

        // B is Mario's button: held, it raises the speed cap; tapped, it throws
        // a soul flame. Holding it does both, which is the point.
        const bool dash_held = _powers.dash &&
                               (driven ? false : bn::keypad::b_held());
        const bn::fixed top = dash_held ? tune::dash_max : tune::run_max;
        const bn::fixed speed_now = _vel.x() < 0 ? -_vel.x() : _vel.x();

        if(dash_held && speed_now >= tune::dash_threshold)
        {
            ++_dash_timer;

            if(_dash_timer == tune::dash_windup)
            {
                ev.dashed = true;
            }
        }
        else
        {
            _dash_timer = 0;
        }

        if(left != right)
        {
            _facing_right = right;
            _vel.set_x(_vel.x() + (right ? accel : -accel));

            if(_vel.x() > top)
            {
                _vel.set_x(top);
            }
            else if(_vel.x() < -top)
            {
                _vel.set_x(-top);
            }
        }
        else if(_grounded)
        {
            const bn::fixed speed = _vel.x() < 0 ? -_vel.x() : _vel.x();
            _vel.set_x(speed <= tune::friction ? bn::fixed(0)
                                               : _vel.x() - sign_of(_vel.x()) * tune::friction);
        }

        if(driven ? ai.press : bn::keypad::a_pressed())
        {
            _buffer = tune::jump_buffer_frames;
        }

        _jump_held = driven ? ai.hold : bn::keypad::a_held();

        if(_buffer > 0 && (_grounded || _coyote > 0))
        {
            _vel.set_y(tune::jump_speed);
            _grounded = false;
            _coyote = 0;
            _buffer = 0;
            ev.jumped = true;
        }

        // Jump height is cut the moment A is let go, which is what makes the
        // jump feel like a decision rather than an animation.
        if(!_jump_held && _vel.y() < tune::jump_cut)
        {
            _vel.set_y(tune::jump_cut);
        }

        if(_powers.flame && !driven && bn::keypad::b_pressed())
        {
            ev.shot = true;
        }
    }

    void luv::_apply_gravity(bool hover_wanted)
    {
        const bool hovering = hover_wanted && !_grounded && _vel.y() > 0 && _hover > 0;

        if(hovering)
        {
            --_hover;
            _vel.set_y(_vel.y() + tune::hover_gravity);

            if(_vel.y() > tune::hover_fall_max)
            {
                _vel.set_y(tune::hover_fall_max);
            }
        }
        else
        {
            _vel.set_y(_vel.y() + tune::gravity);

            if(_vel.y() > tune::fall_max)
            {
                _vel.set_y(tune::fall_max);
            }
        }
    }

    void luv::_move_x(level& lv)
    {
        _pos.set_x(_pos.x() + _vel.x());

        const int px = _pos.x().right_shift_integer();
        const int py = _pos.y().right_shift_integer();
        const int edge = _vel.x() > 0 ? px + tune::luv_half_w : px - tune::luv_half_w;

        if(_vel.x() == 0)
        {
            return;
        }

        for(int dy = -tune::luv_half_h + 2; dy <= tune::luv_half_h - 2; dy += 8)
        {
            if(lv.blocks(edge, py + dy))
            {
                const int tile_x = edge / tune::tile;
                _pos.set_x(_vel.x() > 0 ? (tile_x * tune::tile) - tune::luv_half_w
                                        : ((tile_x + 1) * tune::tile) + tune::luv_half_w);
                _vel.set_x(0);
                return;
            }
        }
    }

    void luv::_move_y(level& lv, luv_events& ev)
    {
        const int prev_foot = _pos.y().right_shift_integer() + tune::luv_half_h;
        _pos.set_y(_pos.y() + _vel.y());

        const int px = _pos.x().right_shift_integer();
        const int py = _pos.y().right_shift_integer();
        const bool was_grounded = _grounded;
        _grounded = false;

        if(_vel.y() >= 0)
        {
            const int foot = py + tune::luv_half_h;

            for(int dx = -tune::luv_half_w + 1; dx <= tune::luv_half_w - 1; dx += 4)
            {
                if(lv.lands_on(px + dx, foot, prev_foot, _vel.y()))
                {
                    _pos.set_y(((foot / tune::tile) * tune::tile) - tune::luv_half_h);
                    _vel.set_y(0);
                    _grounded = true;

                    if(!was_grounded)
                    {
                        ev.landed = true;
                    }

                    break;
                }
            }
        }
        else
        {
            const int head = py - tune::luv_half_h;

            for(int dx = -tune::luv_half_w + 1; dx <= tune::luv_half_w - 1; dx += 4)
            {
                if(lv.blocks(px + dx, head))
                {
                    // A head-butt opens breakable blocks, Mario style.
                    const int col = (px + dx) / tune::tile;
                    const int row = head / tune::tile;

                    if(lv.smash(col, row))
                    {
                        ev.smashed = true;
                        ev.smash_col = col;
                        ev.smash_row = row;
                    }

                    _pos.set_y((((head / tune::tile) + 1) * tune::tile) + tune::luv_half_h);
                    _vel.set_y(0);
                    break;
                }
            }
        }

        if(_grounded)
        {
            _coyote = tune::coyote_frames;
            _hover = bn::min(hover_max(), _hover + tune::hover_regen);
        }
        else if(_coyote > 0)
        {
            --_coyote;
        }
    }

    void luv::_animate()
    {
        int base;

        if(_dead)
        {
            base = f_hurt;
        }
        else if(dashing())
        {
            base = f_dash + ((_anim >> 2) & 1);
        }
        else if(!_grounded)
        {
            const bool hovering = _jump_held && _vel.y() > 0 && _hover > 0;
            base = hovering ? f_hover + ((_anim >> 3) & 1)
                            : (_vel.y() < 0 ? f_jump : f_fall);
        }
        else if(_vel.x() != 0)
        {
            base = f_run + ((_anim >> 2) & 3);
        }
        else
        {
            base = f_idle + ((_anim >> 5) & 1);
        }

        // Carrying a Purple Soul swaps in the violet sheet, so the extra hit is
        // visible at a glance rather than hidden in the status bar.
        if(base != _frame || _powers.soul != _soul_shown)
        {
            _frame = base;
            _soul_shown = _powers.soul;
            _sprite->set_tiles(_soul_shown
                    ? bn::sprite_items::luv_soul.tiles_item().create_tiles(base)
                    : bn::sprite_items::luv.tiles_item().create_tiles(base));
        }

        _sprite->set_horizontal_flip(!_facing_right);
        _sprite->set_position(_pos.x(), _pos.y() + tune::luv_sprite_dy);

        // Blink while the hit is still being shrugged off.
        _sprite->set_visible(_invuln <= 0 || ((_invuln >> 2) & 1) == 0);
    }

    luv_events luv::update(level& lv)
    {
        luv_events ev;
        ++_anim;

        if(_invuln > 0)
        {
            --_invuln;
        }

        if(_buffer > 0)
        {
            --_buffer;
        }

        if(_dead)
        {
            // Death throw: a hop, then out of the world.
            _vel.set_y(_vel.y() + tune::gravity);
            _pos.set_y(_pos.y() + _vel.y());
            _animate();
            ev.died = _pos.y() > lv.pixel_height() + 40;
            return ev;
        }

        _read_input(lv, ev);
        _apply_gravity(_jump_held);
        _move_x(lv);
        _move_y(lv, ev);

        const int px = _pos.x().right_shift_integer();
        const int py = _pos.y().right_shift_integer();

        if(_pos.y() > lv.pixel_height() + 16)
        {
            // Falling out is always fatal. Under the test flag the scene simply
            // does not charge a life for it - teleporting him back up instead
            // drops him into the same pit forever.
            _dead = true;
            ev.hurt = true;
            _powers.clear();
        }
        else if(lv.hurts(px, py) || lv.hurts(px, py + tune::luv_half_h - 1))
        {
            ev.hurt = take_hit();
        }

        _animate();
        return ev;
    }
}
