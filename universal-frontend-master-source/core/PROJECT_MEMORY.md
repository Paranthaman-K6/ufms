# Project Memory

Persistent shared memory lives in `.ufme/`. Every agent reads and updates the artifacts it
owns. The orchestrator owns `AGENT_STATE.md`, `TASKS.md`, and `DECISIONS.md`.

## Required artifacts

| Artifact | Owner | Purpose |
|----------|-------|---------|
| PROJECT_SPEC.md | orchestrator | Project brief, source, constraints |
| PRD.md | product analyst | Product requirements, acceptance criteria |
| FEATURES.md | product analyst | Feature matrix mapped to backend capabilities |
| API_MAP.md | backend-analyst | Method, path, purpose, auth, request, response, errors, frontend use, evidence |
| BACKEND_CAPABILITIES.md | backend-analyst | CONFIRMED / INFERRED / MISSING_BACKEND / NOT_APPLICABLE / DO_NOT_BUILD |
| AUTHENTICATION_MAP.md | backend-analyst | Auth flows, roles, permissions, token storage |
| ERROR_HANDLING.md | backend-analyst | Error codes, frontend mapping, user-facing messages |
| DESIGN_SYSTEM.md | designer | Tokens, typography, spacing, color, components, responsive rules |
| SITEMAP.md | product analyst | Page hierarchy and routes |
| USER_FLOWS.md | product analyst | Key user journeys |
| ARCHITECTURE.md | frontend-architect | Folder structure, routing, state, data fetch, testing strategy |
| TASKS.md | orchestrator | Task list with statuses |
| DECISIONS.md | orchestrator | Dependency/license/asset decisions, conflict resolutions |
| TEST_PLAN.md | frontend-architect | Unit, integration, browser, audit tests |
| VISUAL_AUDIT.md | visual-auditor | Severity-ranked visual issues (ID, Page, Viewport, Screenshot, Severity, Issue, Cause, Fix, Owner, Status, Retest evidence) |
| AUDIT_REPORT.md | orchestrator | Aggregated audit results |
| AGENT_STATE.md | orchestrator | Current agent, status, last delegation |
| ENVIRONMENT.md | orchestrator | Host, toolchain, browsers, Selenium status, missing deps |
| DEPLOYMENT.md | orchestrator | Build output, deploy target, environment variables |

## Update protocol

Each agent appends a timestamped note to the artifacts it touches and updates `AGENT_STATE.md`
with its status before returning control to the orchestrator.
