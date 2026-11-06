#!/usr/bin/env bash
# scaffold-app.sh — Scaffold a frontend app without clobbering state files.
#
# Runs a scaffold command in a temp directory, then moves only the app files
# into the target project, preserving .ufme/, .openchamber/, .git/, node_modules/
# and other state directories that already exist in the target.
#
# Usage:
#   scaffold-app.sh <scaffold-command> [target-dir]
#
#   scaffold-command   Shell command that scaffolds an app (run in the temp dir)
#   target-dir         Project directory to receive the app files (default: .)
#
# Example:
#   scaffold-app.sh "npm create vite@latest app -- --template react" ./my-app
#
set -euo pipefail

log() { echo "[scaffold-app] $*"; }
warn() { echo "[scaffold-app] WARNING: $*" >&2; }

# Directories/files that are state, never touched or moved by the scaffold.
STATE_NAMES=(.ufme .openchamber .git node_modules .next dist build .vite)

SCAFFOLD_CMD="${1:-}"
TARGET="${2:-$PWD}"

if [ -z "$SCAFFOLD_CMD" ]; then
  echo "Usage: $0 <scaffold-command> [target-dir]" >&2
  exit 2
fi

TARGET="$(cd "$TARGET" && pwd)"
[ -d "$TARGET" ] || { log "ERROR: target directory does not exist: $TARGET"; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

log "Scaffolding into temp directory: $TMP"
(
  cd "$TMP"
  eval "$SCAFFOLD_CMD"
)

# Determine the app root: if the scaffold produced exactly one top-level entry
# that is a directory, that is the app root; otherwise the temp root itself.
shopt -s nullglob
entries=("$TMP"/*)
shopt -u nullglob
APP_ROOT="$TMP"
if [ "${#entries[@]}" -eq 1 ] && [ -d "${entries[0]}" ]; then
  APP_ROOT="${entries[0]}"
fi

log "App root detected: $APP_ROOT"

is_state_name() {
  local name="$1"
  for state in "${STATE_NAMES[@]}"; do
    [ "$name" = "$state" ] && return 0
  done
  return 1
}

moved=0
shopt -s nullglob dotglob
for item in "$APP_ROOT"/* "$APP_ROOT"/.*; do
  [ -e "$item" ] || continue
  name="$(basename "$item")"
  if [ "$name" = "." ] || [ "$name" = ".." ]; then
    continue
  fi
  if is_state_name "$name"; then
    warn "skipping state directory in scaffold output: $name"
    continue
  fi
  dest="$TARGET/$name"
  if [ -e "$dest" ]; then
    warn "already exists in target, keeping existing: $name"
    continue
  fi
  mv "$item" "$dest"
  log "moved app file: $name"
  moved=$((moved + 1))
done
shopt -u nullglob dotglob

log "Done. Moved $moved app file(s) into $TARGET"
log "State directories preserved: .ufme/ .openchamber/ .git/ node_modules/"
