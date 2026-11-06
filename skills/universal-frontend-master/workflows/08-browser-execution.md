# 08 — Browser Execution

## Goal
Run native Selenium WebDriver browser tests (Chromium preferred, Firefox fallback) against
the local dev server; capture screenshots and failures.

## Steps
1. Run `scripts/check-native-browser.sh` (detect Chromium/Firefox, Selenium Manager,
   minimal headless launch).
2. If browser launch fails: save error to `.ufme/evidence/browser-setup-error.txt`, prompt
   user with exact setup command, mark browser testing BLOCKED, continue non-browser work.
3. Start the local dev server.
4. Run `scripts/browser-test.sh <URL>` (default `http://localhost:5173`).
5. Capture screenshots into `.ufme/evidence/screenshots/` at mobile/tablet/laptop/desktop,
   dark + light themes.
6. Collect console errors, failed requests, broken links, interaction failures.
7. Save `.ufme/evidence/browser-results.json`.
8. Update `.ufme/TASKS.md` (T-10/T-11) and `.ufme/AGENT_STATE.md`.
9. Delegate next: visual audit.

## Output
- `.ufme/evidence/screenshots/*.png`
- `.ufme/evidence/browser-results.json`
- `.ufme/evidence/browser-setup-error.txt` (on failure)
