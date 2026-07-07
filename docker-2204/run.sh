#!/usr/bin/env bash
# Host-side driver: builds the ubuntu:22.04 image and runs the full
# Qt+Boost+Botan+ComBomb build inside it, producing a ComBombGui whose glibc
# floor is 2.35 (runs on Ubuntu 22.04+).
#
# Qt is built once and left at ~/sw/qt6/Qt-2204 (on the bind-mounted host disk),
# so the first run builds it and every run after that auto-detects it and skips
# straight to Boost/Botan/ComBomb. Force a Qt rebuild with FORCE_QT=1.
#
# Usage:
#   ./run.sh                 # build (builds Qt only if not already installed)
#   FORCE_QT=1 ./run.sh      # force a fresh Qt rebuild (new version / flags)
#   DOCKER="sudo docker" ./run.sh   # if your user isn't in the docker group yet
#
# The whole ~/sw workspace is bind-mounted at the SAME absolute path inside the
# container so the baked-in Qt prefix and all absolute paths line up, and outputs
# are owned by you (container runs as your uid:gid).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SW_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"     # ~/sw
IMAGE="${IMAGE:-combomb-build:2204}"
DOCKER="${DOCKER:-docker}"

echo "### building image $IMAGE"
$DOCKER build -t "$IMAGE" "$SCRIPT_DIR"

echo "### running build (SW_ROOT=$SW_ROOT, FORCE_QT=${FORCE_QT:-0})"
$DOCKER run --rm \
  --user "$(id -u):$(id -g)" \
  -e FORCE_QT="${FORCE_QT:-0}" \
  -e JOBS="${JOBS:-$(nproc)}" \
  -v "$SW_ROOT:$SW_ROOT" \
  -w "$SW_ROOT" \
  "$IMAGE" \
  bash "$SCRIPT_DIR/build-in-container.sh"

echo "### done — binary: $SW_ROOT/ComBomb/build/build/ComBomb/ComBombGui/ComBombGui"
