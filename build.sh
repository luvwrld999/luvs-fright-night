#!/usr/bin/env bash
# Build Luv's Fright Night inside the devkitARM container.
#   ./build.sh            -> build the ROM
#   ./build.sh clean      -> remove build artifacts
#   ./build.sh -j4        -> extra args are passed straight to make
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="devkitpro/devkitarm:latest"
JOBS="$(sysctl -n hw.ncpu 2>/dev/null || nproc)"

if ! docker info >/dev/null 2>&1; then
    echo "Docker isn't running. Start OrbStack (open -a OrbStack) and try again." >&2
    exit 1
fi

# The host path contains a space; /project inside the container does not, which is what
# devkitARM's makefiles need.
docker run --rm -t \
    -v "$PROJECT_DIR":/project \
    -w /project \
    -u "$(id -u):$(id -g)" \
    -e HOME=/tmp \
    "$IMAGE" \
    make -j"$JOBS" "$@"
