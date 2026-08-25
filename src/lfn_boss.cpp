#include "lfn_boss.h"

#include "bn_math.h"
#include "bn_sprite_tiles_ptr.h"

#include "bn_sprite_items_boss_acedia.h"
#include "bn_sprite_items_boss_avaritia.h"
#include "bn_sprite_items_boss_gula.h"
#include "bn_sprite_items_boss_hades.h"
#include "bn_sprite_items_boss_invidia.h"
#include "bn_sprite_items_boss_ira.h"
#include "bn_sprite_items_boss_luxuria.h"
#include "bn_sprite_items_boss_superbia.h"

#include "lfn_tune.h"

namespace lfn
{
    namespace
    {
        // Frame indices in every boss sheet.
        constexpr int f_idle = 0, f_wind = 2, f_atk = 3, f_hurt = 5, f_die = 6;

        constexpr int hit_invuln = 44;
        // Long enough to actually arrive: a lunge that stops short of the
        // player is a fight you cannot win.
        constexpr int lunge_frames = 50;
        // A charger that never stops is a boss you cannot land on. The
        // rebound daze is the opening the fight is built around.
        constexpr int wall_daze = 46;
        constexpr int death_frames = 150;

        struct spec
        {
            const char* name;
            uint8_t health;
            boss_move move;
            boss_attack attack;
            bn::fixed speed;
            uint16_t period;        // frames between attacks
            uint8_t half;           // hitbox half size
        };

        // The seven sins, then the king. Each one is a different verb.
        constexpr spec specs[] = {
            {"SUPERBIA", 5, boss_move::stalk,  boss_attack::rain,   0.9, 96,  15},
            {"AVARITIA", 5, boss_move::hop,    boss_attack::lob,    0.7, 104, 15},
            {"LUXURIA",  6, boss_move::drift,  boss_attack::charm,  0.8, 118, 15},
            {"INVIDIA",  6, boss_move::charge, boss_attack::spread, 1.5, 108, 15},
            {"GULA",     7, boss_move::hop,    boss_attack::spread, 0.55, 88, 15},
            {"IRA",      7, boss_move::charge, boss_attack::slam,   1.7, 120, 15},
            {"ACEDIA",   8, boss_move::still,  boss_attack::rain,   0.0, 62,  15},
            {"HADES",   10, boss_move::drift,  boss_attack::spread, 1.0, 84,  30},
        };

        const bn::sprite_item& sheet(int which)
        {
            switch(which)
            {
            case 1:  return bn::sprite_items::boss_superbia;
            case 2:  return bn::sprite_items::boss_avaritia;
            case 3:  return bn::sprite_items::boss_luxuria;
            case 4:  return bn::sprite_items::boss_invidia;
            case 5:  return bn::sprite_items::boss_gula;
            case 6:  return bn::sprite_items::boss_ira;
            case 7:  return bn::sprite_items::boss_acedia;
            default: return bn::sprite_items::boss_hades;
            }
        }
    }

    const char* boss::name() const
    {
        return _which > 0 ? specs[_which - 1].name : "";
    }

    int boss::_half() const
    {
        return specs[_which - 1].half;
    }

    void boss::clear()
    {
        _sprite.reset();
        _which = 0;
        _dying = false;
    }

    void boss::create(int which, bn::fixed x, bn::fixed floor_y,
                      bn::camera_ptr& camera)
    {
        clear();
        _which = which;

        const spec& s = specs[which - 1];
        _health = s.health;
        _max_health = s.health;
        // Stand it on the floor rather than wherever the spawn marker sat.
        _pos = bn::fixed_point(x, floor_y - s.half);
        _home = _pos;
        _vel = bn::fixed_point(-s.speed, 0);
        _timer = 0;
        _invuln = 0;
        _phase = 0;
        _frame = -1;
        _death_timer = 0;
        _wall_hit = false;
        _stagger = 0;

        _sprite = sheet(which).create_sprite(_pos.x(), _pos.y());
        _sprite->set_camera(camera);
        _sprite->set_z_order(-5);
    }

    void boss::_move(luv& player, level& lv)
    {
        const spec& s = specs[_which - 1];
        const bn::fixed floor_y = _home.y();
        const bn::fixed left = _half() + 8;
        const bn::fixed right = lv.pixel_width() - _half() - 8;

        // Hades speeds up as it loses phases; the others keep their pace.
        const bn::fixed speed = s.speed + (_which == 8 ? _phase * bn::fixed(0.45) : 0);

        // Every boss commits to a run at the player around its attack, so a
        // fight always closes to a range you can answer. A boss that only ever
        // keeps its distance is one you can never hit.
        if(_stagger <= 0 && (_timer % s.period) > int(s.period) - lunge_frames)
        {
            const bn::fixed step = speed + bn::fixed(1.2);
            const bn::fixed dx = player.x() - _pos.x();
            _pos.set_x(bn::clamp(_pos.x() + bn::clamp(dx, -step, step), left, right));
            _pos.set_y(bn::max(floor_y - 4, _pos.y() - bn::fixed(0.6)));
            _facing_right = dx > 0;
            return;
        }

        switch(s.move)
        {
        case boss_move::hop:
        {
            _pos.set_x(_pos.x() + _vel.x());

            if(_pos.x() < left || _pos.x() > right)
            {
                _vel.set_x(-_vel.x());
                _pos.set_x(bn::clamp(_pos.x(), left, right));
            }

            // A slow, heavy bounce.
            _pos.set_y(floor_y - bn::abs(bn::lut_sin((_timer * 14) & 2047)) * 14);
            break;
        }

        case boss_move::drift:
        {
            // A figure of eight around the middle of the room, so it is never
            // quite where you aimed but never off the screen either.
            const bn::fixed middle = lv.pixel_width() / 2;
            _pos.set_x(middle + bn::lut_sin((_timer * 6) & 2047) * 60);
            _pos.set_y(floor_y - 26 + bn::lut_sin((_timer * 12) & 2047) * 18);
            _facing_right = player.x() > _pos.x();
            break;
        }

        case boss_move::charge:
        {
            if(_stagger > 0)
            {
                // Reeling: shudders in place, and this is when to hit it.
                --_stagger;
                _pos.set_x(_pos.x() + (((_stagger >> 1) & 1) ? 1 : -1));
                _pos.set_y(floor_y);
                break;
            }

            const bn::fixed dir = _vel.x() < 0 ? -1 : 1;
            _pos.set_x(_pos.x() + dir * speed);

            if(_pos.x() < left || _pos.x() > right)
            {
                _vel.set_x(-_vel.x());
                _pos.set_x(bn::clamp(_pos.x(), left, right));
                // The rebound is its own cue. Resetting the timer here would
                // also reset the attack cycle, and a charger that crosses the
                // room in about one period would then never attack at all.
                _wall_hit = true;
                _stagger = wall_daze;
            }

            _pos.set_y(floor_y);
            break;
        }

        case boss_move::stalk:
        {
            // Holds station a fixed distance away on whichever side it is on,
            // switching sides when you cross it. Mirroring you all the way to
            // the far wall just means it leaves the screen.
            const bn::fixed keep = 62;
            const bn::fixed want = _pos.x() < player.x() ? player.x() - keep
                                                         : player.x() + keep;
            const bn::fixed target = bn::clamp(want, left, right);
            _pos.set_x(_pos.x() + bn::clamp(target - _pos.x(), -speed, speed));
            _pos.set_y(floor_y - bn::abs(bn::lut_sin((_timer * 9) & 2047)) * 8);
            break;
        }

        case boss_move::still:
        default:
            _pos.set_y(floor_y + bn::lut_sin((_timer * 4) & 2047) * 2);
            break;
        }

        if(s.move != boss_move::drift)
        {
            _facing_right = player.x() > _pos.x();
        }
    }

    void boss::_attack(luv& player, entities& ents)
    {
        const spec& s = specs[_which - 1];
        const boss_attack kind = (_which == 8 && _phase >= 1)
                               ? boss_attack::rain : s.attack;

        switch(kind)
        {
        case boss_attack::rain:
            // Falls from the ceiling over where the player is standing.
            for(int i = -1; i <= 1; ++i)
            {
                ents.spawn_shot(player.x() + (i * 26), _home.y() - 130,
                                0, bn::fixed(1.5) + (_phase * bn::fixed(0.3)), 220);
            }
            break;

        case boss_attack::lob:
        {
            const bn::fixed dir = _facing_right ? 1 : -1;
            ents.spawn_shot(_pos.x(), _pos.y() - 8, dir * bn::fixed(1.3), -2.2, 220);
            ents.spawn_shot(_pos.x(), _pos.y() - 8, dir * bn::fixed(2.0), -1.4, 220);
            break;
        }

        case boss_attack::spread:
        {
            const bn::fixed dir = _facing_right ? 1 : -1;
            for(int i = 0; i < 3; ++i)
            {
                ents.spawn_shot(_pos.x(), _pos.y(), dir * (bn::fixed(0.9) + i * bn::fixed(0.5)),
                                bn::fixed(-0.5) + i * bn::fixed(0.4), 200);
            }
            break;
        }

        case boss_attack::slam:
            // A shockwave that runs along the floor in both directions.
            ents.spawn_shot(_pos.x(), _home.y(), -2.2, 0, 200);
            ents.spawn_shot(_pos.x(), _home.y(), 2.2, 0, 200);
            break;

        case boss_attack::charm:
        default:
            // Keep the room fightable: a couple of charmed demons at a time,
            // not a swarm you cannot see past.
            if(ents.live_enemies() < 2)
            {
                ents.spawn_enemy(ent_kind::cherub, _pos.x(), _pos.y() - 20);
            }
            else
            {
                const bn::fixed dir = _facing_right ? 1 : -1;
                ents.spawn_shot(_pos.x(), _pos.y(), dir * bn::fixed(1.4), -0.6, 200);
            }
            break;
        }
    }

    void boss::_animate()
    {
        const spec& s = specs[_which - 1];
        int base;

        if(_dying)
        {
            base = f_die + ((_death_timer >> 4) & 1);
        }
        else if(_invuln > 0)
        {
            base = f_hurt;
        }
        else
        {
            const int into = _timer % s.period;
            base = into > int(s.period) - 26
                 ? (into > int(s.period) - 10 ? f_atk + ((_timer >> 2) & 1) : f_wind)
                 : f_idle + ((_timer >> 5) & 1);
        }

        if(base != _frame)
        {
            _frame = base;
            _sprite->set_tiles(sheet(_which).tiles_item().create_tiles(base));
        }

        _sprite->set_horizontal_flip(_facing_right);
        _sprite->set_position(_pos);
        _sprite->set_visible(_invuln <= 0 || ((_invuln >> 2) & 1) == 0);
    }

    boss_events boss::update(luv& player, level& lv, entities& ents)
    {
        boss_events ev;

        if(!_which)
        {
            return ev;
        }

        ++_timer;

        if(_dying)
        {
            ++_death_timer;
            _pos.set_y(_pos.y() + bn::fixed(0.4));
            _animate();
            ev.defeated = _death_timer >= death_frames;
            return ev;
        }

        if(_invuln > 0)
        {
            --_invuln;
        }

        _move(player, lv);

        const spec& s = specs[_which - 1];

        if((_timer % s.period) == 0 || _wall_hit)
        {
            _attack(player, ents);
            _wall_hit = false;
        }

        // --- taking damage
        bool wounded = false;

        if(_invuln <= 0)
        {
            if(ents.flame_hits(_pos.x(), _pos.y(), _half()))
            {
                wounded = true;
            }
            else if(player.overlaps(_pos.x(), _pos.y(), _half()))
            {
                // Coming down on it is a hit; anything else is a mistake.
                // Measuring against the boss's head gave almost no window,
                // because a boss on the same floor sits higher than Luv does.
                if(player.velocity_y() > 0)
                {
                    wounded = true;
                    player.bounce();
                }
                else
                {
                    // take_hit() decides whether a power-up eats it; either way
                    // the player felt it and the scene should react.
                    player.take_hit();
                    ev.hurt_player = true;
                }
            }
        }

        if(wounded)
        {
            --_health;
            _invuln = hit_invuln;
            ev.wounded = true;

            const int was = _phase;
            _phase = (_max_health - _health) * 3 / bn::max(_max_health, 1);

            if(_phase != was)
            {
                ev.phase = true;
            }

            if(_health <= 0)
            {
                _dying = true;
                _death_timer = 0;
                _frame = -1;
            }
        }

        _animate();
        return ev;
    }
}
