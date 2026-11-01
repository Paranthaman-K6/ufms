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
- `ufme-researcher` (mode: subagent)
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
