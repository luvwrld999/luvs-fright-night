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

    struct file
    {
        uint32_t magic;
        entry table[table_size];
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
}

#endif
