#!/usr/bin/env bash
# screenshot.sh
# Capture Selenium screenshots: full-page + section-level at
# mobile 390x844, tablet 768x1024, laptop 1280x800, desktop 1440x900,
# dark and light themes where applicable.
#
# Safety: project-local only.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
URL="${1:-http://localhost:5173}"
SCREENSHOT_DIR="${2:-$ROOT_DIR/.ufme/evidence/screenshots}"

mkdir -p "$SCREENSHOT_DIR"

log() { echo "[screenshot] $*"; }

log "Capturing screenshots for $URL into $SCREENSHOT_DIR"
node "$ROOT_DIR/tests/browser/run.js" "$URL" "$SCREENSHOT_DIR" "$ROOT_DIR/.ufme/evidence/browser-results.json" --screenshots-only
RC=$?

if [ $RC -eq 0 ]; then
  log "Screenshots captured."
else
  log "Screenshot capture failed (RC=$RC)."
fi
exit $RC
