---
name: ufmw-frontend-design
description: Arch Linux-native multi-agent frontend engineering skill for building responsive websites with reference-driven design, visual auditing, accessibility, performance, security, and production readiness.
license: MIT
compatibility: opencode
metadata:
  category: frontend-engineering
  architecture: multi-agent
  scope: user
  depends_on: []
---

# ufmw-frontend-design

## Trigger

Use `@ufmw-frontend-design` when the task is building or improving a responsive website frontend — starting from a project brief, an existing repo, API documentation, a screenshot, or a reference site — or extending, redesigning, integrating, or quality-checking (visual, accessibility, performance, security) an existing frontend. Supports reference-driven design: users can provide website URLs as design references, identify individual UI elements they like, and specify where those elements should be implemented.

## Hard Rules

1. Never invent backend endpoints, fields, or roles. Implement only CONFIRMED capabilities from `.ufme/API_MAP.md`; anything else is INFERRED/NOT_FOUND and stays unimplemented.
2. Preserve the existing stack. No framework, build tool, or architectural change without a justified `.ufme/DECISIONS.md` entry.
3. Never run `sudo`, `pacman`, `systemctl`, `doas`, `pkexec`, or `su`; never install system packages; no Playwright, no containers; browser sandbox preserved (never `--no-sandbox`). Missing system dependency → record in `.ufme/ENVIRONMENT.md`, prompt the user, mark BLOCKED.
4. Add assets or libraries only with the license verified for commercial use and recorded in `.ufme/LIBRARY_REGISTRY.md` → `.ufme/DECISIONS.md`.
5. Evidence-first audits: read `.ufme/evidence` JSON (`a11y-results`, `perf-results`, `browser-results`, `visual-diff`) BEFORE screenshots; open screenshots only to investigate flagged sections.

## Agent Router

| Need | @agent |
|------|--------|
| Start session, plan, acceptance checks, memory | `@ufmw-frontend-design` (entry) |
| Profile allows orchestrator (advanced/autonomous) → specialist coordination | `@ufmw-orchestrator` |
| Profile without orchestrator (lite/standard) → direct specialist delegation | `@ufmw-designer`, `@ufmw-builder`, `@ufmw-backend-analyst`, `@ufmw-auditor` |
| Research, product brief, design system, critique | `@ufmw-designer` |
| Backend contract discovery, API map, auth map | `@ufmw-backend-analyst` |
| Build, integrate, test the UI and API layer | `@ufmw-builder` |
| Audit loop — visual, a11y, perf, security, reference-implementation verification | `@ufmw-auditor` |
| Reference-driven design — crawl, analyze, match, adapt, verify UI elements | `@ufmw-designer` + `@ufmw-builder` + `@ufmw-auditor` |

Invoke `@ufmw-frontend-design` to start; it delegates according to the active profile.

## Scripts

Run scripts from `skills/ufmw-frontend-design/scripts/`.

| Script | Purpose |
|--------|---------|
| `detect-stack.sh` | Detect existing framework, package manager, scripts, entry points |
| `detect-platform.sh` | Detect OS platform and installed browser availability |
| `backend-discovery.sh` | Locate backend contracts and source hints |
| `enhance-backend-discovery.py` | Parse OpenAPI, Swagger, Postman, GraphQL, AsyncAPI into contracts |
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
| `theme-showcase.py` | Render every curated theme (palette + type) as a page in `.ufme/theme-showcase.pdf` |
| `execution-profiles.sh` | Read and apply execution profile settings |
| `reference-inspect.js` | Selenium-based reference website element inspector |
| `reference-analyze.py` | Analyze inspected reference elements |
| `reference-match.py` | Match reference elements to target project locations |
| `reference-adapt.py` | Adapt reference elements to target design system |
| `reference-verify.js` | Verify reference implementation against target URL |
| `element-catalog.py` | Maintain persistent catalog of reference elements |

## Profiles

Run any time: `/profile/lite`, `/profile/standard` (default), `/profile/advanced`, `/profile/autonomous`. Conditional chain: skip `@ufmw-backend-analyst` when no backend is detected; skip `@ufmw-designer` for single-page or small edit tasks; `lite` = primary + builder only (orchestrator is not available in lite).

## CLI Commands (ufmw/)

| Command | Purpose |
|---------|---------|
| `ufmw init` | Initialize reference-driven design project |
| `ufmw design reference add <url>` | Add website URL as design reference |
| `ufmw design reference analyze` | Analyze references, extract UI elements |
| `ufmw design reference list` | List all references and elements |
| `ufmw design reference inspect <id>` | Inspect specific element's DOM and styles |
| `ufmw design plan` | Generate implementation plan for adapting references |
| `ufmw design implement` | Implement adapted elements in target project |
| `ufmw design verify <url> [refUrl]` | Verify implementation against reference intent |
| `ufmw build` | Build complete website |
| `ufmw audit [url]` | Quality audit (a11y, perf, visual, security) |
| `ufmw report` | Generate final report |

## Anti-Generic Design

Motion varies with the content hierarchy — no uniform per-section fade-up, no hover animation on every card. Avoid default-template identity: no purple→pink gradient by default, no Inter/Arial-only typography. Reference the actual brand assets recorded in `.ufme/DECISIONS.md`; propose and record new ones when absent.

## Compatibility

This skill complements `skills/ufmw-seo-protocol`. Both skills share the `.ufme/` project memory directory and the `ufmw/` CLI command namespace. The design skill provides browser automation, quality gate, and agent infrastructure that the SEO skill depends on.
