#!/usr/bin/env bash
# tests/uninstall/run.sh — install/uninstall lifecycle.
#
# Installs with the real install.sh into isolated HOME/XDG paths, then removes
# it with uninstall.sh and asserts:
#   * the install created agents, skill, commands and source tree
#   * uninstall removes every managed path
#   * .ufme memory, opencode.json and package.json survive
#   * uninstall is idempotent
#   * --project-only leaves the global install in place
#
# Usage: bash tests/uninstall/run.sh
# Exit: 0 all pass, 1 failure.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PASS=0
FAIL=0
RESULTS=()
pass() { PASS=$((PASS + 1)); RESULTS+=("PASS: $1"); echo "PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); RESULTS+=("FAIL: $1 — $2"); echo "FAIL: $1: $2"; }
check() { if eval "$2"; then pass "$1"; else fail "$1" "${3:-condition failed: $2}"; fi; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export HOME="$TMP/home" XDG_CONFIG_HOME="$TMP/xdg"
export UFME_USER_CONFIG="$TMP/ufme-data" UFME_SOURCE_DIR="$ROOT"
export UFME_SKIP_NPM=1 INSTALL_DIR="$TMP/project"
mkdir -p "$HOME" "$XDG_CONFIG_HOME" "$INSTALL_DIR"
printf '{"name":"user-project"}\n' > "$INSTALL_DIR/package.json"

bash "$ROOT/install.sh" >"$TMP/install.log" 2>&1
check "install exits 0" "[ $? -eq 0 ]" "see $TMP/install.log"

GLOBAL_AGENTS="$XDG_CONFIG_HOME/opencode/agents"
GLOBAL_SKILL="$XDG_CONFIG_HOME/opencode/skills/universal-frontend-master"
GLOBAL_COMMANDS="$XDG_CONFIG_HOME/opencode/commands/ufme"
PROJECT_AGENTS="$INSTALL_DIR/.opencode/agents"
PROJECT_SKILL="$INSTALL_DIR/.opencode/skills/universal-frontend-master"
PROJECT_COMMANDS="$INSTALL_DIR/.opencode/commands/ufme"
SOURCE="$INSTALL_DIR/universal-frontend-master-source"

check "global agents installed" "[ -f '$GLOBAL_AGENTS/universal-frontend-master.md' ]"
check "global skill installed" "[ -f '$GLOBAL_SKILL/SKILL.md' ]"
check "global commands installed" "[ -f '$GLOBAL_COMMANDS/audit.md' ]"
check "project agents installed" "[ -f '$PROJECT_AGENTS/ufme-builder.md' ]"
check "project source installed" "[ -f '$SOURCE/scripts/quality-check.py' ]"

TASKS_BEFORE="$(cat "$INSTALL_DIR/.ufme/TASKS.md")"
printf '{"my_setting": true}\n' > "$INSTALL_DIR/opencode.json"
PACKAGE_BEFORE="$(sha256sum "$INSTALL_DIR/package.json" | awk '{print $1}')"

bash "$ROOT/uninstall.sh" >"$TMP/uninstall.log" 2>&1
check "uninstall exits 0" "[ $? -eq 0 ]" "see $TMP/uninstall.log"
check "global agents removed" "[ ! -e '$GLOBAL_AGENTS/universal-frontend-master.md' ]"
check "global skill removed" "[ ! -e '$GLOBAL_SKILL' ]"
check "global commands removed" "[ ! -e '$GLOBAL_COMMANDS' ]"
check "project agents removed" "[ ! -e '$PROJECT_AGENTS/ufme-builder.md' ]"
check "project skill removed" "[ ! -e '$PROJECT_SKILL' ]"
check "project commands removed" "[ ! -e '$PROJECT_COMMANDS' ]"
check "project source removed" "[ ! -e '$SOURCE' ]"
check "memory preserved" "[ \"\$(cat '$INSTALL_DIR/.ufme/TASKS.md')\" = '$TASKS_BEFORE' ]"
check "opencode.json preserved" "[ -f '$INSTALL_DIR/opencode.json' ]"
check "package.json preserved" \
  "[ \"\$(sha256sum '$INSTALL_DIR/package.json' | awk '{print \$1}')\" = '$PACKAGE_BEFORE' ]"

bash "$ROOT/uninstall.sh" >"$TMP/uninstall2.log" 2>&1
check "second uninstall exits 0" "[ $? -eq 0 ]" "see $TMP/uninstall2.log"

# --project-only must not touch the global install.
bash "$ROOT/install.sh" >"$TMP/reinstall.log" 2>&1
bash "$ROOT/uninstall.sh" --project-only >"$TMP/project-only.log" 2>&1
check "--project-only exits 0" "[ $? -eq 0 ]" "see $TMP/project-only.log"
check "--project-only keeps global agents" "[ -f '$GLOBAL_AGENTS/universal-frontend-master.md' ]"
check "--project-only removes project source" "[ ! -e '$SOURCE' ]"

EVIDENCE_DIR="$ROOT/.ufme/evidence"
mkdir -p "$EVIDENCE_DIR"
{
  printf '{\n  "checks": %d,\n  "pass": %d,\n  "failed": %d,\n  "results": [\n' \
    "$((PASS + FAIL))" "$PASS" "$FAIL"
  first=1
  for result in "${RESULTS[@]}"; do
    [ "$first" -eq 1 ] || printf ',\n'
    first=0
    status="${result%%:*}"
    printf '    {"status": "%s", "name": "%s"}' "$status" \
      "$(printf '%s' "${result#*: }" | sed 's/\\/\\\\/g; s/"/\\"/g')"
  done
  printf '\n  ]\n}\n'
} > "$EVIDENCE_DIR/uninstall-test.json"

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
