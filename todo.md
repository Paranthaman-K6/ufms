# Todo — UFMS Autonomous Agent Optimization

Central execution plan for examining and improving the Universal Frontend Master (UFMS) repository.

Status convention: `[ ]` TODO, `[~]` IN_PROGRESS, `[x]` COMPLETE, `[!]` BLOCKED.

---

## P0 — Core Reliability & Architecture Verification (Immediate)
- [x] **P0.1** Audit existing codebase structure, scripts, and 6-agent setup. *(Assigned: Orchestrator)*
  - Dependencies: None
  - Expected Outcome: Full inventory of current repository state.
  - Acceptance Criteria: `self-improve.py` passes (256/256 PASS, 0 FAIL) and `npm test` passes (5/5).
- [x] **P0.2** Verify user-scope installation flow and cross-project data storage (`~/.config/ufme/`). *(Assigned: Orchestrator)*
  - Dependencies: P0.1
  - Expected Outcome: `install.sh` correctly sets up global agents, skill, commands, and shared registry.
  - Acceptance Criteria: Script syntax check passes, global registry shared correctly.

## P1 — Agent Autonomy & Token Efficiency
- [ ] **P1.1** Refine agent system prompts to maximize autonomy and remove redundant instructions. *(Assigned: Orchestrator & Universal Frontend Master)*
  - Dependencies: P0.1
  - Expected Outcome: Leaner, sharper agent markdown prompts in `universal-frontend-master-source/agents/`.
  - Acceptance Criteria: `build-agents.py --check` succeeds; prompts under 3,500 chars.
- [ ] **P1.2** Optimize context packing (`ctx-pack.py`) for subagents to consume ≤1,500 token briefs. *(Assigned: Builder & Designer)*
  - Dependencies: P1.1
  - Expected Outcome: Subagents load compressed `.ufme/` summaries instead of raw memory files.
  - Acceptance Criteria: `ctx-pack.py` generates concise briefs per agent.
- [ ] **P1.3** Enforce execution profiles (`/profile/lite|standard|advanced|autonomous`) to dynamically restrict/expand agent participation. *(Assigned: Orchestrator)*
  - Dependencies: P1.1
  - Expected Outcome: `execution-profiles.sh --enforce` limits active agents and research depth per profile.
  - Acceptance Criteria: Profile enforcement test passes successfully.

## P2 — Design Intelligence & Prototype Generation
- [ ] **P2.1** Enhance design intelligence search (`design-search.py` + CSV knowledge base) for on-demand palettes, typography, and UX patterns. *(Assigned: Designer)*
  - Dependencies: P0.1
  - Expected Outcome: BM25/TF-IDF design matching provides curated design system tokens.
  - Acceptance Criteria: `design-search.py` returns relevant style/palette matches.
- [ ] **P2.2** Improve prototype generation (`generate-prototype.py`) to produce robust static HTML/CSS scaffolds from project specs. *(Assigned: Designer & Builder)*
  - Dependencies: P2.1
  - Expected Outcome: Instant visual prototypes generated before full implementation.
  - Acceptance Criteria: Prototype script runs cleanly and generates navigable index.

## P3 — Autonomous Auditing & Continuous Improvement
- [ ] **P3.1** Fully wire evidence-driven auditing (axe-core `audit-a11y.js`, Lighthouse `audit-perf.sh`, visual diffs, and slop detection) into the quality gate. *(Assigned: Auditor)*
  - Dependencies: P0.1
  - Expected Outcome: Auditors consume JSON evidence before inspecting screenshots.
  - Acceptance Criteria: `quality-check.py` executes all automated audit gates successfully.
- [ ] **P3.2** Run full end-to-end regression validation and synchronize documentation. *(Assigned: Orchestrator)*
  - Dependencies: P1.1 through P3.1
  - Expected Outcome: 100% test coverage, green CI, and fully updated README/docs.
  - Acceptance Criteria: `self-improve.py` and `npm test` both pass cleanly.
