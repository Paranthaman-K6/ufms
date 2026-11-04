# Multi-Agent Orchestration

## Collaboration model

1. Orchestrator reads `.ufme/AGENT_STATE.md`.
2. Orchestrator creates or updates `.ufme/TASKS.md`.
3. Orchestrator delegates one coherent task at a time to a specialist subagent.
4. Specialist returns a structured result:
   - Status: `COMPLETE`, `BLOCKED`, or `NEEDS_INPUT`
   - Files created or updated
   - Decisions made
   - Open questions
   - Blocking dependencies
   - Recommended next agent
5. Orchestrator updates `.ufme/AGENT_STATE.md` and `.ufme/TASKS.md`.
6. Orchestrator delegates the next dependent task.
7. Parallel work is allowed only when tasks do not modify the same files.
8. If two agents disagree, the orchestrator resolves the conflict and records the decision in
   `.ufme/DECISIONS.md`.

## Delegation examples

```
@ufme-backend-analyst Analyze this backend and create evidence-based API, authentication,
capability, and error maps in `.ufme/`. Do not invent endpoints or fields.
```

```
@ufme-designer Using `.ufme/PRD.md` and `.ufme/API_MAP.md`, create the design system,
sitemap, user flows, responsive rules, and component architecture.
```

```
@ufme-builder Implement the next approved feature slice from `.ufme/TASKS.md`.
Preserve the existing architecture and update relevant `.ufme/` artifacts.
```

```
@ufme-auditor Review the latest Selenium screenshots in
`.ufme/evidence/screenshots/` and create a severity-ranked visual audit.
```

## Agent responsibilities

| Agent | Owns | Delegates from |
|-------|------|----------------|
| ufme-orchestrator (subagent) | AGENT_STATE.md, TASKS.md, DECISIONS.md, plan | all |
| ufme-backend-analyst | API_MAP.md, BACKEND_CAPABILITIES.md, AUTHENTICATION_MAP.md, ERROR_HANDLING.md | orchestrator |
| ufme-designer | LIBRARY_REGISTRY.md, PRD.md, SITEMAP.md, USER_FLOWS.md, FEATURES.md, DESIGN_SYSTEM.md, research notes, wireframes, component architecture | orchestrator |
| ufme-builder | ARCHITECTURE.md, pages, components, navigation, forms, layouts, typed API client, auth flows, validation, error handling | designer/backend-analyst |
| ufme-auditor | AUDIT_REPORT.md (visual, accessibility, performance, security findings) | builder |

## Execution profiles

The orchestrator selects an execution profile via
`scripts/execution-profiles.sh <lite|standard|advanced|autonomous>`. Profile configs live in
`universal-frontend-master-source/profiles/` and control max agents, research depth, allowed
parallelism, verification depth, resource budgets, browser testing level, and self-improvement
policy. Security constraints (no sudo/pacman/systemctl/doas/pkexec/su, no Playwright, no
containers, project-local npm only, mandatory acceptance criteria) are never bypassed by any
profile.

## Task checkpoints

Task state is managed via `scripts/task-checkpoint.py` with dependency-aware transitions:
- `list` — show all tasks
- `status <id>` — show task status
- `complete <id> [deps...]` — mark complete only after dependencies verified and mutation confirmed
- `blocked <id> <reason>` — mark blocked with reason
- `add <id> <desc>` — add a new task

A task is never marked COMPLETE unless dependency completion is verified and the state change
is confirmed by re-reading `.ufme/TASKS.md`.

## Conflict resolution

The orchestrator is the final arbiter. Disagreements are recorded in `.ufme/DECISIONS.md`
with rationale, the chosen agent's approach, and any dissenting view. The losing approach is
not implemented silently.
