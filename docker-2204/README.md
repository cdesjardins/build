# Portable ComBomb build (Ubuntu 22.04 / glibc 2.35)

Builds ComBomb inside an `ubuntu:22.04` container so the resulting `ComBombGui`
binary has a **glibc 2.35 floor** and runs on Ubuntu 22.04 and everything newer.

## Why this exists

Building on a newer host (e.g. Ubuntu 24.04, glibc 2.39, gcc-14) bakes in
`GLIBC_2.38` symbol versions — `__isoc23_strtol/strtoul/strtoll/strtoull/sscanf`
(gcc-14 C23 header redirects) plus `fmod@GLIBC_2.38`. glibc is backward- but
**not** forward-compatible, so such a binary fails on 22.04 with:

```
/lib/x86_64-linux-gnu/libm.so.6: version `GLIBC_2.38' not found
```

Static-linking glibc is **not** a fix (it breaks NSS `getaddrinfo`/DNS, which
ComBomb's SSH/telnet need, and GL driver `dlopen`). The robust fix is to build on
the oldest distro you must support. Everything else *is* statically linked into
the binary: static Qt 6.8.3, vendored Boost, Botan, and `-static-libstdc++`.

## Files

- `Dockerfile` — the 22.04 builder image (`combomb-build:2204`): gcc-12/g++-12,
  modern cmake via pip, and the xcb / wayland / fontconfig / freetype dev libs Qt
  needs. Note `python-is-python3` — the vendored `make*.py` use `/usr/bin/env python`.
- `build-in-container.sh` — runs *inside* the container: builds static Qt (only
  if not already installed), then Boost → Botan → ComBomb. Paths derive from the
  script location; override with `QT_SRC` / `QT_BUILD` / `QT_PREFIX` / `JOBS` /
  `FORCE_QT`.
- `run.sh` — host driver: builds the image and runs the container with `~/sw`
  bind-mounted at the same absolute path, as your uid:gid.

## Prerequisites

- Docker installed; your user in the `docker` group (or use `sudo docker`).
- The Qt 6.8.3 source tree at `~/sw/qt6/qt-everywhere-src-6.8.3` (override with
  `QT_SRC`). Qt installs to `~/sw/qt6/Qt-2204` so your normal `~/Qt/6` is untouched.

## Qt is built once and left on disk

`QT_PREFIX` (`~/sw/qt6/Qt-2204`) lives under the bind-mounted `~/sw`, so the
installed Qt persists on your **host** disk — the `--rm` container is ephemeral,
but its install output is not. The first run builds Qt (~30–40 min); every run
after that detects `Qt-2204/bin/qmake` and skips straight to Boost/Botan/ComBomb.
Force a fresh Qt rebuild (new Qt version, changed configure flags) with `FORCE_QT=1`.

## Usage

```bash
cd ~/sw/ComBomb/build/docker-2204
./run.sh                      # builds Qt only if not already installed, then ComBomb
FORCE_QT=1 ./run.sh           # force a fresh Qt rebuild
DOCKER="sudo docker" ./run.sh # if not yet in the docker group
```

Output binary:
`~/sw/ComBomb/build/build/ComBomb/ComBombGui/ComBombGui`
(a release `build.py` also packages into `~/sw/ComBomb/install/`).

## Deploying to a minimal 22.04 target

Qt is static (qxcb is inside the executable — no `platforms/` dir to ship), but a
minimal target may lack the xcb runtime libs:

```bash
sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-render-util0 libxcb-xkb1
```

Everything else it links (glib, fontconfig, freetype, EGL/GLX, wayland-client)
ships on any Ubuntu desktop. Needs a running X server or XWayland.

## Verify the glibc floor

```bash
objdump -T ComBombGui | grep -o 'GLIBC_[0-9.]*' | sort -uV | tail
# highest should be GLIBC_2.35 — no 2.36/2.37/2.38/2.39
```
