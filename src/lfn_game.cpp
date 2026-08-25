#include "lfn_game.h"

#include "bn_rect_window.h"
#include "bn_window.h"

#include "bn_format.h"
#include "bn_keypad.h"
#include "bn_sprite_tiles.h"
#include "bn_sprite_palette_items_text_gold.h"
#include "bn_sprite_palette_items_text_mag.h"
#include "bn_sprite_palette_ptr.h"

#include "lfn_audio.h"
#include "lfn_trace.h"
#include "lfn_tune.h"

namespace lfn
{
    namespace
    {
        constexpr int death_hold = 110;
        constexpr int clear_hold = 90;
        constexpr int cam_min_y = tune::screen_h / 2;
    }

    game::game(int level_index, const run_state& carried,
               bn::sprite_text_generator& text, int player, bool hand_off) :
        _hud(text),
        _text(text),
        _run(carried),
        _index(level_index),
        _hand_off(hand_off)
    {
        LFN_TRACE("tiles ctor start: ", bn::sprite_tiles::used_items_count());
        _camera = bn::camera_ptr::create(0, 0);
        _level.load(level_index, *_camera);

        const level_data& data = _level.data();

        for(int i = 0; i < data.spawn_count; ++i)
        {
            if(data.spawns[i].type == spawn_type::player)
            {
                _start = bn::fixed_point((data.spawns[i].x * tune::tile) + 8,
                                         (data.spawns[i].y * tune::tile) + 8);
                break;
            }
        }

        LFN_TRACE("tiles before player: ", bn::sprite_tiles::used_items_count());
        _player.create(_start.x(), _start.y(), *_camera);
        LFN_TRACE("tiles before entities: ", bn::sprite_tiles::used_items_count());
        _entities.load(data, *_camera);

        if(data.boss)
        {
            for(int i = 0; i < data.spawn_count; ++i)
            {
                if(data.spawns[i].type == spawn_type::boss)
                {
                    // The arenas all put their floor on the same row.
                    _boss_home = bn::fixed_point((data.spawns[i].x * tune::tile) + 8,
                                                 13 * tune::tile);
                    _boss.create(data.boss, _boss_home.x(), _boss_home.y(), *_camera);
                    break;
                }
            }
        }

        // Writing on the wall of a secret room, pinned to the world not the screen.
        if(data.secret)
        {
            for(int i = 0; i < data.spawn_count; ++i)
            {
                if(data.spawns[i].type == spawn_type::sign)
                {
                    _text.set_center_alignment();
                    _text.generate((data.spawns[i].x * tune::tile) + 8,
                                   (data.spawns[i].y * tune::tile) + 8,
                                   data.secret, _wall_text);

                    for(bn::sprite_ptr& sprite : _wall_text)
                    {
                        sprite.set_camera(*_camera);
                        sprite.set_palette(bn::sprite_palette_items::text_gold);
                        sprite.set_z_order(20);
                    }

                    break;
                }
            }
        }

        LFN_TRACE("tiles before hud: ", bn::sprite_tiles::used_items_count());
        _status.world = data.world;

        // Stages are not two to a world -- each world is two levels plus its
        // arena -- so the number has to be counted, not derived from parity.
        int stage = 0;

        for(int i = 0; i < level_index; ++i)
        {
            if(levels[i].world == data.world)
            {
                ++stage;
            }
        }

        _status.stage = stage;
        _status.player = player;
        _status.time = tune::stage_time;
        LFN_TRACE("tiles after hud: ", bn::sprite_tiles::used_items_count());
        _refresh_hud();
        _follow_camera();

        // Cut the level out of the top strip so the status row always reads
        // against the dark backdrop instead of whatever the stage happens to
        // have up there. A ceiling in a low room used to run straight through
        // the score.
        bn::rect_window bar = bn::rect_window::internal();
        bar.set_boundaries(-80, -120, -65, 120);
        bar.set_show_bg(_level.bg(), false);

        audio::play_music(data.music);
    }

    game::~game()
    {
        // The window is hardware state and outlives this object; menus and
        // cards must not inherit a black bar across their titles.
        bn::rect_window::internal().set_show_all();
    }

    void game::_say(const char* line, int bonus)
    {
        _banner.clear();
        _text.set_center_alignment();
        _text.generate(0, -20, line, _banner);

        for(bn::sprite_ptr& sprite : _banner)
        {
            sprite.set_palette(bn::sprite_palette_items::text_gold);
        }

        if(bonus > 0)
        {
            const int mark = _banner.size();
            _text.generate(0, 0, bn::format<28>("TIME BONUS {}", bonus), _banner);

            for(int i = mark; i < _banner.size(); ++i)
            {
                _banner[i].set_palette(bn::sprite_palette_items::text_mag);
            }
        }
    }

    void game::_add_score(int points)
    {
        _run.score = bn::min(_run.score + points, tune::score_max);
    }

    void game::_refresh_hud()
    {
        _status.lives = bn::max(_run.lives, 0);
        _status.souls = _run.souls;
        _status.score = _run.score;
        _status.hover = _player.hover_left();
        _status.hover_max = _player.hover_max();
        _status.boss = _boss.active() && !_boss.dying() ? _boss.health() : 0;
        _status.boss_max = _boss.max_health();
        _hud.update(_status);
    }

    void game::_restart()
    {
        const bn::fixed_point where = _entities.has_checkpoint()
                                    ? _entities.checkpoint_position() : _start;
        _player.respawn(where.x(), where.y());
        _status.time = tune::stage_time;
        _time_ticks = 0;
        _combo = 0;
        _follow_camera();
        _refresh_hud();
        audio::play_music(_level.data().music);
    }

    void game::_follow_camera()
    {
        const bn::fixed look = _player.facing_right() ? tune::cam_look_ahead
                                                      : -tune::cam_look_ahead;
        bn::fixed x = _camera->x();
        const bn::fixed target = _player.x() + look;

        // A deadzone keeps small hops from sliding the whole world around.
        if(target > x + tune::cam_deadzone_x)
        {
            x += (target - tune::cam_deadzone_x - x) * tune::cam_lerp;
        }
        else if(target < x - tune::cam_deadzone_x)
        {
            x += (target + tune::cam_deadzone_x - x) * tune::cam_lerp;
        }

        const bn::fixed max_x = _level.pixel_width() - (tune::screen_w / 2);
        x = bn::clamp(x, bn::fixed(tune::screen_w / 2), max_x);

        bn::fixed y = _camera->y() + ((_player.y() - _camera->y()) * bn::fixed(0.09));
        y = bn::clamp(y, bn::fixed(cam_min_y),
                      bn::fixed(_level.pixel_height() - cam_min_y));

        _camera->set_position(x, y);
    }

    void game::_handle(const luv_events& le, const world_events& we)
    {
        if(le.jumped)     { audio::sfx_jump(); }
        if(le.dashed)     { audio::sfx_dash(); }

        if(le.landed)
        {
            audio::sfx_land();
            _combo = 0;                  // the air chain ends when he touches down
        }

        if(le.smashed)
        {
            audio::sfx_smash();
            _entities.reveal(le.smash_col, le.smash_row);
            _add_score(tune::score_block);
            LFN_TRACE("ev: block smashed at ", le.smash_col, ",", le.smash_row);
        }

        if(le.shot)
        {
            _entities.spawn_flame(_player.x() + (_player.facing_right() ? 8 : -8),
                                  _player.y() - 2, _player.facing_right());
            audio::sfx_shot();
        }

        if(we.stomped)
        {
            // Chained stomps double in value, the way they should.
            int points = tune::score_stomp;

            for(int i = 0; i < _combo && points < tune::score_stomp * tune::score_combo_cap; ++i)
            {
                points *= 2;
            }

            _add_score(points);
            ++_combo;
            audio::sfx_stomp();
            LFN_TRACE("ev: stomp x", _combo, " for ", points);
        }

        if(we.powered_up)
        {
            _add_score(tune::score_power_up);
            audio::sfx_power_up();
            LFN_TRACE("ev: power-up");
        }

        if(we.checkpoint)
        {
            _add_score(tune::score_checkpoint);
            audio::sfx_checkpoint();
            LFN_TRACE("ev: checkpoint");
        }

        if(we.souls)
        {
            _run.souls += we.souls;
            _add_score(tune::score_soul * we.souls);
            audio::sfx_pickup();

            if(_run.souls >= tune::souls_per_life)
            {
                _run.souls -= tune::souls_per_life;
                ++_run.lives;
                _add_score(tune::score_one_up);
                audio::sfx_one_up();
            }
        }

        if(we.lives)
        {
            _run.lives += we.lives;
            _add_score(tune::score_one_up * we.lives);
            audio::sfx_one_up();
        }

        if(we.hurt || le.hurt)
        {
            audio::sfx_hurt();
        }

        _refresh_hud();
    }

    void game::_die()
    {
        if(!tune::test_invulnerable)
        {
            --_run.lives;
        }

        _combo = 0;
        LFN_TRACE("ev: died at col ", _player.x().right_shift_integer() / tune::tile,
                  ", lives left ", _run.lives);
        audio::stop_music();
        audio::sfx_death();

        if(_run.lives <= 0)
        {
            _result = game_result::game_over;
            audio::play_music(audio::track::game_over);
        }
        else if(_hand_off)
        {
            // Someone else is waiting: the turn ends here and this stage
            // starts over when the pad comes back.
            _result = game_result::handed_over;
        }
        else
        {
            _result = game_result::running;
            _entities.load(_level.data(), *_camera);

            if(_level.data().boss)
            {
                // Losing a life restarts the fight rather than the world.
                _boss.create(_level.data().boss, _boss_home.x(), _boss_home.y(),
                             *_camera);
            }
        }

        _hold = death_hold;
        _say(_run.lives <= 0 ? "NO LIVES LEFT"
                            : (_hand_off ? "YOUR TURN IS OVER" : "ONE LESS LIFE"), 0);
        _refresh_hud();
    }

    game_result game::update()
    {
        audio::new_frame();

        if constexpr(tune::test_fragile > 0)
        {
            // Harness only: die on a fixed clock so turn hand-off can be
            // driven without needing the pilot to find a pit.
            if(_hold == 0 && ++_alive == tune::test_fragile)
            {
                _alive = 0;
                _die();
                return game_result::running;
            }
        }

        if(_hold > 0)
        {
            --_hold;
            _follow_camera();

            if(_hold == 0)
            {
                _banner.clear();

                if(_result != game_result::running)
                {
                    return _result;
                }

                _restart();
            }

            return game_result::running;
        }

        const luv_events le = _player.update(_level);
        const world_events we = _entities.update(_player, _level);
        const boss_events be = _boss.update(_player, _level, _entities);
        _handle(le, we);

        if(be.wounded)
        {
            _add_score(tune::score_boss_hit);
            audio::sfx_boss_hit();
            LFN_TRACE("ev: boss wounded, hp ", _boss.health());
        }

        if(be.hurt_player)
        {
            audio::sfx_hurt();
        }

        if(be.defeated)
        {
            // Beating the boss is what clears a boss stage; there is no gate.
            _add_score(tune::score_boss + (_status.time * tune::score_time_bonus));
            LFN_TRACE("ev: BOSS DEFEATED, score ", _run.score);
            _refresh_hud();
            _say("THE SIN IS UNDONE", _status.time * tune::score_time_bonus);
            _result = game_result::level_cleared;
            _hold = clear_hold;
            audio::stop_music();
            audio::sfx_boss_die();
            return game_result::running;
        }

        if(we.warped)
        {
            LFN_TRACE("ev: WARPED to ", _level.data().warp);
            _warped = true;
            _refresh_hud();
            _say("A WAY THROUGH", 0);
            _result = game_result::level_cleared;
            _hold = clear_hold;
            audio::stop_music();
            audio::sfx_checkpoint();
            return game_result::running;
        }

        if(we.exited)
        {
            // Whatever is left on the clock is worth points.
            _add_score(_status.time * tune::score_time_bonus);
            LFN_TRACE("ev: EXIT REACHED, bonus ", _status.time * tune::score_time_bonus,
                      ", score ", _run.score);
            _refresh_hud();
            _say("STAGE CLEAR", _status.time * tune::score_time_bonus);
            _result = game_result::level_cleared;
            _hold = clear_hold;
            audio::stop_music();
            audio::sfx_level_clear();
            return game_result::running;
        }

        if(le.died)
        {
            _die();
            return game_result::running;
        }

        // The clock only runs while Luv is alive and playing. The test harness
        // stops it, so a slow autoplay is not fighting the timer as well.
        if(!tune::test_invulnerable && ++_time_ticks >= tune::time_frames)
        {
            _time_ticks = 0;

            if(_status.time > 0)
            {
                --_status.time;
                _refresh_hud();
            }
            else
            {
                LFN_TRACE("ev: out of time");
                _die();
                return game_result::running;
            }
        }

        _follow_camera();
        return game_result::running;
    }
}
