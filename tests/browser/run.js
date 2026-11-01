// tests/browser/run.js
// End-to-end Selenium test runner: launches browser, visits URL, captures
// screenshots at all viewports/themes, collects console/failed requests,
// writes browser-results.json.
//
// Usage: node tests/browser/run.js <url> <screenshotDir> <resultsFile> [--screenshots-only]
const browser = require('./browser');
const screenshot = require('./screenshot');
const fs = require('fs');
const path = require('path');

const [, , url, screenshotDir, resultsFile, screenshotsOnly] = process.argv;

(async () => {
  const results = {
    url,
    startedAt: new Date().toISOString(),
    status: 'RUNNING',
    browser: null,
    screenshots: [],
    consoleErrors: [],
    failedRequests: [],
    errors: [],
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
    if (!launched) throw new Error('No browser could launch via Selenium WebDriver');

    await browser.goto(url);
    await new Promise((r) => setTimeout(r, 2000)); // allow initial render

    if (screenshotsOnly === '--screenshots-only') {
      const caps = await screenshot.captureFullPage(browser, screenshotDir, 'fullpage', 'light');
      results.screenshots.push(...caps);
      try {
        const capsDark = await screenshot.captureFullPage(browser, screenshotDir, 'fullpage', 'dark');
        results.screenshots.push(...capsDark);
      } catch (e) { results.errors.push(`dark theme screenshots: ${e.message}`); }
    } else {
      const viewports = ['mobile', 'tablet', 'laptop', 'desktop'];
      for (const vp of viewports) {
        const caps = await screenshot.captureFullPage(browser, screenshotDir, 'home', 'light');
        results.screenshots.push(...caps.filter((c) => c.viewport === vp));
      }
    }

    results.consoleErrors = await browser.collectConsoleErrors();
    results.failedRequests = await browser.collectFailedRequests();
    results.status = 'COMPLETE';
  } catch (e) {
    results.status = 'FAILED';
    results.errors.push(e.message);
  } finally {
    await browser.close();
    results.finishedAt = new Date().toISOString();
    fs.writeFileSync(resultsFile, JSON.stringify(results, null, 2));
    console.log(`Selenium run: ${results.status} (${results.browser}) -> ${resultsFile}`);
    process.exit(results.status === 'COMPLETE' ? 0 : 1);
  }
})();
