#ifndef LFN_HUD_H
#define LFN_HUD_H

#include "bn_sprite_ptr.h"
#include "bn_sprite_text_generator.h"
#include "bn_string.h"
#include "bn_vector.h"

namespace lfn
{
    /**
     * The bottom edge of the status strip, in screen space.
     *
     * The game cuts both background layers out of this band with a rect
     * window, and the entities hide anything that would draw inside it -
     * a window clips backgrounds but not sprites. Both need the same number.
     */
    constexpr int strip_bottom = -65;

    /** Everything the status bar shows. */
    struct status
    {
        int world = 0;          // 0..7
        int stage = 0;          // 0-based position within the world
        int lives = 3;
        int souls = 0;
        int score = 0;
        int time = 0;
        int hover = 1;
        int hover_max = 1;
        int boss = 0;           // remaining boss health, 0 when there is none
        int boss_max = 0;
        int player = 0;         // 0 solo, else which seat is playing
        int continues = 0;      // how many are left to spend
        bool flame = false;     // power-ups in hand, shown as icons
        bool dash = false;
        bool wings = false;
    };

    [[nodiscard]] const char* roman(int world);

    /**
     * Fixed-width decimal with leading zeros. bn::format only understands a
     * bare "{}", so padding has to be built by hand - and a score that keeps a
     * constant width does not jitter as it climbs.
     */
    [[nodiscard]] bn::string<12> zero_pad(int value, int digits);

    /**
     * The status bar. Its sprites carry no camera, so they stay pinned to the
     * screen while the world scrolls underneath. Each field is rebuilt only
     * when its value actually changes - regenerating text every frame would
     * churn sprite tiles for nothing.
     */
    class hud
    {
    public:
        explicit hud(bn::sprite_text_generator& text);

        void update(const status& now);
        void set_visible(bool visible);

    private:
        bn::sprite_text_generator& _text;
        bn::vector<bn::sprite_ptr, 4> _life_icons;
        bn::vector<bn::sprite_ptr, 4> _lives_text;
        bn::vector<bn::sprite_ptr, 6> _continues_text;
        bn::vector<bn::sprite_ptr, 6> _meter;
        bn::vector<bn::sprite_ptr, 10> _boss_pips;
        bn::vector<bn::sprite_ptr, 6> _souls_text;
        bn::vector<bn::sprite_ptr, 6> _world_text;
        bn::vector<bn::sprite_ptr, 6> _time_text;
        bn::vector<bn::sprite_ptr, 8> _score_text;
        bn::vector<bn::sprite_ptr, 4> _player_text;
        bn::vector<bn::sprite_ptr, 3> _power_icons;
        bn::sprite_ptr _soul_icon;
        status _shown;
        bool _visible = true;
        bool _first = true;

        void _show(bn::vector<bn::sprite_ptr, 6>& into, int x, const char* str);
    };
}

#endif
