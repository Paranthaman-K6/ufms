// tests/browser/console.js
// Console error collection helper.
function startConsoleCapture(browser) {
  return browser.collectConsoleErrors ? browser.collectConsoleErrors() : [];
}
module.exports = { startConsoleCapture };
