// universal-frontend-master-source/browser/run.js
// End-to-end Selenium test runner: launches browser, visits URL, captures
// budgeted screenshots (default: viewport-only at 390/1440; --budget=full
// adds full-page + tablet/laptop), collects console/failed requests, writes
// browser-results.json with accurate PASS/FAIL/SKIPPED/BLOCKED status.
//
// Usage:
//   node universal-frontend-master-source/browser/run.js <url> <screenshotDir> <resultsFile> \
//     [--screenshots-only] [--budget=viewport|full] [--sections=selector]
const browser = require('./browser');
const screenshot = require('./screenshot');
const fs = require('fs');
const path = require('path');

const [, , url, screenshotDir, resultsFile] = process.argv;
const screenshotsOnly = process.argv.includes('--screenshots-only');

const VIEWPORTS = ['mobile', 'tablet', 'laptop', 'desktop'];

// Acceptance policy: which checks are mandatory vs optional.
const POLICY = {
  consoleErrors: 'warning',   // console errors are warnings, not automatic FAIL
  httpErrors: 'fail',         // HTTP 4xx/5xx are failures
  networkFailures: 'fail',    // network failures are failures
  screenshots: 'mandatory',   // screenshots are mandatory
  navigation: 'mandatory',    // navigation is mandatory
  browserLaunch: 'mandatory', // browser launch is mandatory
};

(async () => {
  const results = {
    url,
    startedAt: new Date().toISOString(),
    status: 'RUNNING', // PASS | FAIL | SKIPPED | BLOCKED
    browser: null,
    requestedBrowser: null,
    session: null,
    manifest: null,
    screenshots: [],
    consoleErrors: [],
    failedRequests: [],
    httpErrors: [],
    networkFailures: [],
    errors: [],
    checks: [],
    summary: { PASS: 0, FAIL: 0, SKIPPED: 0, BLOCKED: 0 },
  };

  function addCheck(name, status, detail = '') {
    results.checks.push({ name, status, detail });
    results.summary[status] = (results.summary[status] || 0) + 1;
  }

  function isFail(status) {
    return status === 'FAIL' || status === 'BLOCKED';
  }

  try {
    // 1. Browser launch (mandatory)
    let launched = false;
    for (const name of ['chromium', 'firefox']) {
      results.requestedBrowser = name;
      try {
        await browser.launchBrowser(name);
        results.browser = name;
        launched = true;
        addCheck(`browserLaunch:${name}`, 'PASS');
        break;
      } catch (e) {
        results.errors.push(`${name} launch failed: ${e.message}`);
        addCheck(`browserLaunch:${name}`, 'FAIL', e.message);
      }
    }
    if (!launched) {
      results.status = 'BLOCKED';
      addCheck('browserLaunch:all', 'BLOCKED', 'No browser could launch via Selenium WebDriver');
      throw new Error('No browser could launch via Selenium WebDriver');
    }

    // Report the engine that actually launched, not merely the one requested.
    results.session = await browser.getSessionInfo();
    const reported = String((results.session && results.session.browserName) || '').toLowerCase();
    const expected = results.requestedBrowser === 'chromium' ? /chrome|chromium/ : /firefox/;
    if (!reported || !expected.test(reported)) {
      addCheck('browserIdentity', 'FAIL',
        `requested ${results.requestedBrowser}, driver reports ${reported || 'unknown'}`);
    } else {
      addCheck('browserIdentity', 'PASS',
        `${results.session.browserName} ${results.session.browserVersion || ''}`.trim());
    }

    // 2. Navigation (mandatory)
    let navigated = false;
    try {
      await browser.goto(url);
      await new Promise((r) => setTimeout(r, 2000));
      navigated = true;
      addCheck('navigation', 'PASS', url);
    } catch (e) {
      results.errors.push(`navigation failed: ${e.message}`);
      addCheck('navigation', 'FAIL', e.message);
    }

    // 3. Screenshots (budget-scoped), light theme mandatory.
    //    Capture is aborted after a failed navigation: screenshots of the
    //    browser error page would be misleading evidence.
    //    Dark pass runs ONLY when the page defines prefers-color-scheme rules
    //    or a theme toggle exists (todo 4.2); otherwise SKIPPED.
    if (!navigated) {
      addCheck('screenshot:all', 'SKIPPED', 'navigation failed; capture aborted');
    } else {
      try {
        const name = screenshotsOnly ? 'fullpage' : 'home';
        const light = await screenshot.captureBudget(browser, screenshotDir, name, 'light');
        results.screenshots.push(...light);
        addCheck(`screenshot:${name}:light`, 'PASS', `${light.length} capture(s)`);

        const darkSupported = await screenshot.detectDarkSupport(browser);
        if (darkSupported) {
          try {
            const dark = await screenshot.captureBudget(browser, screenshotDir, name, 'dark');
            results.screenshots.push(...dark);
            addCheck(`screenshot:${name}:dark`, 'PASS', `${dark.length} capture(s)`);
          } catch (e) {
            results.errors.push(`dark theme screenshots: ${e.message}`);
            addCheck(`screenshot:${name}:dark`, 'SKIPPED', e.message);
          }
        } else {
          addCheck('dark-theme:detect', 'SKIPPED',
            'page defines no prefers-color-scheme rules or theme toggle; dark pass skipped');
        }
      } catch (e) {
        results.errors.push(`screenshot capture failed: ${e.message}`);
        addCheck('screenshot:all', 'FAIL', e.message);
      }
    }

    // 4. Console errors (policy: warning)
    results.consoleErrors = await browser.collectConsoleErrors();
    if (results.consoleErrors.length > 0) {
      addCheck('consoleErrors', POLICY.consoleErrors, `${results.consoleErrors.length} error(s)`);
    } else {
      addCheck('consoleErrors', 'PASS', 'no console errors');
    }

    // 5. Network monitoring (policy: fail on HTTP errors + network failures)
    const netResult = await browser.getNetworkResult();
    results.httpErrors = netResult.httpErrors || [];
    results.networkFailures = netResult.networkFailures || [];
    results.failedRequests = [...(netResult.networkFailures || [])];

    if (results.httpErrors.length > 0) {
      addCheck('network:httpErrors', POLICY.httpErrors,
        `${results.httpErrors.length} HTTP error(s)`);
    } else {
      addCheck('network:httpErrors', 'PASS', 'no HTTP errors');
    }

    if (results.networkFailures.length > 0) {
      addCheck('network:failures', POLICY.networkFailures,
        `${results.networkFailures.length} failed request(s)`);
    } else {
      addCheck('network:failures', 'PASS', 'no network failures');
    }

    // 5b. Screenshot manifest: dimensions must match the files on disk.
    if (navigated) {
      try {
        if (results.screenshots.length === 0) throw new Error('no screenshots captured');
        results.manifest = screenshot.writeManifest(screenshotDir, results.screenshots, { url });
        addCheck('screenshotManifest', 'PASS',
          `${results.screenshots.length} image(s) -> ${results.manifest}`);
      } catch (e) {
        results.errors.push(`screenshot manifest failed: ${e.message}`);
        addCheck('screenshotManifest', 'FAIL', e.message);
      }
    }

    // Calculate overall status from individual check results.
    let hasBlocked = false;
    let hasFail = false;
    for (const check of results.checks) {
      if (check.status === 'BLOCKED') hasBlocked = true;
      if (check.status === 'FAIL') hasFail = true;
    }

    if (hasBlocked) {
      results.status = 'BLOCKED';
    } else if (hasFail) {
      results.status = 'FAIL';
    } else {
      // Check if any mandatory check was skipped (e.g., screenshots skipped = fail)
      const mandatorySkipped = results.checks.some(c =>
        c.status === 'SKIPPED' &&
        (c.name.includes('screenshot') || c.name.includes('browserLaunch') || c.name.includes('navigation'))
      );
      if (mandatorySkipped) {
        results.status = 'FAIL';
      } else {
        results.status = 'PASS';
      }
    }

  } catch (e) {
    if (results.status !== 'BLOCKED') {
      results.status = 'FAIL';
      results.errors.push(e.message);
    }
  } finally {
    try { await browser.close(); } catch (e) { /* ignore close errors */ }
    results.finishedAt = new Date().toISOString();
    fs.writeFileSync(resultsFile, JSON.stringify(results, null, 2));
    console.log(`Selenium run: ${results.status} (${results.browser || 'none'}) -> ${resultsFile}`);

    const exitCode = results.status === 'PASS' ? 0 : 1;
    process.exit(exitCode);
  }
})();
