// Gameplay tracing for the headless test harness.
//
// Build with -DLFN_TRACE_ENABLED=1 and the game narrates itself over the mGBA
// debug channel, which tools/emu/lfn_runner.c prints. Off by default so a
// shipping ROM carries none of it.
#ifndef LFN_TRACE_H
#define LFN_TRACE_H

#ifndef LFN_TRACE_ENABLED
    #define LFN_TRACE_ENABLED 0
#endif

#if LFN_TRACE_ENABLED
    #include "bn_log.h"
    #define LFN_TRACE(...) BN_LOG(__VA_ARGS__)
#else
    #define LFN_TRACE(...) ((void) 0)
#endif

#endif
