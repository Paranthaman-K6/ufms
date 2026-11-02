#!/usr/bin/env bash
# check-native-browser.sh
# Detect native browsers (Chromium, Google Chrome, Firefox) and Selenium WebDriver
# availability. Attempt a minimal headless Selenium launch (Chromium first, then Firefox).
# On total failure, record the error and prompt the user with a safe setup command.
#
# Safety: never uses sudo/pacman/systemctl/doas/pkexec/su. Project-local only.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
UFME_DIR="$ROOT_DIR/.ufme"
EVIDENCE_DIR="$UFME_DIR/evidence"
BROWSER_ERROR="$EVIDENCE_DIR/browser-setup-error.txt"

mkdir -p "$EVIDENCE_DIR"

log() { echo "[check-native-browser] $*"; }

detect_browsers() {
  CHROMIUM_BIN=""
  CHROME_BIN=""
  FIREFOX_BIN=""

  if command -v chromium >/dev/null 2>&1; then CHROMIUM_BIN="$(command -v chromium)"; fi
  if command -v google-chrome-stable >/dev/null 2>&1; then CHROME_BIN="$(command -v google-chrome-stable)"; fi
  if command -v google-chrome >/dev/null 2>&1; then CHROME_BIN="${CHROME_BIN:-$(command -v google-chrome)}"; fi
  if command -v firefox >/dev/null 2>&1; then FIREFOX_BIN="$(command -v firefox)"; fi

  log "Chromium: ${CHROMIUM_BIN:-NOT FOUND}"
  log "Google Chrome: ${CHROME_BIN:-NOT FOUND}"
  log "Firefox: ${FIREFOX_BIN:-NOT FOUND}"
}

detect_selenium() {
  SELENIUM_AVAILABLE="no"
  if [ -f "$ROOT_DIR/node_modules/selenium-webdriver/index.js" ]; then
    SELENIUM_AVAILABLE="yes"
    log "selenium-webdriver: installed project-local"
  else
    log "selenium-webdriver: NOT installed (run: npm install -D selenium-webdriver)"
  fi
}

# Minimal headless Selenium launch test using a temp JS file.
try_selenium_launch() {
  local browser="$1"
  local bin="$2"
  local tmpfile
  tmpfile="$(mktemp "$ROOT_DIR/.ufme-selenium-check.XXXXXX.js")"
  cat > "$tmpfile" <<EOF
const {Builder, Browser} = require('selenium-webdriver');
(async () => {
  let opts;
  if (process.argv[2] === 'firefox') {
    opts = new (require('selenium-webdriver/firefox').Options)().setBinary(process.env.FIREFOX_BIN || '/usr/bin/firefox').addArguments('-headless');
  } else {
    // Preserve Chromium sandboxing by default; --no-sandbox omitted for security.
    // setBinary() is not available on Chrome Options in selenium-webdriver v4;
    // Chrome locates its binary automatically via CHROME_BIN env var or PATH.
    opts = new (require('selenium-webdriver/chrome').Options)().addArguments('--headless=new', '--disable-dev-shm-usage');
  }
  // Selenium Manager recognizes 'chrome' (not 'chromium') as the browser name.
  let browserName = process.argv[2] === 'chromium' ? 'chrome' : process.argv[2];
  let builder = new Builder().forBrowser(browserName);
  if (process.argv[2] === 'firefox') {
    builder = builder.setFirefoxOptions(opts);
  } else {
    builder = builder.setChromeOptions(opts);
  }
  const driver = await builder.build();
  try {
    await driver.get('data:text/html,<html><body>ok</body></html>');
    const title = await driver.getTitle();
    process.stdout.write('SELENIUM_OK:' + title);
  } finally {
    await driver.quit();
  }
})().catch((err) => { process.stderr.write('SELENIUM_FAIL:' + String(err && err.message ? err.message : err)); process.exit(1); });
EOF

  if [ "$browser" = "firefox" ]; then
    FIREFOX_BIN="$bin" CHROMIUM_BIN="" node "$tmpfile" firefox 2>&1
  else
    CHROMIUM_BIN="$bin" FIREFOX_BIN="" node "$tmpfile" chromium 2>&1
  fi
  local rc=$?
  rm -f "$tmpfile"
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

This agent cannot run sudo/pacman/systemctl. Please install the
missing dependency yourself, then reply "retry browser setup"
so the orchestrator can rerun scripts/check-native-browser.sh.

User-setup command (run yourself):
  $cmd
================================================================
EOF
}

main() {
  detect_browsers
  detect_selenium

  if [ "$SELENIUM_AVAILABLE" != "yes" ]; then
    log "selenium-webdriver not installed; cannot run Selenium launch check."
    prompt_user "selenium-webdriver npm package" "npm install -D selenium-webdriver"
    mark_blocked
    exit 1
  fi

  # Try Chromium first, then Firefox.
  launched="no"
  if [ -n "$CHROMIUM_BIN" ]; then
    log "Attempting headless Selenium launch with Chromium ($CHROMIUM_BIN)..."
    if try_selenium_launch chromium "$CHROMIUM_BIN"; then
      log "Chromium Selenium launch: OK"
      launched="yes"
    else
      log "Chromium Selenium launch: FAILED"
    fi
  fi

  if [ "$launched" != "yes" ] && [ -n "$FIREFOX_BIN" ]; then
    log "Attempting headless Selenium launch with Firefox ($FIREFOX_BIN)..."
    if try_selenium_launch firefox "$FIREFOX_BIN"; then
      log "Firefox Selenium launch: OK"
      launched="yes"
    else
      log "Firefox Selenium launch: FAILED"
    fi
  fi

  if [ "$launched" != "yes" ]; then
    log "No browser could launch via Selenium WebDriver."
    {
      echo "=== check-native-browser failure ==="
      echo "Chromium: ${CHROMIUM_BIN:-NOT FOUND}"
      echo "Google Chrome: ${CHROME_BIN:-NOT FOUND}"
      echo "Firefox: ${FIREFOX_BIN:-NOT FOUND}"
      echo "selenium-webdriver: $SELENIUM_AVAILABLE"
      echo "Selenium Manager: resolved by selenium-webdriver at runtime"
    } > "$BROWSER_ERROR"
    # Identify likely missing browser/library
    if [ -z "$CHROMIUM_BIN" ] && [ -z "$FIREFOX_BIN" ]; then
      prompt_user "system browser (Chromium or Firefox)" "sudo pacman -S chromium firefox"
    elif [ -n "$FIREFOX_BIN" ]; then
      prompt_user "Firefox shared library or driver" "sudo pacman -S firefox"
    else
      prompt_user "Chromium shared library or driver" "sudo pacman -S chromium"
    fi
    mark_blocked
    exit 1
  fi

  log "Native Selenium WebDriver browser setup: READY"
  exit 0
}

main "$@"
