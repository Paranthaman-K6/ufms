// tests/browser/browser.js
// Native Selenium WebDriver browser abstraction.
// Exposes: launchBrowser, goto, click, type, submit, waitForSelector,
// screenshot, collectConsoleErrors, collectFailedRequests, close.
// Backend engines: chromium.js, firefox.js (Selenium WebDriver + Selenium Manager).
const { Builder, Capabilities } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const firefox = require('selenium-webdriver/firefox');

const VIEWPORTS = {
  mobile: { width: 390, height: 844 },
  tablet: { width: 768, height: 1024 },
  laptop: { width: 1280, height: 800 },
  desktop: { width: 1440, height: 900 },
};

let driver = null;
let consoleErrors = [];
let failedRequests = [];

function chromeOptions(binary) {
  const o = new chrome.Options();
  if (binary) o.setBinary(binary);
  // Preserve browser sandboxing by default. --no-sandbox removed for safety;
  // only add it if the environment requires it and the user opts in.
  o.addArguments('--headless=new', '--disable-dev-shm-usage',
    '--disable-gpu', '--window-size=1440,900');
  return o;
}

function firefoxOptions(binary) {
  const o = new firefox.Options();
  if (binary) o.setBinary(binary);
  o.addArguments('-headless');
  return o;
}

async function launchBrowser(engine = 'chromium') {
  const isFirefox = engine === 'firefox';
  const binary = process.env[isFirefox ? 'FIREFOX_BIN' : 'CHROMIUM_BIN'];
  const opts = isFirefox ? firefoxOptions(binary) : chromeOptions(binary);
  driver = await new Builder()
    .forBrowser(isFirefox ? 'firefox' : 'chrome')
    .setChromeOptions(opts)
    .setFirefoxOptions(opts)
    .build();

  // Enable browser logging so console errors can be collected on demand.
  try {
    await driver.manage().logs().getAvailableLogTypes();
  } catch (e) { /* best-effort only */ }

  return driver;
}

async function collectConsoleErrors() {
  if (!driver) return consoleErrors;
  try {
    const entries = await driver.manage().logs().get('browser');
    const now = consoleErrors.length;
    entries.forEach((e) => {
      if (e.level.value >= 900 && !consoleErrors.includes(e.message)) {
        consoleErrors.push(e.message);
      }
    });
    // Deduplicate while preserving order.
    const seen = new Set();
    const unique = [];
    for (const m of consoleErrors) {
      if (!seen.has(m)) { seen.add(m); unique.push(m); }
    }
    consoleErrors.length = 0;
    consoleErrors.push(...unique);
  } catch (e) { /* best-effort only */ }
  return consoleErrors;
}

async function goto(url) {
  if (!driver) throw new Error('Browser not launched. Call launchBrowser() first.');
  await driver.get(url);
}

async function click(selector) {
  const el = await driver.findElement({ css: selector });
  await el.click();
}

async function type(selector, text) {
  const el = await driver.findElement({ css: selector });
  await el.clear();
  await el.sendKeys(text);
}

async function submit(selector) {
  const el = await driver.findElement({ css: selector });
  await el.submit();
}

async function waitForSelector(selector, timeoutMs = 5000) {
  await driver.wait(() => driver.findElement({ css: selector }), timeoutMs);
}

async function setViewport(name) {
  const v = VIEWPORTS[name];
  if (!v) throw new Error(`Unknown viewport: ${name}`);
  await driver.manage().window().setRect({ width: v.width, height: v.height });
}

async function screenshot(name, viewport = 'desktop') {
  if (!driver) throw new Error('Browser not launched.');
  if (viewport) await setViewport(viewport);
  const base64 = await driver.takeScreenshot();
  return base64;
}

async function executeScript(script) {
  if (!driver) throw new Error('Browser not launched.');
  return await driver.executeScript(script);
}

async function collectFailedRequests() {
  if (!driver) return failedRequests;
  try {
    const entries = await driver.manage().logs().get('performance');
    entries.forEach((e) => {
      try {
        const msg = JSON.parse(e.message).message;
        const method = msg.method || '';
        const params = msg.params || {};
        if (method === 'Network.requestFailed') {
          const req = params.request || {};
          failedRequests.push({
            url: req.url,
            type: req.method,
            error: params.errorText || 'failed',
            timestamp: e.timestamp,
          });
        } else if (method === 'Network.responseReceived') {
          const res = params.response || {};
          if (res.status >= 400) {
            failedRequests.push({
              url: res.url,
              type: res.requestMethod,
              status: res.status,
              error: `HTTP ${res.status}`,
              timestamp: e.timestamp,
            });
          }
        }
      } catch (parseErr) { /* ignore unparseable performance log entries */ }
    });
    // Deduplicate by url + error.
    const seen = new Set();
    const unique = [];
    for (const r of failedRequests) {
      const key = `${r.url}|${r.error}`;
      if (!seen.has(key)) { seen.add(key); unique.push(r); }
    }
    failedRequests.length = 0;
    failedRequests.push(...unique);
  } catch (e) { /* performance logs not available */ }
  return failedRequests;
}

async function close() {
  if (driver) {
    await driver.quit();
    driver = null;
  }
}

module.exports = {
  launchBrowser, goto, click, type, submit, waitForSelector,
  screenshot, setViewport, executeScript, collectConsoleErrors, collectFailedRequests, close,
  VIEWPORTS,
};
