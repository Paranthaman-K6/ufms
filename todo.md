# Todo — UFMS Autonomous Production-Readiness Pass

Execution plan for the second autonomous improvement pass on `fix/autonomous-p0-p1-repair`
(PR #3). Status: `[ ]` TODO, `[~]` IN PROGRESS, `[x]` COMPLETE, `[!]` BLOCKED.

Every item below was verified against the working tree before being scheduled. The
previous pass's 262-check `self-improve.py` result and the green CI run `41778560645` are
treated as already-verified and are not rebuilt. This pass only fixes newly verified
defects and extends coverage.

---

## P0 — Runtime, Security, Fail-Closed Gate

- [x] **P0.1 Runtime and dependency compatibility** *(Owner: Builder)*
  - **Verified defect**: `package.json` declared no `engines`, no `.nvmrc`; CI ran Node 20 while `selenium-webdriver@4.52.0` requires `^22.23.4 || ^24.22.1 || >=26.12.1`; README claimed Node 18+.
  - **Expected result**: one declared runtime range matching every direct dependency; CI pins it; docs match.
  - **Acceptance**: `.nvmrc` inside range; `npm ci --engine-strict` exits 0; CI uses the pinned major.
  - **Evidence**: `engines` in `package.json`; `.nvmrc` = 24; `.npmrc` `engine-strict=true`; `npm ci` rc=0 and `npm ci --engine-strict` rc=0 (no `EBADENGINE`); CI `node-version: 24`; README/compatibility/ARCH_LINUX/installation docs updated.
  - **Progress**: COMPLETE.

- [x] **P0.2 Dependency security** *(Owner: Auditor)*
  - **Verified defect**: `npm audit` = 10 high / 20 moderate / 0 critical, rooted in `lighthouse@12.8.2`; the offered `lighthouse@13.6.0` still pulled 5 moderate advisories through `@sentry/node` → `glob`/`minimatch`.
  - **Expected result**: zero known vulnerabilities, or each residual one justified in docs.
  - **Acceptance**: `npm audit --audit-level=moderate` exits 0; lockfile consistent; clean `npm ci` exits 0.
  - **Evidence**: pinned exact `lighthouse@13.5.0` → `npm audit` "found 0 vulnerabilities", rc=0; `npm ci` from the lock rc=0; rationale recorded in `compatibility.md`.
  - **Progress**: COMPLETE.

- [x] **P0.3 Fail-closed quality gate** *(Owner: Builder + Auditor)*
  - **Verified defect**: `quality-check.py` let a required audit check SKIP into overall PASS; a11y/perf/slop/visual PASS was recorded without validating that result JSON existed, was fresh and had the expected fields; visual baseline auto-creation was recorded as PASS.
  - **Expected result**: missing/invalid/skipped evidence for a required check can never yield PASS.
  - **Acceptance**: tests cover required-SKIPPED→BLOCKED, invalid a11y/perf/slop/visual evidence→FAIL, baseline-created→BLOCKED, valid evidence→PASS; existing tests still pass.
  - **Evidence**: `python3 tests/quality/run.py` → 18 passed, 0 failed (9 pre-existing + 9 new). Gate now requires `--require`/`UFME_REQUIRE_CHECKS` ⊆ `--only`, auto-requires a11y/perf/slop/visual for the audit preset, reads per-check result paths from `UFME_*` envs, rejects stale evidence, and emits `required`/`requiredNotPassed` in the report.
  - **Progress**: COMPLETE.

- [x] **P0.4 Complete visual regression** *(Owner: Builder)*
  - **Verified defect**: `visual-diff.js` detected a current image without a baseline but not a baseline image with no current capture.
  - **Expected result**: changed, missing-baseline, missing-current and size-mismatch images are all detected; first-run baseline is not success.
  - **Acceptance**: new visual test for baseline-only image; existing tests still pass.
  - **Evidence**: `node tests/visual/run.js` → 10 passed, 0 failed, including "a baseline image with no current capture FAILs".
  - **Progress**: COMPLETE.

## P1 — Automation, Portability, Agent Consistency

- [x] **P1.1 End-to-end CI quality validation** *(Owner: Auditor)*
  - **Verified defect**: CI ran unit suites and a browser smoke test but never ran `quality-check.py` against the served prototype.
  - **Expected result**: CI executes real audit checks on the generated prototype.
  - **Acceptance**: workflow runs the audit preset with required checks against a live server; local reproduction documented; YAML valid.
  - **Evidence**: `.github/workflows/ufme-ci.yml` merged browser + audit step (generate → serve → browser test → seed baseline → `--only audit --require audit`); YAML parses; the same command locally returned **Overall: PASS** on real Chromium 156 with 0 axe violations, Lighthouse 100/100/96, 0 slop findings and 0 visual diff.
  - **Progress**: COMPLETE.

- [x] **P1.2 Evidence directory and portable shell** *(Owner: Builder)*
  - **Verified defect**: `audit-a11y.js`, `audit-perf.sh`, `browser-test.sh` hardcoded `.ufme/evidence`; `audit-perf.sh`, `browser-test.sh`, `detect-platform.sh` used GNU-only `date -Iseconds`; `install.sh` used `sha256sum` and bash-4 `${var,,}`; `find -print -quit` is not BSD-portable.
  - **Expected result**: `UFME_EVIDENCE_DIR` honored everywhere; checksums and timestamps work on GNU and BSD/macOS; no bash-4-only syntax.
  - **Acceptance**: scripts write under an overridden evidence dir; `bash -n` clean; install test exercises a `sha256` fallback with a `shasum`/`openssl`-only PATH.
  - **Evidence**: real run wrote browser/a11y/perf/slop/visual evidence under `/tmp/opencode/e2e-*` with `UFME_EVIDENCE_DIR`; `bash -n` clean for all touched shell scripts; install test "sha256 falls back to openssl without sha256sum/shasum" PASS; timestamps use POSIX `date -u +...`.
  - **Progress**: COMPLETE.

- [x] **P1.3 Installer installs the full audit dependency set** *(Owner: Builder)*
  - **Verified defect**: `install.sh` installed only `selenium-webdriver`, so axe/Lighthouse/pixelmatch audits SKIPPED after a fresh install.
  - **Expected result**: a project with `package.json` receives all runtime audit dependencies.
  - **Acceptance**: install test with a stub `npm` asserts every required package is passed to `npm install -D`.
  - **Evidence**: `bash tests/install/run.sh` → 34 passed, 0 failed, including "npm receives selenium-webdriver @axe-core/webdriverjs lighthouse pngjs pixelmatch".
  - **Progress**: COMPLETE.

- [x] **P1.4 Profiles are data-driven and contradictions removed** *(Owner: Orchestrator + Designer)*
  - **Verified defect**: `execution-profiles.sh` hardcoded allowed agent sets; `designer.md` set `bash: deny` while instructing the agent to run `scripts/search-libraries.py`.
  - **Expected result**: each profile JSON owns its `allowedAgents`, enforcement reads it, and agent instructions match declared permissions.
  - **Acceptance**: profile test proves a JSON-only change alters enforcement; `build-agents.py --check` passes; no agent instructs a denied tool.
  - **Evidence**: `allowedAgents` added to all four profiles; enforcement reads it (with `UFME_PROFILES_DIR` override and a non-empty check); `python3 tests/profiles/run.py` → 16 passed, 0 failed including "allowedAgents comes from profile JSON"; designer now asks the orchestrator to run the script; `build-agents.py --check` → "in sync".
  - **Progress**: COMPLETE.

- [x] **P1.5 Context efficiency measurement** *(Owner: Orchestrator)*
  - **Verified defect**: `ctx-pack.py` reported packed size but never quantified avoided raw context.
  - **Expected result**: every brief states raw artifact tokens, packed tokens and saved percentage.
  - **Acceptance**: new context test asserts the savings fields; budgets still hold.
  - **Evidence**: `python3 tests/context/run.py` → 12 passed, 0 failed including "packed size is measured against raw artifact tokens"; footer carries `Raw artifacts / packed / saved %`.
  - **Progress**: COMPLETE.

- [x] **P1.6 Documentation synchronization** *(Owner: Universal Frontend Master)*
  - **Verified defect**: README said Node 18+; docs lacked the supported range, fail-closed semantics, visual baseline policy, profile data source and install dependency set.
  - **Acceptance**: docs match implemented behavior; no stale version or topology claims.
  - **Evidence**: README, `compatibility.md`, `troubleshooting.md`, `installation-arch-linux.md`, `ARCH_LINUX.md` updated and reviewed against code.
  - **Progress**: COMPLETE.

## P2 — Final Validation and Delivery

- [x] **P2.1 Full local validation** *(Owner: Auditor)*
  - **Acceptance**: `npm test` exit 0; `build-agents.py --check` in sync; `self-improve.py` 0 FAIL; real browser + audit run produce evidence.
  - **Evidence**: `npm test` rc=0 (visual 10, agents 9, quality 18, profiles 16, context 12, auditor 9, install 34); `build-agents.py --check` "in sync"; `self-improve.py` 262 PASS / 0 FAIL; real Chromium browser run PASS; audit preset PASS (see P1.1).
  - **Progress**: COMPLETE.

- [x] **P2.2 Commit, push, CI green, report** *(Owner: Universal Frontend Master)*
  - **Acceptance**: commit pushed to `fix/autonomous-p0-p1-repair`; PR updated; CI success; final report distinguishes PASS / FAIL / SKIPPED / BLOCKED.
  - **Evidence**: commits `4f497827` and `fbbc1579` pushed; PR #4 opened (PR #3 was already merged); CI run `41803694415` green with the audit step reporting **PASS: 4, FAIL: 0, SKIPPED: 0, BLOCKED: 0 — Overall: PASS** (axe 0 violations, Lighthouse 100/100/96, slop 0, visual 0). The first run `41803217583` honestly reported **BLOCKED** on a skipped Lighthouse check; the fix added `UFME_CHROME_FLAGS` for runner Chromium instead of masking the skip.
  - **Progress**: COMPLETE.

---

## Verified and intentionally skipped (already working)

- Six-agent topology (one primary + orchestrator subagent) — `tests/agents/run.py` (9 PASS).
- Quality report atomic writes, timing, browser PASS/FAIL/BLOCKED/timeout — `tests/quality/run.py`.
- Context budget enforcement and DECISIONS rotation — `tests/context/run.py`.
- Seed-memory preservation, repeat-install merging, missing-source failure — `tests/install/run.sh`.
- Browser abstraction and security flag checks — `tests/browser/*`.
- Full 262-check `self-improve.py` sweep.

## Honest limitations

- The CI visual baseline is seeded from the current build in the same run, so CI validates
  the mechanics (baseline vs. current, pixelmatch, gate wiring), not cross-run pixel drift.
  Cross-run regression needs a committed `.ufme/evidence/baseline` in the consuming project.
- Lighthouse thresholds default to 0 (report scores, no hard minimum) unless
  `UFME_PERF_MIN_SCORE` is set; the gate still fails on invalid evidence.
- The untracked local fixture `prototypes/Portfolio Prototype/` has 2 slop findings; it is
  gitignored and absent from CI checkouts, so it does not affect the gate.
