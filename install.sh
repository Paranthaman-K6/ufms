#!/usr/bin/env bash
# install.sh — Install the Universal Frontend Master skill globally (user scope).
#
# Installs once per user so @universal-frontend-master and all sub-agents are
# available in EVERY project on the machine, plus project-local seed files.
#
# Usage (from GitHub):
#   curl -fsSL https://raw.githubusercontent.com/Paranthaman-K6/ufms/main/install.sh | bash
#
# Optional:
#   INSTALL_DIR=/path/to/project curl -fsSL ... | bash   # project-local seed dir
#   UFME_USER_CONFIG=/custom/path                        # override cross-project data dir
#   UFME_TAG=v1.2.0                                      # pin install to a release tag
#   UFME_TARBALL_SHA256=<sha256>                         # verify tarball checksum, abort on mismatch
#
# Global install (user scope — available to all projects):
#   ~/.config/opencode/agents/*.md              # agent definitions
#   ~/.config/opencode/skills/*/SKILL.md        # skill definition
#   ~/.config/opencode/commands/*               # slash commands (/profile/*, /lite, /standard, ...)
#   ~/.config/opencode/opencode.json            # agent + command registry, default agent
#   ~/.config/ufme/                             # cross-project shared data (library registry, state)
#
# Project-local install (target project only — never overwrites existing):
#   .opencode/skills/universal-frontend-master/  # skill copy (project override)
#   .opencode/agents/*.md                         # agent copy (project override)
#   universal-frontend-master-source/             # source tree (includes browser runner)
#   .ufme/                                        # per-project memory templates (seeded only)
#   opencode.json                                 # permission policy (merged)
#   package.json (dev dep)                        # selenium-webdriver, if npm + package.json exist
set -euo pipefail

REPO="Paranthaman-K6/ufms"
BRANCH="main"
TARGET="${INSTALL_DIR:-$PWD}"
UFME_USER_CONFIG="${UFME_USER_CONFIG:-${XDG_CONFIG_HOME:-$HOME/.config}/ufme}"
OPENCODE_USER_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
NPM_HINT='npm i -D selenium-webdriver'

log() { echo "[ufme-install] $*"; }

command -v curl >/dev/null 2>&1 || { log "ERROR: curl is required"; exit 1; }
command -v tar  >/dev/null 2>&1 || { log "ERROR: tar is required"; exit 1; }

log "Installing Universal Frontend Master skill"
log "Target project: $TARGET"
log "Global config dir: $OPENCODE_USER_CONFIG"
log "Cross-project data dir: $UFME_USER_CONFIG"

# ------------------------------------------------------------------
# 1. Download repository source archive (branch or pinned tag)
# ------------------------------------------------------------------
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if [ -n "${UFME_TAG:-}" ]; then
  TARBALL="https://github.com/${REPO}/archive/refs/tags/${UFME_TAG}.tar.gz"
  REF_LABEL="tag ${UFME_TAG}"
else
  TARBALL="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz"
  REF_LABEL="branch ${BRANCH}"
fi

log "Downloading $REPO ($REF_LABEL)..."
curl -fsSL "$TARBALL" -o "$TMP/repo.tar.gz"

# Optional checksum verification (UFME_TARBALL_SHA256) — abort on mismatch.
if [ -n "${UFME_TARBALL_SHA256:-}" ]; then
  EXPECTED="${UFME_TARBALL_SHA256//[[:space:]]/}"
  EXPECTED="${EXPECTED,,}"
  ACTUAL="$(sha256sum "$TMP/repo.tar.gz" | awk '{print $1}')"
  if [ "$ACTUAL" != "$EXPECTED" ]; then
    log "ERROR: tarball sha256 mismatch — aborting install."
    log "  Expected: $EXPECTED"
    log "  Actual:   $ACTUAL"
    log "The downloaded archive may be truncated or tampered with. Nothing was installed."
    exit 1
  fi
  log "Tarball sha256 verified: $ACTUAL"
fi

tar -xzf "$TMP/repo.tar.gz" -C "$TMP"
# Top-level dir differs between branch archives (ufms-<branch>) and tag
# archives (ufms-<tag>) — detect it instead of hardcoding.
SRC="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d -print -quit)"
[ -n "$SRC" ] || { log "ERROR: empty archive"; exit 1; }

[ -d "$SRC/.opencode/skills/universal-frontend-master" ] || { log "ERROR: skill not found in archive"; exit 1; }

# ------------------------------------------------------------------
# 2. Global install — user scope (all projects)
# ------------------------------------------------------------------
log "Installing agents globally to $OPENCODE_USER_CONFIG/agents ..."
mkdir -p "$OPENCODE_USER_CONFIG/agents"
cp -R "$SRC/.opencode/agents/." "$OPENCODE_USER_CONFIG/agents/" 2>/dev/null || true

log "Installing skill globally to $OPENCODE_USER_CONFIG/skills/universal-frontend-master ..."
mkdir -p "$OPENCODE_USER_CONFIG/skills/universal-frontend-master"
cp -R "$SRC/.opencode/skills/universal-frontend-master/." "$OPENCODE_USER_CONFIG/skills/universal-frontend-master/"

log "Installing global opencode.json (agent registry + default agent + commands) ..."
GLOBAL_CONFIG="$OPENCODE_USER_CONFIG/opencode.json"

# Preserve any existing user settings, but ensure our agents/commands/default_agent are present.
if [ -f "$GLOBAL_CONFIG" ]; then
  cp "$GLOBAL_CONFIG" "$GLOBAL_CONFIG.bak.$(date +%s)"
fi

# Build the global opencode.json from the archive's version as the base, then ensure
# user-scoped agent references point to ~/.config/opencode/agents/*.md.
python3 - "$GLOBAL_CONFIG" "$SRC/opencode.json" <<'PYEOF'
import json, sys, os

global_path = sys.argv[1]
archive_cfg_path = sys.argv[2]

with open(archive_cfg_path) as f:
    archive_cfg = json.load(f)

# Start from archive opencode.json, but remap agent prompt paths to global user dir.
cfg = archive_cfg.get("agent", {})
for agent_id, agent_def in cfg.items():
    prompt = agent_def.get("prompt", "")
    if prompt.startswith("{file:.opencode/agents/"):
        agent_file = prompt.replace("{file:.opencode/agents/", "").rstrip("}")
        agent_def["prompt"] = f"{{file:~/.config/opencode/agents/{agent_file}}}"

# Ensure default_agent points to universal-frontend-master
cfg_default = archive_cfg.get("default_agent", "universal-frontend-master")
cfg = {"default_agent": cfg_default, "agent": cfg}

# Merge commands from archive if any
if "command" in archive_cfg:
    cfg["command"] = archive_cfg["command"]

# Preserve top-level permission rules from archive
if "permission" in archive_cfg:
    cfg["permission"] = archive_cfg["permission"]

# Preserve existing user config keys (later write merges back)
existing = {}
if os.path.exists(global_path):
    try:
        with open(global_path) as f:
            existing = json.load(f)
    except Exception:
        existing = {}

# Merge: archive-provided agents/commands win, but keep any user-only keys.
if "agent" in existing:
    # Keep existing user agents that aren't in our set
    for aid, adef in existing["agent"].items():
        if aid not in cfg["agent"]:
            cfg["agent"][aid] = adef
if "command" in existing:
    for cid, cdef in existing["command"].items():
        if cid not in cfg["command"]:
            cfg["command"][cid] = cdef
if "permission" in existing:
    # Deep-merge permission sections
    for section, rules in existing["permission"].items():
        if section not in cfg["permission"]:
            cfg["permission"][section] = rules
        else:
            if isinstance(rules, dict):
                cfg["permission"][section].update(rules)

with open(global_path, "w") as f:
    json.dump(cfg, f, indent=2)

print(f"Wrote global opencode.json to {global_path}")
PYEOF

# ------------------------------------------------------------------
# 3. Cross-project shared data directory (never overwrite existing)
# ------------------------------------------------------------------
log "Setting up cross-project shared data at $UFME_USER_CONFIG ..."
mkdir -p "$UFME_USER_CONFIG/evidence"

# Library registry — shared catalog available to every project
if [ ! -f "$UFME_USER_CONFIG/LIBRARY_REGISTRY.md" ]; then
  cp "$SRC/universal-frontend-master-source/templates/LIBRARY_REGISTRY.md" "$UFME_USER_CONFIG/LIBRARY_REGISTRY.md"
fi

# ------------------------------------------------------------------
# 4. Project-local install (target project — seed only, never overwrite)
# ------------------------------------------------------------------
log "Installing project-local files into $TARGET ..."
mkdir -p "$TARGET/.opencode/skills" "$TARGET/.opencode/agents" "$TARGET/.ufme"

cp -R "$SRC/.opencode/skills/universal-frontend-master" "$TARGET/.opencode/skills/" 2>/dev/null || true
cp -R "$SRC/.opencode/agents/." "$TARGET/.opencode/agents/" 2>/dev/null || true
cp -R "$SRC/universal-frontend-master-source" "$TARGET/"

# Browser runner check — bundled browser automation lives in the source tree.
if [ -f "$TARGET/universal-frontend-master-source/browser/run.js" ]; then
  log "Browser runner installed: universal-frontend-master-source/browser/run.js"
else
  log "WARNING: universal-frontend-master-source/browser/run.js is missing."
  log "  Browser-driven validation (Selenium) will be unavailable."
  log "  Reinstall, or copy the browser/ directory from the repository manually."
fi

# Seed per-project memory from bundled templates (never overwrite existing).
python3 "$SRC/universal-frontend-master-source/scripts/seed-project-memory.py" "$TARGET"

# Point project opencode.json at global user config (project merges on top).
if [ ! -f "$TARGET/opencode.json" ]; then
  cp "$SRC/opencode.json" "$TARGET/opencode.json"
fi

# ------------------------------------------------------------------
# 5. Project-local npm dependency (selenium-webdriver, best-effort)
# ------------------------------------------------------------------
if [ -f "$TARGET/package.json" ]; then
  if command -v npm >/dev/null 2>&1; then
    log "Installing project-local dev dependency: $NPM_HINT ..."
    if (cd "$TARGET" && npm install -D selenium-webdriver --loglevel=error >"$TMP/npm.log" 2>&1); then
      log "selenium-webdriver installed as a dev dependency."
    else
      log "WARNING: npm install failed. Install the browser dependency manually:"
      log "  cd \"$TARGET\" && $NPM_HINT"
      log "(npm output kept at $TMP — note it is removed when this installer exits; rerun to see the error.)"
    fi
  else
    log "npm not found. Install the browser dependency manually:"
    log "  cd \"$TARGET\" && $NPM_HINT"
  fi
else
  log "No package.json in $TARGET. To enable browser validation, run in your project:"
  log "  $NPM_HINT"
fi

# ------------------------------------------------------------------
# 6. Summary
# ------------------------------------------------------------------
AGENT_COUNT=$(ls "$OPENCODE_USER_CONFIG/agents"/*.md 2>/dev/null | wc -l)
log "Installed agents globally: $AGENT_COUNT (user scope — available to all projects)"
log "Installed skill globally: $OPENCODE_USER_CONFIG/skills/universal-frontend-master"
log "Installed source tree: $TARGET/universal-frontend-master-source"
log "Cross-project data: $UFME_USER_CONFIG (library registry shared across projects)"
log "Project-local seed: $TARGET/.ufme/"
log ""
log "Done. Start OpenCode in any project and invoke: @universal-frontend-master"
log "Run profiles: /profile/lite | /profile/standard | /profile/advanced | /profile/autonomous"
