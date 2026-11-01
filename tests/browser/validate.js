// tests/browser/validate.js
// Validates the Selenium browser abstraction module loads and exports the
// required API surface. Runs without launching a browser (safe in CI).
'use strict';

const browser = require('./browser');

const REQUIRED = [
  'launchBrowser', 'goto', 'click', 'type', 'submit', 'waitForSelector',
  'screenshot', 'setViewport', 'executeScript', 'collectConsoleErrors', 'collectFailedRequests',
  'close', 'VIEWPORTS',
];

let failures = 0;

for (const name of REQUIRED) {
  if (typeof browser[name] === 'function' || (name === 'VIEWPORTS' && browser[name])) {
    console.log(`PASS: exports.${name}`);
  } else {
    console.error(`FAIL: missing export ${name}`);
    failures += 1;
  }
}

const expectedViewports = ['mobile', 'tablet', 'laptop', 'desktop'];
for (const vp of expectedViewports) {
  if (browser.VIEWPORTS[vp] && browser.VIEWPORTS[vp].width && browser.VIEWPORTS[vp].height) {
    console.log(`PASS: viewport ${vp} = ${browser.VIEWPORTS[vp].width}x${browser.VIEWPORTS[vp].height}`);
  } else {
    console.error(`FAIL: invalid viewport ${vp}`);
    failures += 1;
  }
}

if (failures > 0) {
  console.error(`\n${failures} validation check(s) failed`);
  process.exit(1);
}
console.log('\nAll browser abstraction validation checks passed.');
process.exit(0);
