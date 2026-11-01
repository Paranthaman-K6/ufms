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
@ufme-implementer Implement the next approved feature slice from `.ufme/TASKS.md`.
Preserve the existing architecture and update relevant `.ufme/` artifacts.
```

```
@ufme-visual-auditor Review the latest Selenium screenshots in
`.ufme/evidence/screenshots/` and create a severity-ranked visual audit.
```

## Agent responsibilities

| Agent | Owns | Delegates from |
|-------|------|----------------|
| ufme-orchestrator (primary) | AGENT_STATE.md, TASKS.md, DECISIONS.md, plan | all |
| ufme-researcher | research notes, asset decisions | orchestrator |
| ufme-backend-analyst | API_MAP.md, BACKEND_CAPABILITIES.md, AUTHENTICATION_MAP.md, ERROR_HANDLING.md | orchestrator |
| ufme-product-analyst | PRD.md, SITEMAP.md, USER_FLOWS.md, FEATURES.md | orchestrator |
| ufme-designer | DESIGN_SYSTEM.md, wireframes, component architecture | product analyst |
| ufme-frontend-architect | ARCHITECTURE.md, folder structure, routing, state, testing strategy | designer |
| ufme-implementer | pages, components, navigation, forms, layouts | frontend architect |
| ufme-integrator | typed API client, auth flows, validation, error handling | implementer |
| ufme-visual-auditor | VISUAL_AUDIT.md, screenshot review | implementer/integrator |
| ufme-accessibility-auditor | accessibility findings | visual auditor |
| ufme-performance-auditor | performance findings | accessibility auditor |
| ufme-security-auditor | security findings | performance auditor |

## Conflict resolution

The orchestrator is the final arbiter. Disagreements are recorded in `.ufme/DECISIONS.md`
with rationale, the chosen agent's approach, and any dissenting view. The losing approach is
not implemented silently.
