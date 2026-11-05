#!/usr/bin/env bash
# check-native-browser.sh
# Detect native browsers (Chromium/Chrome, Firefox) and verify that the
# project's own Node Selenium stack can launch one headlessly. Writes
# browser-setup.json and, on failure, browser-setup-error.txt, then prints a
# safe user-setup instruction.
#
# Honors UFME_EVIDENCE_DIR and UFME_CHROME_FLAGS (e.g. CI adds --no-sandbox).
# Exit 0 = a browser launched; 1 = BLOCKED (missing dependency or launch failure).
#
# Safety: never uses sudo/pacman/systemctl/doas/pkexec/su. Project-local only.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
UFME_DIR="$ROOT_DIR/.ufme"
EVIDENCE_DIR="${UFME_EVIDENCE_DIR:-$UFME_DIR/evidence}"
BROWSER_ERROR="$EVIDENCE_DIR/browser-setup-error.txt"
SETUP_JSON="$EVIDENCE_DIR/browser-setup.json"

mkdir -p "$EVIDENCE_DIR"

log() { echo "[check-native-browser] $*"; }

TIMEOUT_SEC="${BROWSER_TIMEOUT_SEC:-30}"
CHROMIUM_BIN=""
FIREFOX_BIN=""
LAUNCHED=""
SELENIUM_AVAILABLE="no"

detect_browsers() {
  for bin in chromium chromium-browser google-chrome-stable google-chrome chrome; do
    if command -v "$bin" >/dev/null 2>&1; then
      CHROMIUM_BIN="$(command -v "$bin")"
      break
    fi
  done
  for bin in firefox firefox-developer-edition firefox-bin; do
    if command -v "$bin" >/dev/null 2>&1; then
      FIREFOX_BIN="$(command -v "$bin")"
      break
    fi
  done
}

detect_selenium() {
  if [ -f "$ROOT_DIR/node_modules/selenium-webdriver/index.js" ]; then
    SELENIUM_AVAILABLE="yes"
    log "selenium-webdriver: installed project-local"
  else
    log "selenium-webdriver: NOT installed (project-local install required)"
  fi
}

# Launch one engine through the same selenium-webdriver package run.js uses.
try_selenium_launch() {
  local engine="$1"
  local bin="$2"
  local out
  out="$(ENGINE="$engine" BIN="$bin" UFME_CHROME_FLAGS="${UFME_CHROME_FLAGS:-}" \
    timeout --kill-after=2 "${TIMEOUT_SEC}s" node - <<'EOF' 2>&1
const { Builder } = require('selenium-webdriver');
const engine = process.env.ENGINE;
const bin = process.env.BIN;

(async () => {
  let options;
  if (engine === 'firefox') {
    const firefox = require('selenium-webdriver/firefox');
    options = new firefox.Options().addArguments('-headless');
    if (bin) options.setBinary(bin);
  } else {
    const chrome = require('selenium-webdriver/chrome');
    options = new chrome.Options();
    const extra = (process.env.UFME_CHROME_FLAGS || '').split(/\s+/).filter(Boolean);
    options.addArguments('--headless=new', '--disable-dev-shm-usage', '--disable-gpu', ...extra);
  }
  const builder = new Builder().forBrowser(engine === 'firefox' ? 'firefox' : 'chrome');
  const driver = await (engine === 'firefox'
    ? builder.setFirefoxOptions(options)
    : builder.setChromeOptions(options)
  ).build();
  try {
    await driver.get('data:text/html,<title>ufme</title><body>ok</body>');
    await driver.getTitle();
    const caps = await driver.getCapabilities();
    process.stdout.write(`SELENIUM_OK:${caps.get('browserName') || engine}:${caps.get('browserVersion') || ''}`);
  } finally {
    await driver.quit();
  }
})().catch((err) => {
  process.stderr.write(`SELENIUM_FAIL:${String(err && err.message ? err.message : err)}`);
  process.exit(1);
});
EOF
)"
  local rc=$?
  if [ $rc -eq 0 ]; then
    echo "$out"
    return 0
  fi
  echo "$out" | tail -5 >&2
  return $rc
}

mark_blocked() {
  echo "BROWSER_TESTING=BLOCKED" >> "$UFME_DIR/ENVIRONMENT.md" 2>/dev/null || true
  log "Browser testing marked BLOCKED."
}

prompt_user() {
  local missing="$1"
  local cmd="$2"
  cat <<EOF

================================================================
SELENIUM BROWSER SETUP BLOCKED
----------------------------------------------------------------
Missing: $missing

This agent cannot run sudo/pacman/systemctl. Install the missing
dependency yourself, then reply "retry browser setup" so the
orchestrator can rerun scripts/check-native-browser.sh.

User-setup command (run yourself):
  $cmd
================================================================
EOF
}

write_setup_evidence() {
  local status="$1"
  local reason="$2"
  cat > "$SETUP_JSON" <<JSON
{
  "status": "$status",
  "reason": "$reason",
  "chromium": "${CHROMIUM_BIN:-}",
  "firefox": "${FIREFOX_BIN:-}",
  "selenium": "$SELENIUM_AVAILABLE",
  "launched": "${LAUNCHED:-}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
JSON
}

main() {
  detect_browsers
  detect_selenium

  log "Chromium/Chrome: ${CHROMIUM_BIN:-not installed}"
  log "Firefox: ${FIREFOX_BIN:-not installed}"

  if [ "$SELENIUM_AVAILABLE" != "yes" ]; then
    write_setup_evidence "BLOCKED" "selenium-webdriver is not installed"
    prompt_user "selenium-webdriver npm package" "npm i -D selenium-webdriver"
    mark_blocked
    exit 1
  fi

  if [ -n "$CHROMIUM_BIN" ]; then
    log "Launching headless Chromium via Node Selenium ($CHROMIUM_BIN)..."
    if try_selenium_launch chromium "$CHROMIUM_BIN"; then
      LAUNCHED="chromium"
      log "Chromium Selenium launch: OK"
    else
      log "Chromium Selenium launch: FAILED"
    fi
  fi

  if [ -z "$LAUNCHED" ] && [ -n "$FIREFOX_BIN" ]; then
    log "Launching headless Firefox via Node Selenium ($FIREFOX_BIN)..."
    if try_selenium_launch firefox "$FIREFOX_BIN"; then
      LAUNCHED="firefox"
      log "Firefox Selenium launch: OK"
    else
      log "Firefox Selenium launch: FAILED"
    fi
  fi

  if [ -n "$LAUNCHED" ]; then
    write_setup_evidence "READY" "launched $LAUNCHED via selenium-webdriver"
    log "Native Selenium WebDriver browser setup: READY ($LAUNCHED)"
    exit 0
  fi

  {
    echo "=== check-native-browser failure ==="
    echo "Chromium: ${CHROMIUM_BIN:-not installed}"
    echo "Firefox: ${FIREFOX_BIN:-not installed}"
    echo "selenium-webdriver: $SELENIUM_AVAILABLE"
    echo "UFME_CHROME_FLAGS: ${UFME_CHROME_FLAGS:-<unset>}"
  } > "$BROWSER_ERROR"
  write_setup_evidence "BLOCKED" "no installed browser could launch via selenium-webdriver"

  if [ -z "$CHROMIUM_BIN" ] && [ -z "$FIREFOX_BIN" ]; then
    log "No Chromium/Chrome or Firefox binary found."
    prompt_user "system browser (Chromium or Firefox)" \
      "install the chromium or firefox package via your system package manager"
  else
    log "A browser is installed but could not launch (shared library, driver, or sandbox)."
    prompt_user "working headless browser launch" \
      "repair/reinstall the chromium or firefox package, or set UFME_CHROME_FLAGS (see $BROWSER_ERROR)"
  fi
  mark_blocked
  exit 1
}

main "$@"
