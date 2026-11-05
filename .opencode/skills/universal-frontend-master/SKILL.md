---
name: universal-frontend-master
description: Multi-agent frontend engineering (multi-agent) for building and improving responsive frontend websites, with execution profiles (/profile/lite|standard|advanced|autonomous) and evidence-driven auditors (a11y, perf, visual, security).
license: MIT
compatibility: opencode
metadata:
  category: frontend-engineering
  architecture: multi-agent
  scope: user
---

# universal-frontend-master

## Trigger

Use `@universal-frontend-master` when the task is building or improving a responsive website frontend — starting from a project brief, an existing repo, API documentation, a screenshot, or a reference site — or extending, redesigning, integrating, or quality-checking (visual, accessibility, performance, security) an existing frontend. It orchestrates a small multi-agent pipeline instead of a single one-shot pass.

## Hard rules

1. Never invent backend endpoints, fields, or roles. Implement only CONFIRMED capabilities from `.ufme/API_MAP.md`; anything else is INFERRED/NOT_FOUND and stays unimplemented.
2. Preserve the existing stack. No framework, build tool, or architectural change without a justified `.ufme/DECISIONS.md` entry.
3. Never run `sudo`, `pacman`, `systemctl`, `doas`, `pkexec`, or `su`; never install system packages; no Playwright, no containers; browser sandbox preserved (never `--no-sandbox`). Missing system dependency → record in `.ufme/ENVIRONMENT.md`, prompt the user, mark BLOCKED.
4. Add assets or libraries only with the license verified for commercial use and recorded in `.ufme/LIBRARY_REGISTRY.md` → `.ufme/DECISIONS.md`.
5. Evidence-first audits: read `.ufme/evidence` JSON (`a11y-results`, `perf-results`, `browser-results`, `visual-diff`) BEFORE screenshots; open screenshots only to investigate flagged sections.

## Agent router

| Need | @agent |
|------|--------|
| Start session, plan, acceptance checks, memory | `@universal-frontend-master` (entry) |
| Profile allows orchestrator (advanced/autonomous) → specialist coordination | `@ufme-orchestrator` |
| Profile without orchestrator (lite/standard) → direct specialist delegation | `@ufme-designer`, `@ufme-builder`, `@ufme-backend-analyst`, `@ufme-auditor` |
| Research, product brief, design system, critique | `@ufme-designer` |
| Backend contract discovery, API map, auth map | `@ufme-backend-analyst` |
| Build, integrate, test the UI and API layer | `@ufme-builder` |
| Audit loop — visual, a11y, perf, security from script JSON | `@ufme-auditor` |

Invoke `@universal-frontend-master` to start; it delegates according to the active profile.

## Scripts

Run scripts from `universal-frontend-master-source/scripts/`.

| Script | Purpose |
|--------|---------|
| `detect-stack.sh` | Detect existing framework, package manager, scripts, entry points |
| `detect-platform.sh` | Detect OS platform and installed browser availability |
| `backend-discovery.sh` | Locate backend contracts and source hints |
| `enhance-backend-discovery.py` | Parse OpenAPI, Postman, GraphQL, AsyncAPI into contracts |
| `search-libraries.py` | Search registry + npm for libraries with license checks |
| `discover-assets.py` | Inventory images, fonts, icons, video; hashes and duplicates |
| `generate-prototype.py` | Build a static prototype from project artifacts |
| `task-checkpoint.py` | Dependency-aware `TASKS.md` state with atomic writes |
| `browser-test.sh` | Real Selenium browser tests → `browser-results.json` |
| `screenshot.sh` | Capture browser screenshots (`--budget=viewport\|full`) |
| `page-snapshot.js` | Text-first page outline (structure, headings, landmarks) |
| `visual-diff.js` | Visual regression via pixelmatch; baseline vs compare |
| `audit-a11y.js` | axe-core accessibility audit → a11y results JSON |
| `audit-perf.sh` | Lighthouse performance audit → perf results JSON |
| `detect-slop.py` | Anti-generic design linter (templated look, uniform motion) |
| `quality-check.py` | Type check, lint, tests, build, browser, dependency audit → `quality-report.json` |
| `self-improve.py` | Audit skill source↔install sync; writes self-improve JSON |
| `ctx-pack.py` | Compose ≤1500-token per-agent briefs from project context |
| `api-query.py` | Slice `BACKEND_CONTRACTS` by endpoint, field, or role |
| `design-search.py` | Search design reference CSVs (patterns, palettes, type) |
| `execution-profiles.sh` | Read and apply execution profile settings |

## Profiles

Run any time: `/profile/lite`, `/profile/standard` (default), `/profile/advanced`, `/profile/autonomous`. Conditional chain: skip `@ufme-backend-analyst` when no backend is detected; skip `@ufme-designer` for single-page or small edit tasks; `lite` = primary + builder only (orchestrator is not available in lite).

## Anti-generic design

Motion varies with the content hierarchy — no uniform per-section fade-up, no hover animation on every card.
Avoid default-template identity: no purple→pink gradient by default, no Inter/Arial-only typography.
Reference the actual brand assets recorded in `.ufme/DECISIONS.md`; propose and record new ones when absent.

## Reference router

For details beyond this file, read `universal-frontend-master-source/<path>`:

| Topic | Path |
|-------|------|
| Architecture | `core/SYSTEM_ARCHITECTURE.md` |
| Orchestrator / agent pipeline | `core/MULTI_AGENT_ORCHESTRATION.md` |
| Core agent rules | `core/AGENT_RULES.md` |
| Safety rules | `core/SAFETY.md` |
| Quality standards | `core/QUALITY_STANDARDS.md` |
| Numbered workflows | `workflows/<NN>.md` |
| Installation | `install.sh` + `docs/installation-arch-linux.md` |
| Troubleshooting | `docs/troubleshooting.md` |
