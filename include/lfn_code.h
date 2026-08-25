#ifndef LFN_CODE_H
#define LFN_CODE_H

#include "bn_string.h"

namespace lfn::code
{
    /** Codes are four characters drawn from an unambiguous 16-letter set. */
    constexpr int length = 4;

    /** The alphabet a code can be built from, in cycling order. */
    [[nodiscard]] const char* alphabet();

    /** The code that unlocks `level_index`. */
    [[nodiscard]] bn::string<8> for_level(int level_index);

    /**
     * The level a typed code unlocks, or -1 if nothing answers to it. Codes
     * are checked by generating every level's code and comparing, so a typo
     * can never decode into some other stage by accident.
     */
    [[nodiscard]] int to_level(const char* typed);
}

#endif
