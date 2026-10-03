#!/usr/bin/env bash
# Launch a scratch WINDOWS Anki (isolated ANKI_BASE inside the repo) with
# this addon installed. Never touches the production profile/collection.
#
# Usage:
#   LSA_SELFTEST=1  [LSA_SELFTEST_KEEP=1]  tools/scratch-anki.sh [--fresh]
#
#   LSA_SELFTEST=1     map env to <base>/selftest-results.json and wait for it
#   LSA_SELFTEST_KEEP=1  don't expect the app to exit after self-test
#   --fresh            wipe the scratch base first (profile must be re-created)
#
# Prints the load marker, then either waits for self-test results or leaves
# Anki running (close its window when done).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
BASE="$REPO/.scratch-anki"
MARKER="$BASE/load-marker.txt"
RESULTS="$BASE/selftest-results.json"
LOG="$BASE/launch.log"
ANKI_EXE="$LOCALAPPDATA/Programs/Anki/Anki.exe"

FRESH=0
for arg in "$@"; do
  [ "$arg" = "--fresh" ] && FRESH=1
done

if [ "$FRESH" = 1 ]; then
  rm -rf "$BASE"
fi
mkdir -p "$BASE/addons21"

# Fresh copy of the addon each run (Anki writes meta.json into it).
rm -rf "$BASE/addons21/language_study_anki"
cp -r "$REPO/language_study_anki" "$BASE/addons21/language_study_anki"
find "$BASE/addons21" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
rm -f "$MARKER" "$RESULTS" "$LOG"

SELFTEST="${LSA_SELFTEST:-0}"
if [ "$SELFTEST" = "1" ]; then
  export LSA_SELFTEST="$RESULTS"
fi

ANKI_BASE="$BASE" \
ANKI_SINGLE_INSTANCE_KEY="${ANKI_SINGLE_INSTANCE_KEY:-lsa-win}" \
LSA_DEV_MARKER="$MARKER" \
"$ANKI_EXE" > "$LOG" 2>&1 &
ANKI_PID=$!

# Wait for the load marker (addon loaded).
for _ in $(seq 1 120); do
  [ -f "$MARKER" ] && break
  sleep 0.5
done
if [ -f "$MARKER" ]; then
  echo "--- load marker ---"
  cat "$MARKER"
  echo ""
else
  echo "TIMED OUT waiting for load marker (see $LOG)" >&2
  tail -20 "$LOG" >&2 || true
  exit 1
fi

if [ "$SELFTEST" = "1" ]; then
  # Wait for the self-test results file (self-test exits the app unless kept).
  for _ in $(seq 1 480); do
    [ -f "$RESULTS" ] && break
    sleep 0.5
  done
  if [ -f "$RESULTS" ]; then
    echo "--- self-test results: $RESULTS ---"
  else
    echo "TIMED OUT waiting for self-test results (see $LOG)" >&2
    tail -30 "$LOG" >&2 || true
    exit 1
  fi
fi
echo "Anki pid=$ANKI_PID base=$BASE"
