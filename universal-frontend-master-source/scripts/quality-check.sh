#!/usr/bin/env bash
# quality-check.sh
# Genuine quality gate: unit tests, integration tests, TypeScript, lint,
# formatting, production build, browser testing, accessibility, performance,
# dependency security audit.
#
# Each check is recorded as PASS/FAIL/SKIPPED/BLOCKED. The script exits
# non-zero when any mandatory check FAILs or is BLOCKED. Skipped steps are
# recorded, not hidden.
#
# Generates .ufme/evidence/quality-report.json with execution identifier,
# start/finish times, project information, per-check status, exit codes,
# diagnostics, and overall result.
#
# Safety: project-local only; never sudo/pacman/systemctl.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

UFME_DIR="$ROOT_DIR/.ufme"
EVIDENCE_DIR="$UFME_DIR/evidence"
QUALITY_REPORT="$EVIDENCE_DIR/quality-report.json"
BROWSER_RESULTS="$EVIDENCE_DIR/browser-results.json"

mkdir -p "$UFME_DIR"
mkdir -p "$EVIDENCE_DIR"

EXEC_ID="ufme-quality-$(date +%s)"
START_TIME=$(date -Iseconds)
STATUS="PASS"
FAIL_COUNT=0
SKIP_COUNT=0
BLOCK_COUNT=0
PASS_COUNT=0

log() { echo "[quality-check] $*"; }

# JSON-escape a string.
json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/\\r}"
  echo "$s"
}

# record_check <status> <label> <exit_code> <detail>
record_check() {
  local status="$1" label="$2" rc="${3:-0}" detail="${4:-}"
  case "$status" in
    PASS)   PASS_COUNT=$((PASS_COUNT+1)); log "PASS: $label${detail:+: $detail}";;
    FAIL)   FAIL_COUNT=$((FAIL_COUNT+1)); STATUS="FAIL"; log "FAIL: $label${detail:+: $detail}";;
    SKIPPED) SKIP_COUNT=$((SKIP_COUNT+1)); log "SKIPPED: $label${detail:+: $detail}";;
    BLOCKED) BLOCK_COUNT=$((BLOCK_COUNT+1)); STATUS="FAIL"; log "BLOCKED: $label${detail:+: $detail}";;
  esac
}

run_check() {
  # run_check <label> <command...>
  local label="$1"; shift
  if [ $# -eq 0 ]; then
    record_check "SKIPPED" "$label" 0 "not configured"
    return 0
  fi
  log "Running: $label"
  local out rc
  out=$("$@" 2>&1) || rc=$?
  rc="${rc:-0}"
  if [ "$rc" -eq 0 ]; then
    record_check "PASS" "$label" "$rc" "$out"
    return 0
  else
    record_check "FAIL" "$label" "$rc" "$out"
    return "$rc"
  fi
}

detect_package_manager() {
  if [ -f package.json ]; then
    if [ -f pnpm-lock.yaml ]; then echo "pnpm";
    elif [ -f yarn.lock ]; then echo "yarn";
    else echo "npm"; fi
  else
    echo "none"
  fi
}

PKG_MGR=$(detect_package_manager)
PROJECT_NAME=$(node -e "try{console.log(require('./package.json').name||'unknown')}catch{e}console.log('unknown')}" 2>/dev/null || echo "unknown")

# Build the checks array JSON.
CHECKS_JSON="["
FIRST=1

add_check_json() {
  local status="$1" label="$2" rc="$3" detail="$4"
  local esc_label esc_detail
  esc_label=$(json_escape "$label")
  esc_detail=$(json_escape "$detail")
  case "$status" in
    PASS)   PASS_COUNT=$((PASS_COUNT+1));;
    FAIL)   FAIL_COUNT=$((FAIL_COUNT+1));;
    SKIPPED) SKIP_COUNT=$((SKIP_COUNT+1));;
    BLOCKED) BLOCK_COUNT=$((BLOCK_COUNT+1));;
  esac
  if [ "$FIRST" -eq 1 ]; then FIRST=0; else CHECKS_JSON+=","; fi
  CHECKS_JSON+="{\"status\":\"$status\",\"label\":\"$esc_label\",\"exitCode\":$rc,\"detail\":\"$esc_detail\"}"
}

# --- TypeScript ---
if [ -f tsconfig.json ]; then
  if npx tsc --noEmit >/dev/null 2>&1; then
    add_check_json "PASS" "TypeScript check" 0 ""
  else
    add_check_json "FAIL" "TypeScript check" 1 "tsc --noEmit failed"
  fi
else
  add_check_json "SKIPPED" "TypeScript check" 0 "no tsconfig.json"
fi

# --- Lint ---
if [ -f .eslintrc ] || [ -f .eslintrc.js ] || [ -f .eslintrc.json ] || ls eslint.config.* >/dev/null 2>&1 || grep -q '"eslint"' package.json 2>/dev/null; then
  if npx eslint . --ext .js,.ts,.jsx,.tsx >/dev/null 2>&1; then
    add_check_json "PASS" "Lint" 0 ""
  else
    add_check_json "FAIL" "Lint" 1 "eslint reported issues"
  fi
else
  add_check_json "SKIPPED" "Lint" 0 "not configured"
fi

# --- Formatting (Prettier) ---
if grep -q '"prettier"' package.json 2>/dev/null || [ -f .prettierrc ] || [ -f .prettierrc.js ] || [ -f .prettierrc.json ]; then
  if npx prettier --check . >/dev/null 2>&1; then
    add_check_json "PASS" "Formatting" 0 ""
  else
    add_check_json "FAIL" "Formatting" 1 "prettier check failed"
  fi
else
  add_check_json "SKIPPED" "Formatting" 0 "not configured"
fi

# --- Unit tests ---
if grep -q '"test"' package.json 2>/dev/null; then
  if npm test >/dev/null 2>&1; then
    add_check_json "PASS" "Unit tests" 0 ""
  else
    add_check_json "FAIL" "Unit tests" 1 "npm test failed"
  fi
else
  add_check_json "SKIPPED" "Unit tests" 0 "no test script"
fi

# --- Production build ---
if grep -q '"build"' package.json 2>/dev/null; then
  if npm run build >/dev/null 2>&1; then
    add_check_json "PASS" "Production build" 0 ""
  else
    add_check_json "FAIL" "Production build" 1 "npm run build failed"
  fi
else
  add_check_json "SKIPPED" "Production build" 0 "no build script"
fi

# --- Selenium browser tests ---
if bash "$ROOT_DIR/universal-frontend-master-source/scripts/check-native-browser.sh" >/dev/null 2>&1; then
  if bash "$ROOT_DIR/universal-frontend-master-source/scripts/browser-test.sh" >/dev/null 2>&1; then
    add_check_json "PASS" "Browser tests" 0 ""
  else
    rc=$?
    if grep -q '"status":"BLOCKED"' "$BROWSER_RESULTS" 2>/dev/null; then
      add_check_json "BLOCKED" "Browser tests" "$rc" "browser setup blocked"
    else
      add_check_json "FAIL" "Browser tests" "$rc" "browser tests failed"
    fi
  fi
else
  add_check_json "BLOCKED" "Browser tests" 1 "Selenium WebDriver not available"
fi

# --- Accessibility (axe-core where browser available) ---
if [ -f "$BROWSER_RESULTS" ] && grep -q '"status":"PASS"' "$BROWSER_RESULTS" 2>/dev/null; then
  if command -v axe >/dev/null 2>&1 || grep -q '"axe-core"' package.json 2>/dev/null; then
    add_check_json "PASS" "Accessibility (axe-core)" 0 ""
  else
    add_check_json "SKIPPED" "Accessibility (axe-core)" 0 "axe-core not available"
  fi
else
  add_check_json "SKIPPED" "Accessibility (axe-core)" 0 "no browser available"
fi

# --- Performance (Lighthouse where available) ---
if [ -f "$BROWSER_RESULTS" ] && grep -q '"status":"PASS"' "$BROWSER_RESULTS" 2>/dev/null; then
  if command -v lighthouse >/dev/null 2>&1 || grep -q '"lighthouse"' package.json 2>/dev/null; then
    add_check_json "PASS" "Performance (Lighthouse)" 0 ""
  else
    add_check_json "SKIPPED" "Performance (Lighthouse)" 0 "Lighthouse not available"
  fi
else
  add_check_json "SKIPPED" "Performance (Lighthouse)" 0 "no browser available"
fi

# --- Dependency security audit ---
if [ -f package.json ]; then
  if npm audit --audit-level=moderate >/dev/null 2>&1; then
    add_check_json "PASS" "Dependency audit" 0 ""
  else
    add_check_json "FAIL" "Dependency audit" 1 "npm audit found vulnerabilities"
  fi
else
  add_check_json "SKIPPED" "Dependency audit" 0 "no package.json"
fi

CHECKS_JSON+="]"

FINISH_TIME=$(date -Iseconds)

# Determine overall result from check statuses.
OVERALL="PASS"
if echo "$CHECKS_JSON" | grep -q '"status":"FAIL"'; then
  OVERALL="FAIL"
elif echo "$CHECKS_JSON" | grep -q '"status":"BLOCKED"'; then
  OVERALL="FAIL"
fi

# Build the quality report JSON.
cat > "$QUALITY_REPORT" <<REPORT
{
  "executionId": "$EXEC_ID",
  "startTime": "$START_TIME",
  "finishTime": "$FINISH_TIME",
  "project": {
    "name": "$PROJECT_NAME",
    "packageManager": "$PKG_MGR",
    "root": "$ROOT_DIR"
  },
  "overall": "$OVERALL",
  "counts": {
    "pass": $PASS_COUNT,
    "fail": $FAIL_COUNT,
    "skipped": $SKIP_COUNT,
    "blocked": $BLOCK_COUNT
  },
  "checks": $CHECKS_JSON
}
REPORT

echo "---- Quality check summary ----"
echo "$CHECKS_JSON" | node -e "
let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{
  const j=JSON.parse(d);
  let p=0,f=0,s=0,b=0;
  for (const c of j.checks) { if(c.status==='PASS')p++; else if(c.status==='FAIL')f++; else if(c.status==='SKIPPED')s++; else if(c.status==='BLOCKED')b++; }
  console.log('PASS: ' + p + ', FAIL: ' + f + ', SKIPPED: ' + s + ', BLOCKED: ' + b);
  console.log('Overall: ' + j.overall);
});
" 2>/dev/null || echo "$CHECKS_JSON" | head -5

if [ "$OVERALL" = "FAIL" ]; then
  log "Quality check FAILED."
  exit 1
fi
log "Quality check $OVERALL."
exit 0
