# universal-frontend-master-skill

Build, extend, integrate, audit, and continuously improve complete responsive websites from a
brief, repository, backend, API documentation, screenshot, or reference site.

Arch Linux-aware multi-agent frontend engineering with native Selenium WebDriver browser testing,
visual auditing, accessibility, performance, security, and production readiness.

## What it does

Transforms a project brief, existing frontend, backend repository, API documentation, screenshot,
or reference website into a complete, responsive, accessible, performant, secure, tested, and
maintainable website using:

- **One primary orchestrator agent** + **11 specialist subagents** (multi-agent architecture)
- **Shared persistent project memory** in `.ufme/`
- **Native Selenium WebDriver** (Chromium + Firefox), Selenium Manager, headless by default
- **Visual, accessibility, performance, and security audits** with fix-and-retest loops
- **Self-improvement loop** — the skill audits itself after each delivery
- **Design intelligence** — researches open-source UI libraries and records license/commercial-use decisions
- **Asset intelligence** — discovers and manages images, fonts, icons, videos with license tracking
- **Backend contract discovery** — parses OpenAPI, Swagger, Postman, GraphQL, AsyncAPI contracts
- **Execution profiles** — lite/standard/advanced/autonomous with enforced security constraints

## Quick start

```bash
# Clone the repo
git clone https://github.com/Paranthaman-K6/ufms.git
cd ufms

# Install project-local dependencies
npm install -D selenium-webdriver

# Verify native browser / Selenium setup
bash universal-frontend-master-source/scripts/check-native-browser.sh

# Run the skill test suite
npm test

# Run regression tests
node tests/regression/run.js

# Run quality gate
bash universal-frontend-master-source/scripts/quality-check.sh
```

## Repository layout

| Path | Purpose |
|------|---------|
| `universal-frontend-master-source/core/` | Skill, architecture, orchestration, rules, memory, quality, safety, Arch Linux docs |
| `universal-frontend-master-source/agents/` | 11 agent specifications |
| `universal-frontend-master-source/workflows/` | 14 numbered autonomous workflows |
| `universal-frontend-master-source/templates/` | 17 `.ufme/` memory templates |
| `universal-frontend-master-source/scripts/` | 14 shell scripts (stack detection, backend discovery, browser setup/test, screenshots, quality check, self-improvement, library research, platform detection, asset discovery, backend contract parsing, execution profiles, task checkpoints, prototype generation) |
| `universal-frontend-master-source/profiles/` | 4 execution profile configs (lite, standard, advanced, autonomous) |
| `universal-frontend-master-source/integrations/mcp/` | Optional MCP capability discovery layer |
| `universal-frontend-master-source/docs/` | Installation (Arch Linux), multi-agent usage, compatibility, testing, troubleshooting, MCP integration |
| `tests/browser/` | Selenium WebDriver browser abstraction (Chromium + Firefox) + engines + regression tests |
| `.opencode/agents/` | Installed OpenCode agent definitions (auto-discovered) |
| `.opencode/skills/universal-frontend-master/SKILL.md` | Installed OpenCode skill |
| `.ufme/` | Runtime project memory and evidence |
| `LICENSE` | MIT license |

## Installed OpenCode agents

| Agent | Mode | Role |
|-------|------|------|
| `ufme-orchestrator` | primary | Coordinates all work, owns memory & tasks, enforces acceptance criteria |
| `ufme-researcher` | subagent | Researches requirements, assets, licenses; maintains library registry |
| `ufme-backend-analyst` | subagent (mandatory) | Evidence-based API, auth, capability, error maps |
| `ufme-product-analyst` | subagent | PRD, sitemap, user flows, feature matrix |
| `ufme-designer` | subagent | Design system, wireframes, components |
| `ufme-frontend-architect` | subagent | Architecture, routing, state, testing strategy |
| `ufme-implementer` | subagent | Pages, components, forms, layouts |
| `ufme-integrator` | subagent | Typed API client, auth flows, validation, error handling |
| `ufme-visual-auditor` | subagent (mandatory) | Selenium screenshot review |
| `ufme-accessibility-auditor` | subagent | WCAG 2.1 AA checks |
| `ufme-performance-auditor` | subagent | Core Web Vitals, Lighthouse |
| `ufme-security-auditor` | subagent | XSS, CSRF, CORS, CSP, secrets, dependency audit |

## Safety policy

Hard-denied: `sudo`, `pacman`, `systemctl`, `doas`, `pkexec`, `su`, destructive `rm`.
Ask on: `git push`. Denied: `npm publish`. Project-local npm dependencies only. No containers,
no Playwright. Browser sandboxing preserved by default (no `--no-sandbox`). See `opencode.json`
and `universal-frontend-master-source/core/SAFETY.md`.

## Test evidence

- `npm test`: 16/16 browser abstraction validation checks pass
- All 14 shell scripts: `bash -n` syntax valid + executable
- All JS files: `node --check` valid
- `self-improve.sh`: 69 PASS / 0 FAIL
- Regression tests: 5 pass, 0 fail, 3 skipped
- Quality check: generates `.ufme/evidence/quality-report.json`
- Native Selenium (Firefox headless): OK

## License

MIT
