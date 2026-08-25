#include "lfn_save.h"

#include "bn_sram.h"

#include "lfn_levels.h"
#include "lfn_tune.h"

namespace lfn::save
{
    namespace
    {
        // Bumped when the layout changes, so an older file is discarded rather
        // than read as nonsense.
        constexpr uint32_t magic_value = 0x4C464E33;    // "LFN3"

        // The board a fresh cartridge ships with. Somebody has to be at the top
        // before anyone plays it.
        constexpr entry factory[table_size] = {
            {{'J', 'D', 'K'}, 62000},
            {{'I', 'M', 'K'}, 51500},
            {{'L', 'U', 'V'}, 43000},
            {{'R', 'I', 'P'}, 36500},
            {{'9', '9', '9'}, 29000},
            {{'G', 'H', 'O'}, 21000},
            {{'S', 'I', 'N'}, 14500},
            {{'H', 'A', 'D'},  8000},
        };

        file defaults()
        {
            file data{};
            data.magic = magic_value;

            for(int i = 0; i < table_size; ++i)
            {
                data.table[i] = factory[i];
            }

            data.furthest_level = 0;
            data.souls = 0;
            data.lives = tune::start_lives;
            return data;
        }
    }

    file load()
    {
        file data;
        bn::sram::read(data);

        if(data.magic != magic_value)
        {
            data = defaults();
        }

        if(tune::test_autopilot || tune::test_invulnerable)
        {
            // Test builds unlock everything, so the harness can drive straight
            // to any stage - including the secret rooms - via stage select.
            data.furthest_level = level_count - 1;
        }

        return data;
    }

    void store(const file& data)
    {
        file copy = data;
        copy.magic = magic_value;
        bn::sram::write(copy);
    }

    void wipe()
    {
        file fresh = defaults();
        file current = load();

        // Starting again clears your progress, not everyone else's names.
        for(int i = 0; i < table_size; ++i)
        {
            fresh.table[i] = current.table[i];
        }

        store(fresh);
    }

    uint32_t best(const file& data)
    {
        return data.table[0].score;
    }

    bool qualifies(const file& data, int score)
    {
        return score > 0 && uint32_t(score) > data.table[table_size - 1].score;
    }

    void submit(file& data, const char name[name_length], int score)
    {
        int slot = table_size - 1;

        while(slot > 0 && data.table[slot - 1].score < uint32_t(score))
        {
            data.table[slot] = data.table[slot - 1];
            --slot;
        }

        for(int i = 0; i < name_length; ++i)
        {
            data.table[slot].name[i] = name[i];
        }

        data.table[slot].score = uint32_t(score);
    }
}
