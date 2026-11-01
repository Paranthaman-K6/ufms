// tests/browser/chromium.js
// Chromium-specific launch using Selenium WebDriver + Selenium Manager.
const { Builder } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

async function launchChromium(binary) {
  const o = new chrome.Options();
  if (binary) o.setBinary(binary);
  o.addArguments('--headless=new', '--no-sandbox', '--disable-dev-shm-usage',
    '--disable-gpu', '--window-size=1440,900');
  return await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(o)
    .build();
}

module.exports = { launchChromium };
