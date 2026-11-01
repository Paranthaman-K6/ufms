# UFME Environment Report (Arch Linux)

Generated at session start. Updated by the orchestrator when the environment changes.

## Host
- OS: Arch Linux (rolling)
- Kernel: 6.18.59-1-lts #1 SMP PREEMPT_DYNAMIC x86_64 GNU/Linux
- Shell: /usr/bin/bash
- Session/display server: Wayland
- CPU architecture: x86_64
- Memory: 14 GiB total, ~9.2 GiB available
- Disk: 51 GiB free of 94 GiB (/)
- Working directory: $HOME/Project/MySkills (relative paths used; no hardcoded /home/<user>)

## Toolchain
- Node.js: v26.12.1
- npm: 12.2.1
- Git: 2.56.0
- OpenCode: v2.2.3
- pnpm: not detected (npm used for project-local deps)
- Git repo: not initialized (initialization is part of setup)

## Browsers (native Selenium WebDriver targets)
- Chromium: INSTALLED (user-installed after initial inspection)
- Google Chrome: not detected
- Firefox: INSTALLED at /usr/bin/firefox

## Selenium WebDriver
- selenium-webdriver npm package: not yet installed (project-local `npm install -D selenium-webdriver` required)
- Selenium Manager binary: not on PATH (resolved automatically by the selenium-webdriver package at runtime)
- Preferred browser engines: Chromium and Firefox (both present)
- Browser testing status: READY once selenium-webdriver is installed project-local

## Missing dependencies (browser testing)
None currently known. If Selenium Manager or a browser launch reports a missing shared library
(e.g. libnss3.so, libatk, libcups, libdrm, libgbm), record it here and prompt the user with the
exact `pacman -S <package>` command. Browser testing is BLOCKED until the user confirms
installation.

## Safety constraints enforced
- No sudo, pacman, systemctl, doas, pkexec, su, or any root/system-service operation by this agent.
- No Docker, Podman, or containers.
- No Playwright.
- Project-local npm dependencies only.
- Browser testing is BLOCKED for any missing browser dependency until the user installs it.
BROWSER_TESTING=BLOCKED
BROWSER_TESTING=BLOCKED
BROWSER_TESTING=BLOCKED
