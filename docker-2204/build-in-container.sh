#!/usr/bin/env bash
# Runs INSIDE the ubuntu:22.04 container (see Dockerfile), as the invoking uid,
# with the ~/sw workspace bind-mounted at the SAME absolute path as on the host
# (so the baked-in Qt prefix and all absolute paths match host and container).
#
# Rebuilds the entire static chain — Qt + Boost + Botan + ComBomb — so the final
# ComBombGui binary's glibc floor is 2.35 and it runs on Ubuntu 22.04+.
#
# Paths are derived from this script's location but can be overridden via env:
#   QT_SRC     Qt source tree           (default: $SW_ROOT/qt6/qt-everywhere-src-6.8.3)
#   QT_BUILD   Qt out-of-tree build dir (default: $SW_ROOT/qt6/qt6.8.3-build-2204)
#   QT_PREFIX  Qt install prefix        (default: $SW_ROOT/qt6/Qt-2204)
#   JOBS       parallel build jobs      (default: nproc)
#   FORCE_QT=1 rebuild Qt even if it's already installed at QT_PREFIX
#
# Qt is built ONCE and left at QT_PREFIX (which lives under the bind-mounted
# ~/sw, so it persists on the host across container runs). Subsequent runs detect
# the existing install and skip straight to Boost/Botan/ComBomb. Force a Qt
# rebuild (new Qt version, changed configure flags) with FORCE_QT=1.
set -euo pipefail

export CC=gcc-12 CXX=g++-12
export HOME=/tmp
export PATH=/usr/local/bin:$PATH
git config --global --add safe.directory '*' || true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"          # ComBomb/build
SW_ROOT="$(cd "$BUILD_DIR/../.." && pwd)"          # ~/sw

QT_SRC="${QT_SRC:-$SW_ROOT/qt6/qt-everywhere-src-6.8.3}"
QT_BUILD="${QT_BUILD:-$SW_ROOT/qt6/qt6.8.3-build-2204}"
QT_PREFIX="${QT_PREFIX:-$SW_ROOT/qt6/Qt-2204}"
JOBS="${JOBS:-$(nproc)}"

echo "### env: cmake=$(cmake --version | head -1)  cxx=$($CXX --version | head -1)  jobs=$JOBS"
echo "### QT_SRC=$QT_SRC  QT_PREFIX=$QT_PREFIX"

if [ "${FORCE_QT:-0}" != "1" ] && [ -x "$QT_PREFIX/bin/qmake" ]; then
  echo "### [1/4] Qt already installed at $QT_PREFIX — skipping (FORCE_QT=1 to rebuild)"
else
  echo "### [1/4] Configure + build static Qt (xcb + fontconfig + bundled pcre2)"
  rm -rf "$QT_BUILD"
  mkdir -p "$QT_BUILD"
  cd "$QT_BUILD"
  "$QT_SRC/configure" -prefix "$QT_PREFIX" -opensource -confirm-license -static \
    -c++std c++20 -nomake examples -nomake tests -no-openssl -no-feature-gtk3 \
    -submodules qtbase,qtwayland -qt-pcre -system-freetype -fontconfig
  cmake --build . --parallel "$JOBS"
  cmake --install .
  echo "### QT_OK"
fi

echo "### [2/4] Boost (static, rebuilt on 22.04)"
cd "$BUILD_DIR"
./makeboost.py -j "$JOBS"

echo "### [3/4] Botan (static, rebuilt on 22.04)"
./makebotan.py

echo "### [4/4] ComBomb + helper libs (clean build against 22.04 Qt)"
./build.py -c --qt="$QT_PREFIX"
echo "### COMBOMB_OK"
