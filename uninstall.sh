#!/usr/bin/env bash
# uninstall.sh — remove the Universal Frontend Master skill and its agents.
#
# Removes only files this project installs. It never touches:
#   * .ufme/            (project memory and evidence)
#   * opencode.json     (user/project configuration)
#   * package.json      (dev dependencies)
#
# Usage:
#   INSTALL_DIR=/path/to/project bash uninstall.sh [--project-only|--global-only]
#
# Without a flag both scopes are removed. Removes the frontend and SEO agents,
# skills, and slash commands this installer places. The command is idempotent:
# running it twice still exits 0.
set -uo pipefail

AGENTS=(universal-frontend-master ufme-orchestrator ufme-designer ufme-builder ufme-backend-analyst ufme-auditor ufmw-seo-protocol ufmw-seo-technical ufmw-seo-content ufmw-seo-analyst ufmw-seo-auditor)
TARGET="${INSTALL_DIR:-$PWD}"
OPENCODE_USER_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"

SCOPE="all"
for arg in "$@"; do
  case "$arg" in
    --project-only) SCOPE="project" ;;
    --global-only) SCOPE="global" ;;
    -h|--help)
      echo "Usage: INSTALL_DIR=<project> bash uninstall.sh [--project-only|--global-only]"
      exit 0
      ;;
    *)
      echo "[ufme-uninstall] unknown option: $arg" >&2
      exit 2
      ;;
  esac
done

log() { echo "[ufme-uninstall] $*"; }
REMOVED=0

remove_path() {
  if [ -e "$1" ] || [ -L "$1" ]; then
    rm -rf -- "$1"
    log "removed $1"
    REMOVED=$((REMOVED + 1))
  fi
}

if [ "$SCOPE" != "global" ]; then
  log "Removing project install from $TARGET"
  for agent in "${AGENTS[@]}"; do
    remove_path "$TARGET/.opencode/agents/$agent.md"
  done
  remove_path "$TARGET/.opencode/skills/universal-frontend-master"
  remove_path "$TARGET/.opencode/skills/ufmw-seo-protocol"
  remove_path "$TARGET/.opencode/commands/ufme"
  remove_path "$TARGET/.opencode/commands/ufmw"
  remove_path "$TARGET/universal-frontend-master-source"
fi

if [ "$SCOPE" != "project" ]; then
  log "Removing global install from $OPENCODE_USER_CONFIG"
  for agent in "${AGENTS[@]}"; do
    remove_path "$OPENCODE_USER_CONFIG/agents/$agent.md"
  done
  remove_path "$OPENCODE_USER_CONFIG/skills/universal-frontend-master"
  remove_path "$OPENCODE_USER_CONFIG/skills/ufmw-seo-protocol"
  remove_path "$OPENCODE_USER_CONFIG/commands/ufme"
  remove_path "$OPENCODE_USER_CONFIG/commands/ufmw"
fi

log "Kept: .ufme/ memory, opencode.json, package.json, and all other files."
log "Removed $REMOVED managed path(s)."
