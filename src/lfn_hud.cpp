#include "lfn_hud.h"

#include "bn_format.h"
#include "bn_sprite_items_hud_halo.h"
#include "bn_sprite_items_hud_meter.h"
#include "bn_sprite_items_soul_orb.h"
#include "bn_sprite_tiles_ptr.h"

namespace lfn
{
    namespace
    {
        // One row across the top, laid out like a cartridge status bar.
        constexpr int row = -73;
        constexpr int lives_x = -116;
        constexpr int soul_icon_x = -84;
        constexpr int souls_x = -76;
        constexpr int world_x = -30;
        constexpr int time_x = 22;
        constexpr int score_x = 66;
        constexpr int meter_x = -116;
        constexpr int meter_y = -58;
        constexpr int meter_pips = 6;
        constexpr int boss_pips = 10;
        constexpr int boss_x = 118;
        constexpr int boss_y = -58;
        // Second row, left of the boss pips, so it never fights the status bar.
        constexpr int player_x = -84;

        const char* const ROMAN[] = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII"};
    }

    bn::string<12> zero_pad(int value, int digits)
    {
        bn::string<12> out;
        int scale = 1;

        for(int i = 1; i < digits; ++i)
        {
            scale *= 10;
        }

        for(; scale > 0; scale /= 10)
        {
            out.push_back(char('0' + ((value / scale) % 10)));
        }

        return out;
    }

    const char* roman(int world)
    {
        return ROMAN[world < 0 ? 0 : (world > 7 ? 7 : world)];
    }

    hud::hud(bn::sprite_text_generator& text) :
        _text(text),
        _soul_icon(bn::sprite_items::soul_orb.create_sprite(soul_icon_x, row + 1))
    {
        _text.set_left_alignment();
        _soul_icon.set_bg_priority(0);

        for(int i = 0; i < meter_pips; ++i)
        {
            bn::sprite_ptr pip = bn::sprite_items::hud_meter.create_sprite(
                        meter_x + (i * 7), meter_y, 0);
            pip.set_bg_priority(0);
            _meter.push_back(bn::move(pip));
        }
    }

    void hud::_show(bn::vector<bn::sprite_ptr, 6>& into, int x, const char* str)
    {
        into.clear();
        _text.generate(x, row, str, into);

        for(bn::sprite_ptr& sprite : into)
        {
            sprite.set_visible(_visible);
        }
    }

    void hud::update(const status& now)
    {
        if(_first || now.lives != _shown.lives)
        {
            _life_icons.clear();
            const int shown = bn::clamp(now.lives, 0, 3);

            for(int i = 0; i < shown; ++i)
            {
                bn::sprite_ptr icon = bn::sprite_items::hud_halo.create_sprite(
                            lives_x + (i * 9), row + 1);
                icon.set_visible(_visible);
                _life_icons.push_back(bn::move(icon));
            }
        }

        if(_first || now.souls != _shown.souls)
        {
            _show(_souls_text, souls_x, bn::format<4>("{}", now.souls).c_str());
        }

        if(_first || now.world != _shown.world || now.stage != _shown.stage)
        {
            _show(_world_text, world_x,
                  bn::format<8>("{}-{}", roman(now.world), now.stage + 1).c_str());
        }

        if(_first || now.time != _shown.time)
        {
            _show(_time_text, time_x, bn::format<6>("{}", now.time).c_str());
        }

        if(_first || now.score != _shown.score)
        {
            // Fixed width, so the number never jitters as it grows.
            _score_text.clear();
            _text.generate(score_x, row, zero_pad(now.score, 6), _score_text);

            for(bn::sprite_ptr& sprite : _score_text)
            {
                sprite.set_visible(_visible);
            }
        }

        // Whose turn it is, on the meter row -- the top row has no space left
        // and the marker has to stay visible the whole time.
        if(_first || now.player != _shown.player)
        {
            _player_text.clear();

            if(now.player)
            {
                _text.generate(player_x, meter_y - 3,
                               bn::format<4>("P{}", now.player), _player_text);

                for(bn::sprite_ptr& sprite : _player_text)
                {
                    sprite.set_bg_priority(0);
                    sprite.set_visible(_visible);
                }
            }
        }

        const int pips = now.hover_max > 0
                       ? (now.hover * meter_pips + now.hover_max - 1) / now.hover_max
                       : 0;
        const int was = _shown.hover_max > 0
                      ? (_shown.hover * meter_pips + _shown.hover_max - 1) / _shown.hover_max
                      : -1;

        if(_first || pips != was)
        {
            for(int i = 0; i < meter_pips; ++i)
            {
                _meter[i].set_tiles(bn::sprite_items::hud_meter.tiles_item()
                                    .create_tiles(i < pips ? 1 : 0));
            }
        }

        // The boss bar only exists while there is a boss, and fills from the
        // right so it reads as its health draining toward the edge.
        if(_first || now.boss != _shown.boss || now.boss_max != _shown.boss_max)
        {
            _boss_pips.clear();

            for(int i = 0; i < bn::min(now.boss, boss_pips); ++i)
            {
                bn::sprite_ptr pip = bn::sprite_items::hud_meter.create_sprite(
                            boss_x - (i * 7), boss_y, 1);
                pip.set_bg_priority(0);
                pip.set_visible(_visible);
                _boss_pips.push_back(bn::move(pip));
            }
        }

        _shown = now;
        _first = false;
    }

    void hud::set_visible(bool visible)
    {
        _visible = visible;
        _soul_icon.set_visible(visible);

        for(bn::sprite_ptr& sprite : _life_icons) { sprite.set_visible(visible); }
        for(bn::sprite_ptr& sprite : _meter)      { sprite.set_visible(visible); }
        for(bn::sprite_ptr& sprite : _souls_text) { sprite.set_visible(visible); }
        for(bn::sprite_ptr& sprite : _world_text) { sprite.set_visible(visible); }
        for(bn::sprite_ptr& sprite : _time_text)  { sprite.set_visible(visible); }
        for(bn::sprite_ptr& sprite : _score_text) { sprite.set_visible(visible); }
        for(bn::sprite_ptr& sprite : _boss_pips)  { sprite.set_visible(visible); }
        for(bn::sprite_ptr& sprite : _player_text){ sprite.set_visible(visible); }
    }
}
