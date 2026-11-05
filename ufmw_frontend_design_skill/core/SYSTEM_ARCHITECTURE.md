# System Architecture

## Overview

ufmw-frontend-design is an OpenCode skill built on a multi-agent, multi-phase pipeline.
Agents collaborate through shared persistent project memory in `.ufme/` and a structured
delegation protocol. The system is Arch Linux-native and Arch Linux-only.

## Layers

1. Entry layer — `ufmw-frontend-design` (the only `mode: primary`). Classifies the
   project, applies the execution profile, and delegates per `allowedAgents`.
2. Orchestration layer — `ufmw-orchestrator` (mode: subagent). Packs task context, enforces
   profile limits, owns `.ufme/AGENT_STATE.md` and `.ufme/TASKS.md`, resolves conflicts, and
   enforces acceptance criteria.
3. Specialist layer — `ufmw-designer`, `ufmw-builder`, `ufmw-backend-analyst`, and
   `ufmw-auditor` (mode: subagent). Each owns a domain and returns a structured result
   (status, files, decisions, open questions, blocking deps, next agent).
4. Reference-driven design layer — Selenium-based reference inspection (`reference-inspect.js`),
   element analysis (`reference-analyze.py`), matching (`reference-match.py`), adaptation
   (`reference-adapt.py`), and verification (`reference-verify.js`).
5. Execution layer — shell scripts in `ufmw_frontend_design_skill/scripts/` and the
   Selenium browser abstraction.
6. Memory layer — `.ufme/` templates and evidence. Every agent reads and updates the artifacts
   it owns.

## Data Flow

Brief/repo/screenshot/API docs/reference URL → intake → research → backend intelligence →
product intelligence → design → reference analysis → architecture → implementation → integration
→ browser execution → visual/accessibility/performance/security audits → fix & retest →
continuous improvement → delivery.

## Browser Stack

Native Selenium WebDriver with JavaScript bindings. Selenium Manager resolves and caches
matching Chromium and Firefox drivers automatically. Tests run headlessly by default.
Screenshots captured at mobile/tablet/laptop/desktop viewports, dark and light themes.

## Safety Boundaries

No sudo/pacman/systemctl/doas/pkexec/su. No Docker/Podman/containers. No Playwright.
Project-local npm dependencies only. Missing system browsers/libraries are reported to the
user with the exact setup command; browser testing is marked BLOCKED until confirmed installed.

## Reference-Driven Design Pipeline

1. User provides reference URL(s)
2. `reference-inspect.js` loads page in Selenium, extracts DOM + computed styles per element
3. `reference-analyze.py` groups elements by type, generates REFERENCES.md and ELEMENT_MAP.md
4. User specifies destination and aspects for each element
5. `reference-match.py` creates match plan
6. `reference-adapt.py` generates adapted component code (HTML/CSS with CSS variables)
7. `ufmw-builder` implements adapted elements in source code
8. `reference-verify.js` captures before/after screenshots, verifies implementation
9. `ufmw-auditor` includes reference-implementation findings in AUDIT_REPORT.md
