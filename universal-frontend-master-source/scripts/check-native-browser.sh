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

# Configurable timeout for Selenium tests
TIMEOUT_SEC="${BROWSER_TIMEOUT_SEC:-10}"

detect_browsers() {
  CHROMIUM_BIN=""
  CHROME_BIN=""
  FIREFOX_BIN=""
  SELENIUM_WORKS_CHROMIUM=false
  SELENIUM_WORKS_FIREFOX=false

  # Check for a wider range of common binary names
  for bin in chromium chromium-bin google-chrome-stable google-chrome; do
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

  # Test Selenium with available browsers
  if [ -n "$CHROMIUM_BIN" ]; then
    if timeout --kill-after=2 "${TIMEOUT_SEC}s" python3 -c "
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
opts = Options()
opts.add_argument('--headless')
# Sandbox omitted only in isolated CI containers; not default for normal operation.
# This agent never adds --no-sandbox by default. If needed, user must set via env.
opts.add_argument('--disable-dev-shm-usage')
try:
    driver = webdriver.Chrome(options=opts)
    driver.get('data:text/html,<html><body>Selenium test</body></html>')
    title = driver.title
    driver.quit()
    exit(0)
except Exception as e:
    exit(1)
    " 2>>"$BROWSER_ERROR"; then
      SELENIUM_WORKS_CHROMIUM=true
    fi
  fi

  if [ -n "$FIREFOX_BIN" ]; then
    if timeout --kill-after=2 "${TIMEOUT_SEC}s" python3 -c "
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
opts = Options()
opts.add_argument('--headless')
try:
    driver = webdriver.Firefox(options=opts)
    driver.get('data:text/html,<html><body>Selenium test</body></html>')
    title = driver.title
    driver.quit()
    exit(0)
except Exception as e:
    exit(1)
    " 2>>"$BROWSER_ERROR"; then
      SELENIUM_WORKS_FIREFOX=true
    fi
  fi

  log "Chromium/Chrome: ${CHROMIUM_BIN:-NOT FOUND}"
  log "Firefox: ${FIREFOX_BIN:-NOT FOUND}"
  if [ "$SELENIUM_WORKS_CHROMIUM" = true ]; then
    log "Selenium with Chromium: WORKING"
  else
    log "Selenium with Chromium: NOT TESTED/NOT WORKING"
  fi
  if [ "$SELENIUM_WORKS_FIREFOX" = true ]; then
    log "Selenium with Firefox: WORKING"
  else
    log "Selenium with Firefox: NOT TESTED/NOT WORKING"
  fi
}

detect_selenium() {
  SELENIUM_AVAILABLE="no"
  if [ -f "$ROOT_DIR/node_modules/selenium-webdriver/index.js" ]; then
    SELENIUM_AVAILABLE="yes"
    log "selenium-webdriver: installed project-local"
  else
    log "Missing dependency — run: npm i -D selenium-webdriver"
    log "selenium-webdriver: NOT installed (project-local install required)"
  fi
}

# Minimal headless Selenium launch test using a temp JS file.
try_selenium_launch() {
  local browser="$1"
  local bin="$2"
  local tmpfile
  tmpfile="$(mktemp "$ROOT_DIR/.ufme-selenium-check.XXXXXX.js")"
  trap 'rm -f "$tmpfile"' RETURN
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
    opts = new (require('selenium-webdriver/chrome').Options)();
    if (process.env.CHROMIUM_BIN) opts.setChromeBinaryPath(process.env.CHROMIUM_BIN);
    opts.addArguments('--headless=new', '--disable-dev-shm-usage');
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
    echo "Missing dependency — run: npm i -D selenium-webdriver"
    prompt_user "selenium-webdriver npm package" "npm i -D selenium-webdriver"
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
    # Identify likely missing browser/library and print a clear,
    # action-oriented hint (never sudo/pacman; user installs the browser).
    if [ -z "$CHROMIUM_BIN" ] && [ -z "$FIREFOX_BIN" ]; then
      log "Missing dependency — no Chromium/Chrome and no Firefox browser found."
      log "Install a browser package (e.g. chromium or firefox) with your system package manager, then retry."
      prompt_user "system browser (Chromium or Firefox)" "install the chromium or firefox package via your system package manager"
    elif [ -n "$FIREFOX_BIN" ]; then
      log "Missing dependency — Firefox could not launch (shared library or driver)."
      log "Reinstall/repair the firefox package via your system package manager, then retry."
      prompt_user "Firefox shared library or driver" "reinstall the firefox package via your system package manager"
    else
      log "Missing dependency — Chromium could not launch (shared library or driver)."
      log "Reinstall/repair the chromium package via your system package manager, then retry."
      prompt_user "Chromium shared library or driver" "reinstall the chromium package via your system package manager"
    fi
    mark_blocked
    exit 1
  fi

  log "Native Selenium WebDriver browser setup: READY"
  exit 0
}

main "$@"
