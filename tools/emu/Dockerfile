# Headless mGBA plus a small harness that can drive Luv's Fright Night and dump
# frames, so builds are verified without anyone opening an emulator.
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake git ca-certificates \
        libpng-dev zlib1g-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch 0.10.5 https://github.com/mgba-emu/mgba.git /src/mgba

WORKDIR /src/mgba/build
RUN cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_QT=OFF -DBUILD_SDL=OFF -DBUILD_PERF=ON -DBUILD_EXAMPLE=OFF \
        -DUSE_FFMPEG=OFF -DUSE_LUA=OFF -DUSE_SQLITE3=OFF -DUSE_DISCORD_RPC=OFF \
        -DUSE_EPOXY=OFF -DUSE_ELF=OFF -DUSE_LIBZIP=OFF -DUSE_MINIZIP=OFF \
        -DENABLE_SCRIPTING=OFF \
    && make -j"$(nproc)" mgba-perf

COPY lfn_runner.c /src/lfn_runner.c
RUN gcc -O2 -o /usr/local/bin/lfn-run /src/lfn_runner.c \
        -I/src/mgba/include -I/src/mgba/build/include \
        -L/src/mgba/build -lmgba -lm \
    && echo '/src/mgba/build' > /etc/ld.so.conf.d/mgba.conf && ldconfig

ENTRYPOINT ["/usr/local/bin/lfn-run"]
