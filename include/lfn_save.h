#ifndef LFN_SAVE_H
#define LFN_SAVE_H

#include <cstdint>

namespace lfn::save
{
    constexpr int table_size = 8;
    constexpr int name_length = 3;

    struct entry
    {
        char name[name_length];
        uint32_t score;
    };

    /** How many stages carry a recorded best time. */
    constexpr int timed_stages = 24;

    struct file
    {
        uint32_t magic;
        entry table[table_size];
        // Clock units spent on each stage's fastest clear, 0 for never done.
        // Same units the status bar counts down, so the two always agree.
        uint16_t best_time[timed_stages];
        uint16_t furthest_level;   // highest stage index unlocked
        uint16_t souls;
        uint8_t lives;
        uint8_t pad[3];
    };

    /** Reads the cartridge save, returning defaults if it is blank or foreign. */
    file load();
    void store(const file& data);

    /** Clears progress. The board survives - it is the point of the board. */
    void wipe();

    [[nodiscard]] uint32_t best(const file& data);

    /** Would this score get onto the board? */
    [[nodiscard]] bool qualifies(const file& data, int score);

    /** Put a score on the board, pushing everything below it down. */
    void submit(file& data, const char name[name_length], int score);

    /**
     * Record a stage clear. Returns true if it beat what was there, so the
     * caller can say so.
     */
    bool record_time(file& data, int level_index, int units);
}

#endif
