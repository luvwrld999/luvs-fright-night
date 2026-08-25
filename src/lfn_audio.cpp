#include "lfn_audio.h"

#include "bn_music.h"
#include "bn_music_items.h"
#include "bn_sound.h"
#include "bn_sound_item.h"
#include "bn_sound_items.h"

#include "lfn_tune.h"

namespace lfn::audio
{
    namespace
    {
        // Same order as the MUSIC table the level compiler writes indices from.
        constexpr bn::music_item tracks[] = {
            bn::music_items::title,
            bn::music_items::w1_pride,
            bn::music_items::w2_greed,
            bn::music_items::w3_lust,
            bn::music_items::w4_envy,
            bn::music_items::w5_gluttony,
            bn::music_items::w6_wrath,
            bn::music_items::w7_sloth,
            bn::music_items::w8_hades,
            bn::music_items::boss,
            bn::music_items::victory,
            bn::music_items::game_over,
        };

        int current = -1;

        // Butano's limit is (sound channels * 2) + 1 commands per frame; this
        // stays comfortably under it and keeps a busy moment from turning into
        // mush as well.
        constexpr int per_frame = 4;
        int budget = per_frame;

        void fire(bn::sound_item item, bn::fixed volume)
        {
            if(budget > 0)
            {
                --budget;
                item.play(volume);
            }
        }
    }

    void new_frame()
    {
        budget = per_frame;
    }

    void play_music(int track_index)
    {
        if(track_index == current && bn::music::playing())
        {
            return;
        }

        current = track_index;
        tracks[track_index].play(tune::music_volume);
    }

    void stop_music()
    {
        if(bn::music::playing())
        {
            bn::music::stop();
        }

        current = -1;
    }

    void sfx_jump()          { fire(bn::sound_items::jump, 0.7); }
    void sfx_land()          { fire(bn::sound_items::land, 0.45); }
    void sfx_stomp()         { fire(bn::sound_items::stomp, 0.85); }
    void sfx_shot()          { fire(bn::sound_items::shot, 0.7); }
    void sfx_dash()          { fire(bn::sound_items::dash, 0.75); }
    void sfx_hurt()          { fire(bn::sound_items::hurt, 0.9); }
    void sfx_death()         { fire(bn::sound_items::death, 0.9); }
    void sfx_pickup()        { fire(bn::sound_items::pickup, 0.6); }
    void sfx_power_up()      { fire(bn::sound_items::power_up, 0.85); }
    void sfx_one_up()        { fire(bn::sound_items::one_up, 0.85); }
    void sfx_checkpoint()    { fire(bn::sound_items::checkpoint, 0.8); }
    void sfx_smash()         { fire(bn::sound_items::flame_hit, 0.7); }
    void sfx_boss_hit()      { fire(bn::sound_items::boss_hit, 0.9); }
    void sfx_boss_die()      { fire(bn::sound_items::boss_die, 1.0); }
    void sfx_menu()          { fire(bn::sound_items::menu, 0.7); }
    void sfx_level_clear()   { fire(bn::sound_items::level_clear, 0.9); }
    void sfx_boss_tell()     { fire(bn::sound_items::boss_tell, 0.7); }
    void sfx_warp()          { fire(bn::sound_items::warp, 0.85); }
}
