#!/usr/bin/env bash
# install.sh — install the Universal Frontend Master skill into a project.
#
# Usage (from GitHub):
#   curl -fsSL https://raw.githubusercontent.com/Paranthaman-K6/ufms/main/install.sh | bash
#
# Optional:
#   INSTALL_DIR=/path/to/project curl -fsSL ... | bash
#
# Installs: .opencode/skills/universal-frontend-master/, .opencode/agents/ufme-*.md, .ufme/
# Also seeds the user-level library registry (~/.config/ufme/LIBRARY_REGISTRY.md)
# so the same catalog is available to every project.
set -euo pipefail

REPO="Paranthaman-K6/ufms"
BRANCH="main"
TARBALL="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz"
TARGET="${INSTALL_DIR:-$PWD}"

log() { echo "[ufme-install] $*"; }

command -v curl >/dev/null 2>&1 || { log "ERROR: curl is required"; exit 1; }
command -v tar  >/dev/null 2>&1 || { log "ERROR: tar is required"; exit 1; }

log "Installing into: $TARGET"
mkdir -p "$TARGET/.opencode/skills" "$TARGET/.opencode/agents" "$TARGET/.ufme"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

log "Downloading $REPO ($BRANCH)..."
curl -fsSL "$TARBALL" -o "$TMP/repo.tar.gz"
tar -xzf "$TMP/repo.tar.gz" -C "$TMP"
SRC="$TMP/ufms-${BRANCH}"

[ -d "$SRC/.opencode/skills/universal-frontend-master" ] || { log "ERROR: skill not found in archive"; exit 1; }

cp -R "$SRC/.opencode/skills/universal-frontend-master" "$TARGET/.opencode/skills/"
cp -R "$SRC/.opencode/agents/." "$TARGET/.opencode/agents/" 2>/dev/null || true
cp -R "$SRC/universal-frontend-master-source" "$TARGET/"

# Seed the user-level library registry shared by every project (never overwrite).
UFME_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/ufme"
mkdir -p "$UFME_CONFIG"
if [ ! -f "$UFME_CONFIG/LIBRARY_REGISTRY.md" ]; then
  cp "$SRC/universal-frontend-master-source/templates/LIBRARY_REGISTRY.md" "$UFME_CONFIG/LIBRARY_REGISTRY.md"
fi

# Seed UFME memory from templates (never overwrite existing).
for f in TASKS.md ENVIRONMENT.md SKILL_VALIDATION.md AGENT_STATE.md; do
  [ -f "$TARGET/.ufme/$f" ] && continue
  tpl="$SRC/universal-frontend-master-source/templates/$f"
  if [ -f "$tpl" ]; then cp "$tpl" "$TARGET/.ufme/$f"; else echo "# ${f%.md}" > "$TARGET/.ufme/$f"; fi
done

log "Installed skill: .opencode/skills/universal-frontend-master"
log "Installed source: universal-frontend-master-source"
log "Installed agents: $(ls "$TARGET/.opencode/agents"/ufme-*.md 2>/dev/null | wc -l)"
log "Done. Start OpenCode in $TARGET and run the universal-frontend-master skill."