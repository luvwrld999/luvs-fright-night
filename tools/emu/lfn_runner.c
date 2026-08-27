/*
 * lfn-run - a headless GBA harness for Luv's Fright Night.
 *
 * Runs a ROM under libmgba with no display, injects button presses from a
 * script, and dumps frames as PPM. This is how the game gets verified: the
 * build can be driven and looked at without anyone opening an emulator.
 *
 *   lfn-run rom.gba script.txt outdir
 *
 * Script commands, one per line ('#' starts a comment):
 *   wait N            run N frames
 *   hold KEY[,KEY]    press and keep holding
 *   release KEY|all   let go
 *   tap KEY N         hold KEY for N frames, then release
 *   shot NAME         write outdir/NAME.ppm
 *   reset             reset the console
 * Keys: a b select start right left up down r l
 */

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/core/log.h>

/* GBA button order, as libmgba's setKeys() bitmask expects it. */
static const char* KEY_NAMES[] = {"a", "b", "select", "start",
                                  "right", "left", "up", "down", "r", "l"};
#define KEY_COUNT 10

static unsigned g_width, g_height;
static color_t* g_pixels;
static long g_frame;          /* frames run so far, so logs can be aimed at */

static void logger(struct mLogger* log, int category, enum mLogLevel level,
                   const char* format, va_list args) {
    (void) log;
    (void) level;
    /* bn::log() from the game arrives here, which makes the ROM debuggable.
       The frame number turns a log into a timestamp you can seek back to. */
    printf("[%06ld][%s] ", g_frame, mLogCategoryName(category));
    vprintf(format, args);
    printf("\n");
    fflush(stdout);
}

static int key_index(const char* name) {
    for (int i = 0; i < KEY_COUNT; ++i) {
        if (!strcasecmp(name, KEY_NAMES[i])) {
            return i;
        }
    }
    return -1;
}

static uint32_t parse_keys(const char* list) {
    uint32_t mask = 0;
    char buf[128];
    snprintf(buf, sizeof buf, "%s", list);
    for (char* tok = strtok(buf, ","); tok; tok = strtok(NULL, ",")) {
        while (*tok == ' ') {
            ++tok;
        }
        int k = key_index(tok);
        if (k < 0) {
            fprintf(stderr, "lfn-run: unknown key '%s'\n", tok);
            exit(2);
        }
        mask |= 1u << k;
    }
    return mask;
}

static void write_ppm(const char* dir, const char* name) {
    char path[1024];
    snprintf(path, sizeof path, "%s/%s.ppm", dir, name);
    FILE* f = fopen(path, "wb");
    if (!f) {
        fprintf(stderr, "lfn-run: cannot write %s\n", path);
        exit(3);
    }
    fprintf(f, "P6\n%u %u\n255\n", g_width, g_height);
    for (unsigned i = 0; i < g_width * g_height; ++i) {
        color_t c = g_pixels[i];
#if BYTES_PER_PIXEL == 4
        unsigned char rgb[3] = {c & 0xFF, (c >> 8) & 0xFF, (c >> 16) & 0xFF};
#else
        unsigned char rgb[3] = {M_R8(c), M_G8(c), M_B8(c)};
#endif
        fwrite(rgb, 1, 3, f);
    }
    fclose(f);
    printf("[%06ld] shot %s\n", g_frame, name);
    fflush(stdout);
}

int main(int argc, char** argv) {
    if (argc < 4) {
        fprintf(stderr, "usage: lfn-run rom.gba script.txt outdir\n");
        return 1;
    }
    const char* rom = argv[1];
    const char* script_path = argv[2];
    const char* outdir = argv[3];

    static struct mLogger log_handler;
    log_handler.log = logger;
    mLogSetDefaultLogger(&log_handler);

    struct mCore* core = mCoreFind(rom);
    if (!core) {
        fprintf(stderr, "lfn-run: not a ROM this build understands: %s\n", rom);
        return 1;
    }
    core->init(core);
    mCoreInitConfig(core, NULL);
    core->desiredVideoDimensions(core, &g_width, &g_height);
    g_pixels = calloc(g_width * g_height, sizeof(color_t));
    core->setVideoBuffer(core, g_pixels, g_width);

    if (!mCoreLoadFile(core, rom)) {
        fprintf(stderr, "lfn-run: failed to load %s\n", rom);
        return 1;
    }
    /* Map the cartridge's SRAM to a .sav beside the ROM, so a save written by
       one run is still there for the next one. Without this the battery only
       ever lives in memory and every run starts on a blank cartridge - which
       makes "does the save survive a reset?" a question nothing could ask. */
    mCoreAutoloadSave(core);
    core->reset(core);

    FILE* script = fopen(script_path, "r");
    if (!script) {
        fprintf(stderr, "lfn-run: cannot read %s\n", script_path);
        return 1;
    }

    uint32_t held = 0;
    long total_frames = 0;
    char line[512];

    while (fgets(line, sizeof line, script)) {
        char* hash = strchr(line, '#');
        if (hash) {
            *hash = '\0';
        }
        char cmd[64] = {0}, arg[256] = {0};
        int n = 0;
        int parsed = sscanf(line, "%63s %255s %d", cmd, arg, &n);
        if (parsed < 1) {
            continue;
        }

        if (!strcmp(cmd, "wait")) {
            int frames = atoi(arg);
            for (int i = 0; i < frames; ++i) {
                core->setKeys(core, held);
                core->runFrame(core);
                ++total_frames;
                ++g_frame;
            }
        } else if (!strcmp(cmd, "hold")) {
            held |= parse_keys(arg);
        } else if (!strcmp(cmd, "release")) {
            held = strcasecmp(arg, "all") ? (held & ~parse_keys(arg)) : 0;
        } else if (!strcmp(cmd, "tap")) {
            uint32_t k = parse_keys(arg);
            int frames = n > 0 ? n : 4;
            for (int i = 0; i < frames; ++i) {
                core->setKeys(core, held | k);
                core->runFrame(core);
                ++total_frames;
                ++g_frame;
            }
        } else if (!strcmp(cmd, "shot")) {
            write_ppm(outdir, arg);
        } else if (!strcmp(cmd, "reset")) {
            core->reset(core);
        } else {
            fprintf(stderr, "lfn-run: unknown command '%s'\n", cmd);
            return 2;
        }
    }

    fclose(script);
    printf("ran %ld frames\n", total_frames);
    /* Flush the battery back to disk before the core goes away. */
    core->unloadROM(core);
    core->deinit(core);
    free(g_pixels);
    return 0;
}
