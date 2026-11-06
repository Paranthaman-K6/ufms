# Multi-Agent Usage

## Invoke the skill

```
@universal-frontend-master Build a complete, professional, responsive website for this project.
```

## How agents collaborate

1. The primary entry agent (`universal-frontend-master`) reads `.ufme/AGENT_STATE.md` and
   `.ufme/ENVIRONMENT.md`, then resolves the active execution profile (`lite`, `standard`,
   `advanced`, or `autonomous`).
2. It enforces the profile via `execution-profiles.sh --enforce`, which validates the
   proposed delegation against `allowedAgents` and `maxConcurrentDelegates`.
3. If the profile allows `ufme-orchestrator` (advanced, autonomous), the primary delegates
   planning and specialist coordination to the orchestrator. Otherwise (lite, standard) the
   primary delegates directly to the first permitted specialist.
4. Each specialist subagent returns a structured result: status (`COMPLETE`/`BLOCKED`/`NEEDS_INPUT`),
   files, decisions, open questions, blocking deps, recommended next agent.
5. The orchestrator (when active) updates memory and delegates the next dependent task.
6. Parallel work only when tasks don't modify the same files. Disagreements are resolved by
   the orchestrator and recorded in `.ufme/DECISIONS.md`.

## Specialist agents

- `ufme-orchestrator` — plans, delegates, acceptance checks, project memory (subagent)
- `ufme-designer` — research, PRD, sitemap, flows, design system, critique
- `ufme-backend-analyst` — API/auth/capability/error maps (stdlib contracts; not mandatory when no backend is detected)
- `ufme-builder` — architecture, pages, components, typed API client, integration
- `ufme-auditor` — visual, accessibility, performance, security audits from evidence JSON

## Example delegation

```
@ufme-backend-analyst Analyze this backend and create evidence-based API, authentication,
capability, and error maps in `.ufme/`. Do not invent endpoints or fields.
```

## Project memory

All agents read/write `.ufme/` artifacts: PROJECT_SPEC.md, PRD.md, FEATURES.md, API_MAP.md,
BACKEND_CAPABILITIES.md, AUTHENTICATION_MAP.md, ERROR_HANDLING.md, DESIGN_SYSTEM.md, SITEMAP.md,
USER_FLOWS.md, ARCHITECTURE.md, TASKS.md, DECISIONS.md, TEST_PLAN.md, VISUAL_AUDIT.md,
AUDIT_REPORT.md, AGENT_STATE.md, ENVIRONMENT.md, DEPLOYMENT.md.
