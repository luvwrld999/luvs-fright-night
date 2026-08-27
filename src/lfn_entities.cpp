#include "lfn_entities.h"

#include "lfn_trace.h"

#include "bn_math.h"
#include "bn_sprite_tiles_ptr.h"

#include "bn_sprite_items_bone_bat.h"
#include "bn_sprite_items_censer_wraith.h"
#include "bn_sprite_items_checkpoint.h"
#include "bn_sprite_items_cherub_fiend.h"
#include "bn_sprite_items_gate.h"
#include "bn_sprite_items_gnasher.h"
#include "bn_sprite_items_halo_imp.h"
#include "bn_sprite_items_one_up.h"
#include "bn_sprite_items_pu_purple_soul.h"
#include "bn_sprite_items_pu_devil_dash.h"
#include "bn_sprite_items_pu_soul_flame.h"
#include "bn_sprite_items_pu_wisp_wings.h"
#include "bn_sprite_items_soul_flame.h"
#include "bn_sprite_items_soul_bonus.h"
#include "bn_sprite_items_soul_orb.h"
#include "bn_sprite_items_spike_flame.h"

namespace lfn
{
    namespace
    {
        // Entities only exist as sprites while they are near the view.
        constexpr int wake_distance = 160;
        constexpr int sleep_distance = 200;

        [[nodiscard]] bool is_enemy(ent_kind k)
        {
            return k >= ent_kind::imp && k <= ent_kind::jet;
        }

        [[nodiscard]] bool is_pickup(ent_kind k)
        {
            return k >= ent_kind::soul && k <= ent_kind::one_up;
        }

        /**
         * How many frames each kind's sheet actually holds.
         *
         * Every kind is listed. This used to end in `default: return 4`, and a
         * warp door - which draws with the two frame gate sheet - inherited
         * that four, walked its animation onto frame 2 and tripped Butano's
         * bounds assert the moment one came on screen. A silent default is not
         * worth the lines it saves when the cost of being wrong is the game
         * stopping dead.
         */
        [[nodiscard]] int frames_of(ent_kind k)
        {
            switch(k)
            {
            case ent_kind::imp:
            case ent_kind::cherub:
            case ent_kind::gnasher:
            case ent_kind::wraith:
            case ent_kind::bat:
            case ent_kind::jet:
            case ent_kind::soul:
            case ent_kind::soul_ten:
            case ent_kind::flame:
            case ent_kind::ember:
            case ent_kind::puff:
            case ent_kind::checkpoint:
                return 4;
            case ent_kind::pu_flame:
            case ent_kind::pu_soul:
            case ent_kind::pu_dash:
            case ent_kind::pu_wings:
            case ent_kind::one_up:
            case ent_kind::exit_gate:
            case ent_kind::warp:
                return 2;
            // A count of one can never index past the end of any sheet, so a
            // kind added without being listed here misdraws rather than
            // halting the game.
            case ent_kind::none:
            default:
                return 1;
            }
        }

        bn::sprite_ptr make_sprite(ent_kind k, bn::fixed x, bn::fixed y)
        {
            switch(k)
            {
            case ent_kind::imp:        return bn::sprite_items::halo_imp.create_sprite(x, y);
            case ent_kind::cherub:     return bn::sprite_items::cherub_fiend.create_sprite(x, y);
            case ent_kind::gnasher:    return bn::sprite_items::gnasher.create_sprite(x, y);
            case ent_kind::wraith:     return bn::sprite_items::censer_wraith.create_sprite(x, y);
            case ent_kind::bat:        return bn::sprite_items::bone_bat.create_sprite(x, y);
            case ent_kind::jet:        return bn::sprite_items::spike_flame.create_sprite(x, y);
            case ent_kind::soul:       return bn::sprite_items::soul_orb.create_sprite(x, y);
            case ent_kind::soul_ten:   return bn::sprite_items::soul_bonus.create_sprite(x, y);
            case ent_kind::pu_flame:   return bn::sprite_items::pu_soul_flame.create_sprite(x, y);
            case ent_kind::pu_soul:    return bn::sprite_items::pu_purple_soul.create_sprite(x, y);
            case ent_kind::pu_dash:    return bn::sprite_items::pu_devil_dash.create_sprite(x, y);
            case ent_kind::pu_wings:   return bn::sprite_items::pu_wisp_wings.create_sprite(x, y);
            case ent_kind::one_up:     return bn::sprite_items::one_up.create_sprite(x, y);
            case ent_kind::checkpoint: return bn::sprite_items::checkpoint.create_sprite(x, y);
            case ent_kind::exit_gate:
            case ent_kind::warp:       return bn::sprite_items::gate.create_sprite(x, y);
            case ent_kind::ember:
            case ent_kind::puff:       return bn::sprite_items::soul_flame.create_sprite(x, y);
            default:                   return bn::sprite_items::soul_flame.create_sprite(x, y);
            }
        }

        void set_frame(entity& e, int frame)
        {
            // Entities keep thinking in the band between wake and sleep range,
            // where they have no sprite to animate yet.
            if(!e.sprite)
            {
                return;
            }

            const int count = frames_of(e.kind);
            const int f = frame % count;

            if(f == e.frame)
            {
                return;
            }

            e.frame = uint8_t(f);

            switch(e.kind)
            {
            case ent_kind::imp:        e.sprite->set_tiles(bn::sprite_items::halo_imp.tiles_item().create_tiles(f)); break;
            case ent_kind::cherub:     e.sprite->set_tiles(bn::sprite_items::cherub_fiend.tiles_item().create_tiles(f)); break;
            case ent_kind::gnasher:    e.sprite->set_tiles(bn::sprite_items::gnasher.tiles_item().create_tiles(f)); break;
            case ent_kind::wraith:     e.sprite->set_tiles(bn::sprite_items::censer_wraith.tiles_item().create_tiles(f)); break;
            case ent_kind::bat:        e.sprite->set_tiles(bn::sprite_items::bone_bat.tiles_item().create_tiles(f)); break;
            case ent_kind::jet:        e.sprite->set_tiles(bn::sprite_items::spike_flame.tiles_item().create_tiles(f)); break;
            case ent_kind::soul:       e.sprite->set_tiles(bn::sprite_items::soul_orb.tiles_item().create_tiles(f)); break;
            case ent_kind::soul_ten:   e.sprite->set_tiles(bn::sprite_items::soul_bonus.tiles_item().create_tiles(f)); break;
            case ent_kind::pu_flame:   e.sprite->set_tiles(bn::sprite_items::pu_soul_flame.tiles_item().create_tiles(f)); break;
            case ent_kind::pu_soul:    e.sprite->set_tiles(bn::sprite_items::pu_purple_soul.tiles_item().create_tiles(f)); break;
            case ent_kind::pu_dash:    e.sprite->set_tiles(bn::sprite_items::pu_devil_dash.tiles_item().create_tiles(f)); break;
            case ent_kind::pu_wings:   e.sprite->set_tiles(bn::sprite_items::pu_wisp_wings.tiles_item().create_tiles(f)); break;
            case ent_kind::one_up:     e.sprite->set_tiles(bn::sprite_items::one_up.tiles_item().create_tiles(f)); break;
            case ent_kind::checkpoint: e.sprite->set_tiles(bn::sprite_items::checkpoint.tiles_item().create_tiles(f)); break;
            case ent_kind::exit_gate:
            case ent_kind::warp:       e.sprite->set_tiles(bn::sprite_items::gate.tiles_item().create_tiles(f)); break;
            case ent_kind::flame:
            case ent_kind::ember:
            case ent_kind::puff:       e.sprite->set_tiles(bn::sprite_items::soul_flame.tiles_item().create_tiles(f)); break;
            default: break;
            }
        }

        ent_kind kind_of_spawn(uint8_t type)
        {
            switch(type)
            {
            case spawn_type::imp:        return ent_kind::imp;
            case spawn_type::cherub:     return ent_kind::cherub;
            case spawn_type::gnasher:    return ent_kind::gnasher;
            case spawn_type::wraith:     return ent_kind::wraith;
            case spawn_type::bat:        return ent_kind::bat;
            case spawn_type::jet:        return ent_kind::jet;
            case spawn_type::soul:       return ent_kind::soul;
            case spawn_type::soul_ten:   return ent_kind::soul_ten;
            case spawn_type::pu_flame:   return ent_kind::pu_flame;
            case spawn_type::pu_soul:    return ent_kind::pu_soul;
            case spawn_type::pu_dash:    return ent_kind::pu_dash;
            case spawn_type::pu_wings:   return ent_kind::pu_wings;
            case spawn_type::one_up:     return ent_kind::one_up;
            case spawn_type::checkpoint: return ent_kind::checkpoint;
            case spawn_type::exit:       return ent_kind::exit_gate;
            case spawn_type::warp:       return ent_kind::warp;
            default:                     return ent_kind::none;
            }
        }
    }

    void entities::clear()
    {
        _pool.clear();
        _has_checkpoint = false;
    }

    void entities::load(const level_data& data, bn::camera_ptr& camera)
    {
        clear();
        _camera = camera;

        for(int i = 0; i < data.spawn_count; ++i)
        {
            const spawn_point& sp = data.spawns[i];
            const ent_kind kind = kind_of_spawn(sp.type);

            if(kind == ent_kind::none || _pool.full())
            {
                continue;
            }

            entity e;
            e.kind = kind;
            e.pos = bn::fixed_point((sp.x * tune::tile) + 8, (sp.y * tune::tile) + 8);
            e.home = e.pos;
            e.alive = true;

            // A pickup authored on top of a breakable block is that block's
            // contents: it stays sealed until Luv knocks the block open.
            if(is_pickup(kind) &&
               data.tiles[(sp.y * data.columns) + sp.x] == tile::breakable)
            {
                e.hidden = true;
            }
            e.timer = i * 7;                 // stagger so they don't animate in lockstep
            e.facing_right = (i & 1) != 0;

            if(kind == ent_kind::imp || kind == ent_kind::gnasher)
            {
                e.vel.set_x(e.facing_right ? tune::imp_speed : -tune::imp_speed);
            }
            else if(kind == ent_kind::cherub)
            {
                e.vel.set_x(e.facing_right ? tune::cherub_speed : -tune::cherub_speed);
            }

            _pool.push_back(bn::move(e));
        }
    }

    entity* entities::_free_slot()
    {
        for(entity& e : _pool)
        {
            if(!e.alive)
            {
                return &e;
            }
        }

        if(!_pool.full())
        {
            _pool.push_back(entity());
            return &_pool.back();
        }

        return nullptr;
    }

    void entities::spawn_flame(bn::fixed x, bn::fixed y, bool right)
    {
        entity* slot = _free_slot();

        if(!slot)
        {
            return;
        }

        *slot = entity();
        slot->kind = ent_kind::flame;
        slot->pos = bn::fixed_point(x, y);
        slot->vel = bn::fixed_point(right ? tune::flame_speed : -tune::flame_speed, -1);
        slot->alive = true;
        slot->life = tune::flame_life;
        _wake(*slot);
    }

    void entities::reveal(int col, int row)
    {
        for(entity& e : _pool)
        {
            if(!e.alive || !e.hidden)
            {
                continue;
            }

            if(e.home.x().right_shift_integer() / tune::tile != col ||
               e.home.y().right_shift_integer() / tune::tile != row)
            {
                continue;
            }

            // Pop it out of the block and let it drop to the floor, so it
            // ends up somewhere Luv can simply walk into.
            e.hidden = false;
            e.life = 1;
            e.vel.set_y(-2.4);
            _wake(e);
            LFN_TRACE("ev: prize out of block ", col, ",", row);
            return;
        }
    }

    void entities::spawn_shot(bn::fixed x, bn::fixed y, bn::fixed vx, bn::fixed vy,
                              int life)
    {
        entity* slot = _free_slot();

        if(!slot)
        {
            return;
        }

        *slot = entity();
        slot->kind = ent_kind::ember;
        slot->pos = bn::fixed_point(x, y);
        slot->vel = bn::fixed_point(vx, vy);
        slot->alive = true;
        slot->life = life;
        _wake(*slot);
    }

    void entities::spawn_puff(bn::fixed x, bn::fixed y)
    {
        entity* slot = _free_slot();

        if(!slot)
        {
            return;
        }

        // Enemies used to vanish on the frame they died, so a stomp that
        // landed looked exactly like one that missed. This rises and fades
        // out over about a fifth of a second.
        *slot = entity();
        slot->kind = ent_kind::puff;
        slot->pos = bn::fixed_point(x, y);
        slot->vel = bn::fixed_point(0, -0.7);
        slot->alive = true;
        slot->life = 14;
        _wake(*slot);
    }

    void entities::spawn_enemy(ent_kind kind, bn::fixed x, bn::fixed y)
    {
        entity* slot = _free_slot();

        if(!slot)
        {
            return;
        }

        *slot = entity();
        slot->kind = kind;
        slot->pos = bn::fixed_point(x, y);
        slot->home = slot->pos;
        slot->alive = true;
        slot->vel.set_x(tune::imp_speed);
        _wake(*slot);
    }

    int entities::live_enemies() const
    {
        int count = 0;

        for(const entity& e : _pool)
        {
            if(e.alive && !e.hidden && is_enemy(e.kind))
            {
                ++count;
            }
        }

        return count;
    }

    bool entities::flame_hits(bn::fixed x, bn::fixed y, int half)
    {
        for(entity& e : _pool)
        {
            if(!e.alive || e.kind != ent_kind::flame)
            {
                continue;
            }

            const bn::fixed dx = e.pos.x() - x;
            const bn::fixed dy = e.pos.y() - y;
            const int reach = half + 4;

            if(dx > -reach && dx < reach && dy > -reach && dy < reach)
            {
                e.alive = false;
                _sleep(e);
                return true;
            }
        }

        return false;
    }

    void entities::_wake(entity& e)
    {
        if(e.awake)
        {
            return;
        }

        e.sprite = make_sprite(e.kind, e.pos.x(), e.pos.y());
        e.sprite->set_camera(*_camera);
        // In front of both background layers; Butano starts sprites at 3.
        e.sprite->set_bg_priority(1);
        e.awake = true;
        e.frame = 0xFF;                      // force the next set_frame to apply
    }

    void entities::_sleep(entity& e)
    {
        e.sprite.reset();
        e.awake = false;
    }

    void entities::_behave(entity& e, luv& player, level& lv, world_events& ev)
    {
        ++e.timer;

        switch(e.kind)
        {
        case ent_kind::imp:
        {
            e.pos.set_x(e.pos.x() + e.vel.x());
            const int px = e.pos.x().right_shift_integer();
            const int py = e.pos.y().right_shift_integer();
            const int ahead = e.vel.x() > 0 ? px + tune::enemy_half + 1 : px - tune::enemy_half - 1;

            // Turn at a wall, and at the edge of the floor - imps never jump.
            if(lv.blocks(ahead, py) || !lv.blocks(ahead, py + tune::enemy_half + 4))
            {
                e.vel.set_x(-e.vel.x());
                e.pos.set_x(e.pos.x() + e.vel.x());
            }

            e.facing_right = e.vel.x() > 0;
            set_frame(e, e.timer >> 3);
            break;
        }

        case ent_kind::gnasher:
        {
            const bn::fixed dx = player.x() - e.pos.x();
            const bn::fixed adx = dx < 0 ? -dx : dx;
            const bn::fixed dy = player.y() - e.pos.y();
            const bn::fixed ady = dy < 0 ? -dy : dy;
            const bool charging = adx < 88 && ady < 24;

            if(charging)
            {
                e.vel.set_x(dx > 0 ? tune::gnasher_charge : -tune::gnasher_charge);
            }
            else if(e.vel.x() > -tune::gnasher_speed && e.vel.x() < tune::gnasher_speed)
            {
                e.vel.set_x(e.facing_right ? tune::gnasher_speed : -tune::gnasher_speed);
            }
            else
            {
                e.vel.set_x(e.vel.x() * bn::fixed(0.92));
            }

            e.pos.set_x(e.pos.x() + e.vel.x());
            const int px = e.pos.x().right_shift_integer();
            const int py = e.pos.y().right_shift_integer();
            const int ahead = e.vel.x() > 0 ? px + tune::enemy_half + 1 : px - tune::enemy_half - 1;

            if(lv.blocks(ahead, py) || !lv.blocks(ahead, py + tune::enemy_half + 4))
            {
                e.vel.set_x(-e.vel.x() * bn::fixed(0.5));
                e.facing_right = !e.facing_right;
                e.pos.set_x(e.pos.x() + e.vel.x());
            }

            set_frame(e, charging ? 2 + ((e.timer >> 2) & 1) : (e.timer >> 4) & 1);
            break;
        }

        case ent_kind::cherub:
        {
            e.pos.set_x(e.pos.x() + e.vel.x());
            e.pos.set_y(e.home.y() + bn::lut_sin((e.timer * 8) & 2047) * tune::cherub_amp);

            const int px = e.pos.x().right_shift_integer();
            const int py = e.pos.y().right_shift_integer();

            if(lv.blocks(px + (e.vel.x() > 0 ? 10 : -10), py))
            {
                e.vel.set_x(-e.vel.x());
            }

            e.facing_right = e.vel.x() > 0;
            set_frame(e, e.timer >> 3);
            break;
        }

        case ent_kind::bat:
        {
            // 0 hover, 1 wind-up, 2 diving, 3 resting, 4 climbing back.
            // It spends most of its life in the air, and the wind-up gives you
            // a beat to move before it drops.
            const bn::fixed dx = player.x() - e.pos.x();
            const bn::fixed adx = dx < 0 ? -dx : dx;

            if(e.life == 0)
            {
                e.pos.set_y(e.home.y() +
                            bn::lut_sin((e.timer * 7) & 2047) * tune::bat_bob);

                if(adx < 30 && player.y() > e.pos.y())
                {
                    e.life = 1;
                    e.timer = 0;
                }
            }
            else if(e.life == 1)
            {
                e.pos.set_x(e.home.x() + (((e.timer >> 1) & 1) ? 1 : -1));

                if(e.timer >= tune::bat_windup)
                {
                    e.life = 2;
                }
            }
            else if(e.life == 2)
            {
                e.pos.set_y(e.pos.y() + tune::bat_dive);

                if(lv.blocks(e.pos.x().right_shift_integer(),
                             e.pos.y().right_shift_integer() + tune::enemy_half))
                {
                    e.life = 3;
                    e.timer = 0;
                }
            }
            else if(e.life == 3)
            {
                if(e.timer >= tune::bat_rest)
                {
                    e.life = 4;
                }
            }
            else
            {
                e.pos.set_x(e.home.x());
                e.pos.set_y(e.pos.y() - tune::bat_rise);

                if(e.pos.y() <= e.home.y())
                {
                    e.pos.set_y(e.home.y());
                    e.life = 0;
                }
            }

            set_frame(e, e.life == 1 ? 2 : (e.life == 2 ? 3 : ((e.timer >> 4) & 1)));
            break;
        }


        case ent_kind::wraith:
        {
            e.pos.set_y(e.home.y() + bn::lut_sin((e.timer * 6) & 2047) * 6);

            if((e.timer % 110) == 0)
            {
                entity* shot = _free_slot();

                if(shot)
                {
                    const bn::fixed dx = player.x() - e.pos.x();
                    *shot = entity();
                    shot->kind = ent_kind::ember;
                    shot->pos = e.pos;
                    shot->vel = bn::fixed_point(dx > 0 ? tune::ember_speed : -tune::ember_speed,
                                                bn::fixed(0.35));
                    shot->alive = true;
                    shot->life = 180;
                    _wake(*shot);
                }
            }

            set_frame(e, e.timer >> 3);
            break;
        }

        case ent_kind::jet:
            set_frame(e, e.timer >> 3);
            break;

        case ent_kind::flame:
        {
            e.pos.set_x(e.pos.x() + e.vel.x());
            e.vel.set_y(e.vel.y() + bn::fixed(0.18));
            e.pos.set_y(e.pos.y() + e.vel.y());

            const int px = e.pos.x().right_shift_integer();
            const int py = e.pos.y().right_shift_integer();

            if(lv.blocks(px, py + 4) && e.vel.y() > 0)
            {
                e.vel.set_y(tune::flame_bounce);
            }

            if(lv.blocks(px + (e.vel.x() > 0 ? 4 : -4), py) || --e.life <= 0)
            {
                e.alive = false;
                _sleep(e);
                return;
            }

            set_frame(e, e.timer >> 2);
            break;
        }

        case ent_kind::puff:
        {
            // Rises, slows, and goes out. It hurts nothing on the way.
            e.pos.set_y(e.pos.y() + e.vel.y());
            e.vel.set_y(e.vel.y() * bn::fixed(0.88));

            if(--e.life <= 0)
            {
                e.alive = false;
                _sleep(e);
                return;
            }

            set_frame(e, (14 - e.life) >> 2);
            break;
        }

        case ent_kind::ember:
        {
            e.pos.set_x(e.pos.x() + e.vel.x());
            e.pos.set_y(e.pos.y() + e.vel.y());

            const int px = e.pos.x().right_shift_integer();
            const int py = e.pos.y().right_shift_integer();

            if(lv.blocks(px, py) || --e.life <= 0)
            {
                e.alive = false;
                _sleep(e);
                return;
            }

            set_frame(e, e.timer >> 2);
            break;
        }

        case ent_kind::soul:
            e.pos.set_y(e.home.y() + bn::lut_sin((e.timer * 18) & 2047) * 2);
            set_frame(e, e.timer >> 3);
            break;

        case ent_kind::checkpoint:
            set_frame(e, e.life ? 2 + ((e.timer >> 3) & 1) : 0);
            break;

        default:                             // pickups and the exit gate
            if(e.life == 1)                  // thrown out of a block, still falling
            {
                e.vel.set_y(e.vel.y() + bn::fixed(0.22));
                e.pos.set_y(e.pos.y() + e.vel.y());

                const int px = e.pos.x().right_shift_integer();
                const int foot = e.pos.y().right_shift_integer() + tune::enemy_half;

                if(e.vel.y() > 0 && lv.blocks(px, foot))
                {
                    e.pos.set_y(((foot / tune::tile) * tune::tile) - tune::enemy_half);
                    e.vel.set_y(0);
                    e.home = e.pos;
                    e.life = 0;
                }
            }
            else
            {
                e.pos.set_y(e.home.y() + bn::lut_sin((e.timer * 12) & 2047) * 2);
            }

            set_frame(e, e.timer >> 4);
            break;
        }

        (void) ev;
    }

    void entities::_collide(entity& e, luv& player, world_events& ev)
    {
        const int half = (e.kind == ent_kind::exit_gate ||
                          e.kind == ent_kind::warp) ? 12 : tune::enemy_half;

        if(!player.overlaps(e.pos.x(), e.pos.y(), half))
        {
            return;
        }

        if(is_enemy(e.kind))
        {
            const bool from_above = player.velocity_y() > 0 &&
                                    player.y() < e.pos.y() - 4;

            if(e.kind != ent_kind::jet && (from_above || player.dashing()))
            {
                const bn::fixed_point where = e.pos;
                e.alive = false;
                _sleep(e);
                spawn_puff(where.x(), where.y());
                ev.stomped = true;
                ev.enemy_killed = true;

                if(from_above)
                {
                    player.bounce();
                }
            }
            else
            {
                // take_hit() decides whether a power-up absorbs it; either way
                // the player felt something, so the scene gets told.
                player.take_hit();
                ev.hurt = true;
            }

            return;
        }

        if(e.kind == ent_kind::ember)
        {
            player.take_hit();
            ev.hurt = true;
            e.alive = false;
            _sleep(e);
            return;
        }

        if(is_pickup(e.kind))
        {
            switch(e.kind)
            {
            case ent_kind::soul:     ev.souls += 1; break;
            case ent_kind::soul_ten: ev.souls += tune::bonus_soul_worth; break;
            case ent_kind::one_up:   ev.lives += 1; break;
            case ent_kind::pu_flame: player.carrying().flame = true; ev.powered_up = true; break;
            case ent_kind::pu_soul:  player.carrying().soul = true;  ev.powered_up = true; break;
            case ent_kind::pu_dash:  player.carrying().dash = true;  ev.powered_up = true; break;
            case ent_kind::pu_wings: player.carrying().wings = true; ev.powered_up = true; break;
            default: break;
            }

            e.alive = false;
            _sleep(e);
            return;
        }

        if(e.kind == ent_kind::checkpoint && !e.life)
        {
            e.life = 1;
            _checkpoint = bn::fixed_point(e.pos.x(), e.pos.y() - 8);
            _has_checkpoint = true;
            ev.checkpoint = true;
            return;
        }

        if(e.kind == ent_kind::exit_gate)
        {
            ev.exited = true;
        }
        else if(e.kind == ent_kind::warp)
        {
            ev.warped = true;
        }
    }

    bool entities::_burn(entity& target)
    {
        for(entity& shot : _pool)
        {
            if(!shot.alive || shot.kind != ent_kind::flame)
            {
                continue;
            }

            const bn::fixed dx = shot.pos.x() - target.pos.x();
            const bn::fixed dy = shot.pos.y() - target.pos.y();
            const int reach = tune::enemy_half + 4;

            if(dx > -reach && dx < reach && dy > -reach && dy < reach)
            {
                const bn::fixed_point where = target.pos;
                shot.alive = false;
                _sleep(shot);
                target.alive = false;
                _sleep(target);
                spawn_puff(where.x(), where.y());
                return true;
            }
        }

        return false;
    }

    void entities::_draw(entity& e)
    {
        if(e.sprite)
        {
            e.sprite->set_position(e.pos);
            e.sprite->set_horizontal_flip(e.facing_right);
        }
    }

    world_events entities::update(luv& player, level& lv)
    {
        world_events ev;
        _cam_x = player.x();

        for(entity& e : _pool)
        {
            if(!e.alive || e.hidden)
            {
                continue;
            }

            const bn::fixed dx = e.pos.x() - _cam_x;
            const bn::fixed adx = dx < 0 ? -dx : dx;

            if(adx > sleep_distance)
            {
                if(e.awake)
                {
                    _sleep(e);
                }

                // Off-screen enemies stop thinking, but projectiles must still
                // expire or the pool leaks.
                if(e.kind != ent_kind::flame && e.kind != ent_kind::ember)
                {
                    continue;
                }
            }
            else if(!e.awake && adx < wake_distance)
            {
                _wake(e);
            }

            _behave(e, player, lv, ev);

            if(e.alive && !player.dead())
            {
                _collide(e, player, ev);
            }

            // A soul flame in flight burns whatever enemy it reaches.
            if(e.alive && is_enemy(e.kind) && e.kind != ent_kind::jet &&
               _burn(e))
            {
                ev.enemy_killed = true;
                ev.stomped = true;
                continue;
            }

            if(e.alive)
            {
                _draw(e);
            }
        }

        return ev;
    }
}
