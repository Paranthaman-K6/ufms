#!/usr/bin/env bash
# tests/install/run.sh — clean-install and repeat-install tests.
#
# Runs the real install.sh from the local checkout (no network) with an isolated
# HOME/XDG_CONFIG_HOME, then asserts:
#   * six agents, the skill and a file-based global config are installed
#   * the global config preserves user keys and drops any legacy inline registry
#   * project-local agents, source tree and seed memory exist
#   * repeat installs merge instead of nesting directories
#   * existing .ufme memory is never overwritten
#   * UFME_SKIP_NPM leaves package.json untouched
#   * a source tree without the skill fails cleanly
#
# Usage: bash tests/install/run.sh
# Exit: 0 all pass, 1 failure.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INSTALL="$ROOT/install.sh"
AGENTS=(universal-frontend-master ufme-orchestrator ufme-designer ufme-builder ufme-backend-analyst ufme-auditor)
PASS=0
FAIL=0
RESULTS=()

pass() { PASS=$((PASS + 1)); RESULTS+=("PASS: $1"); echo "PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); RESULTS+=("FAIL: $1 — $2"); echo "FAIL: $1: $2"; }
check() { if eval "$2"; then pass "$1"; else fail "$1" "${3:-condition failed: $2}"; fi; }

setup() {
  TMP="$(mktemp -d)"
  export HOME="$TMP/home"
  export XDG_CONFIG_HOME="$TMP/xdg"
  export UFME_USER_CONFIG="$TMP/ufme-data"
  export UFME_SOURCE_DIR="$ROOT"
  export UFME_SKIP_NPM=1
  export INSTALL_DIR="$TMP/project"
  mkdir -p "$HOME" "$XDG_CONFIG_HOME" "$INSTALL_DIR"
}
teardown() { rm -rf "$TMP"; }

setup
trap teardown EXIT

run_install() {
  bash "$INSTALL" >"$TMP/install.log" 2>&1
}

# ------------------------------------------------------------------
# First install
# ------------------------------------------------------------------
if run_install; then pass "clean install exits 0"; else fail "clean install exits 0" "see $TMP/install.log"; fi

GLOBAL_AGENTS="$XDG_CONFIG_HOME/opencode/agents"
check "six agents installed globally" "[ \$(find '$GLOBAL_AGENTS' -maxdepth 1 -name '*.md' | wc -l) -eq 6 ]"
for agent in "${AGENTS[@]}"; do
  check "global agent $agent" "[ -f '$GLOBAL_AGENTS/$agent.md' ]"
done
check "global skill installed" "[ -f '$XDG_CONFIG_HOME/opencode/skills/universal-frontend-master/SKILL.md' ]"
check "project skill installed" "[ -f '$INSTALL_DIR/.opencode/skills/universal-frontend-master/SKILL.md' ]"
check "project source tree installed" "[ -f '$INSTALL_DIR/universal-frontend-master-source/scripts/quality-check.py' ]"
check "project agents installed" "[ \$(find '$INSTALL_DIR/.opencode/agents' -maxdepth 1 -name '*.md' | wc -l) -eq 6 ]"
check "project opencode.json installed" "[ -f '$INSTALL_DIR/opencode.json' ]"
check "project memory seeded" "[ -f '$INSTALL_DIR/.ufme/TASKS.md' ] && [ -f '$INSTALL_DIR/.ufme/ENVIRONMENT.md' ]"
check "library registry seeded" "[ -f '$UFME_USER_CONFIG/LIBRARY_REGISTRY.md' ]"

check "global config has no inline agent registry" \
  "! python3 -c \"import json,sys; sys.exit(0 if 'agent' in json.load(open('$XDG_CONFIG_HOME/opencode/opencode.json')) else 1)\""
check "global config sets default_agent" \
  "python3 -c \"import json,sys; sys.exit(0 if json.load(open('$XDG_CONFIG_HOME/opencode/opencode.json')).get('default_agent')=='universal-frontend-master' else 1)\""

# ------------------------------------------------------------------
# Existing user config and memory are preserved
# ------------------------------------------------------------------
printf '{"my_setting": {"keep": true}, "agent": {"legacy": {}}}\n' \
  > "$XDG_CONFIG_HOME/opencode/opencode.json"
printf '# user tasks\n' > "$INSTALL_DIR/.ufme/TASKS.md"
printf '{"name": "user-project", "scripts": {"test": "true"}}\n' > "$INSTALL_DIR/package.json"
BEFORE_PACKAGE="$(sha256sum "$INSTALL_DIR/package.json" | awk '{print $1}')"

if run_install; then pass "repeat install exits 0"; else fail "repeat install exits 0" "see $TMP/install.log"; fi

check "user config key preserved" \
  "python3 -c \"import json,sys; sys.exit(0 if json.load(open('$XDG_CONFIG_HOME/opencode/opencode.json')).get('my_setting',{}).get('keep') else 1)\""
check "legacy inline agent block removed" \
  "! python3 -c \"import json,sys; sys.exit(0 if 'agent' in json.load(open('$XDG_CONFIG_HOME/opencode/opencode.json')) else 1)\""
check "existing project memory preserved" "[ \"\$(cat '$INSTALL_DIR/.ufme/TASKS.md')\" = '# user tasks' ]"
check "UFME_SKIP_NPM leaves package.json untouched" \
  "[ \"\$(sha256sum '$INSTALL_DIR/package.json' | awk '{print \$1}')\" = '$BEFORE_PACKAGE' ]"
check "repeat install does not nest the source tree" \
  "[ ! -d '$INSTALL_DIR/universal-frontend-master-source/universal-frontend-master-source' ]"
check "repeat install does not nest the skill" \
  "[ ! -d '$INSTALL_DIR/.opencode/skills/universal-frontend-master/universal-frontend-master' ]"
check "repeat install keeps one source tree" \
  "[ \$(find '$INSTALL_DIR' -maxdepth 2 -type d -name 'universal-frontend-master-source' | wc -l) -eq 1 ]"

# ------------------------------------------------------------------
# Failure path: local source without the skill
# ------------------------------------------------------------------
EMPTY_SRC="$TMP/empty-source"
mkdir -p "$EMPTY_SRC"
if UFME_SOURCE_DIR="$EMPTY_SRC" bash "$INSTALL" >"$TMP/empty.log" 2>&1; then
  fail "missing skill source fails" "installer exited 0"
else
  pass "missing skill source fails"
fi
check "missing skill error is explicit" "grep -q 'skill not found' '$TMP/empty.log'"

# ------------------------------------------------------------------
# Report
# ------------------------------------------------------------------
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
} > "$EVIDENCE_DIR/install-test.json"

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
