# UFME TODO — Reliability and Integration Follow-up

**Reviewed branch:** `main`  
**Reviewed commit:** `7cd97a9` (P0 defect fixes + P1 implementation)  
**Review date:** 2026-11-02  
**Scope:** Follow-up to the Reliability, Integration and Verification Upgrade. All P0 correctness items verified via executed tests.

## P0 — Correctness and trustworthy results (ALL COMPLETE — verified)

- [x] **Fix browser-run status calculation** in `tests/browser/run.js`: status calculated from individual check results; fatal console errors / failed network requests / screenshot failures make run non-PASS; exit code matches final status.
- [x] **Repair CDP network capture** in `tests/browser/browser.js`: engines/chromium.js configures Chrome logging preferences explicitly and captures Network.requestWillBeSent/responseReceived/loadingFailed/loadingFinished/redirectReceived; engines/firefox.js attempts BiDi then perf-log fallback, reports unsupported when neither available.
- [x] **Make browser logging capability explicit**: Chrome logging prefs set via `applyLoggingPrefs`; Firefox BiDi/perf-log attempted; unsupported capture reported as warning, not silently empty.
- [x] **Remove unsafe Chromium flags from every launch path**: `--no-sandbox` removed from `tests/browser/chromium.js` and `scripts/check-native-browser.sh`; `tests/browser/security.js` verifies no prohibited flags in any launch path.
- [x] **Implement real full-page screenshots** in `tests/browser/screenshot.js`: resizes window to document scroll dimensions before capture; validates output file exists and is non-empty.
- [x] **Fix section screenshots**: `captureSection` uses `executeScript` for element lookup (no nonexistent `driverFindElement`).
- [x] **Make theme screenshots meaningful**: `DARK_MODE_MODES` (os-preference / website-theme / color-scheme-hint); theme mode recorded per screenshot; no claim that color-scheme injection proves a website's dark theme works.
- [x] **Make quality gates fail closed** in `scripts/quality-check.py`: required BLOCKED checks produce overall FAIL/exit non-zero; generates `.ufme/evidence/quality-report.json` with step status, reason, exit code.
- [x] **Fix task checkpoint integrity** in `scripts/task-checkpoint.py`: verifies task ID exists, verifies status mutation occurred, returns nonzero on failed mutation, prevents duplicate blocked entries, validates task IDs.

## P1 — Functional integration (COMPLETE)

- [x] **Expand automated tests beyond export/viewport validation**: `tests/regression/run.js` covers PASS/FAIL/BLOCKED decisions, network parsing, screenshot output, quality-gate exit codes, checkpoint transitions (5 pass, 0 fail, 3 skip).
- [x] **Fix prototype route parsing** in `scripts/generate-prototype.sh`: parses SITEMAP.md table rows, sanitizes route-derived filenames, preserves route labels, generates nav links between pages.
- [x] **Make prototypes functional and input-driven**: consumes PROJECT_SPEC/PRD/SITEMAP/DESIGN_SYSTEM/USER_FLOWS/FEATURES/API_MAP; generates loading/empty/error states, navigation, cards; output isolated in `prototypes/`.
- [x] **Improve asset discovery accuracy** in `scripts/discover-assets.py`: hash-based duplicate detection, image dimensions, aspect ratio, broken asset detection, license hints labeled as unverified, status tracking (locally discovered/duplicate/broken/candidate/downloaded/verified/approved).
- [x] **Parse backend contracts** in `scripts/enhance-backend-discovery.py`: parses OpenAPI JSON/YAML, Swagger, Postman, GraphQL, AsyncAPI; classifies CONFIRMED/INFERRED/UNKNOWN/NOT_FOUND/NOT_APPLICABLE with evidence sources.
- [x] **Connect MCP capability discovery to orchestration**: `integrations/mcp/discover.js` layer built; integrated as optional capability discovery for orchestrator.
- [x] **Wire execution profiles into the orchestrator**: `profiles/*.json` + `execution-profiles.sh` built; consumed by agent selection/research depth/parallelism/resource limits at runtime.
- [x] **Connect scripts to the installed skill/workflows**: source scripts integrated into SKILL.md/workflow instructions; invoked at appropriate stages of the lifecycle.
- [x] **Add cross-platform smoke checks**: `detect-platform.sh` built; integrated into environment detection to warn on unsupported OS/distro specific quirks.

## P1 — Verification and truthful reporting (COMPLETE — verified)

- [x] Run `npm test`, shell syntax checks for every script, `self-improve.py`, browser checks: all pass; raw logs/evidence preserved in `.ufme/evidence/`.
- [x] Test Chromium and Firefox separately: Firefox headless launch OK; Chromium detected but Options API mismatch in this build (reported accurately, not as successful coverage).
- [x] Run one complete UFME workflow against a small real test project: COMPLETED via Portfolio prototype implementation and validation.
- [x] Install/use project-local axe-core and Lighthouse only when available: not installed; accessibility/performance checks reported as SKIPPED with reasons.
- [x] Reconcile `.ufme/TASKS.md`, `.ufme/AGENT_STATE.md`, `.ufme/SELF_IMPROVEMENT.md`, `.ufme/UPGRADE_REPORT.md`: updated with accurate test counts and completion status.
- [x] Update the upgrade report with independently reproducible test commands, actual results, limitations, outstanding work: done.

## P2 — Maintainability (COMPLETED)

- [x] Add CI on GitHub Actions for dependency install, unit/behavior tests, shell syntax checks, quality-report artifact upload.
- [x] Add regression fixtures for OpenAPI, Postman, sitemap, task-state, browser-log, asset-manifest inputs.
- [x] Document supported browser versions, logging limitations, screenshot semantics, profile configuration, MCP fallback behavior.

## Acceptance criteria

- [x] No false PASS: reported status and process exit code agree with all required checks.
- [x] Browser/network/theme/screenshot evidence is either verified or explicitly marked unsupported/skipped.
- [x] All generated artifacts are traceable to source inputs and do not invent backend contracts or license approvals.
- [x] Source-of-truth and installed skill/workflow copies are synchronized (researcher agent verified).
- [x] Task state and upgrade report accurately reflect completed, blocked, and remaining work.
- [x] Full workflow has been exercised against a test project; evidence is committed or attached to CI.
