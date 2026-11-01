# Agent Rules

## General rules (all agents)

1. Read `.ufme/AGENT_STATE.md` and `.ufme/ENVIRONMENT.md` before acting.
2. Update only the artifacts you own; do not overwrite another agent's output.
3. Return a structured result: status, files, decisions, open questions, blocking deps, next agent.
4. Never invent backend endpoints, fields, roles, permissions, or responses.
5. Never silently bypass missing system dependencies — record in `.ufme/ENVIRONMENT.md` and
   prompt the user with the exact setup command.
6. Use only free and open-source dependencies. Record UI libraries, icon sets, fonts, images,
   animation libraries, and templates in `.ufme/DECISIONS.md` before adding.
7. No sudo, pacman, systemctl, doas, pkexec, su. No Docker/Podman/containers. No Playwright.
8. Browser tests run headlessly by default; capture screenshots at all viewports.

## Specialist prohibitions

- ufme-backend-analyst: do not generate API code; produce evidence-based maps only.
- ufme-implementer: do not invent backend capabilities; implement only what is confirmed.
- ufme-visual-auditor: review actual Selenium screenshots, not mockups.
- ufme-security-auditor: do not store or log secrets; flag exposed secrets instead.

## Escalation

Escalate to the orchestrator when: a dependency is missing, two agents conflict, a backend
capability cannot be confirmed, browser testing is blocked, or acceptance criteria cannot be
met without user action.
