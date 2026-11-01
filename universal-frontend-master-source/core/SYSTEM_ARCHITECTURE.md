# System Architecture

## Overview

universal-frontend-master is an OpenCode skill built on a multi-agent, multi-phase pipeline.
Agents collaborate through shared persistent project memory in `.ufme/` and a structured
delegation protocol. The system is Arch Linux-first but portable.

## Layers

1. Orchestration layer — `ufme-orchestrator` (primary, mode: primary). Coordinates all work,
   owns `.ufme/AGENT_STATE.md` and `.ufme/TASKS.md`, resolves conflicts, enforces acceptance
   criteria.
2. Specialist layer — 11 subagents (mode: subagent). Each owns a domain and returns a
   structured result (status, files, decisions, open questions, blocking deps, next agent).
3. Execution layer — shell scripts in `universal-frontend-master-source/scripts/` and the
   Selenium browser abstraction in `tests/browser/`.
4. Memory layer — `.ufme/` templates and evidence. Every agent reads and updates the artifacts
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
