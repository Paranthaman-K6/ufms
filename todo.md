# Todo — UFMS Autonomous P0/P1 Repair & Optimization

Central execution plan for UFMS autonomous agent optimization, reliability hardening, profile enforcement, and evidence-driven auditing.

Status convention: `[ ]` TODO, `[~]` IN_PROGRESS, `[x]` COMPLETE, `[!]` BLOCKED.

**Audit note (2026-11-04):** the previous revision marked every item `[x]` without evidence. A direct inspection of `main` found real gaps (orchestrator mode, profile enforcement breadth, slop/visual/audit thresholds, context-pack integration, install tests). Statuses below reflect verified evidence only.

**Verification note (2026-11-04):** all suites below were run on `fix/autonomous-p0-p1-repair` after the repairs. `npm test` exited 0; `self-improve.py` reported 262 PASS / 0 FAIL; a real Chromium Selenium run against the generated prototype returned PASS.

---

## P0 — Critical Reliability

- [x] **P0.1 Agent Orchestration** *(Assigned: Universal Frontend Master & Orchestrator)*
  - **Dependencies**: None
  - **Gap found**: `ufme-orchestrator` was `mode: primary` (two primary entry agents); docs still said "11 specialist agents"; no structural validation of agent references.
  - **Repair**: `universal-frontend-master` is the only primary; `ufme-orchestrator` is `mode: subagent`; all six agents rebuilt from `universal-frontend-master-source/agents/`; `build-agents.py` validates exactly one primary, orchestrator mode, permission keys and every referenced script.
  - **Acceptance Criteria**: `build-agents.py --check` passes; exactly one primary agent; orchestrator mode `subagent`; `opencode debug agents` lists all 6; delegation smoke test passes.
  - **Evidence**: `python3 tests/agents/run.py` → 9 passed, 0 failed; `build-agents.py --check` → `check: in sync`; clean-config `opencode debug agents` resolves all six.
  - **Tests**: `python3 tests/agents/run.py`.

- [x] **P0.2 Quality-Check Runtime** *(Assigned: Builder)*
  - **Dependencies**: P0.1
  - **Gap found**: startup indentation defect was fixed, but there was no integration test for browser PASS/FAIL/BLOCKED/timeout, no per-check timing, incomplete report metadata, and BLOCKED was folded into FAIL.
  - **Repair**: `quality-check.py` gained `--only`, `--target`, `--report`, flag/env thresholds, per-check `startedAt`/`durationMs`, atomic report writes, and status precedence `FAIL > BLOCKED > PASS`.
  - **Acceptance Criteria**: Python compile passes; integration harness exercises browser PASS/FAIL/BLOCKED/timeout; report counts match checks; atomic write verified.
  - **Evidence**: `python3 tests/quality/run.py` → 9 passed, 0 failed.
  - **Tests**: `python3 tests/quality/run.py`.

- [x] **P0.3 Regression Protection** *(Assigned: Auditor)*
  - **Dependencies**: P0.1, P0.2
  - **Repair**: new hermetic suites for agents, quality gate, profiles, context, visual diff, auditor contract and install; wired into `npm test` and CI; CI uses `npm ci`, waits for the prototype server, and no longer swallows browser failures with `|| true`.
  - **Acceptance Criteria**: `npm test` includes the new suites; CI runs them from a clean install.
  - **Evidence**: `npm test` → exit 0; suite totals: visual 9, agents 9, quality 9, profiles 15, context 11, auditor 9, install 27, all 0 failed.
  - **Tests**: `npm test`; `.github/workflows/ufme-ci.yml`.

---

## P1 — Agent Autonomy and Optimization

- [x] **P1.1 Genuine Execution-Profile Enforcement** *(Assigned: Orchestrator)*
  - **Dependencies**: P0.1
  - **Gap found**: `execution-profiles.sh --enforce` only checked a worst-case count; research depth, parallelism, verification depth, browser level and self-improvement settings were printed but never applied or recorded.
  - **Repair**: enforcement validates ceilings (Lite 2 / Standard 4 / Advanced 7 / Autonomous 12), allowed sets, duplicates, parallelism, research/verification/browser depth; records `.ufme/evidence/profile-enforcement.json`; `UFME_EVIDENCE_DIR` keeps tests hermetic.
  - **Acceptance Criteria**: all four profiles pass within limits; exceeding any limit exits non-zero; Lite skips optional stages; Autonomous enables exhaustive verification.
  - **Evidence**: `python3 tests/profiles/run.py` → 15 passed, 0 failed.
  - **Tests**: `python3 tests/profiles/run.py`.

- [x] **P1.2 Complete Automated Auditing** *(Assigned: Auditor)*
  - **Dependencies**: P0.2
  - **Gap found**: `quality-check.py` ran axe/Lighthouse but not `detect-slop.py`; no visual-diff implementation existed; Lighthouse scores were never thresholded; audit evidence was not fully recorded per check.
  - **Repair**: added `visual-diff.js` (pngjs + pixelmatch, baseline creation, per-image ratio, size/unreadable handling, atomic JSON); the gate now runs slop + visual + a11y + perf + browser + deps with configurable thresholds and PASS/FAIL/SKIPPED/BLOCKED semantics.
  - **Acceptance Criteria**: each enabled audit produces valid evidence; missing deps are SKIPPED; browser failures BLOCKED; real violations FAIL; visual baseline/identical/modified/threshold cases pass.
  - **Evidence**: `node tests/visual/run.js` → 9 passed, 0 failed; `python3 tests/quality/run.py` → 9 passed; real `bash browser-test.sh http://localhost:5173` → `Selenium run: PASS (chromium)`.
  - **Tests**: `python3 tests/quality/run.py`; `node tests/visual/run.js`.

- [x] **P1.3 Task-Aware Token-Efficient Context** *(Assigned: Builder & Designer)*
  - **Dependencies**: P0.1
  - **Gap found**: `ctx-pack.py` existed but the orchestrator never called it; missing artifacts were skipped silently; the auditor did not receive compact a11y/perf/browser/visual evidence.
  - **Repair**: the orchestrator runs `ctx-pack.py --task` before delegation; packs use tiktoken `cl100k_base` when available (chars/4 fallback), fair-share budgets, a hard final ceiling, explicit missing/truncated/skipped footer, summarized evidence JSON and `--archive` rotation.
  - **Acceptance Criteria**: all five specialist roles pack correctly at 500 and 1,500 tokens; evidence summaries present; orchestrator prompt invokes `ctx-pack.py --task`.
  - **Evidence**: `python3 tests/context/run.py` → 11 passed, 0 failed.
  - **Tests**: `python3 tests/context/run.py`.

- [x] **P1.4 Auditor Permissions and Reporting** *(Assigned: Auditor)*
  - **Dependencies**: P1.2
  - **Gap found**: auditor had `edit: deny` but its prompt said it writes `.ufme/AUDIT_REPORT.md`; referenced tool paths were not validated.
  - **Repair**: auditor is `subagent` with `read/bash: allow`, `edit/task: deny`; it returns a severity-ranked report (source/severity/location/finding/recommendation/retest) for orchestrator synthesis; all six evidence files and every referenced script are validated.
  - **Acceptance Criteria**: permissions valid; documented commands exist; report structure verified from fixture evidence.
  - **Evidence**: `python3 tests/auditor/run.py` → 9 passed, 0 failed.
  - **Tests**: `python3 tests/auditor/run.py`.

- [x] **P1.5 Installation and Documentation Integrity** *(Assigned: Orchestrator)*
  - **Dependencies**: P0.1 through P1.4
  - **Gap found**: no clean-install test; install wrote a stale inline "agent registry" and could not install from a local source for offline/CI testing; README/architecture still described a primary orchestrator.
  - **Repair**: `install.sh` supports `UFME_SOURCE_DIR` and `UFME_SKIP_NPM`, merges the global config without an inline `agent` block, preserves user keys, and merges repeat installs instead of nesting; README, architecture, MUST_SKILL and installation docs now describe one primary and five subagents.
  - **Acceptance Criteria**: clean install + repeat install pass; source/install sync clean; no broken script/agent references; shell syntax valid.
  - **Evidence**: `bash tests/install/run.sh` → 27 passed, 0 failed; `self-improve.py` → 262 PASS / 0 FAIL; `build-agents.py --check` → in sync.
  - **Tests**: `bash tests/install/run.sh`; `python3 universal-frontend-master-source/scripts/self-improve.py`.

---

## Verification evidence (2026-11-04)

| Command | Result | Evidence |
|---------|--------|----------|
| `build-agents.py --check` | PASS — in sync, one primary, orchestrator subagent | `.ufme/evidence/agents-test.json` |
| `python3 tests/agents/run.py` | 9 passed, 0 failed | `.ufme/evidence/agents-test.json` |
| `python3 tests/quality/run.py` | 9 passed, 0 failed | `.ufme/evidence/quality-test.json` |
| `python3 tests/profiles/run.py` | 15 passed, 0 failed | `.ufme/evidence/profiles-test.json` |
| `python3 tests/context/run.py` | 11 passed, 0 failed | `.ufme/evidence/context-test.json` |
| `node tests/visual/run.js` | 9 passed, 0 failed | `.ufme/evidence/visual-test.json` |
| `bash tests/install/run.sh` | 27 passed, 0 failed | `.ufme/evidence/install-test.json` |
| `python3 tests/auditor/run.py` | 9 passed, 0 failed | `.ufme/evidence/auditor-test.json` |
| `npm test` | exit 0 — all suites in one command | `/tmp/opencode/npm-test2.log` |
| `self-improve.py` | 262 PASS, 0 FAIL | `.ufme/evidence/self-improve-summary.json` |
| `npm run test:browser -- http://localhost:5173` | PASS (Chromium, real Selenium run) | `.ufme/evidence/browser-results.json` |

## Remaining limitations

- Real browser audit checks require a locally installed Chromium/Firefox; without one they report `BLOCKED`, never a fake pass.
- Lighthouse and axe thresholds default to permissive values (`minPerfScore=0`, `maxA11yViolations=0`) and are set per project via flags/`UFME_*` env vars.
- The autonomous profile's 12-slot ceiling allows parallel subagents, but the current OpenCode setup runs one model session at a time; enforcement validates the declared set rather than spawning 12 live sessions.
- Live model-to-model delegation is not exercised in CI; agent contracts are tested structurally and through the real deterministic scripts.

## Verification commands

```bash
python3 universal-frontend-master-source/scripts/build-agents.py --check
python3 universal-frontend-master-source/scripts/self-improve.py
npm test
python3 tests/quality/run.py
python3 tests/profiles/run.py
python3 tests/context/run.py
python3 tests/agents/run.py
python3 tests/auditor/run.py
node tests/visual/run.js
bash tests/install/run.sh
npm run test:browser -- http://localhost:5173
```
