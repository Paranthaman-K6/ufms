#!/usr/bin/env bash
# browser-test.sh
# Run native Selenium WebDriver browser tests against a base URL.
# Default URL: http://localhost:5173. Prefers Chromium, falls back to Firefox.
# Headless by default. Captures screenshots, console errors, failed requests,
# broken links, interaction failures. Saves browser-results.json.
#
# Safety: project-local only; never sudo/pacman/systemctl.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
UFME_DIR="$ROOT_DIR/.ufme"
EVIDENCE_DIR="${UFME_EVIDENCE_DIR:-$UFME_DIR/evidence}"
SCREENSHOT_DIR="$EVIDENCE_DIR/screenshots"
RESULTS_FILE="$EVIDENCE_DIR/browser-results.json"
CHECK_SCRIPT="$ROOT_DIR/skills/universal-frontend-master/scripts/check-native-browser.sh"

URL="${1:-http://localhost:5173}"
mkdir -p "$SCREENSHOT_DIR"

log() { echo "[browser-test] $*"; }

# Step 1: check native browser setup
log "Running check-native-browser.sh..."
bash "$CHECK_SCRIPT"
CHECK_RC=$?
if [ $CHECK_RC -ne 0 ]; then
  log "Browser setup BLOCKED. Browser-dependent tests cannot run."
  cat > "$RESULTS_FILE" <<JSON
{"url":"$URL","status":"BLOCKED","reason":"browser setup failed","timestamp":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
JSON
  exit 1
fi

# Step 2: detect whether the target URL responds. A dead server is a real
# failure of the system under test, not an unsupported environment.
if ! command -v curl >/dev/null 2>&1; then
  log "curl not available; skipping URL responsiveness check."
else
  if curl -fsS -o /dev/null --max-time 10 "$URL" >/dev/null 2>&1; then
    log "URL responds: $URL"
  else
    log "FAIL: URL did not respond: $URL (is the dev server running?)"
    cat > "$RESULTS_FILE" <<JSON
{"url":"$URL","status":"FAIL","reason":"URL did not respond","timestamp":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
JSON
    exit 1
  fi
fi

# Step 3: run Selenium test suite via node abstraction (budgeted screenshots)
log "Running Selenium browser tests against $URL..."
node "$ROOT_DIR/skills/universal-frontend-master/browser/run.js" "$URL" "$SCREENSHOT_DIR" "$RESULTS_FILE"
RC=$?

if [ $RC -eq 0 ]; then
  log "Browser tests complete. Results: $RESULTS_FILE"
else
  log "Browser tests completed with errors (RC=$RC). Results: $RESULTS_FILE"
fi

exit $RC
