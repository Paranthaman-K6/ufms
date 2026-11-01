// tests/browser/network.js
// Failed network request collection helper (best-effort via WebDriver logs).
async function collectFailedRequests(browser) {
  return browser.collectFailedRequests ? browser.collectFailedRequests() : [];
}
module.exports = { collectFailedRequests };
