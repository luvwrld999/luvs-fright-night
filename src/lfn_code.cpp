#include "lfn_code.h"

#include "lfn_levels.h"

namespace lfn::code
{
    namespace
    {
        // No vowels, and nothing that reads as a digit on a small screen, so a
        // code can be written on paper and typed back without ambiguity.
        constexpr char letters[] = "BCDFGHJKLMNPRSTV";
        constexpr int base = 16;

        // Odd multiplier, so every level maps to its own 16-bit value; the
        // salt stops stage 1 from being an obvious run of the same letter.
        constexpr unsigned scramble(int level_index)
        {
            return ((unsigned(level_index) + 1u) * 2749u ^ 0x3C5Au) & 0xFFFFu;
        }
    }

    const char* alphabet()
    {
        return letters;
    }

    bn::string<8> for_level(int level_index)
    {
        unsigned v = scramble(level_index);
        bn::string<8> out;

        for(int i = 0; i < length; ++i)
        {
            out.push_back(letters[(v >> ((length - 1 - i) * 4)) & 0xF]);
        }

        return out;
    }

    int to_level(const char* typed)
    {
        for(int i = 0; i < level_count; ++i)
        {
            const bn::string<8> want = for_level(i);
            bool same = true;

            for(int c = 0; c < length; ++c)
            {
                if(typed[c] != want[c])
                {
                    same = false;
                    break;
                }
            }

            if(same)
            {
                return i;
            }
        }

        return -1;
    }
}
