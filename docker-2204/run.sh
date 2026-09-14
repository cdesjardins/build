#!/usr/bin/env bash
# Host-side driver for the ubuntu:22.04 build container.
#
#   ./run.sh          one-shot build: Qt (first run only), then Boost, Botan and
#                     ComBomb, producing a ComBombGui whose glibc floor is 2.35
#                     (runs on Ubuntu 22.04+).
#   ./run.sh shell    interactive shell in the same container, sitting in
#                     ComBomb/build, for running ./build.py and friends by hand.
#
# The container is the only thing that knows about docker: build.py and the
# make*.py scripts behave identically inside it and on the host.
#
# Qt is built once and left at ~/sw/qt6/Qt-2204 (on the bind-mounted host disk),
# so the first build builds it and every run after that auto-detects it and skips
# straight to Boost/Botan/ComBomb. Force a Qt rebuild with FORCE_QT=1.
#
# Usage:
#   ./run.sh                        # build (builds Qt only if not already installed)
#   FORCE_QT=1 ./run.sh             # force a fresh Qt rebuild (new version / flags)
#   DOCKER="sudo docker" ./run.sh   # if your user isn't in the docker group yet
#   ./run.sh shell                  # drop into the container instead of building
#
# The whole ~/sw workspace is bind-mounted at the SAME absolute path inside the
# container so the baked-in Qt prefix and all absolute paths line up, and outputs
# are owned by you (container runs as your uid:gid).
set -euo pipefail

MODE="${1:-build}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"         # ComBomb/build
SW_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"     # ~/sw
QT_PREFIX="${QT_PREFIX:-$SW_ROOT/qt6/Qt-2204}"
IMAGE="${IMAGE:-combomb-build:2204}"
DOCKER="${DOCKER:-docker}"

echo "### building image $IMAGE"
$DOCKER build -t "$IMAGE" "$SCRIPT_DIR"

case "$MODE" in
build)
    echo "### running build (SW_ROOT=$SW_ROOT, FORCE_QT=${FORCE_QT:-0})"
    $DOCKER run --rm \
      --user "$(id -u):$(id -g)" \
      -e FORCE_QT="${FORCE_QT:-0}" \
      -e JOBS="${JOBS:-$(nproc)}" \
      -e QT_PREFIX="$QT_PREFIX" \
      -v "$SW_ROOT:$SW_ROOT" \
      -w "$SW_ROOT" \
      "$IMAGE" \
      bash "$SCRIPT_DIR/build-in-container.sh"
    echo "### done — binary: $SW_ROOT/ComBomb/build/build/ComBomb/ComBombGui/ComBombGui"
    ;;
shell)
    if [ ! -x "$QT_PREFIX/bin/qmake" ] ; then
        echo "### warning: no Qt at $QT_PREFIX — run './run.sh' once to build it"
    fi
    echo "### shell in $IMAGE (workspace at $SW_ROOT, starting in $BUILD_DIR)"
    echo "### CMAKE_PREFIX_PATH is set, so ./build.py picks up the 22.04 Qt"
    # Ask docker for a tty only when there is one, so that
    #   echo ./build.py | ./run.sh shell
    # works as well as an interactive session does.
    TTY=""
    if [ -t 0 ] ; then
        TTY="-t"
    fi
    # CMAKE_PREFIX_PATH is what build.py falls back to when --qt is not given.
    $DOCKER run --rm -i $TTY \
      --user "$(id -u):$(id -g)" \
      -e JOBS="${JOBS:-$(nproc)}" \
      -e QT_PREFIX="$QT_PREFIX" \
      -e CMAKE_PREFIX_PATH="$QT_PREFIX" \
      -v "$SW_ROOT:$SW_ROOT" \
      -w "$BUILD_DIR" \
      "$IMAGE" \
      bash
    ;;
*)
    echo "usage: $0 [build|shell]" >&2
    exit 1
    ;;
esac
