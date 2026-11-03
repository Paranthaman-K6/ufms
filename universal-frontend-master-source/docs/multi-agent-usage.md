# Multi-Agent Usage

## Invoke the skill

```
@universal-frontend-master Build a complete, professional, responsive website for this project.
```

## How agents collaborate

1. The primary orchestrator (`ufme-orchestrator`) reads `.ufme/AGENT_STATE.md` and
   `.ufme/ENVIRONMENT.md`.
2. It creates/updates `.ufme/TASKS.md` and delegates one coherent task at a time.
3. Each specialist subagent (`mode: subagent`) returns a structured result: status
   (`COMPLETE`/`BLOCKED`/`NEEDS_INPUT`), files, decisions, open questions, blocking deps,
   recommended next agent.
4. The orchestrator updates memory and delegates the next dependent task.
5. Parallel work only when tasks don't modify the same files. Disagreements are resolved by
   the orchestrator and recorded in `.ufme/DECISIONS.md`.

## Specialist agents

- `ufme-orchestrator` — plans, delegates, acceptance checks, project memory (primary)
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
