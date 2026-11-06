# System Architecture

## Overview

universal-frontend-master is an OpenCode skill built on a multi-agent, multi-phase pipeline.
Agents collaborate through shared persistent project memory in `.ufme/` and a structured
delegation protocol. The system is Arch Linux-native and Arch Linux-only.

## Layers

1. Entry layer — `universal-frontend-master` (the only `mode: primary`). Classifies the
   project, applies the execution profile, and delegates per `allowedAgents` (orchestrator
   only in advanced/autonomous; direct specialist delegation in lite/standard).
2. Orchestration layer — `ufme-orchestrator` (mode: subagent). Packs task context, enforces
   profile limits, owns `.ufme/AGENT_STATE.md` and `.ufme/TASKS.md`, resolves conflicts, and
   enforces acceptance criteria.
3. Specialist layer — `ufme-designer`, `ufme-builder`, `ufme-backend-analyst`, and
   `ufme-auditor` (mode: subagent). Each owns a domain and returns a structured result
   (status, files, decisions, open questions, blocking deps, next agent).
4. Execution layer — shell scripts in `skills/universal-frontend-master/scripts/` and the
   Selenium browser abstraction in `tests/browser/`.
5. Memory layer — `.ufme/` templates and evidence. Every agent reads and updates the artifacts
   it owns.

## Data flow

Brief/repo/screenshot/API docs → intake → research → backend intelligence → product
intelligence → design → architecture → implementation → integration → browser execution →
visual/accessibility/performance/security audits → fix & retest → continuous improvement →
delivery.

## Browser stack

Native Selenium WebDriver with JavaScript bindings. Selenium Manager resolves and caches
matching Chromium and Firefox drivers automatically. Tests run headlessly by default.
Screenshots captured at mobile/tablet/laptop/desktop viewports, dark and light themes.

## Safety boundaries

No sudo/pacman/systemctl/doas/pkexec/su. No Docker/Podman/containers. No Playwright.
Project-local npm dependencies only. Missing system browsers/libraries are reported to the
user with the exact setup command; browser testing is marked BLOCKED until confirmed installed.
