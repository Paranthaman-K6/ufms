// tests/browser/firefox.js
// Firefox-specific launch using Selenium WebDriver + Selenium Manager.
const { Builder } = require('selenium-webdriver');
const firefox = require('selenium-webdriver/firefox');

async function launchFirefox(binary) {
  const o = new firefox.Options();
  if (binary) o.setBinary(binary);
  o.addArguments('-headless');
  return await new Builder()
    .forBrowser('firefox')
    .setFirefoxOptions(o)
    .build();
}

module.exports = { launchFirefox };
