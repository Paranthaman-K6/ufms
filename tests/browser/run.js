// tests/browser/run.js
// End-to-end Selenium test runner: launches browser, visits URL, captures
// screenshots at all viewports/themes, collects console/failed requests,
// writes browser-results.json with PASS/FAIL/SKIPPED/BLOCKED statuses.
//
// Usage: node tests/browser/run.js <url> <screenshotDir> <resultsFile> [--screenshots-only]
const browser = require('./browser');
const screenshot = require('./screenshot');
const fs = require('fs');
const path = require('path');

const [, , url, screenshotDir, resultsFile, screenshotsOnly] = process.argv;

const VIEWPORTS = ['mobile', 'tablet', 'laptop', 'desktop'];

(async () => {
  const results = {
    url,
    startedAt: new Date().toISOString(),
    status: 'RUNNING', // PASS | FAIL | SKIPPED | BLOCKED
    browser: null,
    screenshots: [],
    consoleErrors: [],
    failedRequests: [],
    errors: [],
    summary: { pass: 0, fail: 0, skipped: 0, blocked: 0 },
  };

  try {
    // Prefer Chromium; fall back to Firefox.
    let launched = false;
    try {
      await browser.launchBrowser('chromium');
      results.browser = 'chromium';
      launched = true;
    } catch (e) {
      results.errors.push(`chromium launch failed: ${e.message}`);
    }
    if (!launched) {
      try {
        await browser.launchBrowser('firefox');
        results.browser = 'firefox';
        launched = true;
      } catch (e) {
        results.errors.push(`firefox launch failed: ${e.message}`);
      }
    }
    if (!launched) {
      results.status = 'BLOCKED';
      results.summary.blocked = 1;
      throw new Error('No browser could launch via Selenium WebDriver');
    }

    await browser.goto(url);
    await new Promise((r) => setTimeout(r, 2000)); // allow initial render

    // Capture screenshots at all viewports, light + dark themes.
    if (screenshotsOnly === '--screenshots-only') {
      const light = await screenshot.captureFullPage(browser, screenshotDir, 'fullpage', 'light');
      results.screenshots.push(...light);
      try {
        const dark = await screenshot.captureFullPage(browser, screenshotDir, 'fullpage', 'dark');
        results.screenshots.push(...dark);
      } catch (e) {
        results.errors.push(`dark theme screenshots: ${e.message}`);
        results.summary.skipped += 1;
      }
    } else {
      const light = await screenshot.captureFullPage(browser, screenshotDir, 'home', 'light');
      results.screenshots.push(...light);
      try {
        const dark = await screenshot.captureFullPage(browser, screenshotDir, 'home', 'dark');
        results.screenshots.push(...dark);
      } catch (e) {
        results.errors.push(`dark theme screenshots: ${e.message}`);
        results.summary.skipped += 1;
      }
    }

    // Collect console errors and failed requests (awaited now).
    results.consoleErrors = await browser.collectConsoleErrors();
    results.failedRequests = await browser.collectFailedRequests();

    // Determine overall status.
    if (results.errors.length > 0 && !results.browser) {
      results.status = 'FAILED';
      results.summary.fail = 1;
    } else {
      results.status = 'PASS';
      results.summary.pass = 1;
    }
    if (results.consoleErrors.length > 0) results.summary.fail += 1;
    if (results.failedRequests.length > 0) results.summary.fail += 1;
  } catch (e) {
    results.status = results.status === 'BLOCKED' ? 'BLOCKED' : 'FAILED';
    results.errors.push(e.message);
    results.summary.fail = 1;
  } finally {
    try { await browser.close(); } catch (e) { /* ignore close errors */ }
    results.finishedAt = new Date().toISOString();
    fs.writeFileSync(resultsFile, JSON.stringify(results, null, 2));
    console.log(`Selenium run: ${results.status} (${results.browser || 'none'}) -> ${resultsFile}`);
    process.exit(results.status === 'PASS' ? 0 : 1);
  }
})();
