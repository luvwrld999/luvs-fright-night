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

    /** Separate games can share one cartridge. */
    constexpr int slot_count = 3;

    /** Which board a score belongs on. A rush is not a run. */
    enum class board : uint8_t { story, rush };

    /** One person's game in progress. */
    struct progress
    {
        uint16_t furthest_level;   // highest stage index unlocked
        uint16_t souls;
        uint8_t lives;
        uint8_t used;              // 0 while the slot has never been played
        uint8_t pad[2];
    };

    struct file
    {
        uint32_t magic;
        entry table[table_size];
        entry rush[table_size];
        // Clock units spent on each stage's fastest clear, 0 for never done.
        // Same units the status bar counts down, so the two always agree.
        uint16_t best_time[timed_stages];
        progress slots[slot_count];
        uint8_t active;            // the slot currently being played
        uint8_t pad[3];
    };

    /**
     * The slot in play. Everything that used to read progress straight off the
     * file goes through here, so which game is loaded is decided in one place.
     */
    [[nodiscard]] progress& slot(file& data);
    [[nodiscard]] const progress& slot(const file& data);

    /** Point the file at a different game. */
    void choose(file& data, int index);

    /** How many slots have ever been played. */
    [[nodiscard]] int slots_used(const file& data);

    /** Reads the cartridge save, returning defaults if it is blank or foreign. */
    file load();
    void store(const file& data);

    /**
     * Clears the slot in play. The boards and the times survive - they are
     * records, and they belong to the cartridge rather than to one game.
     */
    void wipe();

    [[nodiscard]] uint32_t best(const file& data, board which = board::story);

    /** Would this score get onto the board? */
    [[nodiscard]] bool qualifies(const file& data, int score,
                                 board which = board::story);

    /** Put a score on the board, pushing everything below it down. */
    void submit(file& data, const char name[name_length], int score,
                board which = board::story);

    /** The rows of one board. */
    [[nodiscard]] entry* rows(file& data, board which);
    [[nodiscard]] const entry* rows(const file& data, board which);

    /**
     * Record a stage clear. Returns true if it beat what was there, so the
     * caller can say so.
     */
    bool record_time(file& data, int level_index, int units);
}

#endif
