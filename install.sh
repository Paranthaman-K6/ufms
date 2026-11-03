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
#   universal-frontend-master-source/             # source tree
#   .ufme/                                        # per-project memory templates (seeded only)
#   opencode.json                                 # permission policy (merged)
set -euo pipefail

REPO="Paranthaman-K6/ufms"
BRANCH="main"
TARBALL="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz"
TARGET="${INSTALL_DIR:-$PWD}"
UFME_USER_CONFIG="${UFME_USER_CONFIG:-${XDG_CONFIG_HOME:-$HOME/.config}/ufme}"
OPENCODE_USER_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"

log() { echo "[ufme-install] $*"; }

command -v curl >/dev/null 2>&1 || { log "ERROR: curl is required"; exit 1; }
command -v tar  >/dev/null 2>&1 || { log "ERROR: tar is required"; exit 1; }

log "Installing Universal Frontend Master skill"
log "Target project: $TARGET"
log "Global config dir: $OPENCODE_USER_CONFIG"
log "Cross-project data dir: $UFME_USER_CONFIG"

# ------------------------------------------------------------------
# 1. Download repository source archive
# ------------------------------------------------------------------
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

log "Downloading $REPO ($BRANCH)..."
curl -fsSL "$TARBALL" -o "$TMP/repo.tar.gz"
tar -xzf "$TMP/repo.tar.gz" -C "$TMP"
SRC="$TMP/ufms-${BRANCH}"

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

# Seed per-project memory from templates (never overwrite existing).
for f in TASKS.md ENVIRONMENT.md SKILL_VALIDATION.md AGENT_STATE.md DECISIONS.md ARCHITECTURE.md DESIGN_SYSTEM.md API_MAP.md AUTHENTICATION_MAP.md BACKEND_CAPABILITIES.md ERROR_HANDLING.md VISUAL_AUDIT.md AUDIT_REPORT.md; do
  [ -f "$TARGET/.ufme/$f" ] && continue
  tpl="$SRC/universal-frontend-master-source/templates/$f"
  if [ -f "$tpl" ]; then
    cp "$tpl" "$TARGET/.ufme/$f"
  else
    echo "# ${f%.md}" > "$TARGET/.ufme/$f"
  fi
done

# Point project opencode.json at global user config (project merges on top).
if [ ! -f "$TARGET/opencode.json" ]; then
  cp "$SRC/opencode.json" "$TARGET/opencode.json"
fi

# ------------------------------------------------------------------
# 5. Summary
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
