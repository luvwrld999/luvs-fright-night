#!/usr/bin/env bash
# Headless verification: build a traced, invulnerable ROM and walk every stage.
#
#   ./test.sh              full marathon across all 16 levels
#   ./test.sh <script.txt> run one script from tools/emu/
#
# Screenshots land in tools/emu/shots as PPM; tools/shots.py turns them into a
# contact sheet. The shipping ROM is rebuilt at the end so the tree is left
# holding a real build, not a test one.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="${1:-tools/emu/marathon.txt}"
FLAGS='-DBN_CFG_ASSERT_ENABLED=true -DBN_CFG_LOG_ENABLED=true -DLFN_TRACE_ENABLED=1 -DLFN_TEST_INVULNERABLE=1'

cd "$DIR"
rm -f tools/emu/shots/*.ppm

# Butano's make does not notice compiler-flag changes, so a test build has to
# start from clean or it silently reuses shipping objects.
./build.sh clean > /dev/null
./build.sh "USERFLAGS=$FLAGS" > /dev/null
mv LuvsFrightNight.gba tools/emu/lfn_test.gba

docker run --rm -v "$DIR":/w -w /w lfn-mgba \
    /w/tools/emu/lfn_test.gba "/w/$SCRIPT" /w/tools/emu/shots 2>&1 \
    | grep -E 'ev:|main:|ran |shot |invalid address|ERROR' || true

rm -f tools/emu/lfn_test.gba
./build.sh clean > /dev/null
./build.sh > /dev/null
echo "shipping ROM rebuilt: $(ls -lh LuvsFrightNight.gba | awk '{print $5}')"
