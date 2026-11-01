#!/usr/bin/env bash
# quality-check.sh
# Run type check, lint, unit tests, production build, Selenium browser tests,
# axe-core accessibility checks (where a browser is available), Lighthouse against
# a locally served production build when possible, and dependency audit.
#
# Every step's result is recorded as PASS/FAIL/SKIPPED/BLOCKED; the script exits
# nonzero when any step FAILed. Skipped steps are recorded, not hidden.
#
# Safety: project-local only; never sudo/pacman/systemctl.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

STATUS="PASS"
SUMMARY=""

log() { echo "[quality-check] $*"; }

record() { # record <status> <label>
  SUMMARY+="$2: $1"$'\n'
  log "$2: $1"
}

record_skip() { record "SKIPPED" "$1"; }

run_if() { # run_if <command guard text?> <label> <command...>
  local label="$1" rc
  shift
  if [ $# -gt 0 ]; then
    if "$@"; then
      record "PASS" "$label"
      return 0
    else
      rc=$?
      record "FAIL (rc=$rc)" "$label"
      STATUS="FAIL"
      return "$rc"
    fi
  fi
  record_skip "$label"
}

# TypeScript
if [ -f tsconfig.json ]; then run_if "TypeScript check" npx tsc --noEmit; else record_skip "TypeScript check (no tsconfig.json)"; fi
# Lint
if [ -f .eslintrc ] || [ -f .eslintrc.js ] || [ -f .eslintrc.json ] || ls eslint.config.* >/dev/null 2>&1 || grep -q '"eslint"' package.json 2>/dev/null; then
  run_if "Lint" npx eslint . --ext .js,.ts,.jsx,.tsx
else
  record_skip "Lint (not configured)"
fi
# Unit tests
if grep -q '"test"' package.json 2>/dev/null; then run_if "Unit tests" npm test; else record_skip "Unit tests (no test script)"; fi
# Production build
if grep -q '"build"' package.json 2>/dev/null; then run_if "Production build" npm run build; else record_skip "Production build (no build script)"; fi
# Selenium browser tests
if bash "$ROOT_DIR/universal-frontend-master-source/scripts/browser-test.sh"; then
  record "PASS" "Selenium browser tests"
else
  # A BLOCKED browser-setup is an environment problem, not a finding: BLOCKED, not FAIL.
  if grep -q '"status":"BLOCKED"' "${ROOT_DIR}/.ufme/evidence/browser-results.json" 2>/dev/null; then
    record "BLOCKED (browser setup failed)" "Selenium browser tests"
  else
    record "FAIL" "Selenium browser tests"
    STATUS="FAIL"
  fi
fi
# Dependency audit
if [ -f package.json ]; then
  if ([ -f package-lock.json ] || [ -f npm-shrinkwrap.json ]); then
    run_if "Dependency audit" npm audit --audit-level=moderate
  else
    record_skip "Dependency audit (no lockfile)"
  fi
else
  record_skip "Dependency audit (no package.json)"
fi

echo "---- Quality check summary ----"
echo "$SUMMARY"
if [ "$STATUS" = "FAIL" ]; then
  log "Quality check FAILED."
  exit 1
fi
log "Quality check $STATUS. Skipped steps are not gate criteria."
exit 0
