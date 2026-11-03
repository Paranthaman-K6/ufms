#!/usr/bin/env bash
# audit-perf.sh — run Lighthouse against <url> and summarize the result.
#
#   npx lighthouse <url> --output json --quiet --chrome-flags="--headless=new"
#
# Extracts the performance, accessibility and best-practices category scores
# (0-100) and the top 5 opportunities (title + numeric savings in ms),
# writes .ufme/evidence/perf-results.json and prints a compact table.
#
# Graceful: when Lighthouse or the browser is unavailable the script records
# { "status": "SKIPPED", "reason": ... } and exits 5. Scores are NEVER
# fabricated. JSON parsing uses a node one-liner (no jq dependency).
#
# Usage: bash audit-perf.sh <url>
# Exit codes: 0 = ran and recorded results, 2 = bad invocation,
#             5 = skipped (dependency or browser missing / lighthouse failed)
#
# Safety: project-local npm only; never sudo/pacman/systemctl; the Chromium
# sandbox is preserved (no --no-sandbox in chrome-flags).
set -u

log() { echo "[audit-perf] $*"; }
err() { echo "[audit-perf] $*" >&2; }

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EVIDENCE_DIR="$ROOT_DIR/.ufme/evidence"
RESULTS_FILE="$EVIDENCE_DIR/perf-results.json"
mkdir -p "$EVIDENCE_DIR"

TIMESTAMP="$(date -Iseconds)"

if [ $# -lt 1 ] || [ -z "${1:-}" ]; then
  err "Usage: bash audit-perf.sh <url>"
  exit 2
fi
URL="$1"

skip() {
  # Write a SKIPPED record and exit 5 — never fabricate scores.
  local reason="$1"
  node -e '
    const fs = require("fs");
    const [file, url, timestamp, reason] = process.argv.slice(1);
    fs.writeFileSync(file, JSON.stringify({url, timestamp, status: "SKIPPED", reason}, null, 2) + "\n");
  ' "$RESULTS_FILE" "$URL" "$TIMESTAMP" "$reason"
  err "SKIPPED: $reason"
  exit 5
}

# --- Dependency checks -----------------------------------------------------
if [ -f "$ROOT_DIR/node_modules/lighthouse/package.json" ]; then
  LH_BIN="npx"
  log "lighthouse: installed project-local"
else
  skip "lighthouse not installed — run: npm i -D lighthouse"
fi

CHROME_BIN=""
for bin in chromium chromium-browser google-chrome-stable google-chrome chrome; do
  if command -v "$bin" >/dev/null 2>&1; then
    CHROME_BIN="$(command -v "$bin")"
    break
  fi
done
[ -n "$CHROME_BIN" ] || skip "no Chromium/Chrome binary found on PATH (install a browser, e.g. your distro chromium package)"

log "Using Chromium/Chrome: $CHROME_BIN"
log "Running lighthouse against $URL ..."

LH_JSON="$(mktemp "$ROOT_DIR/.ufme-lighthouse.XXXXXX.json")"
trap 'rm -f "$LH_JSON"' EXIT

if ! CHROME_PATH="$CHROME_BIN" npx --no-install lighthouse "$URL" \
    --output json --quiet \
    --chrome-flags="--headless=new" \
    >"$LH_JSON" 2>"$ROOT_DIR/.ufme-lighthouse.log"; then
  reason="lighthouse run failed (see .ufme-lighthouse.log)"
  [ -s "$ROOT_DIR/.ufme-lighthouse.log" ] || reason="lighthouse run failed with no output"
  skip "$reason"
fi

# --- Parse and summarize via a node one-liner (no jq) -----------------------
node -e '
const fs = require("fs");
const [, resultsFile, url, timestamp, lhFile] = process.argv;
let report;
try {
  report = JSON.parse(fs.readFileSync(lhFile, "utf-8"));
} catch (e) {
  fs.writeFileSync(resultsFile, JSON.stringify({url, timestamp, status: "SKIPPED", reason: "lighthouse output was not valid JSON"}, null, 2) + "\n");
  process.stderr.write("[audit-perf] lighthouse output was not valid JSON\n");
  process.exit(5);
}
if (!report || !report.categories) {
  fs.writeFileSync(resultsFile, JSON.stringify({url, timestamp, status: "SKIPPED", reason: "lighthouse report missing categories"}, null, 2) + "\n");
  process.stderr.write("[audit-perf] lighthouse report missing categories\n");
  process.exit(5);
}
const score = (key) => {
  const cat = report.categories[key];
  const s = cat && cat.score;
  return typeof s === "number" ? Math.round(s * 100) : null;
};
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
const result = {
  url,
  timestamp,
  status: "RAN",
  scores: {
    performance: score("performance"),
    accessibility: score("accessibility"),
    bestPractices: score("best-practices"),
  },
  opportunities,
};
fs.writeFileSync(resultsFile, JSON.stringify(result, null, 2) + "\n");
process.stdout.write(`performance | ${result.scores.performance}\n`);
process.stdout.write(`accessibility | ${result.scores.accessibility}\n`);
process.stdout.write(`best-practices | ${result.scores.bestPractices}\n`);
process.stdout.write("top opportunities:\n");
for (const o of opportunities) {
  process.stdout.write(`  ${o.savingsMs}ms | ${o.title}\n`);
}
' "$RESULTS_FILE" "$URL" "$TIMESTAMP" "$LH_JSON" || exit 5

log "Results: $RESULTS_FILE"
