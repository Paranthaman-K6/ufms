---
name: universal-frontend-master
description: Multi-agent frontend engineering (multi-agent) for building and improving responsive frontend websites, with execution profiles (/profile/lite|standard|advanced|autonomous) and evidence-driven auditors (a11y, perf, visual, security).
license: MIT
---

# universal-frontend-master — Master Skill (pointer)

`SKILL.md` is the single compact entry point for this skill. Read it first:

- Repo copy: `.opencode/skills/universal-frontend-master/SKILL.md`
- Installed (user scope): `~/.config/opencode/skills/universal-frontend-master/SKILL.md`

This file stays a thin pointer: trigger, hard rules, agent routing, scripts, and the
reference router all live in `SKILL.md`.

## Agents (final set)

| Agent | Mode | Role |
|-------|------|------|
| `universal-frontend-master` | primary | Entry point; starts the session, delegates per active profile |
| `ufme-orchestrator` | subagent | Plans, delegates, enforces acceptance, owns memory |
| `ufme-designer` | subagent | Research, product brief, design system, critique |
| `ufme-backend-analyst` | subagent | API map, auth map, backend contracts (skipped when no backend detected) |
| `ufme-builder` | subagent | Build, integrate, test UI and API layer |
| `ufme-auditor` | subagent | Visual, accessibility, performance, security audits — evidence-driven from script JSON |

## Execution profiles

- `/profile/lite` — primary + builder (1 concurrent delegate; small edits, quick prototypes)
- `/profile/standard` — default; designer, builder, backend-analyst and auditor (2 concurrent delegates)
- `/profile/advanced` — all six roles including the orchestrator (4 concurrent delegates, full audit loop)
- `/profile/autonomous` — all six roles (5 concurrent delegates, unattended exhaustive verification)

## Install paths (user scope)

- Agents, skill, commands, `opencode.json`: `~/.config/opencode/`
- Cross-project shared data: `~/.config/ufme/` (`LIBRARY_REGISTRY.md`, `evidence/`)
- Per-project memory: `.ufme/` in each target project (seeded on install, never overwritten)

## Safety summary

Never `sudo`, `pacman`, `systemctl`, `doas`, `pkexec`, `su`; no system package installs.
No Playwright, no containers; browser sandbox preserved (never `--no-sandbox`).
Project-local npm dependencies only; assets/libraries require verified licenses recorded in
`.ufme/DECISIONS.md`. Evidence-first: audits read script JSON before screenshots. Details in
`skills/universal-frontend-master/core/SAFETY.md`.

## Anti-generic design (standing rule)

Motion varies with the content hierarchy — no uniform per-section fade-up, no hover animation
on every card. Avoid default identity (system/Inter/Arial-only type, purple→pink gradients,
violet-on-dark as the default palette) and reference the actual brand assets recorded in
`.ufme/DECISIONS.md`.

`detect-slop.py` enforces this: it scans component files too, flags one entrance variant
reused on 4+ components, and fails when `.ufme/DESIGN_SYSTEM.md` is still the seeded template.
Fill `## Design direction` (tone, two distinct type roles, palette rationale, layout concept,
motion hierarchy) before implementation; the visual audit must record findings in
`.ufme/VISUAL_AUDIT.md`, and an empty table is FAIL.
