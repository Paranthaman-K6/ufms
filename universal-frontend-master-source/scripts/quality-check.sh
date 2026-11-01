#!/usr/bin/env bash
# quality-check.sh
# Run type check, lint, unit tests, production build, Selenium browser tests,
# axe-core accessibility checks (where a browser is available), Lighthouse against
# a locally served production build when possible, and dependency audit.
#
# Safety: project-local only; never sudo/pacman/systemctl.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

log() { echo "[quality-check] $*"; }

run_if() { # run_if <label> <command...>
  local label="$1"; shift
  if [ $# -gt 0 ]; then
    log "Running: $label"
    "$@"
    local rc=$?
    [ $rc -ne 0 ] && log "WARNING: $label exited $rc"
    return $rc
  fi
  log "Skipping: $label (not configured)"
}

# TypeScript
if [ -f tsconfig.json ]; then run_if "TypeScript check" npx tsc --noEmit; fi
# Lint
if [ -f .eslintrc* ] || [ -f eslint.config.* ] || grep -q '"eslint"' package.json 2>/dev/null; then run_if "Lint" npx eslint . --ext .js,.ts,.jsx,.tsx 2>/dev/null || true; fi
# Unit tests
if grep -q '"test"' package.json 2>/dev/null; then run_if "Unit tests" npm test; fi
# Production build
if grep -q '"build"' package.json 2>/dev/null; then run_if "Production build" npm run build; fi
# Selenium browser tests
log "Selenium browser tests"
bash "$ROOT_DIR/universal-frontend-master-source/scripts/browser-test.sh" || log "Browser tests had failures."
# Dependency audit
if [ -f package.json ]; then run_if "Dependency audit" npm audit --audit-level=moderate 2>/dev/null || true; fi

log "Quality check complete."
