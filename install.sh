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
#   INSTALL_SCOPE=project|global|both                      # install scope (skips the TUI)
#   UFME_SKILLS=name1,name2                               # only these skills (default: all)
#   UFME_SKIP_AGENTS=1                                    # skip agents
#   UFME_SKIP_COMMANDS=1                                  # skip slash commands
#   UFME_SKIP_MEMORY=1                                    # skip .ufme/ project memory seeding
#   UFME_SKIP_NPM=1                                       # skip the project-local npm install step
#   UFME_NONINTERACTIVE=1                                 # never open the TUI
#
# Interactive install: a single TUI screen asks what to install — scope, skills,
# agents, commands, project memory, audit dependencies — with everything selected
# (scope both) as the recommendation. Press Enter to accept, q to cancel.
# Non-interactive installs (INSTALL_SCOPE set, no terminal) install everything.
#
# Install scopes:
#   project  — only the current project folder ($TARGET/.opencode/, $TARGET/skills/, $TARGET/.ufme/)
#   global   — only OpenCode user config ($HOME/.config/opencode/, $HOME/.config/ufme/)
#   both     — global + project (recommended; the default when non-interactive)
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
      echo "Interactive (no env vars, terminal attached): a TUI asks what to install."
      echo "Everything is selected by default; Enter installs, q cancels."
      echo
      echo "Environment overrides (skip the TUI):"
      echo "  INSTALL_DIR, UFME_USER_CONFIG, UFME_TAG, UFME_TARBALL_SHA256,"
      echo "  UFME_SOURCE_DIR, INSTALL_SCOPE=project|global|both,"
      echo "  UFME_SKILLS=a,b, UFME_SKIP_AGENTS=1, UFME_SKIP_COMMANDS=1,"
      echo "  UFME_SKIP_MEMORY=1, UFME_SKIP_NPM=1, UFME_NONINTERACTIVE=1"
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
# Install selection — TUI when interactive, env overrides when scripted
# ------------------------------------------------------------------
INSTALL_SCOPE="${INSTALL_SCOPE:-}"
DO_GLOBAL=0
DO_PROJECT=0

WANT_AGENTS=1
WANT_COMMANDS=1
WANT_MEMORY=1
WANT_NPM=1
SELECTED_SKILLS=()
AVAILABLE_SKILLS=()
SCOPE_CHOICES=(project global both)
SCOPE_HINTS=("this project only" "all projects (user config)" "every project - recommended")

skill_available() {
  local want="$1" name
  for name in "${AVAILABLE_SKILLS[@]}"; do
    [ "$name" = "$want" ] && return 0
  done
  return 1
}

skill_selected() {
  local want="$1" name
  for name in ${SELECTED_SKILLS[@]+"${SELECTED_SKILLS[@]}"}; do
    [ "$name" = "$want" ] && return 0
  done
  return 1
}

# Environment selection: validates INSTALL_SCOPE and UFME_SKILLS, applies skips.
select_from_env() {
  case "$INSTALL_SCOPE" in
    project|global|both) ;;
    "")
      return 1
      ;;
    *)
      log "ERROR: invalid INSTALL_SCOPE='$INSTALL_SCOPE' (use project, global, or both)"
      exit 1
      ;;
  esac

  if [ -n "${UFME_SKILLS:-}" ]; then
    SELECTED_SKILLS=()
    local name
    local IFS=','
    for name in $UFME_SKILLS; do
      name="$(printf '%s' "$name" | tr -d '[:space:]')"
      [ -n "$name" ] || continue
      if ! skill_available "$name"; then
        log "ERROR: unknown skill '$name'"
        log "  Available: ${AVAILABLE_SKILLS[*]}"
        exit 1
      fi
      SELECTED_SKILLS+=("$name")
    done
    if [ "${#SELECTED_SKILLS[@]}" -eq 0 ]; then
      log "ERROR: UFME_SKILLS selected no skills"
      exit 1
    fi
  else
    SELECTED_SKILLS=("${AVAILABLE_SKILLS[@]}")
  fi

  if [ -n "${UFME_SKIP_AGENTS:-}" ]; then WANT_AGENTS=0; fi
  if [ -n "${UFME_SKIP_COMMANDS:-}" ]; then WANT_COMMANDS=0; fi
  if [ -n "${UFME_SKIP_MEMORY:-}" ]; then WANT_MEMORY=0; fi
  if [ -n "${UFME_SKIP_NPM:-}" ]; then WANT_NPM=0; fi
  return 0
}

tui_line() {
  local row="$1" text="$2"
  if [ "$row" -eq "$TUI_CURSOR" ]; then
    printf '\033[7m%s\033[0m\n' "$text"
  else
    printf '%s\n' "$text"
  fi
}

tui_toggle() {
  local row="$1" count="$2" index name kept
  if [ "$row" -eq 0 ]; then
    TUI_SCOPE=$(( (TUI_SCOPE + 1) % 3 ))
  elif [ "$row" -le "$count" ]; then
    index=$((row - 1))
    name="${AVAILABLE_SKILLS[$index]}"
    if skill_selected "$name"; then
      local -a next=()
      for kept in ${SELECTED_SKILLS[@]+"${SELECTED_SKILLS[@]}"}; do
        [ "$kept" = "$name" ] || next+=("$kept")
      done
      SELECTED_SKILLS=(${next[@]+"${next[@]}"})
    else
      SELECTED_SKILLS+=("$name")
    fi
  elif [ "$row" -eq $((count + 1)) ]; then
    WANT_AGENTS=$((1 - WANT_AGENTS))
  elif [ "$row" -eq $((count + 2)) ]; then
    WANT_COMMANDS=$((1 - WANT_COMMANDS))
  elif [ "$row" -eq $((count + 3)) ]; then
    WANT_MEMORY=$((1 - WANT_MEMORY))
  elif [ "$row" -eq $((count + 4)) ]; then
    WANT_NPM=$((1 - WANT_NPM))
  fi
}

# Single-screen TUI. Everything is selected by default (the recommendation);
# Enter installs, q cancels. Returns 1 when the user cancels.
tui_pick() {
  local count=${#AVAILABLE_SKILLS[@]}
  local total=$((count + 7))
  local prev_trap key seq i name box

  TUI_CURSOR=0
  TUI_SCOPE=2
  SELECTED_SKILLS=("${AVAILABLE_SKILLS[@]}")
  WANT_AGENTS=1
  WANT_COMMANDS=1
  WANT_MEMORY=1
  WANT_NPM=1

  prev_trap="$(trap -p EXIT)"
  trap 'printf "\033[?25h"' EXIT
  printf '\033[?25l'

  while true; do
    printf '\033[H\033[2J'
    printf '  UFMW installer - choose what to install\n'
    printf '  ------------------------------------------------------------\n'
    tui_line 0 "  Scope: < ${SCOPE_CHOICES[$TUI_SCOPE]} >  ${SCOPE_HINTS[$TUI_SCOPE]}"
    printf '  ------------------------------------------------------------\n'
    printf '  Skills\n'
    for i in "${!AVAILABLE_SKILLS[@]}"; do
      name="${AVAILABLE_SKILLS[$i]}"
      if skill_selected "$name"; then box='[x]'; else box='[ ]'; fi
      tui_line $((i + 1)) "  $box $name"
    done
    printf '  Include\n'
    if [ "$WANT_AGENTS" -eq 1 ]; then box='[x]'; else box='[ ]'; fi
    tui_line $((count + 1)) "  $box agents"
    if [ "$WANT_COMMANDS" -eq 1 ]; then box='[x]'; else box='[ ]'; fi
    tui_line $((count + 2)) "  $box slash commands"
    if [ "$WANT_MEMORY" -eq 1 ]; then box='[x]'; else box='[ ]'; fi
    tui_line $((count + 3)) "  $box project memory (.ufme seed)"
    if [ "$WANT_NPM" -eq 1 ]; then box='[x]'; else box='[ ]'; fi
    tui_line $((count + 4)) "  $box audit npm dependencies"
    printf '  ------------------------------------------------------------\n'
    tui_line $((count + 5)) "  [ Install ]"
    tui_line $((count + 6)) "  [ Cancel ]"
    printf '\n  Up/Down move   Space toggle   Left/Right scope   Enter install   q cancel\n'
    printf '  Recommended: scope both, every skill, agents, commands, memory, npm\n'

    IFS= read -rsn1 -u "$TUI_IN" key || key="q"
    case "$key" in
      $'\033')
        seq=""
        IFS= read -rsn2 -t 1 -u "$TUI_IN" seq || true
        case "$seq" in
          '[A') if [ "$TUI_CURSOR" -gt 0 ]; then TUI_CURSOR=$((TUI_CURSOR - 1)); fi ;;
          '[B') if [ "$TUI_CURSOR" -lt $((total - 1)) ]; then TUI_CURSOR=$((TUI_CURSOR + 1)); fi ;;
          '[C') if [ "$TUI_CURSOR" -eq 0 ]; then TUI_SCOPE=$(( (TUI_SCOPE + 1) % 3 )); fi ;;
          '[D') if [ "$TUI_CURSOR" -eq 0 ]; then TUI_SCOPE=$(( (TUI_SCOPE + 2) % 3 )); fi ;;
          '')
            printf '\033[?25h'
            trap - EXIT
            if [ -n "$prev_trap" ]; then eval "$prev_trap"; fi
            return 1
            ;;
        esac
        ;;
      ' ')
        tui_toggle "$TUI_CURSOR" "$count"
        ;;
      ''|$'\r'|$'\n')
        if [ "$TUI_CURSOR" -eq $((count + 6)) ]; then
          printf '\033[?25h'
          trap - EXIT
          if [ -n "$prev_trap" ]; then eval "$prev_trap"; fi
          return 1
        fi
        break
        ;;
      q|Q)
        printf '\033[?25h'
        trap - EXIT
        if [ -n "$prev_trap" ]; then eval "$prev_trap"; fi
        return 1
        ;;
    esac
  done

  printf '\033[?25h'
  trap - EXIT
  if [ -n "$prev_trap" ]; then eval "$prev_trap"; fi
  INSTALL_SCOPE="${SCOPE_CHOICES[$TUI_SCOPE]}"
  return 0
}

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

# Skills available in the resolved source tree (the TUI lists these).
AVAILABLE_SKILLS=()
for skill_dir in "$SRC"/skills/*/; do
  [ -d "$skill_dir" ] || continue
  AVAILABLE_SKILLS+=("$(basename "$skill_dir")")
done
[ "${#AVAILABLE_SKILLS[@]}" -gt 0 ] || { log "ERROR: no skills found in $SRC/skills"; exit 1; }

# ------------------------------------------------------------------
# 2. What to install — TUI when interactive, env overrides when scripted
# ------------------------------------------------------------------
# TUI needs a terminal. With `curl | bash`, stdin is the script, so fall back
# to /dev/tty when one is attached.
TUI_IN=0
INTERACTIVE=0
if [ -z "${INSTALL_SCOPE:-}" ] && [ -z "${UFME_NONINTERACTIVE:-}" ]; then
  if [ -t 0 ]; then
    INTERACTIVE=1
  elif exec 3<>/dev/tty 2>/dev/null; then
    TUI_IN=3
    INTERACTIVE=1
  fi
fi

if [ "$INTERACTIVE" -eq 1 ]; then
  if ! tui_pick; then
    log "Install cancelled."
    exit 0
  fi
else
  if [ -z "${INSTALL_SCOPE:-}" ]; then
    INSTALL_SCOPE="both"
    log "Non-interactive install - installing everything (scope: both)"
  fi
  select_from_env
fi

case "$INSTALL_SCOPE" in
  project) DO_PROJECT=1 ;;
  global)  DO_GLOBAL=1 ;;
  both)    DO_GLOBAL=1; DO_PROJECT=1 ;;
esac

log "Installing Universal Frontend Master skill"
log "Target project: $TARGET"
log "Global config dir: $OPENCODE_USER_CONFIG"
log "Cross-project data dir: $UFME_USER_CONFIG"
log "Install scope: $INSTALL_SCOPE (global=$DO_GLOBAL project=$DO_PROJECT)"
log "Skills: ${SELECTED_SKILLS[*]}"
log "Agents: $WANT_AGENTS  Commands: $WANT_COMMANDS  Memory: $WANT_MEMORY  npm: $WANT_NPM"

# ------------------------------------------------------------------
# 3. Global install — user scope (all projects)
# ------------------------------------------------------------------
if [ "$DO_GLOBAL" -eq 1 ]; then
  if [ "$WANT_AGENTS" -eq 1 ]; then
    log "Installing agents globally to $OPENCODE_USER_CONFIG/agents ..."
    mkdir -p "$OPENCODE_USER_CONFIG/agents"
    cp -R "$SRC/agents/." "$OPENCODE_USER_CONFIG/agents/"
  fi

  if [ "$WANT_COMMANDS" -eq 1 ]; then
    log "Installing slash commands globally to $OPENCODE_USER_CONFIG/commands ..."
    mkdir -p "$OPENCODE_USER_CONFIG/commands"
    cp -R "$SRC/commands/." "$OPENCODE_USER_CONFIG/commands/"
  fi

  for skill_name in ${SELECTED_SKILLS[@]+"${SELECTED_SKILLS[@]}"}; do
    skill_dir="$SRC/skills/$skill_name"
    [ -d "$skill_dir" ] || continue
    log "Installing skill globally: $skill_name ..."
    mkdir -p "$OPENCODE_USER_CONFIG/skills/$skill_name"
    cp -R "$skill_dir/." "$OPENCODE_USER_CONFIG/skills/$skill_name/"
  done

  log "Installing global opencode.json (default agent, commands, permissions) ..."
  GLOBAL_CONFIG="$OPENCODE_USER_CONFIG/opencode.json"

  # Preserve any existing user settings, but ensure our agents/commands/default_agent are present.
  if [ -f "$GLOBAL_CONFIG" ]; then
    cp "$GLOBAL_CONFIG" "$GLOBAL_CONFIG.bak.$(date +%s)"
  fi

  # Build the global opencode.json from the archive's version as the base, preserve
  # existing user keys, and keep file-based agent discovery (no inline agent registry).
  python3 - "$GLOBAL_CONFIG" "$SRC/opencode.json" "$WANT_AGENTS" "$WANT_COMMANDS" <<'PYEOF'
import json, sys, os

global_path = sys.argv[1]
archive_cfg_path = sys.argv[2]
want_agents = sys.argv[3] == "1"
want_commands = sys.argv[4] == "1"

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
# Only point at an agent we actually installed.
if want_agents:
    cfg["default_agent"] = archive_cfg.get("default_agent", "universal-frontend-master")

for key in ("command", "permission"):
    if key == "command" and not want_commands:
        continue
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
  # 4. Cross-project shared data directory (never overwrite existing)
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
# 5. Project-local install (target project — seed only, never overwrite)
# ------------------------------------------------------------------
if [ "$DO_PROJECT" -eq 1 ]; then
  log "Installing project-local files into $TARGET ..."
  mkdir -p "$TARGET/.opencode/agents" "$TARGET/.opencode/commands" \
           "$TARGET/.opencode/skills" "$TARGET/.ufme" "$TARGET/skills"

  # Agents and commands: one source, mirrored into the project override.
  if [ "$WANT_AGENTS" -eq 1 ]; then
    cp -R "$SRC/agents/." "$TARGET/.opencode/agents/"
  fi
  if [ "$WANT_COMMANDS" -eq 1 ]; then
    cp -R "$SRC/commands/." "$TARGET/.opencode/commands/"
  fi

  # Skills: full source tree for scripts/templates, SKILL.md for the project override.
  for skill_name in ${SELECTED_SKILLS[@]+"${SELECTED_SKILLS[@]}"}; do
    skill_dir="$SRC/skills/$skill_name"
    [ -d "$skill_dir" ] || continue
    mkdir -p "$TARGET/skills/$skill_name" "$TARGET/.opencode/skills/$skill_name"
    cp -R "$skill_dir/." "$TARGET/skills/$skill_name/"
    cp "$skill_dir/SKILL.md" "$TARGET/.opencode/skills/$skill_name/SKILL.md"
  done

  # Browser runner check — bundled browser automation lives in the source tree.
  if [ -f "$TARGET/skills/universal-frontend-master/browser/run.js" ]; then
    log "Browser runner installed: skills/universal-frontend-master/browser/run.js"
  elif [ -f "$TARGET/skills/universal-frontend-master/SKILL.md" ]; then
    log "WARNING: skills/universal-frontend-master/browser/run.js is missing."
    log "  Browser-driven validation (Selenium) will be unavailable."
    log "  Reinstall, or copy the browser/ directory from the repository manually."
  fi

  # Seed per-project memory from bundled templates (never overwrite existing).
  if [ "$WANT_MEMORY" -eq 1 ]; then
    python3 "$SRC/skills/universal-frontend-master/scripts/seed-project-memory.py" "$TARGET"
  fi

  # Point project opencode.json at global user config (project merges on top).
  if [ ! -f "$TARGET/opencode.json" ]; then
    cp "$SRC/opencode.json" "$TARGET/opencode.json"
  fi
else
  log "Skipping project-local install (scope: $INSTALL_SCOPE)"
fi

# ------------------------------------------------------------------
# 6. Project-local npm dependencies (full audit set, best-effort)
# ------------------------------------------------------------------
if [ "$DO_PROJECT" -eq 1 ]; then
  if [ "$WANT_NPM" -eq 1 ] && [ -f "$TARGET/package.json" ]; then
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
    log "Skipping audit npm dependencies (not selected, or no package.json in $TARGET). To enable browser and audit validation, run in your project:"
    log "  $NPM_HINT"
  fi
else
  log "Skipping project-local npm dependencies (scope: $INSTALL_SCOPE)"
fi

# ------------------------------------------------------------------
# 7. Summary
# ------------------------------------------------------------------
if [ "$DO_GLOBAL" -eq 1 ]; then
  if [ "$WANT_AGENTS" -eq 1 ]; then
    AGENT_COUNT=$(ls "$OPENCODE_USER_CONFIG/agents"/*.md 2>/dev/null | wc -l)
    log "Installed agents globally: $AGENT_COUNT (user scope — available to all projects)"
  fi
  log "Installed skills globally: ${SELECTED_SKILLS[*]}"
fi
if [ "$DO_PROJECT" -eq 1 ]; then
  log "Installed source tree: $TARGET/skills/"
  if [ "$WANT_MEMORY" -eq 1 ]; then
    log "Project-local seed: $TARGET/.ufme/"
  fi
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
