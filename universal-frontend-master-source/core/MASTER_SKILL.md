# universal-frontend-master — Master Skill

OpenCode skill that transforms a project brief, existing frontend, backend repository, API
documentation, screenshot, or reference website into a complete, responsive, accessible,
performant, secure, tested, and maintainable website.

## Purpose

Autonomous frontend engineering on Arch Linux using a multi-agent architecture, native Selenium
WebDriver browser testing (Chromium + Firefox), and persistent project memory in `.ufme/`.

## Architecture

- One primary orchestrator agent (`ufme-orchestrator`).
- Multiple specialist subagents (`ufme-researcher`, `ufme-backend-analyst`,
  `ufme-product-analyst`, `ufme-designer`, `ufme-frontend-architect`, `ufme-implementer`,
  `ufme-integrator`, `ufme-visual-auditor`, `ufme-accessibility-auditor`,
  `ufme-performance-auditor`, `ufme-security-auditor`).
- Shared persistent project memory under `.ufme/`.
- Native Selenium WebDriver (Selenium Manager resolves drivers automatically).
- No containers, no Playwright, no sudo/pacman/systemctl.

## Entry point

```
@universal-frontend-master Build a complete, professional, responsive website for this project.
```

The orchestrator reads `.ufme/AGENT_STATE.md` and `.ufme/ENVIRONMENT.md`, classifies the
project, delegates to specialists, runs browser tests, audits, fixes findings, and retests
until acceptance criteria pass or limitations are documented.

## Source repository

All skill source lives in `universal-frontend-master-source/` and is installed into
`.opencode/skills/universal-frontend-master/` and `.opencode/agents/`.

## Safety

Hard-deny `sudo`, `pacman`, `systemctl`, `doas`, `pkexec`, `su`. Deny destructive `rm -rf /`
and `rm -rf ~`. Require approval for `git push`. Deny `npm publish`. See `opencode.json` and
`core/SAFETY.md`.
