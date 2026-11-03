---
name: universal-frontend-master
description: Build, extend, integrate, audit, and continuously improve complete responsive websites from a brief, repository, backend, API documentation, screenshot, or reference site. Arch Linux-aware multi-agent frontend engineering with native Selenium WebDriver browser testing, visual auditing, accessibility, performance, security, and production readiness.
license: MIT
metadata:
  category: frontend-engineering
  platform: arch-linux
  browser-engine: selenium-webdriver
  architecture: multi-agent
  workflow: autonomous-website-development
  version: "2.0"
  scope: user
---

# universal-frontend-master — Master Skill

OpenCode skill that transforms a project brief, existing frontend, backend repository, API
documentation, screenshot, or reference website into a complete, responsive, accessible,
performant, secure, tested, and maintainable website.

Installed once per user (user scope) so `@universal-frontend-master` and all sub-agents are
available in EVERY project on the machine. Cross-project data lives in `~/.config/ufme/`;
project-local artifacts live in `.ufme/`.

## Entry point

```
@universal-frontend-master Build a complete, professional, responsive website for this project.
```

`@universal-frontend-master` is the only user-facing primary agent. It delegates orchestration
to `ufme-orchestrator`, which coordinates 11 specialist subagents.

## Proper workflow (multi-agent pipeline)

Follow these phases in order; do not skip stages.

### Phase 1 — Intake (session start)

1. Read `.ufme/AGENT_STATE.md` and `.ufme/ENVIRONMENT.md`.
2. Detect whether the project is new, frontend-only, backend-only, or full-stack.
3. Detect the existing stack and preserve its architecture — no forced framework change without technical justification in `.ufme/DECISIONS.md`.
4. Set execution profile: `/profile/lite`, `/profile/standard`, `/profile/advanced`, or `/profile/autonomous` (default: `standard`).
5. Record classification and stack in `.ufme/AGENT_STATE.md`.

### Phase 2 — Research

Delegate to `@ufme-researcher`:
- Gather references, components, fonts, icons, images, videos.
- Verify licenses and commercial-use permissions.
- Record candidates in `.ufme/LIBRARY_REGISTRY.md` and the shared catalog `~/.config/ufme/LIBRARY_REGISTRY.md`.

### Phase 3 — Backend intelligence (mandatory)

Delegate to `@ufme-backend-analyst`:
- Parse OpenAPI/Swagger (JSON/YAML), Postman, GraphQL, AsyncAPI, WebSocket/SSE/auth hints.
- Produce `.ufme/API_MAP.md`, `.ufme/BACKEND_CAPABILITIES.md`, `.ufme/AUTHENTICATION_MAP.md`, `.ufme/ERROR_HANDLING.md`.
- Capabilities: CONFIRMED / INFERRED / NOT_FOUND.

### Phase 4 — Product intelligence

Delegate to `@ufme-product-analyst`:
- `.ufme/PRD.md`, `.ufme/SITEMAP.md`, `.ufme/USER_FLOWS.md`, `.ufme/FEATURES.md`.
- Map confirmed backend capabilities to frontend features; document gaps.

### Phase 5 — Design system

Delegate to `@ufme-designer`:
- `.ufme/DESIGN_SYSTEM.md` (tokens, typography, spacing, color, components).
- Record new assets in `.ufme/DECISIONS.md` before adding.

### Phase 6 — Architecture

Delegate to `@ufme-frontend-architect`:
- Folder structure, routing, state, data fetching, component boundaries, error boundaries, testing strategy.
- Preserve existing architecture unless justified.

### Phase 7 — Prototype (optional)

Run `scripts/generate-prototype.py` to build a static prototype.

### Phase 8 — Implementation

Delegate to `@ufme-implementer`:
- Pages, components, navigation, forms, state, loading/error/empty states, responsive layouts, animations, PWA readiness.
- Implement only confirmed backend capabilities.

### Phase 9 — Integration

Delegate to `@ufme-integrator`:
- Typed API clients, auth flows, authorization-aware UI, validation, error handling, retries, network failure states.

### Phase 10 — Browser execution

Real Chromium/Firefox via Selenium WebDriver at four viewports (mobile, tablet, laptop, desktop), headless by default.
- `scripts/browser-test.sh` → `browser-results.json`
- `scripts/screenshot.sh` → viewport screenshots
- No Playwright, no containers, no `--no-sandbox`.

### Phase 11 — Audits (fix and retest loop)

Run all four audits; fix critical/major findings; retest until pass or BLOCKED:

| Audit | Agent | Target |
|-------|-------|--------|
| Visual | `@ufme-visual-auditor` | Screenshots, alignment, spacing, typography, contrast, overflow |
| Accessibility | `@ufme-accessibility-auditor` | WCAG 2.1 AA, semantic HTML, landmarks, keyboard |
| Performance | `@ufme-performance-auditor` | Core Web Vitals, bundle size, Lighthouse |
| Security | `@ufme-security-auditor` | XSS, CSRF, CORS, CSP, cookies, token storage, secrets, deps |

### Phase 12 — Self-improvement

Run `scripts/self-improve.py` after each delivery. Audits source↔installed sync, script references, phantom agents, prohibited content. Writes `.ufme/evidence/self-improve-summary.json`.

### Phase 13 — Delivery

Write `.ufme/evidence/quality-report.json`. Document limitations in `.ufme/AUDIT_REPORT.md`. Clean handover.

## Execution profiles (sub-commands)

Run any time: `/profile/lite`, `/profile/standard`, `/profile/advanced`, `/profile/autonomous`.

Configs: `universal-frontend-master-source/profiles/{lite,standard,advanced,autonomous}.json`

| Profile | Use when | Max agents |
|---------|----------|------------|
| lite | Small change / quick prototype | 2 |
| standard | Normal feature work (default) | 4 |
| advanced | Production-bound delivery | 7 |
| autonomous | Unattended run | 12 |

## Installed agents

| Agent | Mode | Role |
|-------|------|------|
| `universal-frontend-master` | primary | Entry point; delegates to orchestrator |
| `ufme-orchestrator` | primary | Plans, delegates, enforces acceptance, owns memory |
| `ufme-researcher` | subagent | Research, library registry, licenses |
| `ufme-backend-analyst` | subagent (mandatory) | API map, auth map, capabilities |
| `ufme-product-analyst` | subagent | PRD, sitemap, flows, features |
| `ufme-designer` | subagent | Design system, tokens, components |
| `ufme-frontend-architect` | subagent | Architecture, routing, state, tests |
| `ufme-implementer` | subagent | Pages, components, forms, layouts |
| `ufme-integrator` | subagent | Typed API client, auth, validation |
| `ufme-visual-auditor` | subagent (mandatory) | Screenshot review |
| `ufme-accessibility-auditor` | subagent | WCAG 2.1 AA |
| `ufme-performance-auditor` | subagent | Core Web Vitals, Lighthouse |
| `ufme-security-auditor` | subagent | XSS, CSRF, CSP, secrets, deps |

## Safety model

- Deny `sudo`, `pacman`, `systemctl`, `doas`, `pkexec`, `su`.
- Deny `rm -rf /`, `rm -rf ~`; `git push` ask; `npm publish` deny.
- Project-local npm only; no Playwright, no containers.
- Browser sandbox preserved.
- Missing system dependency → `.ufme/ENVIRONMENT.md`, prompt user, mark BLOCKED.

## Cross-project data (user scope — shared across all projects)

- `~/.config/ufme/LIBRARY_REGISTRY.md` — shared library catalog
- `~/.config/ufme/evidence/` — shared evidence
- `~/.config/opencode/agents/*.md` — agent definitions
- `~/.config/opencode/skills/universal-frontend-master/SKILL.md` — skill definition
- `~/.config/opencode/commands/` — slash commands
- `~/.config/opencode/opencode.json` — agent registry + default agent

## Project-local artifacts (`.ufme/`)

Seeded on install, never overwritten: `AGENT_STATE.md`, `ENVIRONMENT.md`, `TASKS.md`,
`DECISIONS.md`, `ARCHITECTURE.md`, `DESIGN_SYSTEM.md`, `API_MAP.md`,
`AUTHENTICATION_MAP.md`, `BACKEND_CAPABILITIES.md`, `ERROR_HANDLING.md`,
`VISUAL_AUDIT.md`, `AUDIT_REPORT.md`, `LIBRARY_REGISTRY.md`, `evidence/`.

## Source of truth

`universal-frontend-master-source/` is the source of truth. Installed copies in `.opencode/`
are deployed from source and kept in sync by `scripts/self-improve.py`.
