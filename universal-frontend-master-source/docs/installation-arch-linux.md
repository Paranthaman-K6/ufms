# Installation — Arch Linux

## Overview

universal-frontend-master uses **native Selenium WebDriver** with **system Chromium and
Firefox**. It does **not** use containers, Docker, Podman, or Playwright. Selenium Manager
(resolved automatically by the `selenium-webdriver` npm package) downloads and caches the
matching browser drivers.

## Prerequisites (Arch Linux)

- Node.js `^22.23.4`, `^24.22.1`, or `>=26.12.1` and npm (system or nvm; `.nvmrc` pins 24)
- System Chromium: `sudo pacman -S chromium`
- System Firefox: `sudo pacman -S firefox`

## Install the skill

1. Clone or copy this repository into your project.
2. Install project-local dependencies:
   ```
   npm install
   ```
   This installs Selenium, axe-core, Lighthouse, `pngjs` and `pixelmatch` (visual diffs).
3. The OpenCode skill and agents are installed under `.opencode/skills/universal-frontend-master/`
   and `.opencode/agents/`.

For an offline or CI install from a checkout (no network):

```
UFME_SOURCE_DIR=/path/to/ufms UFME_SKIP_NPM=1 INSTALL_DIR=/path/to/project bash install.sh
```

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
