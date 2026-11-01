# universal-frontend-master-skill

Build, extend, integrate, audit, and continuously improve complete responsive websites from a
brief, repository, backend, API documentation, screenshot, or reference site. Arch Linux-aware
multi-agent frontend engineering with native Selenium WebDriver browser testing, visual
auditing, accessibility, performance, security, and production readiness.

## What it does

Transforms a project brief, existing frontend, backend repository, API documentation,
screenshot, or reference website into a complete, responsive, accessible, performant, secure,
tested, and maintainable website using:

- One primary orchestrator agent + 11 specialist subagents
- Shared persistent project memory in `.ufme/`
- Native Selenium WebDriver (Chromium + Firefox), Selenium Manager, headless by default
- Visual, accessibility, performance, and security audits with fix-and-retest loops

## Quick start

```
@universal-frontend-master Build a complete, professional, responsive website for this project.
```

## Install

```
npm install -D selenium-webdriver
bash universal-frontend-master-source/scripts/check-native-browser.sh
```

## Repository layout

- `universal-frontend-master-source/core/` — skill, architecture, orchestration, rules,
  memory, quality, safety, Arch Linux docs
- `universal-frontend-master-source/agents/` — 11 agent specs
- `universal-frontend-master-source/workflows/` — 14 numbered workflows
- `universal-frontend-master-source/templates/` — 17 `.ufme/` templates
- `universal-frontend-master-source/scripts/` — detect-stack, backend-discovery,
  check-native-browser, browser-test, screenshot, quality-check
- `universal-frontend-master-source/docs/` — installation-arch-linux, multi-agent-usage,
  compatibility, testing, troubleshooting
- `universal-frontend-master-source/examples/` — from-scratch, existing-backend,
  complex-landing-page
- `.opencode/skills/universal-frontend-master/SKILL.md` — installed OpenCode skill
- `.opencode/agents/` — discovered OpenCode agents
- `tests/browser/` — Selenium WebDriver browser abstraction
- `.ufme/` — runtime project memory and evidence

## Safety

Hard-deny: `sudo`, `pacman`, `systemctl`, `doas`, `pkexec`, `su`, destructive `rm`.
Ask on: `git push`. Deny: `npm publish`. See `opencode.json` and `core/SAFETY.md`.

## License

MIT
