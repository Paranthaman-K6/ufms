# Safety

## Permanently denied commands and operations

sudo, pacman, systemctl, doas, pkexec, su. Any root, package-manager, systemd, kernel,
firewall, user-management, network-manager, boot, or system-service operation.

## What this agent must never do

- Install system packages.
- Modify system files or pacman configuration.
- Start, stop, enable, or restart system services.
- Install Docker or Podman.
- Modify system libraries or library sonames.
- Create system-wide symlinks.
- Modify firewall, user, boot, or network configuration.

## Missing dependency handling

If a required browser, driver, font, codec, shared library, or system dependency is missing:

1. Stop the affected setup or browser-testing step.
2. Record the missing dependency in `.ufme/ENVIRONMENT.md`.
3. Prompt the user with the exact command they may choose to run themselves.
4. Do not continue browser testing until the user confirms the dependency is installed.
5. Continue with non-browser work where possible.

## Allowed autonomously

Read and create project files; install project-local npm dependencies; run builds, unit tests,
linting, and type checks; start local development servers; run Selenium browser tests using
already-installed system browsers; capture screenshots; create non-destructive Git commits.

## Requires approval

git push; deleting files, branches, databases, caches, or user data; handling secrets;
publishing packages; external deployment; activating paid services or APIs.
