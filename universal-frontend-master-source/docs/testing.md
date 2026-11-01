# Testing

## Browser tests (native Selenium WebDriver)
```
bash universal-frontend-master-source/scripts/browser-test.sh [URL]
```
Default URL: `http://localhost:5173`. Prefers Chromium, falls back to Firefox. Headless by
default. Captures screenshots to `.ufme/evidence/screenshots/` and writes
`.ufme/evidence/browser-results.json`.

## Screenshots
```
bash universal-frontend-master-source/scripts/screenshot.sh [URL] [screenshotDir]
```
Captures full-page + section screenshots at mobile (390x844), tablet (768x1024),
laptop (1280x800), desktop (1440x900); dark and light themes where applicable.

## Browser setup check
```
bash universal-frontend-master-source/scripts/check-native-browser.sh
```

## Full quality check
```
bash universal-frontend-master-source/scripts/quality-check.sh
```
Runs TypeScript check, lint, unit tests, production build, Selenium browser tests,
axe-core accessibility (where a browser is available), Lighthouse against a locally served
production build when possible, and dependency audit.

## Where results live
- Screenshots: `.ufme/evidence/screenshots/`
- Browser results: `.ufme/evidence/browser-results.json`
- Setup errors: `.ufme/evidence/browser-setup-error.txt`
- Visual audit: `.ufme/VISUAL_AUDIT.md`
- Audit report: `.ufme/AUDIT_REPORT.md`
