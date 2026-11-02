// tests/browser/security.js
// Automated test: detects prohibited default browser security-disabling flags
// in all Selenium launch paths. Runs without launching a browser.
//
// Prohibited flags: --no-sandbox, --disable-web-security, --ignore-certificate-errors
// These weaken browser security and must never be default options.
'use strict';

const fs = require('fs');
const path = require('path');

const PROHIBITED_FLAGS = [
  '--no-sandbox',
  '--disable-web-security',
  '--ignore-certificate-errors',
];

const LAUNCH_FILES = [
  'tests/browser/browser.js',
  'tests/browser/engines/chromium.js',
  'tests/browser/engines/firefox.js',
  'universal-frontend-master-source/scripts/check-native-browser.sh',
];

let failures = 0;

for (const file of LAUNCH_FILES) {
  if (!fs.existsSync(file)) {
    console.error(`FAIL: launch file not found: ${file}`);
    failures += 1;
    continue;
  }
  const content = fs.readFileSync(file, 'utf8');
  const lines = content.split('\n');
  for (let i = 0; i < lines.length; i++) {
    for (const flag of PROHIBITED_FLAGS) {
      if (lines[i].includes(flag)) {
        // Allow comments that explicitly explain why a flag is NOT used
        const trimmed = lines[i].trim();
        if (trimmed.startsWith('//') || trimmed.startsWith('#') || trimmed.startsWith('*')) {
          continue;
        }
        console.error(`FAIL: ${file}:${i + 1} contains prohibited flag "${flag}"`);
        console.error(`  ${lines[i].trim()}`);
        failures += 1;
      }
    }
  }
}

if (failures > 0) {
  console.error(`\n${failures} prohibited browser flag(s) found`);
  process.exit(1);
}
console.log('PASS: No prohibited browser security-disabling flags found in launch paths');
process.exit(0);
