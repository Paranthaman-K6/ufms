# Todo — UFMS (Universal Frontend Master)

Generated from `UFMS Deep Research Audit.md` (audited 3 Nov 2026, repo `Paranthaman-K6/ufms`).

Status convention: `[ ]` TODO, `[~]` IN_PROGRESS, `[x]` COMPLETE, `[!]` BLOCKED.

## Critical — broken on install (must fix first)

- [x] **1.1** `install.sh` copies `universal-frontend-master-source/browser/` into target projects; `browser-test.sh`/`screenshot.sh` reference it relative to the script.
- [x] **1.2** `install.sh` runs `npm install -D selenium-webdriver` as a project-local dev dependency (best-effort, with manual fallback hint).
- [x] **1.3** Invalid OpenCode permission keys fixed: `write`→`edit`, `subagent`→`task` in all agents + opencode.json.
- [x] **1.4** Non-standard agent frontmatter stripped: removed `inputs`, `outputs`, `role_definition`, `prohibited_actions`, `escalation_rules`, `source` from all 6 agents.

## High — correctness and drift

- [x] **2.1** Agents defined once: single source in `universal-frontend-master-source/agents/`; removed duplicate `agent` registry block from opencode.json.
- [x] **2.2** Source vs installed drift fixed: `build-agents.py` regenerates `.opencode/agents/` from source; CI workflow runs `--check`.
- [x] **2.3** Portfolio-specific rules removed from SKILL.md; replaced with anti-generic design section (motion varies by content hierarchy, no purple→pink gradients, no Inter/Arial-only identity).
- [x] **2.4** `SKILL_VALIDATION.md` template added at `universal-frontend-master-source/templates/SKILL_VALIDATION.md`; install.sh seeds it.
- [x] **2.5** Profiles enforced: `execution-profiles.sh --enforce` validates agent lists against profile maxAgents; conditional pipeline skips unnecessary agents.
- [x] **2.6** a11y/perf gates wired into quality-check.py: `audit-a11y.js` (axe-core) + `audit-perf.sh` (Lighthouse); SKIPPED/BLOCKED with actionable reasons instead of always-SKIPPED.
- [x] **2.7** `package.json` name → `universal-frontend-master`; keywords filled; Arch-Linux framing softened to "Arch-aware but runs anywhere npm does".

## Medium — security/safety gaps

- [x] **3.1** Bash deny list tightened: added `rm -rf ~/`, `rm -rf $HOME`, `rm -rf *`, `git reset --hard`, `curl | bash` to deny rules.
- [x] **3.2** `curl | bash` install supports pinned tag/checksum: `UFME_TAG` + `UFME_TARBALL_SHA256` abort on mismatch before any install.

## Scripts/programs to add (all complete)

- [x] **4.1** `page-snapshot.js` — text-first page outline via Selenium.
- [x] **4.2** Screenshot budget in `screenshot.js` — viewport-only at 390/1440 default, `--budget=full` adds more.
- [x] **4.3** `visual-diff.js` — baseline/compare with pixelmatch in `.ufme/evidence/baseline/`.
- [x] **4.4** `audit-a11y.js` — axe-core via Selenium; wired into quality-check.py.
- [x] **4.5** `audit-perf.sh` — Lighthouse CLI summarized; wired into quality-check.py.
- [x] **4.6** `detect-slop.py` — deterministic design linter; exit 2 on findings.
- [x] **4.7** `ctx-pack.py` — compact per-agent brief ≤1,500 tokens; `--archive` rotates old DECISIONS.
- [x] **4.8** `design-search.py` + `data/*.csv` — design knowledge base with BM25/TF-IDF matching.
- [x] **4.9** `api-query.py` — slices BACKEND_CONTRACTS.md by tag/path/method.
- [x] **4.10** `build-agents.py` — generates `.opencode/agents/` from source; CI drift check.

## Restructure for token efficiency (all complete)

- [x] **5.1** SKILL.md cut to 89 lines (≤150 target): trigger, 5 hard rules, agent router table, script list.
- [x] **5.2** Removed `role_definition`/`inputs`/`outputs` from frontmatter; one body per agent.
- [x] **5.3** Merged 12 agents → 6: universal-frontend-master, ufme-orchestrator, ufme-designer, ufme-backend-analyst, ufme-builder, ufme-auditor.
- [x] **5.4** Conditional pipeline: skip backend-analyst when no backend; skip designer for single-page edits; lite = orchestrator + builder + audits.
- [x] **5.5** Auditors consume JSON from scripts (a11y-results, perf-results, visual-diff) before screenshots.
- [x] **5.6** Deleted portfolio-specific rules; anti-generic design section added.
- [x] **5.7** Steer commands added: `/ufme polish`, `/ufme harden`, `/ufme critique`, `/ufme audit`.

## Suggested roadmap (all complete)

- [x] Week 1 (fix): shipped browser runtime with install; fixed permission keys; single agent-definition source + build-agents.py; seeded templates; GitHub Actions CI.
- [x] Week 2 (token cuts): page-snapshot.js, screenshot budget, ctx-pack.py, slim SKILL.md, conditional pipeline, profile enforcement.
- [x] Week 3 (quality): axe-core + Lighthouse runners, detect-slop.py, design CSV + design-search.py.
- [x] Week 4 (reach): steer commands, visual diff.

## Verification

- `self-improve.py`: PASSED (0 FAIL)
- `npm test`: 5 passed, 0 failed
