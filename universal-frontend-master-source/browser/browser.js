// universal-frontend-master-source/browser/browser.js
// Native Selenium WebDriver browser abstraction.
// Engine-specific launch and network capture live in browser/engines/.
'use strict';

const chromiumEngine = require('./engines/chromium');
const firefoxEngine = require('./engines/firefox');
const { VIEWPORTS } = require('./viewport');

let driver = null;
let engineName = null;
let consoleErrors = [];
let consoleSupported = false;
let networkResult = {
  events: [], httpErrors: [], networkFailures: [], total: 0, hasErrors: false, supported: false,
};

async function launchBrowser(name = 'chromium') {
  const isFirefox = name === 'firefox';
  const binary = process.env[isFirefox ? 'FIREFOX_BIN' : 'CHROMIUM_BIN'];

  driver = isFirefox
    ? await firefoxEngine.launchFirefoxWithNetwork(binary)
    : await chromiumEngine.launchChromiumWithNetwork(binary);
  engineName = name;

  // Console capture needs the 'browser' log type; not every engine exposes it.
  try {
    const types = await driver.manage().logs().getAvailableLogTypes();
    consoleSupported = types.includes('browser');
  } catch (e) {
    consoleSupported = false;
  }
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

async function setWindowSize(width, height) {
  if (!driver) throw new Error('Browser not launched.');
  await driver.manage().window().setRect({ width: Math.round(width), height: Math.round(height) });
}

async function screenshot(name, viewport) {
  if (!driver) throw new Error('Browser not launched.');
  if (viewport) await setViewport(viewport);
  return await driver.takeScreenshot();
}

async function screenshotElement(selector) {
  if (!driver) throw new Error('Browser not launched.');
  const el = await driver.findElement({ css: selector });
  return await el.takeScreenshot();
}

async function executeScript(script, ...args) {
  if (!driver) throw new Error('Browser not launched.');
  return await driver.executeScript(script, ...args);
}

async function collectConsoleErrors() {
  if (!driver || !consoleSupported) return consoleErrors;
  try {
    const entries = await driver.manage().logs().get('browser');
    for (const e of entries) {
      if (e.level.value >= 900 && !consoleErrors.includes(e.message)) {
        consoleErrors.push(e.message);
      }
    }
  } catch (e) { /* best-effort only */ }
  return consoleErrors;
}

async function collectFailedRequests() {
  if (!driver) return networkResult.networkFailures;
  try {
    networkResult = engineName === 'firefox'
      ? await firefoxEngine.collectEvents(driver)
      : await chromiumEngine.collectEvents(driver);
  } catch (e) {
    networkResult = { ...networkResult, supported: false };
  }
  return networkResult.networkFailures;
}

async function getNetworkResult() {
  await collectFailedRequests();
  return networkResult;
}

async function validateLinks() {
  if (!driver) throw new Error('Browser not launched.');
  const hrefs = await driver.executeScript(
    () => Array.from(document.querySelectorAll('a[href]')).map((a) => a.getAttribute('href'))
  );
  const brokenLinks = [];
  for (const href of hrefs) {
    if (!href || !href.startsWith('#') || href === '#') continue;
    const found = await driver.executeScript((id) => !!document.getElementById(id), href.slice(1));
    if (!found) brokenLinks.push({ href, type: 'broken-anchor' });
  }
  return brokenLinks;
}

async function close() {
  if (driver) {
    try { await driver.quit(); } finally { driver = null; engineName = null; }
  }
  consoleErrors = [];
  consoleSupported = false;
  networkResult = {
    events: [], httpErrors: [], networkFailures: [], total: 0, hasErrors: false, supported: false,
  };
}

function isConsoleSupported() {
  return consoleSupported;
}

module.exports = {
  launchBrowser, goto, click, type, submit, waitForSelector,
  screenshot, setViewport, setWindowSize, executeScript, collectConsoleErrors,
  collectFailedRequests, getNetworkResult, validateLinks, isConsoleSupported,
  close, screenshotElement, VIEWPORTS,
};
