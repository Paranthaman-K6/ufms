# Todo — UFMS Autonomous Production Hardening (pass 3)

Branch `fix/autonomous-p0-p1-repair` rebased onto `origin/main` (`3220d96b`, PR #4 merged).
Status: `[ ]` TODO, `[~]` IN PROGRESS, `[x]` COMPLETE, `[!]` BLOCKED.
Every `[x]` must carry executable evidence below it.

Independent findings from this pass (not copied from prior reports):

- Profiles: lite excludes the builder (cannot implement); standard excludes backend-analyst and auditor (cannot integrate or audit); `maxAgents` mixes the always-on primary with delegates; autonomous advertises 12 concurrent agents but only 5 delegate roles exist.
- Screenshots: `encodeImage()` passes the PNG via an IIFE with no arguments, so canvas encoding always fails and silently falls back to PNG; the documented JPEG budget is dead code. Meanwhile `visual-diff.js` only reads PNG, so fixing the encoder alone would break comparison.
- Visual gate: a missing baseline is auto-created during ordinary validation; `--update-baseline` silently overwrites the baseline; no expected-dimension check; no page-state/viewport manifest.
- CI seeds the visual baseline from the same build it then compares, which cannot detect a regression introduced by that build.
- Lighthouse failures (browser launch, crash, invalid report) are all reported as SKIPPED, so a broken audit looks like a missing dependency; best-practices is not required or range-checked.
- Browser: `browser/run.js` writes status `FAILED` while the contract is `FAIL`; the selected browser and its version are not verified against the driver that actually ran. `check-native-browser.sh` probes Python Selenium (not the project's Node stack), so it reports "NOT TESTED/NOT WORKING" even when Node Selenium works, and ignores `UFME_EVIDENCE_DIR`.
- `browser-test.sh` records BLOCKED when the target URL does not respond (server problem, not an unsupported environment).
- CI uses `actions/checkout@v4`/`setup-node@v4` (Node 20 deprecation warnings) and uploads no evidence or diagnostic artifacts; it does not enforce profiles, installer behavior, or dependency security.
- No uninstall path is documented, and install/upgrade behavior is only covered by the installer test, not by CI.

---

## P0 — Profiles

- [x] **P0.1 Redesign profile schema and enforcement** *(Owner: Orchestrator)*
  - **Evidence**: `python3 tests/profiles/run.py` → 31 PASS. All four profiles (lite/standard/advanced/autonomous) rewritten with `primaryAgent`/`allowedAgents`/`maxConcurrentDelegates`; `--enforce` accepts designed delegation, rejects unknown/duplicate roles, rejects missing primary, enforces delegate concurrency and parallelism semantics, writes `profile-enforcement.json`.
  - **Values**: lite=1 delegate, standard=2, advanced=4, autonomous=5 (= real delegate role count; no phantom 12).

- [x] **P0.2 Align orchestrator, skill docs and commands with the schema**
  - **Evidence**: `tests/agents/run.py` → 9 PASS; `build-agents.py --check` in sync; core docs (MUST_SKILL.md, MASTER_SKILL.md, MULTI_AGENT_ORCHESTRATION.md, agents/orchestrator.md, agents/universal-frontend-master.md, README.md) rewritten; no doc references `maxAgents` or ceilings 2/4/7/12.

## P0 — Visual regression

- [x] **P0.3 Baseline lifecycle is explicit and safe**
  - **Evidence**: `node tests/visual/run.js` → 25 PASS. Missing baseline → `BASELINE_MISSING` exit 4 (nothing written); `--create-baseline` creates only when absent, refuses existing baseline exit 2; `--update-baseline` explicit, reports `BASELINE_UPDATED`, removes stale baseline files; ordinary runs never modify baseline (content hash asserted in tests).

- [x] **P0.4 Detect all regression classes + expected dimensions**
  - **Evidence**: `node tests/visual/run.js` → 25 PASS covering unchanged, changed, missing-baseline, missing-current, size-mismatch, unreadable, plus manifest `missing-screenshot`, `unexpected-screenshot`, `dimension-mismatch`, `manifest-invalid`. One test per class; manifest width/height mismatch fails.

- [x] **P0.5 Screenshots must be valid comparison inputs**
  - **Evidence**: Real browser run `browser-run.js` → `browser-base.json`/`browser-head.json` status PASS, Chromium 156.0.8078.79, 4 screenshots captured, manifest written with actual width/height/viewport/theme. `node tests/visual/run.js` → 25 PASS (pngjs-decodable PNGs, manifest matches pixels).

- [x] **P0.6 Real cross-commit comparison in CI**
  - **Evidence**: `tests/visual/cross-commit.js` → 4 PASS (two real git commits; base-vs-head FAIL on change, base/base and head/head PASS). Real local run: base(origin/main) vs HEAD → visual-diff.json PASS, maxDiffRatio=0, 4 images unchanged. CI step added to `.github/workflows/ufme-ci.yml`.

## P0 — Lighthouse and gate evidence

- [x] **P0.7 Separate failure classes and validate every score**
  - **Evidence**: `python3 tests/quality/run.py` → 21 PASS (incl. 8 perf cases: SKIPPED 5 / BLOCKED 6 / FAIL 4 / contradicting exit-status / valid all-three PASS / missing best-practices / below threshold / unreachable URL). `bash tests/perf/run.sh` → 9 PASS (missing dep → SKIPPED 5, no browser → BLOCKED 6, browser failure → FAIL 4 kind=browser, crash → FAIL 4 kind=audit, invalid JSON → FAIL 4, missing score → FAIL 4, out-of-range → FAIL 4, valid RAN 0 three scores, missing URL → exit 2).
  - Real Lighthouse run against local prototype: performance=100, accessibility=100, bestPractices=96, status=RAN, exit 0.

## P0 — Browser consistency

- [x] **P0.8 One browser truth**
  - **Evidence**: Real browser run → `status: PASS`, `browser: chromium`, `session: {engine: chromium, browserName: chrome, browserVersion: 156.0.8078.79, platformName: linux}`; capture aborts after navigation failure; `check-native-browser.sh` → READY (Chromium 156.0.8078.79), writes `browser-setup.json`, honors `UFME_EVIDENCE_DIR`, no "NOT TESTED" claims. `browser-test.sh` → URL unreachable records `status: FAIL`. `UFME_CHROME_FLAGS`/`UFME_FIREFOX_FLAGS` supported by engines + setup probe.

## P0 — CI completeness and retention

- [x] **P0.9 Integrated CI + artifacts + supported actions**
  - **Evidence**: `.github/workflows/ufme-ci.yml` rewritten: `actions/checkout@v5`, `setup-node@v5`, `upload-artifact@v4 if: always()`, fetch-depth: 0, profile enforcement (all four), installer/uninstaller smoke test, `npm audit --audit-level=high`, cross-commit visual capture from `origin/main` via worktree, full audit preset with `UFME_CHROME_FLAGS="--headless=new --no-sandbox --disable-dev-shm-usage"`, Lighthouse gate with `UFME_LH_MIN_SCORE: "80"`.
  - Local validation: `npm test` → 198 PASS / 0 FAIL; `self-improve.py` → 262 PASS / 0 FAIL; real browser + Lighthouse + cross-commit all pass.

## P1 — Whole-system review fixes

- [x] **P1.1 Uninstall/upgrade path documented and tested**
  - **Evidence**: New `uninstall.sh` (idempotent, `--project-only`/`--global-only`, removes only managed agents/skill/commands/source tree, preserves `.ufme/`, `opencode.json`, `package.json`). `tests/uninstall/run.sh` → 21 PASS (install→uninstall, removals verified, user files preserved, repeat uninstall, `--project-only`). README documents uninstall. `install.sh` now copies slash commands globally and project-locally.

- [x] **P1.2 Context/token efficiency measured on real memory**
  - **Evidence**: ran `ctx-pack.py` for all five agents against real `.ufme/` memory and compared pack size vs. the loose `.md`/JSON files each agent would otherwise read:
    - orchestrator: 9121B → 4800B (47.4% saved)
    - builder: 7162B → 3567B (50.2% saved)
    - auditor: 3570B → 1030B (71.1% saved)
    - designer: 3860B → 4103B (−6.3%, pack header overhead dominates tiny 2-file scope)
    - backend-analyst: 1252B → 1822B (−45.5%, overhead dominates tiny 4-file scope)
    - **TOTAL: 24965B → 15322B = 9643B (38.6%) saved**
  - Honest finding: packs shrink byte-count for every agent that reads ≥4 files; for tiny 2–4 file scopes the fixed pack header (tokenizer, missing-artifacts, truncation notes) can exceed savings. Real-world `.ufme/` directories with larger DECISIONS.md and more evidence save more. Packs always stay ≤1500-token budget and state tokenizer/truncation.

- [x] **P1.3 Docs match behavior** (profiles, visual lifecycle, Lighthouse statuses, CI)
  - **Evidence**: README updated (uninstall section, test scripts list incl. `test:uninstall`/`test:perf`/`test:visual-cross`, explicit baseline lifecycle, sandbox opt-in via UFME_CHROME_FLAGS). Installation docs updated with commands install + uninstall subsection.

- [x] **P1.4 Independent review pass** (fresh eyes over the diff; fix what it finds)
  - **Evidence**: re-read `audit-perf.sh`, `visual-diff.js`, `quality-check.py` visual gate, `install.sh`/`uninstall.sh`, `cross-commit.js`, CI workflow. Found and fixed 2 bugs before CI: (1) CI invoked `advanced` with `--parallel` and 5 delegates but `maxConcurrentDelegates=4` → removed `--parallel` from advanced (sequential delegation uses full allowed set); (2) CI passed a results-file positional arg to `audit-a11y.js`, which doesn't accept one (it reads `UFME_EVIDENCE_DIR` env) → removed the arg. All local suites green.

## P2 — Final validation and delivery

- [x] **P2.1 Full local suite**, `self-improve.py`, real browser + audit + cross-commit
  - **Evidence**: `npm test` → 198 PASS / 0 FAIL (rc=0). `self-improve.py` → 262 PASS / 0 FAIL. Real browser run (Chromium 156.0.8078.79) → PASS on base and HEAD. Real Lighthouse → performance=100 / accessibility=100 / bestPractices=96 / status=RAN / exit 0. Real cross-commit visual diff → PASS, maxDiffRatio=0.

- [x] **P2.2 Commit, push, PR #5, green CI on the final commit, final report.**
  - **Evidence**: PR #5 opened (https://github.com/Paranthaman-K6/ufms/pull/5). Final commit `898b8312` pushed; CI `UFME CI` = **success** (1m37s) on the final commit. Local validation before push: `npm test` 198 PASS/0 FAIL, `self-improve.py` 262 PASS/0 FAIL, `npm audit` clean, real browser + Lighthouse + cross-commit all pass.

## Verified and intentionally unchanged

- Six-agent topology (one primary + five specialists) and installed/source parity.
- Fail-closed quality gate core (required-SKIPPED → BLOCKED, stale/invalid → FAIL).
- Install portability (sha256 fallbacks, POSIX dates), repeat-install memory preservation.
- ctx-pack budget enforcement and DECISIONS rotation.
- Security: Selenium-only, no Playwright/containers/sudo, `npm audit` clean (0 vulnerabilities).
