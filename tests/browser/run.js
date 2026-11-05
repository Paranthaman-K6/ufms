// tests/browser/run.js
// End-to-end Selenium test runner: launches browser, visits URL, captures
// screenshots at all viewports/themes, collects console/failed requests,
// writes browser-results.json with accurate PASS/FAIL/SKIPPED/BLOCKED status.
//
// Usage: node tests/browser/run.js <url> <screenshotDir> <resultsFile> [--screenshots-only]
const browser = require('./browser');
const screenshot = require('./screenshot');
const fs = require('fs');
const path = require('path');

const [, , url, screenshotDir, resultsFile, screenshotsOnly] = process.argv;

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
    try {
      await browser.launchBrowser('chromium');
      results.browser = 'chromium';
      launched = true;
      addCheck('browserLaunch:chromium', 'PASS');
    } catch (e) {
      results.errors.push(`chromium launch failed: ${e.message}`);
      addCheck('browserLaunch:chromium', 'FAIL', e.message);
    }
    if (!launched) {
      try {
        await browser.launchBrowser('firefox');
        results.browser = 'firefox';
        launched = true;
        addCheck('browserLaunch:firefox', 'PASS');
      } catch (e) {
        results.errors.push(`firefox launch failed: ${e.message}`);
        addCheck('browserLaunch:firefox', 'FAIL', e.message);
      }
    }
    if (!launched) {
      results.status = 'BLOCKED';
      addCheck('browserLaunch:all', 'BLOCKED', 'No browser could launch via Selenium WebDriver');
      throw new Error('No browser could launch via Selenium WebDriver');
    }

    // 2. Navigation (mandatory)
    try {
      await browser.goto(url);
      await new Promise((r) => setTimeout(r, 2000));
      addCheck('navigation', 'PASS', url);
    } catch (e) {
      results.errors.push(`navigation failed: ${e.message}`);
      addCheck('navigation', 'FAIL', e.message);
    }

    // 3. Screenshots at all viewports, light + dark themes (mandatory)
    try {
      if (screenshotsOnly === '--screenshots-only') {
        const light = await screenshot.captureFullPage(browser, screenshotDir, 'fullpage', 'light');
        results.screenshots.push(...light);
        addCheck('screenshot:fullpage:light', 'PASS', `${light.length} viewports`);
        try {
          const dark = await screenshot.captureFullPage(browser, screenshotDir, 'fullpage', 'dark');
          results.screenshots.push(...dark);
          addCheck('screenshot:fullpage:dark', 'PASS', `${dark.length} viewports`);
        } catch (e) {
          results.errors.push(`dark theme screenshots: ${e.message}`);
          addCheck('screenshot:fullpage:dark', 'SKIPPED', e.message);
        }
      } else {
        const light = await screenshot.captureFullPage(browser, screenshotDir, 'home', 'light');
        results.screenshots.push(...light);
        addCheck('screenshot:home:light', 'PASS', `${light.length} viewports`);
        try {
          const dark = await screenshot.captureFullPage(browser, screenshotDir, 'home', 'dark');
          results.screenshots.push(...dark);
          addCheck('screenshot:home:dark', 'PASS', `${dark.length} viewports`);
        } catch (e) {
          results.errors.push(`dark theme screenshots: ${e.message}`);
          addCheck('screenshot:home:dark', 'SKIPPED', e.message);
        }
      }
    } catch (e) {
      results.errors.push(`screenshot capture failed: ${e.message}`);
      addCheck('screenshot:all', 'FAIL', e.message);
    }

    // 3b. Section screenshot capture (when --sections provided).
    // Tests valid selectors, missing selectors, multiple sections, viewport
    // sizes, image integrity. Section failures are recorded as FAIL entries
    // rather than silently swallowed.
    const sectionSelectors = screenshot.sectionSelectors();
    if (sectionSelectors.length > 0) {
      try {
        const sectionResults = [];
        const sectionViewports = ['mobile', 'desktop'];
        for (const selector of sectionSelectors) {
          for (const vp of sectionViewports) {
            try {
              const r = await screenshot.captureSection(
                browser, screenshotDir, 'home-section', selector, vp, 'light'
              );
              sectionResults.push(r);
              results.screenshots.push(r);
              addCheck(`screenshot:section:${r.selector}@${r.viewport}`, 'PASS', `${r.size} bytes`);
            } catch (e) {
              sectionResults.push({ selector, viewport: vp, status: 'FAIL', error: e.message });
              addCheck(`screenshot:section:${selector}@${vp}`, 'FAIL', e.message);
            }
          }
        }
        const sectionFails = sectionResults.filter((s) => s.status === 'FAIL');
        if (sectionFails.length > 0) {
          addCheck('screenshot:sections', 'FAIL',
            `${sectionFails.length} section capture(s) failed: ` +
            sectionFails.map((f) => `${f.selector}@${f.viewport}: ${f.error}`).join('; '));
        } else {
          addCheck('screenshot:sections', 'PASS',
            `${sectionResults.length} section capture(s) across ` +
            `${new Set(sectionResults.map((s) => s.selector)).size} selector(s), ` +
            `${sectionViewports.length} viewport(s)`);
        }
        // Verify every section screenshot file is a non-empty PNG.
        const fs = require('fs');
        for (const s of sectionResults) {
          if (s.status === 'FAIL') continue;
          const buf = fs.readFileSync(s.file);
          const isPng = buf.length >= 8 && buf.subarray(0, 8).equals(
            Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]));
          if (!isPng || buf.length === 0) {
            addCheck(`screenshot:integrity:${path.basename(s.file)}`, 'FAIL', 'not a valid PNG');
          } else {
            addCheck(`screenshot:integrity:${path.basename(s.file)}`, 'PASS', `${buf.length} bytes`);
          }
        }
      } catch (e) {
        results.errors.push(`section screenshot capture failed: ${e.message}`);
        addCheck('screenshot:sections', 'FAIL', e.message);
      }
    } else {
      addCheck('screenshot:sections', 'SKIPPED', 'no --sections selectors provided');
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
      results.status = 'FAILED';
    } else {
      // Check if any mandatory check was skipped (e.g., screenshots skipped = fail)
      const mandatorySkipped = results.checks.some(c =>
        c.status === 'SKIPPED' &&
        (c.name.includes('screenshot') || c.name.includes('browserLaunch') || c.name.includes('navigation'))
      );
      if (mandatorySkipped) {
        results.status = 'FAILED';
      } else {
        results.status = 'PASS';
      }
    }

  } catch (e) {
    if (results.status !== 'BLOCKED') {
      results.status = 'FAILED';
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
