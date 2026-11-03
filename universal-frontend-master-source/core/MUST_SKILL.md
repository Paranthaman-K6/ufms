---
name: universal-frontend-master
description: Build, extend, integrate, audit, and continuously improve complete responsive websites from a brief, repository, backend, API documentation, screenshot, or reference site. Arch Linux-aware multi-agent frontend engineering with native Selenium WebDriver browser testing, visual auditing, accessibility, performance, security, and production readiness.
license: MIT
compatibility: opencode
metadata:
  category: frontend-engineering
  platform: arch-linux
  browser-engine: selenium-webdriver
  architecture: multi-agent
  workflow: autonomous-website-development
  version: "2.0"
  scope: user
---

# universal-frontend-master — OpenCode Skill

## Primary entry point agent: `@universal-frontend-master`

Invoke this agent directly with `@universal-frontend-master` to start a frontend engineering session. It is the only user-facing primary agent; it delegates orchestration to `ufme-orchestrator`, which coordinates 4 specialist subagents.

## Proper workflow (multi-agent pipeline)

Follow this workflow in order. Do not skip stages.

### Phase 1 — Intake (session start)

1. Read `.ufme/AGENT_STATE.md` and `.ufme/ENVIRONMENT.md`.
2. Detect whether the project is new, frontend-only, backend-only, or full-stack.
3. Detect the existing stack and preserve its architecture — do not force a framework change without technical justification recorded in `.ufme/DECISIONS.md`.
4. Set execution profile: `/profile/lite`, `/profile/standard`, `/profile/advanced`, or `/profile/autonomous` (default: `standard`).
5. Record the classification and stack in `.ufme/AGENT_STATE.md`.

### Phase 2 — Research

Delegate to `@ufme-designer` (research slice):
- Gather references, components, fonts, icons, images, videos.
- Verify licenses and commercial-use permissions.
- Record candidate libraries in `.ufme/LIBRARY_REGISTRY.md`.
- Maintain the shared user-level catalog at `~/.config/ufme/LIBRARY_REGISTRY.md` (available to every project).

### Phase 3 — Backend intelligence (mandatory)

Delegate to `@ufme-backend-analyst`:
- Parse OpenAPI/Swagger (JSON/YAML), Postman, GraphQL, AsyncAPI, and source hints for WebSocket/SSE/auth.
- Produce `.ufme/API_MAP.md`, `.ufme/BACKEND_CAPABILITIES.md`, `.ufme/AUTHENTICATION_MAP.md`, `.ufme/ERROR_HANDLING.md`.
- Mark capabilities as CONFIRMED / INFERRED / NOT_FOUND.

### Phase 4 — Product intelligence

Delegate to `@ufme-designer` (product slice):
- Create `.ufme/PRD.md`, `.ufme/SITEMAP.md`, `.ufme/USER_FLOWS.md`, `.ufme/FEATURES.md`.
- Map confirmed backend capabilities to frontend features; document gaps.

### Phase 5 — Design system

Delegate to `@ufme-designer`:
- Create `.ufme/DESIGN_SYSTEM.md` (tokens, typography, spacing, color, components).
- Record any new asset (font, icon, image) in `.ufme/DECISIONS.md` before adding.

### Phase 6 — Architecture

Delegate to `@ufme-builder` (architecture slice):
- Define folder structure, routing, state management, data-fetching patterns, component boundaries, error boundaries, testing strategy.
- Preserve existing architecture unless justified.

### Phase 7 — Prototype (optional)

Run `scripts/generate-prototype.py` to build a static prototype from project artifacts.

### Phase 8 — Implementation

Delegate to `@ufme-builder` (implementation slice):
- Build pages, reusable components, navigation, forms, state, loading/error/empty states, responsive layouts, animations, PWA readiness where justified.
- Implement only backend capabilities confirmed by the backend analyst.
- Library installation is handled by the orchestrator via `scripts/search-libraries.py`.

### Phase 9 — Integration

Delegate to `@ufme-builder` (integration slice):
- Implement typed API clients, authentication flows, authorization-aware UI, validation, error handling, retries, network failure states.
- Only use endpoints confirmed by the backend analyst.

### Phase 10 — Browser execution

Run real Chromium/Firefox via Selenium WebDriver at four viewports (mobile, tablet, laptop, desktop), headless by default.
- `scripts/browser-test.sh` — run browser tests, write `browser-results.json`.
- `scripts/screenshot.sh` — capture viewport screenshots.
- No Playwright. No containers. No `--no-sandbox`.

### Phase 11 — Audits (fix and retest loop)

Run all four audits, fix critical/major findings, retest until pass or BLOCKED:

| Audit | Agent | Target |
|-------|-------|--------|
| Visual | `@ufme-auditor` | Selenium screenshots, alignment, spacing, typography, contrast, overflow |
| Accessibility | `@ufme-auditor` | WCAG 2.1 AA, semantic HTML, landmarks, headings, keyboard |
| Performance | `@ufme-auditor` | Core Web Vitals, bundle size, Lighthouse |
| Security | `@ufme-auditor` | XSS, CSRF, CORS, CSP, cookies, token storage, exposed secrets, dep audit |

### Phase 12 — Self-improvement

After each delivery run `scripts/self-improve.py` to audit:
- Source ↔ installed sync (agents, skill, scripts, docs)
- Script reference integrity (no stale `.sh` references)
- Phantom agent detection (no `@` mentions without agent files)
- Prohibited content sweep (hardcoded models, local paths, sudo/pacman/systemctl)
- Writes machine-readable JSON to `.ufme/evidence/self-improve-summary.json`

### Phase 13 — Delivery

Write quality report to `.ufme/evidence/quality-report.json`. Document limitations in `.ufme/AUDIT_REPORT.md`. Handover clean.

## Execution profiles (sub-commands)

Run any time to switch profile:

- `/profile/lite` — minimal agents, shallow research, basic verification (max 2 agents)
- `/profile/standard` — balanced for typical frontend projects (max 4 agents, default)
- `/profile/advanced` — full agents for complex projects with full audits (max 7 agents)
- `/profile/autonomous` — all specialist agents with exhaustive verification (max 12 agents)

Profiles live in `universal-frontend-master-source/profiles/{lite,standard,advanced,autonomous}.json`.

## Installed agents

| Agent | Mode | Role | Invoke with |
|-------|------|------|-------------|
| `universal-frontend-master` | primary | Primary entry point; delegates to orchestrator | `@universal-frontend-master` |
| `ufme-orchestrator` | primary | Plans, delegates, enforces acceptance, owns memory | N/A (internal) |
| `ufme-backend-analyst` | subagent (mandatory) | API map, auth map, capabilities | `@ufme-backend-analyst` |
| `ufme-designer` | subagent | Research, licenses, PRD/flows, design system | `@ufme-designer` |
| `ufme-builder` | subagent | Architecture, pages, API client, integration | `@ufme-builder` |
| `ufme-auditor` | subagent (mandatory) | Visual + a11y + perf + security audits | `@ufme-auditor` |

## Safety model

- Never run `sudo`, `pacman`, `systemctl`, `doas`, `pkexec`, or `su`.
- Never install system packages or modify system files.
- Project-local npm dependencies only.
- No Playwright, no containers, no WebKit requirement.
- Browser sandbox preserved (never `--no-sandbox`).
- Missing system dependency → record in `.ufme/ENVIRONMENT.md`, prompt user, mark BLOCKED.

## Cross-project data (user scope)

Shared across every project on the machine (never overwritten by install):

- `~/.config/ufme/LIBRARY_REGISTRY.md` — shared library catalog
- `~/.config/ufme/evidence/` — shared evidence directory
- `~/.config/opencode/agents/*.md` — agent definitions (global)
- `~/.config/opencode/skills/universal-frontend-master/SKILL.md` — skill definition (global)
- `~/.config/opencode/commands/` — slash commands (global)
- `~/.config/opencode/opencode.json` — agent registry + default agent

## Project-local artifacts

Stored in `.ufme/` per project (seeded only on install, never overwritten):

`AGENT_STATE.md`, `ENVIRONMENT.md`, `TASKS.md`, `DECISIONS.md`, `ARCHITECTURE.md`, `DESIGN_SYSTEM.md`, `API_MAP.md`, `AUTHENTICATION_MAP.md`, `BACKEND_CAPABILITIES.md`, `ERROR_HANDLING.md`, `VISUAL_AUDIT.md`, `AUDIT_REPORT.md`, `LIBRARY_REGISTRY.md`, `evidence/`.

## Source of truth

`universal-frontend-master-source/` is the source of truth. Installed copies in `.opencode/` are deployed from source and kept in sync by `scripts/self-improve.py`.
