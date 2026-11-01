# UFME TODO — Reliability and Integration Follow-up

**Reviewed branch:** `main`  
**Reviewed commit:** `f948a55915efeeea025c86ac96ed21d91b86ef75`  
**Review date:** 2026-11-01  
**Scope:** Follow-up to the Reliability, Integration and Verification Upgrade. Items below are based on source inspection; tests were not executed during this review.

## P0 — Correctness and trustworthy results

- [ ] **Fix browser-run status calculation** in `tests/browser/run.js`: any configured fatal console error, failed network request, screenshot failure, or required check failure must make the run non-PASS; distinguish warnings from errors and make exit code match the final status.
- [ ] **Repair CDP network capture** in `tests/browser/browser.js`: use valid events (including `Network.loadingFailed`), enable Network domain/performance logging explicitly, correlate request/response IDs to capture request methods, and surface unsupported capture as `SKIPPED`/warning rather than silently returning an empty list.
- [ ] **Make browser logging capability explicit**: configure Chrome logging preferences/capabilities; report when browser console/network logs are unavailable. Add a documented Firefox limitation or supported BiDi implementation.
- [ ] **Remove unsafe Chromium flags from every launch path**: remove `--no-sandbox` from `tests/browser/chromium.js` and `scripts/check-native-browser.sh`; verify no other launch path disables sandboxing by default.
- [ ] **Implement real full-page screenshots** in `tests/browser/screenshot.js` (document-height capture or supported browser full-page mechanism); current helper captures viewport screenshots only.
- [ ] **Fix section screenshots**: expose a selector/element screenshot method through the browser abstraction and use it instead of the nonexistent `browser.driverFindElement`.
- [ ] **Make theme screenshots meaningful**: reset theme state between light/dark captures, trigger app-supported theme controls or document when only a color-scheme hint is applied, and verify the resulting theme before labeling evidence.
- [ ] **Make quality gates fail closed** in `scripts/quality-check.sh`: required browser checks marked BLOCKED must not produce overall PASS/exit 0; generate the promised machine-readable quality report (e.g. `.ufme/evidence/quality-report.json`) with step status, reason, and exit code.
- [ ] **Fix task checkpoint integrity** in `scripts/task-checkpoint.sh`: verify the task ID exists, verify the status mutation actually occurred, return nonzero on failed mutation, prevent duplicate blocked entries, and safely handle task IDs/arguments.

## P1 — Functional integration, not just scaffolding

- [ ] **Expand automated tests beyond export/viewport validation**: add behavior tests for PASS/FAIL/BLOCKED decisions, network parsing, screenshot output, quality-gate exit codes, and checkpoint transitions; correct the test-count claims in reports.
- [ ] **Fix prototype route parsing** in `scripts/generate-prototype.sh`: parse Markdown table rows robustly (avoid the current grep pattern that can match every line), sanitize route-derived filenames, preserve route labels, and generate valid links between pages.
- [ ] **Make prototypes functional and input-driven**: consume design tokens and PRD/sitemap/user-flow content; add realistic navigation, forms, interactive states, and responsive components rather than generic placeholder pages. Keep generated output isolated in `prototypes/`.
- [ ] **Improve asset discovery accuracy** in `scripts/discover-assets.sh`: correct duplicate detection, handle paths with spaces, exclude generated/build/runtime folders, label license results as unverified hints, and add explicit manual verification fields. Online image/video discovery remains optional and must respect provider licensing.
- [ ] **Parse backend contracts instead of only detecting filenames** in `scripts/enhance-backend-discovery.sh`: parse OpenAPI/Swagger and Postman (and supported GraphQL/AsyncAPI inputs), extract operations/schemas/auth/error details into the documented artifacts, and clearly separate verified facts from source-code hints.
- [ ] **Connect MCP capability discovery to orchestration**: implement an actual host-capability discovery/selection flow, record which MCP capabilities were available/used, define fallback behavior, and keep Selenium as the browser engine. Documentation alone is not runtime integration.
- [ ] **Wire execution profiles into the orchestrator**: make profile values structured and consumed by agent selection, research depth, parallelism, verification, and resource limits; validate unknown profile names and never bypass safety/acceptance rules.
- [ ] **Connect scripts to the installed skill/workflows**: update source and installed `SKILL.md`/workflow instructions so prototype, asset, backend-contract, profile, and checkpoint scripts are invoked at the appropriate stages.
- [ ] **Add cross-platform smoke checks** for Arch Linux (primary), Ubuntu/Debian, Fedora, WSL, and macOS; platform detection alone must not be reported as full platform support.

## P1 — Verification and truthful reporting

- [ ] Run `npm test`, shell syntax checks for every script, `self-improve.sh`, and browser checks where the environment supports them; preserve raw logs/evidence.
- [ ] Test Chromium and Firefox separately; report launch/API compatibility issues as BLOCKED or unsupported, not as successful browser coverage.
- [ ] Run one complete UFME workflow against a small real test project and record which workflows actually execute end-to-end.
- [ ] Install/use project-local axe-core and Lighthouse only when available and permitted; otherwise report accessibility/performance checks as SKIPPED with reasons.
- [ ] Reconcile `.ufme/TASKS.md`, `.ufme/AGENT_STATE.md`, `.ufme/SELF_IMPROVEMENT.md`, and `.ufme/UPGRADE_REPORT.md`. Do not mark priorities complete while task rows remain TODO or runtime integration is only documented.
- [ ] Update the upgrade report with independently reproducible test commands, actual results, limitations, and outstanding work. Do not claim tests were run unless logs/evidence exist.

## P2 — Maintainability

- [ ] Add CI on GitHub Actions for dependency install, unit/behavior tests, shell syntax checks, and quality-report artifact upload; browser jobs should clearly distinguish missing system browsers from code failures.
- [ ] Add regression fixtures for representative OpenAPI, Postman, sitemap, task-state, browser-log, and asset-manifest inputs.
- [ ] Document supported browser versions, logging limitations, screenshot semantics, profile configuration, MCP fallback behavior, and the distinction between detected, verified, and skipped capabilities.

## Acceptance criteria

- [ ] No false PASS: reported status and process exit code agree with all required checks.
- [ ] Browser/network/theme/screenshot evidence is either verified or explicitly marked unsupported/skipped.
- [ ] All generated artifacts are traceable to source inputs and do not invent backend contracts or license approvals.
- [ ] Source-of-truth and installed skill/workflow copies are synchronized.
- [ ] Task state and upgrade report accurately reflect completed, blocked, and remaining work.
- [ ] Full workflow has been exercised against a test project; evidence is committed or attached to CI.
