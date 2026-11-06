#!/usr/bin/env bash
# screenshot.sh
# Capture Selenium screenshots via the runtime abstraction in
# skills/universal-frontend-master/browser/. Default screenshot budget is
# viewport-only at mobile 390x844 and desktop 1440x900 (native PNG plus a
# manifest of actual dimensions). Dark theme is captured only when the page
# defines prefers-color-scheme rules or a theme toggle.
#
# Safety: project-local only.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
URL="${1:-http://localhost:5173}"
SCREENSHOT_DIR="${2:-$ROOT_DIR/.ufme/evidence/screenshots}"

mkdir -p "$SCREENSHOT_DIR"

log() { echo "[screenshot] $*"; }

log "Capturing screenshots for $URL into $SCREENSHOT_DIR"
node "$ROOT_DIR/skills/universal-frontend-master/browser/run.js" "$URL" "$SCREENSHOT_DIR" "$ROOT_DIR/.ufme/evidence/browser-results.json" --screenshots-only
RC=$?

if [ $RC -eq 0 ]; then
  log "Screenshots captured."
else
  log "Screenshot capture failed (RC=$RC)."
fi
exit $RC
