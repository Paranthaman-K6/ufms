#!/usr/bin/env bash
# audit-perf.sh — run Lighthouse against <url> and summarize the result.
#
#   npx lighthouse <url> --output json --quiet --chrome-flags="--headless=new"
#
# Extracts the performance, accessibility and best-practices category scores
# (0-100) and the top 5 opportunities (title + numeric savings in ms),
# writes .ufme/evidence/perf-results.json and prints a compact table.
#
# Failure classes are explicit and never collapse into SKIPPED:
#   dependency unavailable (lighthouse package)   -> status SKIPPED, exit 5
#   unsupported environment (no browser binary)   -> status BLOCKED, exit 6
#   browser launched but failed / crashed         -> status FAIL,    exit 4
#   audit failed (bad report, missing scores)     -> status FAIL,    exit 4
#   ran with three valid scores                   -> status RAN,     exit 0
#
# Scores are NEVER fabricated. JSON parsing uses a node one-liner (no jq).
#
# Usage: bash audit-perf.sh <url>
# Exit codes: 0 = ran, 2 = bad invocation, 4 = audit/browser FAIL,
#             5 = SKIPPED dependency, 6 = BLOCKED environment.
#
# Safety: project-local npm only; never sudo/pacman/systemctl; the Chromium
# sandbox is preserved by default (no --no-sandbox in chrome-flags). Set
# UFME_CHROME_FLAGS to add runner-specific flags (CI needs --no-sandbox).
set -u

log() { echo "[audit-perf] $*"; }
err() { echo "[audit-perf] $*" >&2; }

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EVIDENCE_DIR="${UFME_EVIDENCE_DIR:-$ROOT_DIR/.ufme/evidence}"
RESULTS_FILE="$EVIDENCE_DIR/perf-results.json"
LOG_FILE="$EVIDENCE_DIR/lighthouse.log"
mkdir -p "$EVIDENCE_DIR"

TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
CHROME_FLAGS="${UFME_CHROME_FLAGS:---headless=new}"
# CI/container environments need --no-sandbox for Chromium to launch.
# Add it automatically if not already present and we're not in a desktop session.
if echo "$CHROME_FLAGS" | grep -q -- '--no-sandbox'; then
  : # already present
elif [ -n "${CI:-}" ] || [ ! -d "${XDG_RUNTIME_DIR:-}" ]; then
  CHROME_FLAGS="$CHROME_FLAGS --no-sandbox"
fi

if [ $# -lt 1 ] || [ -z "${1:-}" ]; then
  err "Usage: bash audit-perf.sh <url>"
  exit 2
fi
URL="$1"

write_failure() {
  local status="$1" kind="$2" reason="$3"
  node -e '
    const fs = require("fs");
    const [file, url, timestamp, status, kind, reason] = process.argv.slice(1);
    fs.writeFileSync(file, JSON.stringify({
      url, timestamp, status, failureKind: kind, reason,
    }, null, 2) + "\n");
  ' "$RESULTS_FILE" "$URL" "$TIMESTAMP" "$status" "$kind" "$reason"
  err "$status ($kind): $reason"
}

skip() { write_failure "SKIPPED" "dependency" "$1"; exit 5; }
block() { write_failure "BLOCKED" "environment" "$1"; exit 6; }
fail() { write_failure "FAIL" "$1" "$2"; exit 4; }

# --- Dependency and environment checks -------------------------------------
if [ ! -f "$ROOT_DIR/node_modules/lighthouse/package.json" ]; then
  skip "lighthouse not installed — run: npm i -D lighthouse"
fi
log "lighthouse: installed project-local"

CHROME_BIN=""
for bin in chromium chromium-browser google-chrome-stable google-chrome chrome; do
  if command -v "$bin" >/dev/null 2>&1; then
    CHROME_BIN="$(command -v "$bin")"
    break
  fi
done
[ -n "$CHROME_BIN" ] || block "no Chromium/Chrome binary found on PATH (install a browser: your distro chromium package)"

log "Using Chromium/Chrome: $CHROME_BIN"
log "Running lighthouse against $URL ..."

LH_JSON="$(mktemp "${TMPDIR:-/tmp}/ufme-lighthouse.XXXXXX.json")"
trap 'rm -f "$LH_JSON"' EXIT

if ! CHROME_PATH="$CHROME_BIN" npx --no-install lighthouse "$URL" \
    --output json --quiet \
    --chrome-flags="$CHROME_FLAGS" \
    >"$LH_JSON" 2>"$LOG_FILE"; then
  if [ -s "$LOG_FILE" ]; then
    err "lighthouse output (last 20 lines):"
    tail -20 "$LOG_FILE" >&2
    if grep -Eqi 'could not find chrome|failed to launch|chrome failed to start|unable to connect to the browser|no usable sandbox|error while loading shared libraries|devtools' "$LOG_FILE"; then
      fail "browser" "browser could not start for Lighthouse (see $LOG_FILE)"
    fi
    fail "audit" "lighthouse run failed (see $LOG_FILE)"
  fi
  fail "audit" "lighthouse run failed with no output"
fi

# --- Parse and validate via a node one-liner (no jq) -----------------------
node -e '
const fs = require("fs");
const [, resultsFile, url, timestamp, lhFile, logFile] = process.argv;
function failure(reason) {
  fs.writeFileSync(resultsFile, JSON.stringify({
    url, timestamp, status: "FAIL", failureKind: "audit", reason,
  }, null, 2) + "\n");
  process.stderr.write(`[audit-perf] ${reason}\n`);
  process.exit(4);
}
let report;
try {
  report = JSON.parse(fs.readFileSync(lhFile, "utf-8"));
} catch (e) {
  failure("lighthouse output was not valid JSON");
}
if (!report || typeof report !== "object" || !report.categories) {
  failure("lighthouse report missing categories");
}
const score = (key) => {
  const cat = report.categories[key];
  const s = cat && cat.score;
  return typeof s === "number" && Number.isFinite(s) ? Math.round(s * 100) : null;
};
const scores = {
  performance: score("performance"),
  accessibility: score("accessibility"),
  bestPractices: score("best-practices"),
};
for (const [key, value] of Object.entries(scores)) {
  if (value === null || value < 0 || value > 100) {
    failure(`lighthouse report has no valid ${key} score`);
  }
}
const opportunities = Object.entries(report.audits || {})
  .map(([id, a]) => ({audit: id, title: a.title, details: a.details}))
  .filter((e) => e.details && e.details.type === "opportunity" && typeof e.details.overallSavingsMs === "number")
  .map((e) => {
    const entry = {audit: e.audit, title: e.title, savingsMs: Math.round(e.details.overallSavingsMs)};
    // Numeric render-blocking savings are surfaced where the audit reports them
    // (e.g. render-blocking-resources) instead of trusting prose text.
    if (e.audit === "render-blocking-resources") entry.renderBlockingSavingsMs = Math.round(e.details.overallSavingsMs);
    if (typeof e.details.overallSavingsBytes === "number") entry.savingsBytes = e.details.overallSavingsBytes;
    return entry;
  })
  .filter((e) => e.savingsMs > 0)
  .sort((a, b) => b.savingsMs - a.savingsMs)
  .slice(0, 5);
const result = { url, timestamp, status: "RAN", scores, opportunities };
fs.writeFileSync(resultsFile, JSON.stringify(result, null, 2) + "\n");
process.stdout.write(`performance | ${scores.performance}\n`);
process.stdout.write(`accessibility | ${scores.accessibility}\n`);
process.stdout.write(`best-practices | ${scores.bestPractices}\n`);
process.stdout.write("top opportunities:\n");
for (const o of opportunities) {
  process.stdout.write(`  ${o.savingsMs}ms | ${o.title}\n`);
}
' "$RESULTS_FILE" "$URL" "$TIMESTAMP" "$LH_JSON" "$LOG_FILE"
rc=$?
[ $rc -eq 0 ] || exit $rc

log "Results: $RESULTS_FILE"
