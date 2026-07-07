# Ubuntu 22.04 (glibc 2.35) build env for ComBomb — produces binaries whose
# glibc floor is 2.35 so they run on 22.04 and everything newer.
#
# Why: building on a newer host (e.g. Ubuntu 24.04 / glibc 2.39 with gcc-14)
# bakes in GLIBC_2.38 symbol versions (__isoc23_strtol/sscanf, fmod@2.38) that
# don't exist on 22.04, so the binary fails there with
# "libm.so.6: version GLIBC_2.38 not found". glibc is backward- but NOT
# forward-compatible, so we build on the oldest distro we need to support.
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc-12 g++-12 \
      python3 python3-pip python-is-python3 perl git pkg-config ninja-build bison flex make ca-certificates \
      libgl1-mesa-dev libegl1-mesa-dev libgles2-mesa-dev libglu1-mesa-dev \
      libx11-dev libx11-xcb-dev libxext-dev libxfixes-dev libxi-dev libxrender-dev \
      libxkbcommon-dev libxkbcommon-x11-dev \
      libxcb1-dev libxcb-glx0-dev libxcb-keysyms1-dev libxcb-image0-dev libxcb-shm0-dev \
      libxcb-icccm4-dev libxcb-sync-dev libxcb-xfixes0-dev libxcb-shape0-dev libxcb-randr0-dev \
      libxcb-render-util0-dev libxcb-render0-dev libxcb-util-dev libxcb-xinerama0-dev \
      libxcb-xkb-dev libxcb-cursor-dev \
      libfontconfig1-dev libfreetype6-dev \
      libglib2.0-dev libdbus-1-dev \
      zlib1g-dev libpng-dev libjpeg-dev \
      libwayland-dev wayland-protocols libwayland-egl-backend-dev \
    && rm -rf /var/lib/apt/lists/*

# 22.04 ships cmake 3.22; Qt 6.8 builds with it but pull a modern cmake to be safe.
RUN pip3 install --no-cache-dir "cmake>=3.28,<4"
