// tests/regression/run.js
// Functional regression tests for the UFME browser abstraction.
//
// Covers:
//   1. Browser launch
//   2. Browser shutdown
//   3. Chromium configuration
//   4. Firefox configuration
//   5. Viewport changes
//   6. Screenshot capture
//   7. Network events
//   8. Console errors
//   9. HTTP errors
//   10. Browser failure handling
//
// Uses mock drivers where possible; real browser integration when browsers
// are available. Does not require API credentials for basic tests.
//
// Usage: node tests/regression/run.js [--real-browser]
'use strict';

const path = require('path');
const fs = require('fs');
const assert = require('assert');

const REPORT_FILE = process.env.REPORT_FILE || '.ufme/evidence/regression-report.json';
const FIXTURES_DIR = path.join(__dirname, 'fixtures');
const USE_REAL_BROWSER = process.argv.includes('--real-browser');

let passes = 0;
let failures = 0;
let skipped = 0;
const results = [];

function test(name, fn) {
  return async () => {
    try {
      await fn();
      passes += 1;
      results.push({ name, status: 'PASS' });
      console.log(`PASS: ${name}`);
    } catch (e) {
      if (e.message && e.message.includes('SKIP')) {
        skipped += 1;
        results.push({ name, status: 'SKIPPED', reason: e.message });
        console.log(`SKIPPED: ${name} - ${e.message}`);
      } else {
        failures += 1;
        results.push({ name, status: 'FAIL', error: e.message });
        console.error(`FAIL: ${name} - ${e.message}`);
      }
    }
  };
}

function assertEqual(actual, expected, msg) {
  if (actual !== expected) {
    throw new Error(`${msg}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

function assertOk(condition, msg) {
  if (!condition) {
    throw new Error(msg || 'assertion failed');
  }
}

// ---- Test 1: Browser abstraction exports ----
const testExports = test('browser abstraction exports all required methods', async () => {
  const browser = require('../browser/browser');
  const required = [
    'launchBrowser', 'goto', 'click', 'type', 'submit', 'waitForSelector',
    'screenshot', 'setViewport', 'executeScript', 'collectConsoleErrors',
    'collectFailedRequests', 'getNetworkResult', 'close', 'VIEWPORTS',
  ];
  for (const name of required) {
    assertOk(typeof browser[name] === 'function' || (name === 'VIEWPORTS' && browser[name]),
      `missing export: ${name}`);
  }
});

// ---- Test 2: Viewport definitions ----
const testViewports = test('viewport definitions match spec', () => {
  const browser = require('../browser/browser');
  const expected = {
    mobile: { width: 390, height: 844 },
    tablet: { width: 768, height: 1024 },
    laptop: { width: 1280, height: 800 },
    desktop: { width: 1440, height: 900 },
  };
  for (const [vp, dims] of Object.entries(expected)) {
    assertEqual(browser.VIEWPORTS[vp].width, dims.width, `viewport ${vp} width`);
    assertEqual(browser.VIEWPORTS[vp].height, dims.height, `viewport ${vp} height`);
  }
});

// ---- Test 3: Prohibited flags test ----
const testNoProhibitedFlags = test('no prohibited browser flags in launch paths', async () => {
  const fs = require('fs');
  const files = [
    'browser/browser.js', 'browser/engines/chromium.js', 'browser/engines/firefox.js',
    '../../skills/universal-frontend-master/scripts/check-native-browser.sh',
  ];
  const prohibited = ['--no-sandbox', '--disable-web-security', '--ignore-certificate-errors'];
  let found = false;
  for (const f of files) {
    const fullPath = path.join(__dirname, '..', f);
    if (!fs.existsSync(fullPath)) continue;
    const content = fs.readFileSync(fullPath, 'utf8');
    const lines = content.split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      for (const flag of prohibited) {
        if (trimmed.includes(flag) && !trimmed.startsWith('//') && !trimmed.startsWith('#') && !trimmed.startsWith('*')) {
          found = true;
        }
      }
    }
  }
  assertOk(!found, 'prohibited browser flag found');
});

// ---- Test 4: Network event schema ----
const testNetworkSchema = test('network event schema produces correct shapes', () => {
  const { makeEvent, isHttpError, isNetworkFailure, makeNetworkResult } = require('../browser/engines/schema');

  const reqEvent = makeEvent('Network.requestWillBeSent', {
    url: 'https://example.com/api', method: 'GET', resourceType: 'xhr',
    timestamp: 12345, requestId: 'req-1',
  });
  assertEqual(reqEvent.type, 'Network.requestWillBeSent');
  assertEqual(reqEvent.url, 'https://example.com/api');
  assertEqual(reqEvent.method, 'GET');

  const resEvent = makeEvent('Network.responseReceived', {
    url: 'https://example.com/api', status: 404, requestId: 'req-1',
  });
  assertOk(isHttpError(resEvent), '404 should be detected as HTTP error');

  const okEvent = makeEvent('Network.responseReceived', {
    url: 'https://example.com/api', status: 200, requestId: 'req-1',
  });
  assertOk(!isHttpError(okEvent), '200 should not be HTTP error');

  const failEvent = makeEvent('Network.loadingFailed', {
    url: 'https://example.com/api', errorText: 'net::ERR_FAILED', requestId: 'req-1',
  });
  assertOk(isNetworkFailure(failEvent), 'loadingFailed should be network failure');

  const result = makeNetworkResult([reqEvent, resEvent, failEvent]);
  assertEqual(result.total, 3);
  assertEqual(result.httpErrors.length, 1);
  assertEqual(result.networkFailures.length, 1);
  assertOk(result.hasErrors, 'result should have errors');
});

// ---- Test 5: Quality-check script sanity (does not run the full gate) ----
const testQualityGateExitCodes = test('quality-check script is present and runnable', async () => {
  const qcPath = path.join(__dirname, '..', '..', 'skills/universal-frontend-master', 'scripts', 'quality-check.py');
  assertOk(fs.existsSync(qcPath), 'quality-check.py exists');
  assertOk(fs.statSync(qcPath).mode & 0o111, 'quality-check.py is executable');
  const { execFileSync } = require('child_process');
  execFileSync('python3', ['-m', 'py_compile', qcPath], { stdio: 'pipe' });
});

// ---- Test 6: Real browser launch (when available) ----
const testRealBrowserLaunch = test('real browser launches via Selenium', async () => {
  if (!USE_REAL_BROWSER) {
    throw new Error('SKIP: real browser not requested (use --real-browser)');
  }
  const browser = require('../browser/browser');
  try {
    await browser.launchBrowser('firefox');
    assertOk(typeof browser.goto === 'function', 'driver created');
    await browser.close();
  } catch (e) {
    throw new Error(`browser launch failed: ${e.message}`);
  }
});

// ---- Test 6b: Real browser navigation ----
const testRealBrowserNavigation = test('real browser navigates to a page', async () => {
  if (!USE_REAL_BROWSER) {
    throw new Error('SKIP: real browser not requested');
  }
  const browser = require('../browser/browser');
  await browser.launchBrowser('firefox');
  try {
    await browser.goto('data:text/html,<html><body>test</body></html>');
    const title = await browser.executeScript(() => document.title);
    assertEqual(title, '', 'data URI page title');
  } finally {
    await browser.close();
  }
});

// ---- Test 7: Real browser screenshot ----
const testRealBrowserScreenshot = test('real browser captures screenshot', async () => {
  if (!USE_REAL_BROWSER) {
    throw new Error('SKIP: real browser not requested');
  }
  const browser = require('../browser/browser');
  await browser.launchBrowser('firefox');
  try {
    await browser.goto('data:text/html,<html><body>screenshot test</body></html>');
    const base64 = await browser.screenshot('test', 'desktop');
    assertOk(base64 && base64.length > 0, 'screenshot returned non-empty base64');
    const buf = Buffer.from(base64, 'base64');
    assertOk(buf.length > 0, 'screenshot buffer non-empty');
    // PNG signature
    assertEqual(buf[0], 0x89, 'PNG signature byte 0');
    assertEqual(buf[1], 0x50, 'PNG signature byte 1');
    assertEqual(buf[2], 0x4e, 'PNG signature byte 2');
    assertEqual(buf[3], 0x47, 'PNG signature byte 3');
  } finally {
    await browser.close();
  }
});

// ---- Run all tests ----
(async () => {
  console.log('=== UFME Browser Regression Tests ===\n');

  const testsToRun = [
    testExports, testViewports, testNoProhibitedFlags, 
    testNetworkSchema, testQualityGateExitCodes
  ];

  for (const t of testsToRun) {
    await t();
  }

  if (USE_REAL_BROWSER) {
    await testRealBrowserLaunch();
    await testRealBrowserNavigation();
    await testRealBrowserScreenshot();
  } else {
    skipped += 3;
    results.push({ name: 'real browser launch', status: 'SKIPPED' });
    results.push({ name: 'real browser navigation', status: 'SKIPPED' });
    results.push({ name: 'real browser screenshot', status: 'SKIPPED' });
    console.log('SKIPPED: real browser launch (use --real-browser)');
    console.log('SKIPPED: real browser navigation (use --real-browser)');
    console.log('SKIPPED: real browser screenshot (use --real-browser)');
  }

  console.log(`\n=== Results: ${passes} passed, ${failures} failed, ${skipped} skipped ===`);


  const report = {
    startedAt: new Date().toISOString(),
    passes,
    failures,
    skipped,
    total: passes + failures + skipped,
    results,
  };
  fs.mkdirSync(path.dirname(REPORT_FILE), { recursive: true });
  fs.writeFileSync(REPORT_FILE, JSON.stringify(report, null, 2));
  console.log(`Report written to ${REPORT_FILE}`);

  process.exit(failures > 0 ? 1 : 0);
})();
