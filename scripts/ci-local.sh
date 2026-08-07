#!/usr/bin/env bash
# Run exactly what .github/workflows/ci.yml runs, against a FRESH CLONE with an
# empty data/ tree. Must pass before every push.
#
# Written 7 Aug 2026 after CI failed on a PR for two reasons neither of which
# the local suite could see:
#   1. `ruff check` was never run locally at all -- 4 lint errors.
#   2. Behind the lint failure, a test read a live capture via load_capture().
#      It passed here (146 captures on disk) and failed in CI (data/ is
#      git-ignored, so a clone has none). The suite is meant to be data-free.
#
# Both are invisible to `python -m unittest` in a working tree. Cloning is the
# point: it reproduces what the runner actually sees.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo "== cloning $BRANCH into a scratch tree (uncommitted changes are copied in)"
git clone -q "$REPO_ROOT" "$WORK/repo"
git -C "$WORK/repo" checkout -q "$BRANCH" 2>/dev/null || true
# copy the WORKING tree over the clone so uncommitted work is tested too
cp -a "$REPO_ROOT/scripts" "$REPO_ROOT/tests" "$WORK/repo/"
mkdir -p "$WORK/repo/data"          # fresh-clone condition: empty data tree
cd "$WORK/repo"

fail=0
echo "== ruff check scripts tests"
ruff check scripts tests || fail=1

echo "== python -m unittest discover tests"
python3 -m unittest discover tests -q || fail=1

echo "== fresh-clone import (empty data/)"
python3 -c "import sys; sys.path.insert(0, 'scripts'); import ihlib, experiments" || fail=1

if [ "$fail" -ne 0 ]; then
  echo ""
  echo "FAILED — fix before pushing. This is what GitHub Actions will report."
  exit 1
fi
echo ""
echo "PASSED — matches CI (ruff + unittest + fresh-clone import)."
