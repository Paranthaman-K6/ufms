# Installation — Arch Linux

## Overview

universal-frontend-master uses **native Selenium WebDriver** with **system Chromium and
Firefox**. It does **not** use containers, Docker, Podman, or Playwright. Selenium Manager
(resolved automatically by the `selenium-webdriver` npm package) downloads and caches the
matching browser drivers.

## Prerequisites (Arch Linux)

- Node.js and npm (system or nvm)
- System Chromium: `sudo pacman -S chromium`
- System Firefox: `sudo pacman -S firefox`

## Install the skill

1. Clone or copy this repository into your project.
2. Install project-local dependencies:
   ```
   npm install -D selenium-webdriver
   ```
3. The OpenCode skill and agents are installed under `.opencode/skills/universal-frontend-master/`
   and `.opencode/agents/`.

## Browser setup

Run:
```
bash universal-frontend-master-source/scripts/check-native-browser.sh
```

This detects Chromium/Firefox, verifies Selenium Manager, and attempts a minimal headless
Selenium launch. If a browser or shared library is missing, the agent stops browser testing,
records the missing dependency in `.ufme/ENVIRONMENT.md`, and prompts you with the exact
`pacman -S` command to run yourself.

## Safety rules (enforced)

This agent never runs `sudo`, `pacman`, `systemctl`, `doas`, `pkexec`, or `su`.
No Docker/Podman/containers. No Playwright. Project-local npm dependencies only.

## Missing browser dependency

If Chromium/Firefox headless launch fails (e.g. missing `libnss3.so`, `libatk`, `libcups`,
`libdrm`, `libgbm`):

1. Browser testing stops.
2. The missing dependency is recorded in `.ufme/ENVIRONMENT.md`.
3. You are prompted with the exact setup command (e.g. `sudo pacman -S nss`).
4. Browser testing stays BLOCKED until you confirm installation.

## Verify

```
bash universal-frontend-master-source/scripts/detect-stack.sh
bash universal-frontend-master-source/scripts/check-native-browser.sh
```
