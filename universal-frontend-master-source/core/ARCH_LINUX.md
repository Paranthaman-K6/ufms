# Arch Linux Support

## Browser targets

- Native system Chromium and Firefox are the Selenium WebDriver targets.
- Selenium Manager (bundled with the `selenium-webdriver` npm package) resolves, downloads,
  and caches matching browser drivers automatically. Do not download drivers manually unless
  Selenium Manager fails.

## What this skill does NOT do on Arch Linux

- No `sudo`, `pacman`, `systemctl`, `doas`, `pkexec`, or `su`.
- No Docker, Podman, or containers.
- No Playwright and no `playwright install-deps`.
- No WebKit requirement.

## Missing browser dependencies

If Chromium or Firefox headless launch fails (e.g. missing `libnss3.so`, `libatk`,
`libcups`, `libdrm`, `libgbm`):

1. Stop the browser-testing step.
2. Record the missing dependency in `.ufme/ENVIRONMENT.md`.
3. Prompt the user with the exact command (e.g. `sudo pacman -S nss`).
4. Wait for the user to confirm installation before retrying.

## Portability

The skill is Arch Linux-first but the same scripts, agents, and Selenium abstraction work on
any Linux or macOS with Node.js `^22.23.4 || ^24.22.1 || >=26.12.1`, npm, a system browser,
and the project-local audit dependencies.
