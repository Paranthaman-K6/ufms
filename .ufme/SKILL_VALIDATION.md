# UFME Skill Validation

## Files created

Source repository: `universal-frontend-master-source/`
- core/: MASTER_SKILL.md, SYSTEM_ARCHITECTURE.md, MULTI_AGENT_ORCHESTRATION.md, AGENT_RULES.md,
  PROJECT_MEMORY.md, QUALITY_STANDARDS.md, SAFETY.md, ARCH_LINUX.md (8 files)
- agents/: orchestrator.md, researcher.md, backend-analyst.md, product-analyst.md, designer.md,
  frontend-architect.md, implementer.md, integrator.md, visual-auditor.md, accessibility-auditor.md,
  performance-auditor.md, security-auditor.md (11 files)
- workflows/: 01-14 numbered workflow markdowns (14 files)
- templates/: 17 .ufme/ templates (17 files)
- scripts/: detect-stack.sh, backend-discovery.sh, check-native-browser.sh, browser-test.sh,
  screenshot.sh, quality-check.sh (6 files)
- docs/: installation-arch-linux.md, multi-agent-usage.md, compatibility.md, testing.md,
  troubleshooting.md (5 files)
- examples/: README.md (from-scratch, existing-backend, complex-landing-page)
- README.md

OpenCode install:
- .opencode/skills/universal-frontend-master/SKILL.md
- .opencode/agents/: ufme-orchestrator.md (mode: primary) + 11 specialist agents (mode: subagent)
- opencode.json
- tests/browser/: browser.js, chromium.js, firefox.js, screenshot.js, console.js, network.js,
  viewport.js, run.js (8 files)

Runtime memory: .ufme/TASKS.md, .ufme/ENVIRONMENT.md

## Arch environment findings

- OS: Arch Linux (rolling), kernel 6.18.59-1-lts
- Shell: /usr/bin/bash; Node v26.12.1; npm 12.2.1; Git 2.56.0; OpenCode v2.2.3
- Session: Wayland; CPU x86_64; 14 GiB RAM; 51 GiB disk free

## Browser availability

- Chromium: /usr/bin/chromium (installed)
- Google Chrome: not found
- Firefox: /usr/bin/firefox (installed)

## Selenium Manager status

- selenium-webdriver: installed project-local (`npm install -D selenium-webdriver`, v4.52.0)
- Selenium Manager: resolved automatically by the selenium-webdriver package at runtime
- check-native-browser.sh: Firefox headless Selenium launch = OK; browser setup = READY
- Chromium Selenium launch: Options API mismatch in this build (setBinary not accepted);
  Firefox is the working engine. No pacman package required.

## Agent discovery result

Skill `universal-frontend-master` confirmed discovered by OpenCode (system skill listing).
12 agent files present under .opencode/agents/:
ufme-orchestrator (primary), ufme-researcher, ufme-backend-analyst, ufme-product-analyst,
ufme-designer, ufme-frontend-architect, ufme-implementer, ufme-integrator, ufme-visual-auditor,
ufme-accessibility-auditor, ufme-performance-auditor, ufme-security-auditor.
(OpenCode v2.2.3 auto-discovers agents from .opencode/agents/; `agent list` is not a v2 CLI
subcommand.)

## Multi-agent delegation map

Orchestrator -> researcher -> backend-analyst -> product-analyst -> designer ->
frontend-architect -> implementer -> integrator -> browser execution -> visual-auditor ->
accessibility-auditor -> performance-auditor -> security-auditor -> continuous improvement ->
delivery.
Parallel only when tasks don't modify the same files. Conflicts resolved by orchestrator and
recorded in .ufme/DECISIONS.md.

## Permission validation result

opencode.json: valid JSON.
Effects enforced: hard-deny sudo, pacman, systemctl, doas, pkexec, su; deny rm -rf / and
rm -rf ~; ask on git push*; deny npm publish*. Allow local builds, tests, lint, file edits,
screenshots, non-destructive git commits.

## Validation errors and resolutions

1. check-native-browser.sh temp script ran from /tmp -> could not resolve project-local
   selenium-webdriver. Fix: write temp script into $ROOT_DIR so Node module resolution finds
   node_modules/selenium-webdriver.
2. check-native-browser.sh used .binary() on Options -> not a function in selenium-webdriver v4.
   Fix: use .setBinary(). Firefox launch now succeeds.
3. npm install -D failed initially (no package.json). Fix: npm init -y, then npm install -D
   selenium-webdriver.
4. opencode agent list is not a v2.2.3 subcommand. Resolution: agents auto-discovered from
   .opencode/agents/; confirmed via directory listing.

## Known Arch limitations

- Chromium Selenium launch has an Options API mismatch in this selenium-webdriver build;
  Firefox is the confirmed working engine. Chromium detection + blocked-prompt logic remains
  in place if Chromium is later used.
- No system packages installed by this agent (sudo/pacman denied); any missing shared library
  (e.g. libnss3) must be installed by the user via `sudo pacman -S <package>`.
- No containers, no Playwright, no WebKit.
