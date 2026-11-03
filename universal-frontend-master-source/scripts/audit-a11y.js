#!/usr/bin/env node
/*
audit-a11y.js — all: run axe-core against <url> via Selenium WebDriver.

Uses @axe-core/webdriverjs so the scan runs against a real, native browser.
Prefers headless Chromium/Chrome, falls back to headless Firefox. The
sandbox is always preserved (--no-sandbox is never added).

Writes .ufme/evidence/a11y-results.json and prints one line per violation:

    rule-id | impact | count | first selector

Exit codes:
  0  no violations
  1  violations found
  2  bad invocation
  3  missing dependency (see message)
  5  browser/runtime failure (reason printed; no fake numbers reported)

Safety: project-local npm only; never sudo/pacman/systemctl; never --no-sandbox.
*/
'use strict';

const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..', '..');
const EVIDENCE_DIR = path.join(ROOT_DIR, '.ufme', 'evidence');
const RESULTS_FILE = path.join(EVIDENCE_DIR, 'a11y-results.json');

const EXIT_OK = 0;
const EXIT_VIOLATIONS = 1;
const EXIT_USAGE = 2;
const EXIT_MISSING_DEP = 3;
const EXIT_RUNTIME = 5;

const log = (msg) => console.log(`[audit-a11y] ${msg}`);
const logErr = (msg) => console.error(`[audit-a11y] ${msg}`);

// --- Dependency gate -------------------------------------------------------
let webdriver;
let FirefoxOptions;
let ChromeOptions;
let AxeBuilder;
try {
  webdriver = require('selenium-webdriver');
  FirefoxOptions = require('selenium-webdriver/firefox').Options;
  ChromeOptions = require('selenium-webdriver/chrome').Options;
  const axeModule = require('@axe-core/webdriverjs');
  AxeBuilder = axeModule.AxeBuilder || axeModule.default || axeModule;
} catch (err) {
  logErr('Missing dependency — run: npm i -D @axe-core/webdriverjs');
  process.exit(EXIT_MISSING_DEP);
}

// --- CLI parsing -----------------------------------------------------------
const argv = process.argv.slice(2);
let url = null;
let timeoutMs = 120000;

for (let i = 0; i < argv.length; i++) {
  if (argv[i] === '--timeout') {
    const n = Number(argv[i + 1]);
    if (!Number.isFinite(n) || n <= 0) {
      logErr('--timeout requires a positive number of milliseconds');
      process.exit(EXIT_USAGE);
    }
    timeoutMs = n;
    i += 1;
  } else if (argv[i] === '--help' || argv[i] === '-h') {
    console.log('Usage: node audit-a11y.js <url> [--timeout <ms>]');
    process.exit(EXIT_OK);
  } else if (argv[i] === null || argv[i].startsWith('--')) {
    logErr(`unknown option: ${argv[i]}`);
    process.exit(EXIT_USAGE);
  } else if (url === null) {
    url = argv[i];
  } else {
    logErr(`unexpected argument: ${argv[i]}`);
    process.exit(EXIT_USAGE);
  }
}

if (!url) {
  logErr('Usage: node audit-a11y.js <url>');
  process.exit(EXIT_USAGE);
}

// --- Browser discovery -----------------------------------------------------
function findBinary(candidates, envKeys) {
  for (const key of envKeys) {
    if (process.env[key]) return process.env[key];
  }
  const dirs = (process.env.PATH || '').split(path.delimiter).filter(Boolean);
  for (const name of candidates) {
    for (const dir of dirs) {
      const full = path.join(dir, name);
      try {
        fs.accessSync(full, fs.constants.X_OK);
        return full;
      } catch {
        /* keep looking */
      }
    }
  }
  return null;
}

const CHROME_CANDIDATES = [
  'chromium',
  'chromium-browser',
  'google-chrome-stable',
  'google-chrome',
  'chrome',
];
const FIREFOX_CANDIDATES = ['firefox', 'firefox-developer-edition', 'firefox-bin'];

function buildDriver(mode, bin) {
  const { Builder } = webdriver;
  if (mode === 'firefox') {
    const opts = new FirefoxOptions().setBinary(bin).addArguments('-headless');
    return new Builder().forBrowser('firefox').setFirefoxOptions(opts).build();
  }
  // Chromium sandbox is preserved: --no-sandbox is never added.
  const opts = new ChromeOptions();
  opts.setChromeBinaryPath(bin);
  opts.addArguments('--headless=new', '--disable-dev-shm-usage');
  // Selenium Manager recognizes the browser name 'chrome' for chromium too.
  return new Builder().forBrowser('chrome').setChromeOptions(opts).build();
}

function withTimeout(promise, label) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error(`${label} timed out after ${timeoutMs}ms`)),
      timeoutMs,
    );
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (err) => {
        clearTimeout(timer);
        reject(err);
      },
    );
  });
}

function writeResults(data) {
  fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
  fs.writeFileSync(RESULTS_FILE, `${JSON.stringify(data, null, 2)}\n`, 'utf-8');
}

function exitRuntime(reason, url) {
  logErr(`Degraded: ${reason}`);
  // Never report fake numbers — evidence records the failure, not numbers.
  writeResults({ url, timestamp: new Date().toISOString(), status: 'DEGRADED', reason });
  process.exit(EXIT_RUNTIME);
}

async function main() {
  const chromeBin = findBinary(CHROME_CANDIDATES, ['CHROMIUM_BIN', 'CHROME_BIN']);
  const firefoxBin = findBinary(FIREFOX_CANDIDATES, ['FIREFOX_BIN']);

  if (!chromeBin && !firefoxBin) {
    exitRuntime('no Chromium/Chrome or Firefox binary found on PATH', url);
  }

  let driver = null;
  let attempt = chromeBin ? ['chrome', chromeBin] : null;
  const fallback = firefoxBin ? ['firefox', firefoxBin] : null;

  if (attempt) {
    log(`Launching headless Chromium/Chrome (${attempt[1]})...`);
  } else if (fallback) {
    attempt = fallback;
    log(`Launching headless Firefox (${attempt[1]})...`);
  }

  while (attempt) {
    try {
      driver = await withTimeout(
        buildDriver(attempt[0], attempt[1]),
        `Selenium ${attempt[0]} driver build`,
      );
      break;
    } catch (err) {
      log(`${attempt[0]} launch failed: ${err.message}`);
      if (fallback && attempt[0] === 'chrome') {
        attempt = fallback;
        log(`Falling back to headless Firefox (${attempt[1]})...`);
        continue;
      }
      driver = null;
      break;
    }
  }

  if (!driver) {
    exitRuntime('no browser could launch via Selenium WebDriver', url);
  }

  try {
    log(`Navigating to ${url} ...`);
    await withTimeout(driver.get(url), `page load of ${url}`);
    await withTimeout(
      driver.wait(webdriver.until.elementLocated(webdriver.By.css('body')), Math.min(timeoutMs, 30000)),
      'waiting for document body',
    ).catch(() => {
      // Pages without a <body> element locator still scanned; do not fake results.
      log('body element locator timed out; continuing scan');
    });

    log('Running axe-core scan...');
    const results = await withTimeout(new AxeBuilder(driver).analyze(), 'axe-core analyze');

    const violations = Array.isArray(results.violations) ? results.violations : [];
    const violationsByRule = violations.map((v) => {
      const nodes = Array.isArray(v.nodes) ? v.nodes : [];
      return {
        id: v.id,
        impact: v.impact || 'unknown',
        count: nodes.length,
        firstSelector: nodes[0] && Array.isArray(nodes[0].target)
          ? nodes[0].target.join(' ')
          : '',
      };
    });
    const totalViolations = violationsByRule.reduce((sum, v) => sum + v.count, 0);

    const timestamp = new Date().toISOString();
    writeResults({
      url,
      timestamp,
      browser: `${attempt[0]}:${attempt[1]}`,
      status: 'RAN',
      violationsByRule,
      totalViolations,
    });

    for (const v of violationsByRule) {
      console.log(`${v.id} | ${v.impact} | ${v.count} | ${v.firstSelector}`);
    }
    log(`Total violations: ${totalViolations}`);
    log(`Results: ${RESULTS_FILE}`);

    process.exitCode = totalViolations === 0 ? EXIT_OK : EXIT_VIOLATIONS;
  } catch (err) {
    exitRuntime(`axe-core scan failed: ${err.message}`, url);
  } finally {
    try {
      await driver.quit();
    } catch {
      /* driver already gone */
    }
  }
}

main().catch((err) => {
  logErr(`unexpected failure: ${err.message}`);
  exitRuntime(`unexpected failure: ${err.message}`, url);
});
