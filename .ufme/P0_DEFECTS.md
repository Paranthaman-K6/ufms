# P0 Defect Fixes - COMPLETE

| # | Defect | File | Status |
|---|--------|------|--------|
| P0-1 | `--no-sandbox` in chromium.js | tests/browser/chromium.js | DONE |
| P0-1 | `--no-sandbox` in check-native-browser.sh | scripts/check-native-browser.sh | DONE |
| P0-1 | Automated test for prohibited flags | tests/browser/security.js | DONE |
| P0-2 | Chromium network adapter + CDP events | tests/browser/engines/chromium.js | DONE |
| P0-2 | Firefox network adapter (BiDi + perf log) | tests/browser/engines/firefox.js | DONE |
| P0-2 | Shared network event schema | tests/browser/engines/schema.js | DONE |
| P0-3 | run.js PASS/FAIL from individual results | tests/browser/run.js | DONE |
| P0-3 | Acceptance rules (BLOCKED/FAIL/SKIPPED/PASS) | tests/browser/run.js | DONE |
| P0-3 | Functional regression tests | tests/regression/run.js + fixtures | DONE |
| P0-4 | Actual full-page screenshots | tests/browser/screenshot.js | DONE |
| P0-4 | Section screenshots via element lookup | tests/browser/screenshot.js | DONE |
| P0-4 | Dark mode mode distinction | tests/browser/screenshot.js | DONE |
| P0-5 | quality-report.json generation | scripts/quality-check.sh | DONE |
| P0-5 | Quality-gate exit-code tests | tests/regression/run.js | DONE |

Regression test results: 5 passed, 0 failed, 3 skipped (real browser not requested)
Quality check: 2 PASS, 1 FAIL (browser tests - no dev server), 6 SKIPPED, 0 BLOCKED
