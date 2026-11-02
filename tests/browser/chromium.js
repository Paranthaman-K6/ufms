// tests/browser/chromium.js
// Chromium-specific launch using Selenium WebDriver + Selenium Manager.
const { Builder } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

async function launchChromium(binary) {
  const o = new chrome.Options();
  if (binary) o.setBinary(binary);
  // Preserve Chromium sandboxing by default. --no-sandbox is intentionally omitted;
  // it weakens browser security and should only be added if the environment requires it.
  o.addArguments('--headless=new', '--disable-dev-shm-usage',
    '--disable-gpu', '--window-size=1440,900');
  return await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(o)
    .build();
}

module.exports = { launchChromium };
