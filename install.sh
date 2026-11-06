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
#   UFME_SOURCE_DIR=/path/to/checkout                     # install from a local checkout (offline/CI)
#   UFME_SKIP_NPM=1                                      # skip the project-local npm install step
#   INSTALL_SCOPE=project|global|both                      # install scope (non-interactive)
#
# Install scopes:
#   project  — only the current project folder ($TARGET/.opencode/, $TARGET/skills/, $TARGET/.ufme/)
#   global   — only OpenCode user config ($HOME/.config/opencode/, $HOME/.config/ufme/)
#   both     — global + project (default when run interactively without INSTALL_SCOPE)
#
# Global install (user scope — available to all projects):
#   $HOME/.config/opencode/agents/*.md         # every agent from top-level agents/
#   $HOME/.config/opencode/commands/**         # every command from top-level commands/
#   $HOME/.config/opencode/skills/<name>/      # each skill in full (scripts, templates, workflows)
#   $HOME/.config/opencode/opencode.json       # agent + command registry, default agent
#   $HOME/.config/ufme/                        # cross-project shared data (library registry, state)
#
# Project-local install (target project only — never overwrites existing):
#   $TARGET/.opencode/agents/*.md              # agent copy (project override)
#   $TARGET/.opencode/commands/**              # command copy (project override)
#   $TARGET/.opencode/skills/<name>/SKILL.md   # skill definition (project override)
#   $TARGET/skills/<name>/                     # full skill source tree
#   $TARGET/.ufme/                             # per-project memory templates (seeded only)
#   $TARGET/opencode.json                      # permission policy (merged)
#   $TARGET/package.json (dev dep)             # full audit dependency set, if npm + package.json exist
set -euo pipefail

REPO="Paranthaman-K6/ufms"
BRANCH="main"
TARGET="${INSTALL_DIR:-$PWD}"
UFME_USER_CONFIG="${UFME_USER_CONFIG:-${XDG_CONFIG_HOME:-$HOME/.config}/ufme}"
OPENCODE_USER_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
NPM_DEPS=(selenium-webdriver @axe-core/webdriverjs lighthouse pngjs pixelmatch)
NPM_HINT="npm i -D ${NPM_DEPS[*]}"

log() { echo "[ufme-install] $*"; }

# Cross-platform helpers: macOS ships shasum, minimal Linux images may only have openssl.
sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v openssl >/dev/null 2>&1; then
    openssl dgst -sha256 "$1" | awk '{print $NF}'
  else
    log "ERROR: no sha256 tool found (need sha256sum, shasum or openssl)"
    return 1
  fi
}

# ------------------------------------------------------------------
# Self-update: replace this installer with the latest copy from main.
# ------------------------------------------------------------------
SELF_UPDATE=0
CHECK_UPDATE=0
for arg in "$@"; do
  case "$arg" in
    --self-update) SELF_UPDATE=1 ;;
    --check-update) CHECK_UPDATE=1 ;;
    -h|--help)
      echo "Usage: install.sh [--self-update|--check-update] [env vars...]"
      echo
      echo "  --self-update   Replace this installer with the latest copy from main"
      echo "  --check-update  Report whether a newer installer is available"
      echo
      echo "Environment overrides:"
      echo "  INSTALL_DIR, UFME_USER_CONFIG, UFME_TAG, UFME_TARBALL_SHA256,"
      echo "  UFME_SOURCE_DIR, UFME_SKIP_NPM"
      exit 0
      ;;
  esac
done

INSTALLER_URL="https://raw.githubusercontent.com/${REPO}/${BRANCH}/install.sh"

fetch_latest_installer() {
  local out="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$INSTALLER_URL" -o "$out"
  elif command -v wget >/dev/null 2>&1; then
    wget -q "$INSTALLER_URL" -O "$out"
  else
    log "ERROR: neither curl nor wget is available; cannot self-update"
    return 1
  fi
}

do_self_update() {
  local tmp_new
  tmp_new="$(mktemp)"

  log "Checking for latest installer at $INSTALLER_URL ..."
  if ! fetch_latest_installer "$tmp_new"; then
    rm -f "$tmp_new"
    log "ERROR: failed to download latest installer"
    return 1
  fi

  local current new
  current="$(sha256_of "$0")"
  new="$(sha256_of "$tmp_new")"
  if [ "$current" = "$new" ]; then
    rm -f "$tmp_new"
    log "Installer is already up to date (sha256: $new)"
    return 0
  fi

  cp "$tmp_new" "$0"
  chmod +x "$0"
  rm -f "$tmp_new"
  log "Installer updated to latest (sha256: $new)"
  log "Re-running the updated installer (normal install mode)..."
  # Re-exec without --self-update so we proceed to the actual install.
  filtered=()
  for a in "$@"; do
    [ "$a" != "--self-update" ] && filtered+=("$a")
  done
  exec "$0" "${filtered[@]+"${filtered[@]}"}"
}

do_check_update() {
  local tmp_new
  tmp_new="$(mktemp)"

  log "Checking for latest installer at $INSTALLER_URL ..."
  if ! fetch_latest_installer "$tmp_new"; then
    rm -f "$tmp_new"
    log "ERROR: failed to download latest installer"
    return 1
  fi

  local current new
  current="$(sha256_of "$0")"
  new="$(sha256_of "$tmp_new")"
  rm -f "$tmp_new"
  if [ "$current" = "$new" ]; then
    log "Installer is already up to date (sha256: $new)"
  else
    log "UPDATE AVAILABLE: current=$current latest=$new"
    log "Run: install.sh --self-update"
  fi
}

if [ "$SELF_UPDATE" -eq 1 ]; then
  do_self_update
  exit 0
fi

if [ "$CHECK_UPDATE" -eq 1 ]; then
  do_check_update
  exit 0
fi

# ------------------------------------------------------------------
# Install scope selection
# ------------------------------------------------------------------
# Non-interactive: honor INSTALL_SCOPE env var, default to "both".
# Interactive: prompt the user unless INSTALL_SCOPE is set.
INSTALL_SCOPE="${INSTALL_SCOPE:-}"
DO_GLOBAL=0
DO_PROJECT=0

pick_scope() {
  if [ -n "$INSTALL_SCOPE" ]; then
    case "$INSTALL_SCOPE" in
      project|global|both) ;;
      *)
        log "ERROR: invalid INSTALL_SCOPE='$INSTALL_SCOPE' (use project, global, or both)"
        exit 1
        ;;
    esac
    return
  fi

  # Non-interactive (CI, piped input, no TTY): default to both.
  if [ ! -t 0 ]; then
    INSTALL_SCOPE="both"
    log "Non-interactive install detected — defaulting to scope: both"
    return
  fi

  echo
  echo "============================================================"
  echo "  UFMW Install Scope"
  echo "============================================================"
  echo "  Project folder ($TARGET):"
  echo "    .opencode/agents/*, .opencode/skills/, .opencode/commands/"
  echo "    skills/universal-frontend-master/, .ufme/, opencode.json"
  echo "    npm dev dependencies (if package.json exists)"
  echo ""
  echo "  OpenCode config / home:"
  echo "    $HOME/.config/opencode/agents/*, skills/, commands/"
  echo "    $HOME/.config/opencode/opencode.json"
  echo "    $HOME/.config/ufme/ (shared library registry, evidence)"
  echo ""
  echo "  1) Project folder only"
  echo "  2) OpenCode config / home only (global)"
  echo "  3) Both (recommended — agents available in every project)"
  echo "  4) Cancel"
  echo "============================================================"
  echo -n "Choose scope [1-4]: "
  read -r choice || true
  case "$choice" in
    1) INSTALL_SCOPE="project" ;;
    2) INSTALL_SCOPE="global" ;;
    3) INSTALL_SCOPE="both" ;;
    4|"") log "Install cancelled by user."; exit 0 ;;
    *) log "Invalid choice — install cancelled."; exit 1 ;;
  esac
}

pick_scope

case "$INSTALL_SCOPE" in
  project) DO_PROJECT=1 ;;
  global)  DO_GLOBAL=1 ;;
  both)    DO_GLOBAL=1; DO_PROJECT=1 ;;
esac

log "Install scope: $INSTALL_SCOPE (global=$DO_GLOBAL project=$DO_PROJECT)"

log "Installing Universal Frontend Master skill"
log "Target project: $TARGET"
log "Global config dir: $OPENCODE_USER_CONFIG"
log "Cross-project data dir: $UFME_USER_CONFIG"

# ------------------------------------------------------------------
# 1. Download repository source archive (branch or pinned tag)
# ------------------------------------------------------------------
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if [ -n "${UFME_SOURCE_DIR:-}" ]; then
  SRC="$(cd "$UFME_SOURCE_DIR" && pwd)"
  log "Installing from local source: $SRC"
else
  command -v curl >/dev/null 2>&1 || { log "ERROR: curl is required"; exit 1; }
  command -v tar  >/dev/null 2>&1 || { log "ERROR: tar is required"; exit 1; }

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
    EXPECTED="$(printf '%s' "$UFME_TARBALL_SHA256" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')"
    ACTUAL="$(sha256_of "$TMP/repo.tar.gz")"
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
  SRC="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d -print | sed -n '1p')"
  [ -n "$SRC" ] || { log "ERROR: empty archive"; exit 1; }
fi

[ -d "$SRC/skills/universal-frontend-master" ] || { log "ERROR: skill not found in archive"; exit 1; }

# ------------------------------------------------------------------
# 2. Global install — user scope (all projects)
# ------------------------------------------------------------------
if [ "$DO_GLOBAL" -eq 1 ]; then
  log "Installing agents globally to $OPENCODE_USER_CONFIG/agents ..."
  mkdir -p "$OPENCODE_USER_CONFIG/agents"
  cp -R "$SRC/agents/." "$OPENCODE_USER_CONFIG/agents/"

  log "Installing slash commands globally to $OPENCODE_USER_CONFIG/commands ..."
  mkdir -p "$OPENCODE_USER_CONFIG/commands"
  cp -R "$SRC/commands/." "$OPENCODE_USER_CONFIG/commands/"

  for skill_dir in "$SRC"/skills/*/; do
    [ -d "$skill_dir" ] || continue
    skill_name="$(basename "$skill_dir")"
    log "Installing skill globally: $skill_name ..."
    mkdir -p "$OPENCODE_USER_CONFIG/skills/$skill_name"
    cp -R "$skill_dir." "$OPENCODE_USER_CONFIG/skills/$skill_name/"
  done

  log "Installing global opencode.json (default agent, commands, permissions) ..."
  GLOBAL_CONFIG="$OPENCODE_USER_CONFIG/opencode.json"

  # Preserve any existing user settings, but ensure our agents/commands/default_agent are present.
  if [ -f "$GLOBAL_CONFIG" ]; then
    cp "$GLOBAL_CONFIG" "$GLOBAL_CONFIG.bak.$(date +%s)"
  fi

  # Build the global opencode.json from the archive's version as the base, preserve
  # existing user keys, and keep file-based agent discovery (no inline agent registry).
  python3 - "$GLOBAL_CONFIG" "$SRC/opencode.json" <<'PYEOF'
import json, sys, os

global_path = sys.argv[1]
archive_cfg_path = sys.argv[2]

with open(archive_cfg_path) as f:
    archive_cfg = json.load(f)

existing = {}
if os.path.exists(global_path):
    try:
        with open(global_path) as f:
            existing = json.load(f)
    except Exception:
        existing = {}

cfg = dict(existing)
# File-based agents live in ~/.config/opencode/agents, so no inline "agent" block.
cfg.pop("agent", None)
cfg.setdefault("$schema", archive_cfg.get("$schema", "https://opencode.ai/config.json"))
cfg["default_agent"] = archive_cfg.get("default_agent", "universal-frontend-master")

for key in ("command", "permission"):
    if key not in archive_cfg:
        continue
    if isinstance(archive_cfg[key], dict) and isinstance(cfg.get(key), dict):
        merged = dict(archive_cfg[key])
        for name, value in cfg[key].items():
            if isinstance(value, dict) and isinstance(merged.get(name), dict):
                merged[name] = {**value, **merged[name]}
            else:
                merged.setdefault(name, value)
        cfg[key] = merged
    else:
        cfg[key] = archive_cfg[key]

with open(global_path, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")

print(f"Wrote global opencode.json to {global_path}")
PYEOF

  # ------------------------------------------------------------------
  # 3. Cross-project shared data directory (never overwrite existing)
  # ------------------------------------------------------------------
  log "Setting up cross-project shared data at $UFME_USER_CONFIG ..."
  mkdir -p "$UFME_USER_CONFIG/evidence"

  # Library registry — shared catalog available to every project
  if [ ! -f "$UFME_USER_CONFIG/LIBRARY_REGISTRY.md" ]; then
    cp "$SRC/skills/universal-frontend-master/templates/LIBRARY_REGISTRY.md" "$UFME_USER_CONFIG/LIBRARY_REGISTRY.md"
  fi
else
  log "Skipping global install (scope: $INSTALL_SCOPE)"
fi

# ------------------------------------------------------------------
# 4. Project-local install (target project — seed only, never overwrite)
# ------------------------------------------------------------------
if [ "$DO_PROJECT" -eq 1 ]; then
  log "Installing project-local files into $TARGET ..."
  mkdir -p "$TARGET/.opencode/agents" "$TARGET/.opencode/commands" \
           "$TARGET/.opencode/skills" "$TARGET/.ufme" "$TARGET/skills"

  # Agents and commands: one source, mirrored into the project override.
  cp -R "$SRC/agents/." "$TARGET/.opencode/agents/"
  cp -R "$SRC/commands/." "$TARGET/.opencode/commands/"

  # Skills: full source tree for scripts/templates, SKILL.md for the project override.
  for skill_dir in "$SRC"/skills/*/; do
    [ -d "$skill_dir" ] || continue
    skill_name="$(basename "$skill_dir")"
    mkdir -p "$TARGET/skills/$skill_name" "$TARGET/.opencode/skills/$skill_name"
    cp -R "$skill_dir." "$TARGET/skills/$skill_name/"
    cp "$skill_dir/SKILL.md" "$TARGET/.opencode/skills/$skill_name/SKILL.md"
  done

  # Browser runner check — bundled browser automation lives in the source tree.
  if [ -f "$TARGET/skills/universal-frontend-master/browser/run.js" ]; then
    log "Browser runner installed: skills/universal-frontend-master/browser/run.js"
  else
    log "WARNING: skills/universal-frontend-master/browser/run.js is missing."
    log "  Browser-driven validation (Selenium) will be unavailable."
    log "  Reinstall, or copy the browser/ directory from the repository manually."
  fi

  # Seed per-project memory from bundled templates (never overwrite existing).
  python3 "$SRC/skills/universal-frontend-master/scripts/seed-project-memory.py" "$TARGET"

  # Point project opencode.json at global user config (project merges on top).
  if [ ! -f "$TARGET/opencode.json" ]; then
    cp "$SRC/opencode.json" "$TARGET/opencode.json"
  fi
else
  log "Skipping project-local install (scope: $INSTALL_SCOPE)"
fi

# ------------------------------------------------------------------
# 5. Project-local npm dependencies (full audit set, best-effort)
# ------------------------------------------------------------------
if [ "$DO_PROJECT" -eq 1 ]; then
  if [ -f "$TARGET/package.json" ] && [ -z "${UFME_SKIP_NPM:-}" ]; then
    if command -v npm >/dev/null 2>&1; then
      log "Installing project-local dev dependencies: $NPM_HINT ..."
      if (cd "$TARGET" && npm install -D "${NPM_DEPS[@]}" --loglevel=error >"$TMP/npm.log" 2>&1); then
        log "Audit dependencies installed: ${NPM_DEPS[*]}"
      else
        log "WARNING: npm install failed. Install the browser/audit dependencies manually:"
        log "  cd \"$TARGET\" && $NPM_HINT"
        log "(npm output kept at $TMP — note it is removed when this installer exits; rerun to see the error.)"
      fi
    else
      log "npm not found. Install the browser/audit dependencies manually:"
      log "  cd \"$TARGET\" && $NPM_HINT"
    fi
  else
    log "No package.json in $TARGET (or UFME_SKIP_NPM set). To enable browser and audit validation, run in your project:"
    log "  $NPM_HINT"
  fi
else
  log "Skipping project-local npm dependencies (scope: $INSTALL_SCOPE)"
fi

# ------------------------------------------------------------------
# 6. Summary
# ------------------------------------------------------------------
if [ "$DO_GLOBAL" -eq 1 ]; then
  AGENT_COUNT=$(ls "$OPENCODE_USER_CONFIG/agents"/*.md 2>/dev/null | wc -l)
  log "Installed agents globally: $AGENT_COUNT (user scope — available to all projects)"
  log "Installed skill globally: $OPENCODE_USER_CONFIG/skills/"
  log "Installed SEO skill globally: $OPENCODE_USER_CONFIG/skills/ufmw-seo-protocol"
  log "Installed init-frontend skill globally: $OPENCODE_USER_CONFIG/skills/init-frontend"
fi
if [ "$DO_PROJECT" -eq 1 ]; then
  log "Installed source tree: $TARGET/skills/"
  log "Project-local seed: $TARGET/.ufme/"
  log "Project-local init-frontend skill: $TARGET/.opencode/skills/init-frontend/"
fi
if [ "$DO_GLOBAL" -eq 1 ]; then
  log "Cross-project data: $UFME_USER_CONFIG (library registry shared across projects)"
fi
log ""
if [ "$DO_GLOBAL" -eq 1 ] && [ "$DO_PROJECT" -eq 1 ]; then
  log "Done. Start OpenCode in any project and invoke: @universal-frontend-master"
  log "Run profiles: /profile/lite | /profile/standard | /profile/advanced | /profile/autonomous"
elif [ "$DO_PROJECT" -eq 1 ]; then
  log "Done. Project-local install complete in $TARGET"
  log "Start OpenCode in this project and invoke: @universal-frontend-master"
else
  log "Done. Global install complete in $OPENCODE_USER_CONFIG"
  log "Start OpenCode in any project and invoke: @universal-frontend-master"
fi
