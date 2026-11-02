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
---

# universal-frontend-master OpenCode Skill

## Primary orchestrator instructions

At the start of every session, the primary orchestrator (`ufme-orchestrator`) must:

1. Read `.ufme/AGENT_STATE.md` and `.ufme/ENVIRONMENT.md` at session start.
2. Detect whether the project is new, frontend-only, backend-only, or full-stack.
3. Detect the existing stack and preserve its architecture (do not force a framework change
   without technical justification).
4. Delegate research, backend analysis, product analysis, design, implementation,
   integration, and audits to specialist subagents.
5. Run backend intelligence before implementing API-dependent UI.
6. Create and maintain all `.ufme/` artifacts.
7. Implement only backend capabilities confirmed by code or specifications (never invent
   endpoints, fields, roles, permissions, or responses).
8. Build real pages, reusable components, responsive layouts, forms, navigation,
   loading/error/empty states, authentication where supported, and PWA readiness where
   justified.
9. Test in native Chromium and Firefox using Selenium WebDriver (headless by default;
   Selenium Manager resolves drivers automatically).
10. Capture and inspect screenshots at mobile, tablet, laptop, and desktop viewports
    (390x844, 768x1024, 1280x800, 1440x900), dark and light themes where applicable.
11. Run visual, accessibility, performance, and security audits.
12. Fix critical and major findings, then retest.
13. Repeat until acceptance criteria pass or limitations are explicitly documented.
14. Self-improvement: after each delivery, run `scripts/self-improve.sh` to audit the skill
    itself (templates, agents, scripts, docs, OpenCode install) and apply fixes back into
    `universal-frontend-master-source/`, re-deploying changed agents and skill files.
15. Library research: before adding any web library (UI components, icons, fonts,
    animation libraries, templates), record it in `.ufme/LIBRARY_REGISTRY.md` via the
    researcher agent; only free and open-source, commercially usable assets are approved
    into `.ufme/DECISIONS.md`.

## Browser engine

Native Selenium WebDriver with JavaScript bindings, installed project-local
(`npm install -D selenium-webdriver`). Selenium Manager resolves and caches matching
Chromium and Firefox drivers automatically. Chromium is preferred; Firefox is the fallback.
No Playwright. No containers. No WebKit requirement.

## Safety

Never run `sudo`, `pacman`, `systemctl`, `doas`, `pkexec`, or `su`. Never install system
packages or modify system files. If a browser or shared library is missing, stop browser
testing, record it in `.ufme/ENVIRONMENT.md`, and prompt the user with the exact setup
command. Browser testing stays BLOCKED until the user confirms installation.

## Installed agents

- `ufme-orchestrator` (mode: primary) — `.opencode/agents/ufme-orchestrator.md`
- `ufme-researcher` (mode: subagent) — now performs web research and maintains `.ufme/LIBRARY_REGISTRY.md`
- `ufme-backend-analyst` (mode: subagent, mandatory)
- `ufme-product-analyst` (mode: subagent)
- `ufme-designer` (mode: subagent)
- `ufme-frontend-architect` (mode: subagent)
- `ufme-implementer` (mode: subagent)
- `ufme-integrator` (mode: subagent)
- `ufme-visual-auditor` (mode: subagent, mandatory)
- `ufme-accessibility-auditor` (mode: subagent)
- `ufme-performance-auditor` (mode: subagent)
- `ufme-security-auditor` (mode: subagent)

## Self-improvement

The skill improves itself after each delivery via `scripts/self-improve.sh`, which audits
all skill source files (core, agents, workflows, templates, scripts, docs, OpenCode install)
and writes `.ufme/SELF_IMPROVEMENT.md` with findings and recommendations. The orchestrator
applies fixes back into `universal-frontend-master-source/` and re-deploys changed agents and
the skill file.

## Library research

The researcher agent discovers candidate frontend libraries from the web and records them in
`.ufme/LIBRARY_REGISTRY.md` via `scripts/research-libraries.sh`. Approved free/open-source/commercially-usable assets are moved into `.ufme/DECISIONS.md` before installation (project-local npm only).

## Asset intelligence

The researcher/designer agents discover and manage project assets via
`scripts/discover-assets.sh`. Assets are recorded in `.ufme/ASSET_MANIFEST.md` with
hash-based duplicate detection, dimensions, aspect ratio, broken-asset detection, and
license hints (labeled as unverified until manually confirmed). Status tracking:
locally discovered / duplicate / broken / remotely discovered candidate / downloaded /
license verified / approved for production use.

## Backend contract discovery

The backend-analyst agent discovers and parses backend contracts via
`scripts/enhance-backend-discovery.sh`. Supported formats: OpenAPI JSON/YAML, Swagger,
Postman collections, GraphQL schemas, AsyncAPI. Extracted capabilities include methods,
paths, parameters, request/response schemas, authentication requirements, error responses,
pagination, WebSocket channels, SSE events. Every extracted capability includes an evidence
source and is classified CONFIRMED / INFERRED / UNKNOWN / NOT_FOUND / NOT_APPLICABLE.
Frontend API clients are generated ONLY from CONFIRMED capabilities.

## Execution profiles

The orchestrator selects an execution profile via
`scripts/execution-profiles.sh <lite|standard|advanced|autonomous>`. Profile configs live
in `universal-frontend-master-source/profiles/` and control: max agents, research depth,
allowed parallelism, verification depth, resource budgets, browser testing level, and
self-improvement policy. Security constraints (no sudo/pacman/systemctl/doas/pkexec/su, no
Playwright, no containers, project-local npm only, mandatory acceptance criteria) are
never bypassed by any profile.

## Task checkpoints

The orchestrator tracks task state via `scripts/task-checkpoint.sh`. Supported actions:
`list`, `status <id>`, `complete <id> [deps...]`, `blocked <id> <reason>`, `add <id> <desc>`.
A task is marked COMPLETE only after dependency completion is verified AND the state
mutation is confirmed by re-reading `.ufme/TASKS.md`. Duplicate task entries are prevented.

## Script inventory (all project-local, `bash -n` valid + executable)

| Script | Purpose |
|--------|---------|
| `scripts/detect-stack.sh` | Detects frontend/backend frameworks, build tools, styling, API specs |
| `scripts/backend-discovery.sh` | Detects backend framework (Spring Boot, Express, Django, etc.) |
| `scripts/check-native-browser.sh` | Detects Chromium/Firefox + Selenium Manager; minimal headless launch check |
| `scripts/browser-test.sh` | Runs Selenium tests against a URL; captures screenshots/console/network; writes browser-results.json |
| `scripts/screenshot.sh` | Captures full-page + section screenshots at all viewports, dark+light themes |
| `scripts/quality-check.sh` | Type check, lint, formatting, unit tests, build, browser tests, a11y, perf, dep audit; writes quality-report.json |
| `scripts/self-improve.sh` | Audits all skill source files; writes SELF_IMPROVEMENT.md |
| `scripts/research-libraries.sh` | Fetches real npm metadata for candidate UI libraries |
| `scripts/detect-platform.sh` | Detects OS/distro and reports UFME compatibility |
| `scripts/discover-assets.sh` | Discovers images/fonts/videos; duplicate detection; license hints; manifest |
| `scripts/enhance-backend-discovery.sh` | Parses backend contracts; writes BACKEND_CONTRACTS.md |
| `scripts/execution-profiles.sh` | Reads profile configs; validates and outputs profile settings |
| `scripts/generate-prototype.sh` | Generates HTML/CSS prototypes from .ufme/ memory files |
| `scripts/task-checkpoint.sh` | Dependency-aware task state transitions in TASKS.md |

## Browser abstraction (tests/browser/)

Native Selenium WebDriver abstraction with engine-specific network adapters:
- `tests/browser/browser.js` — launch/goto/click/type/submit/waitForSelector/screenshot/setViewport/executeScript/collectConsoleErrors/collectFailedRequests/getNetworkResult/close
- `tests/browser/engines/chromium.js` — Chrome performance logging + CDP network events
- `tests/browser/engines/firefox.js` — WebDriver BiDi + perf-log fallback
- `tests/browser/screenshot.js` — full-page + section screenshots with DARK_MODE_MODES
- `tests/browser/security.js` — automated test for prohibited browser flags

## Regression tests

`tests/regression/run.js` covers browser abstraction exports, viewport definitions,
prohibited-flag detection, network event schema, and quality-gate exit-code behavior.
Run with `node tests/regression/run.js` (add `--real-browser` for live browser tests).

