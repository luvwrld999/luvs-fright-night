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
        constexpr uint32_t magic_value = 0x4C464E35;    // "LFN5"

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

        // The rush is a short, dense game, so it needs its own ladder rather
        // than being buried under forty-minute runs on the story board.
        constexpr entry rush_factory[table_size] = {
            {{'J', 'D', 'K'}, 41000},
            {{'I', 'M', 'K'}, 34500},
            {{'L', 'U', 'V'}, 28000},
            {{'H', 'A', 'D'}, 22500},
            {{'9', '9', '9'}, 17000},
            {{'S', 'I', 'N'}, 12500},
            {{'G', 'H', 'O'},  8000},
            {{'R', 'I', 'P'},  4500},
        };

        void blank(progress& p)
        {
            p.furthest_level = 0;
            p.souls = 0;
            p.lives = tune::start_lives;
            p.used = 0;
        }

        file defaults()
        {
            file data{};
            data.magic = magic_value;

            for(int i = 0; i < table_size; ++i)
            {
                data.table[i] = factory[i];
                data.rush[i] = rush_factory[i];
            }

            for(int i = 0; i < timed_stages; ++i)
            {
                data.best_time[i] = 0;
            }

            for(int i = 0; i < slot_count; ++i)
            {
                blank(data.slots[i]);
            }

            data.active = 0;
            return data;
        }
    }

    progress& slot(file& data)
    {
        return data.slots[data.active < slot_count ? data.active : 0];
    }

    const progress& slot(const file& data)
    {
        return data.slots[data.active < slot_count ? data.active : 0];
    }

    void choose(file& data, int index)
    {
        data.active = uint8_t(index >= 0 && index < slot_count ? index : 0);
    }

    int slots_used(const file& data)
    {
        int count = 0;

        for(int i = 0; i < slot_count; ++i)
        {
            if(data.slots[i].used)
            {
                ++count;
            }
        }

        return count;
    }

    file load()
    {
        file data;
        bn::sram::read(data);

        if(data.magic != magic_value)
        {
            data = defaults();
        }

        // A blank active slot with a played one beside it means the file was
        // last left on an erased game; point it at something real.
        if(!data.slots[data.active < slot_count ? data.active : 0].used)
        {
            for(int i = 0; i < slot_count; ++i)
            {
                if(data.slots[i].used)
                {
                    data.active = uint8_t(i);
                    break;
                }
            }
        }

        if(tune::test_autopilot || tune::test_invulnerable)
        {
            // Test builds unlock everything, so the harness can drive straight
            // to any stage - including the secret rooms - via stage select.
            for(int i = 0; i < slot_count; ++i)
            {
                data.slots[i].furthest_level = level_count - 1;
                data.slots[i].used = 1;
            }
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
        // Only the game in play. The boards and the times belong to the
        // cartridge, not to one person's save.
        file current = load();
        blank(slot(current));
        store(current);
    }

    entry* rows(file& data, board which)
    {
        return which == board::rush ? data.rush : data.table;
    }

    const entry* rows(const file& data, board which)
    {
        return which == board::rush ? data.rush : data.table;
    }

    uint32_t best(const file& data, board which)
    {
        return rows(data, which)[0].score;
    }

    bool qualifies(const file& data, int score, board which)
    {
        return score > 0 &&
               uint32_t(score) > rows(data, which)[table_size - 1].score;
    }

    void submit(file& data, const char name[name_length], int score, board which)
    {
        entry* table = rows(data, which);
        int slot = table_size - 1;

        while(slot > 0 && table[slot - 1].score < uint32_t(score))
        {
            table[slot] = table[slot - 1];
            --slot;
        }

        for(int i = 0; i < name_length; ++i)
        {
            table[slot].name[i] = name[i];
        }

        table[slot].score = uint32_t(score);
    }
}

namespace lfn::save
{
    bool record_time(file& data, int level_index, int units)
    {
        if(level_index < 0 || level_index >= timed_stages || units <= 0)
        {
            return false;
        }

        const uint16_t was = data.best_time[level_index];

        if(was && int(was) <= units)
        {
            return false;
        }

        data.best_time[level_index] = uint16_t(units);
        return true;
    }
}
