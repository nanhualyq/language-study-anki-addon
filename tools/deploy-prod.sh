#!/usr/bin/env bash
# Deploy language_study_anki/ into the PRODUCTION Anki add-on folder —
# the local default base (the one the default profile runs from):
#
#   Windows : %APPDATA%\Anki2\addons21\language_study_anki
#   macOS   : ~/Library/Application Support/Anki2/addons21/language_study_anki
#   Linux   : ~/.local/share/Anki2/addons21/language_study_anki
#
# Add-ons live in the BASE folder and are shared by every profile of that
# install, so one deploy covers the default profile (deploying while a
# different profile is selected would also apply on next switch).
#
# Usage:
#   tools/deploy-prod.sh [--force] [--no-backup] [--dry-run] [--base DIR]
#
#   --force     deploy even if Anki appears to be running (changes only
#               take effect on restart; a scratch Anki also trips the check)
#   --no-backup don't keep a backup of the previously installed copy
#   --dry-run   print the plan and change nothing
#   --base DIR  deploy into DIR instead of the default Anki base
#               (same meaning as Anki's ANKI_BASE env var)
#
# The previously installed copy is moved to <dest>.bak first; its meta.json
# (Anki's per-install add-on state) is carried over, not the repo's.
# Excluded from the copy: __pycache__/, *.pyc, meta.json.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO/language_study_anki"
PKG="language_study_anki"

FORCE=0
BACKUP=1
DRY_RUN=0
BASE_OVERRIDE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --force)   FORCE=1 ;;
    --no-backup) BACKUP=0 ;;
    --dry-run) DRY_RUN=1 ;;
    --base)    shift; BASE_OVERRIDE="${1:?--base needs a directory}" ;;
    -h|--help) sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown argument: $1 (see --help)" >&2; exit 2 ;;
  esac
  shift
done

# --- resolve the production base ------------------------------------------
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) PLATFORM=windows ;;
  Darwin)               PLATFORM=macos ;;
  *)                    PLATFORM=linux ;;
esac

if [ -n "$BASE_OVERRIDE" ]; then
  BASE="$BASE_OVERRIDE"
elif [ -n "${ANKI_BASE:-}" ]; then
  BASE="$ANKI_BASE"
elif [ "$PLATFORM" = windows ]; then
  BASE="${APPDATA:?APPDATA is not set}/Anki2"
elif [ "$PLATFORM" = macos ]; then
  BASE="$HOME/Library/Application Support/Anki2"
else
  BASE="${XDG_DATA_HOME:-$HOME/.local/share}/Anki2"
fi

DEST="$BASE/addons21/$PKG"

# --- sanity checks ---------------------------------------------------------
[ -f "$SRC/manifest.json" ] || { echo "source addon not found: $SRC" >&2; exit 1; }
if [ ! -d "$BASE" ]; then
  echo "Anki base not found: $BASE" >&2
  echo "Is Anki installed? (use --base DIR for a non-default install)" >&2
  exit 1
fi

# Default (last loaded) profile — informational only: add-ons live in the
# base and are shared by all profiles. Older Anki: profiles.json;
# current Anki (25+): prefs21.db (sqlite, pickled meta in _global row).
find_default_profile() {
  if [ -f "$BASE/profiles.json" ]; then
    grep -o '"currentProfile"[[:space:]]*:[[:space:]]*"[^"]*"' \
      "$BASE/profiles.json" | head -1 | sed 's/.*: *"\([^"]*\)"$/\1/' || true
    return
  fi
  if [ -f "$BASE/prefs21.db" ]; then
    for py in python3 python "py -3"; do
      name=$($py - "$BASE/prefs21.db" 2>/dev/null <<'PY' || true
import pickle, sqlite3, sys
try:
    con = sqlite3.connect(sys.argv[1])
    row = con.execute("select data from profiles where name='_global'").fetchone()
    print(pickle.loads(row[0]).get("last_loaded_profile_name", ""))
except Exception:
    pass
PY
      )
      if [ -n "$name" ]; then printf '%s\n' "$name"; return; fi
    done
  fi
  # Fallback: a base with exactly one profile folder.
  local dirs
  dirs=$(find "$BASE" -maxdepth 2 -name collection.anki2 2>/dev/null | wc -l | tr -d ' ')
  if [ "$dirs" = 1 ]; then
    find "$BASE" -maxdepth 2 -name collection.anki2 2>/dev/null \
      | head -1 | sed 's|/collection.anki2||; s|.*[\\/]||'
  fi
}

DEFAULT_PROFILE="$(find_default_profile)"

# --- is Anki running? ------------------------------------------------------
anki_running() {
  case "$PLATFORM" in
    windows) out=$(tasklist //NH //FI "IMAGENAME eq Anki.exe" 2>/dev/null || true)
             printf '%s' "$out" | grep -qi '^Anki\.exe' ;;
    macos)   pgrep -x Anki >/dev/null 2>&1 ;;
    *)       pgrep -x anki >/dev/null 2>&1 ;;
  esac
}

RUNNING=0
if anki_running; then RUNNING=1; fi

if [ "$RUNNING" = 1 ] && [ "$FORCE" = 0 ] && [ "$DRY_RUN" = 0 ]; then
  cat >&2 <<EOF
Anki appears to be running. The deployed copy only takes effect after a
restart, and Anki may rewrite files we are replacing.

Close Anki first, or re-run with --force
(ignored if the running instance is only a scratch/dev Anki).
EOF
  exit 1
fi

# --- plan ------------------------------------------------------------------
FILE_COUNT=$(find "$SRC" -type f ! -name '*.pyc' ! -name 'meta.json' \
  ! -path '*/__pycache__/*' | wc -l | tr -d ' ')

echo "source : $SRC ($FILE_COUNT files)"
echo "target : $DEST"
[ -n "$DEFAULT_PROFILE" ] && echo "base   : $BASE  (default profile: $DEFAULT_PROFILE)"
[ -e "$DEST" ] && echo "backup : $DEST.bak (previous copy, unless --no-backup)"
if [ "$RUNNING" = 1 ]; then echo "note   : Anki is running (--force)"; fi

if [ "$DRY_RUN" = 1 ]; then
  echo "dry run — nothing changed"
  exit 0
fi

# --- deploy ----------------------------------------------------------------
# Preserve the installed copy's meta.json (enabled state, user config);
# the repo copy of it is a dev artifact and is never deployed.
SAVED_META=""
if [ -f "$DEST/meta.json" ]; then
  SAVED_META="$(mktemp)"
  cp "$DEST/meta.json" "$SAVED_META"
fi

if [ -e "$DEST" ]; then
  if [ "$BACKUP" = 1 ]; then
    rm -rf "$DEST.bak"
    mv "$DEST" "$DEST.bak"
  else
    rm -rf "$DEST"
  fi
fi

mkdir -p "$(dirname "$DEST")"
cp -R "$SRC" "$DEST"

# Strip dev/runtime artifacts from the deployed copy.
rm -rf "$DEST/__pycache__"
find "$DEST" -type f -name '*.pyc' -delete
rm -f "$DEST/meta.json"
if [ -n "$SAVED_META" ]; then
  mv "$SAVED_META" "$DEST/meta.json"
fi

echo "deployed $FILE_COUNT files (+ meta.json) -> $DEST"
if [ "$RUNNING" = 1 ]; then
  echo "restart Anki to load the new version"
else
  echo "start Anki to load it"
fi
