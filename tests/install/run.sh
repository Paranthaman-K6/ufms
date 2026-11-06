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
AGENTS=(universal-frontend-master ufme-orchestrator ufme-designer ufme-builder ufme-backend-analyst ufme-auditor ufmw-seo-protocol ufmw-seo-technical ufmw-seo-content ufmw-seo-analyst ufmw-seo-auditor init-frontend)
SEO_AGENTS=(ufmw-seo-protocol ufmw-seo-technical ufmw-seo-content ufmw-seo-analyst ufmw-seo-auditor)
PASS=0
FAIL=0
RESULTS=()

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    openssl dgst -sha256 "$1" | awk '{print $NF}'
  fi
}

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
check "twelve agents installed globally" "[ \$(find '$GLOBAL_AGENTS' -maxdepth 1 -name '*.md' | wc -l) -eq 12 ]"
for agent in "${AGENTS[@]}"; do
  check "global agent $agent" "[ -f '$GLOBAL_AGENTS/$agent.md' ]"
done
for agent in "${SEO_AGENTS[@]}"; do
  check "global SEO agent $agent" "[ -f '$GLOBAL_AGENTS/$agent.md' ]"
done
check "global skill installed" "[ -f '$XDG_CONFIG_HOME/opencode/skills/universal-frontend-master/SKILL.md' ]"
check "global SEO skill installed" "[ -f '$XDG_CONFIG_HOME/opencode/skills/ufmw-seo-protocol/SKILL.md' ]"
check "global SEO command installed" "[ -f '$XDG_CONFIG_HOME/opencode/commands/ufmw/seo-crawl.md' ]"
check "global init-frontend skill installed" "[ -f '$XDG_CONFIG_HOME/opencode/skills/init-frontend/SKILL.md' ]"
check "global init-frontend command installed" "[ -f '$XDG_CONFIG_HOME/opencode/commands/ufmw/init-frontend.md' ]"
check "project skill installed" "[ -f '$INSTALL_DIR/.opencode/skills/universal-frontend-master/SKILL.md' ]"
check "project SEO skill installed" "[ -f '$INSTALL_DIR/.opencode/skills/ufmw-seo-protocol/SKILL.md' ]"
check "project init-frontend skill installed" "[ -f '$INSTALL_DIR/.opencode/skills/init-frontend/SKILL.md' ]"
check "project source tree installed" "[ -f '$INSTALL_DIR/universal-frontend-master-source/scripts/quality-check.py' ]"
check "twelve project agents installed" "[ \$(find '$INSTALL_DIR/.opencode/agents' -maxdepth 1 -name '*.md' | wc -l) -eq 12 ]"
for agent in "${AGENTS[@]}"; do
  check "project agent $agent" "[ -f '$INSTALL_DIR/.opencode/agents/$agent.md' ]"
done
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
BEFORE_PACKAGE="$(sha256_of "$INSTALL_DIR/package.json")"

if run_install; then pass "repeat install exits 0"; else fail "repeat install exits 0" "see $TMP/install.log"; fi

check "user config key preserved" \
  "python3 -c \"import json,sys; sys.exit(0 if json.load(open('$XDG_CONFIG_HOME/opencode/opencode.json')).get('my_setting',{}).get('keep') else 1)\""
check "legacy inline agent block removed" \
  "! python3 -c \"import json,sys; sys.exit(0 if 'agent' in json.load(open('$XDG_CONFIG_HOME/opencode/opencode.json')) else 1)\""
check "existing project memory preserved" "[ \"\$(cat '$INSTALL_DIR/.ufme/TASKS.md')\" = '# user tasks' ]"
check "UFME_SKIP_NPM leaves package.json untouched" \
  "[ \"\$(sha256_of '$INSTALL_DIR/package.json')\" = '$BEFORE_PACKAGE' ]"
check "repeat install does not nest the source tree" \
  "[ ! -d '$INSTALL_DIR/universal-frontend-master-source/universal-frontend-master-source' ]"
check "repeat install does not nest the skill" \
  "[ ! -d '$INSTALL_DIR/.opencode/skills/universal-frontend-master/universal-frontend-master' ]"
check "repeat install keeps one source tree" \
  "[ \$(find '$INSTALL_DIR' -maxdepth 2 -type d -name 'universal-frontend-master-source' | wc -l) -eq 1 ]"

# ------------------------------------------------------------------
# Full audit dependency set is installed with a real npm invocation
# ------------------------------------------------------------------
STUB_BIN="$TMP/bin"
mkdir -p "$STUB_BIN"
cat > "$STUB_BIN/npm" <<'SH'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "${NPM_STUB_LOG:?}"
exit 0
SH
chmod +x "$STUB_BIN/npm"
NPM_LOG="$TMP/npm.args"
if PATH="$STUB_BIN:$PATH" NPM_STUB_LOG="$NPM_LOG" UFME_SKIP_NPM= \
   bash "$INSTALL" >"$TMP/npm-install.log" 2>&1; then
  pass "dependency install run exits 0"
else
  fail "dependency install run exits 0" "see $TMP/npm-install.log"
fi
for dep in selenium-webdriver @axe-core/webdriverjs lighthouse pngjs pixelmatch; do
  if grep -Fq -- "$dep" "$NPM_LOG" 2>/dev/null; then
    pass "npm receives $dep"
  else
    fail "npm receives $dep" "not present in: $(cat "$NPM_LOG" 2>/dev/null)"
  fi
done

# ------------------------------------------------------------------
# sha256 fallback works without sha256sum/shasum (macOS/minimal Linux)
# ------------------------------------------------------------------
if command -v sha256sum >/dev/null 2>&1; then
  PORTABLE_BIN="$TMP/portable-bin"
  SHA_BIN="$(command -v sha256sum)"
  BASH_BIN="$(command -v bash)"
  mkdir -p "$PORTABLE_BIN"
  ln -s "$(command -v awk)" "$PORTABLE_BIN/awk"
  cat > "$PORTABLE_BIN/openssl" <<SH
#!$BASH_BIN
"$SHA_BIN" "\${@: -1}" | awk '{print "SHA2-256(" \$2 ")= " \$1}'
SH
  chmod +x "$PORTABLE_BIN/openssl"
  HELPER="$(sed -n '/^sha256_of()/,/^}/p' "$INSTALL")"
  ACTUAL="$(PATH="$PORTABLE_BIN" "$BASH_BIN" -c "$HELPER
sha256_of '$INSTALL_DIR/package.json'")"
  check "sha256 falls back to openssl without sha256sum/shasum" \
    "[ '$ACTUAL' = '$BEFORE_PACKAGE' ]"
else
  printf 'SKIP: sha256 fallback test (sha256sum unavailable)\n'
fi

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
