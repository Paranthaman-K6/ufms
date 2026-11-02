// tests/browser/browser.js
// Native Selenium WebDriver browser abstraction.
// Exposes: launchBrowser, goto, click, type, submit, waitForSelector,
// screenshot, collectConsoleErrors, collectFailedRequests, close.
// Backend engines: tests/browser/engines/chromium.js, tests/browser/engines/firefox.js
const chrome = require('selenium-webdriver/chrome');
const firefox = require('selenium-webdriver/firefox');
const chromiumEngine = require('./engines/chromium');
const firefoxEngine = require('./engines/firefox');

const VIEWPORTS = {
  mobile: { width: 390, height: 844 },
  tablet: { width: 768, height: 1024 },
  laptop: { width: 1280, height: 800 },
  desktop: { width: 1440, height: 900 },
};

let driver = null;
let consoleErrors = [];
let networkResult = { events: [], httpErrors: [], networkFailures: [], total: 0, hasErrors: false };
let engine = null; // 'chromium' | 'firefox'

function chromeOptions(binary) {
  const o = new chrome.Options();
  if (binary) o.setBinary(binary);
  // Preserve Chromium sandboxing by default. --no-sandbox intentionally omitted.
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

async function launchBrowser(engineName = 'chromium') {
  const isFirefox = engineName === 'firefox';
  const binary = process.env[isFirefox ? 'FIREFOX_BIN' : 'CHROMIUM_BIN'];

  if (isFirefox) {
    driver = await firefoxEngine.launchFirefoxWithNetwork(binary);
  } else {
    driver = await chromiumEngine.launchChromiumWithNetwork(binary);
  }
  engine = engineName;

  // Enable browser logging so console errors can be collected on demand.
  try {
    await driver.manage().logs().getAvailableLogTypes();
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

async function executeScript(script) {
  if (!driver) throw new Error('Browser not launched.');
  return await driver.executeScript(script);
}

async function collectConsoleErrors() {
  if (!driver) return consoleErrors;
  try {
    const entries = await driver.manage().logs().get('browser');
    entries.forEach((e) => {
      if (e.level.value >= 900 && !consoleErrors.includes(e.message)) {
        consoleErrors.push(e.message);
      }
    });
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

async function collectFailedRequests() {
  if (!driver) return networkResult.networkFailures;
  try {
    if (engine === 'chromium') {
      networkResult = await chromiumEngine.collectEvents(driver);
    } else if (engine === 'firefox') {
      networkResult = await firefoxEngine.collectEvents(driver);
    }
  } catch (e) {
    // Network collection failed; keep previous result.
  }
  return networkResult.networkFailures;
}

async function getNetworkResult() {
  return networkResult;
}

async function validateLinks() {
  if (!driver) throw new Error('Browser not launched.');
  const links = await driver.findElements({ css: 'a' });
  const brokenLinks = [];
  for (const link of links) {
    const href = await link.getAttribute('href');
    if (!href) continue;
  
      const id = href.substring(1);
      const element = await driver.findElements({ css: `#${id}` });
      if (element.length === 0) {
        brokenLinks.push({ href, type: 'broken-anchor' });
      }
    }
    // External links are checked via collectFailedRequests (4xx/5xx)
  }
  return brokenLinks;
}

module.exports = {
  launchBrowser, goto, click, type, submit, waitForSelector,
  screenshot, setViewport, executeScript, collectConsoleErrors,
  collectFailedRequests, getNetworkResult, close, validateLinks,
  VIEWPORTS,
};
