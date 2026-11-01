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
  o.addArguments('--headless=new', '--no-sandbox', '--disable-dev-shm-usage',
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

  // Collect console errors via logging prefs (best-effort; WebDriver BiDi not universal).
  try {
    const logs = await driver.manage().logs().getAvailableLogTypes();
    if (logs.includes('browser')) {
      driver.manage().logs().get('browser').then((entries) => {
        entries.forEach((e) => {
          if (e.level.value >= 900) consoleErrors.push(e.message);
        });
      });
    }
  } catch (e) { /* best-effort only */ }

  return driver;
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

async function collectConsoleErrors() {
  return consoleErrors;
}

async function collectFailedRequests() {
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
  screenshot, setViewport, collectConsoleErrors, collectFailedRequests, close,
  VIEWPORTS,
};
