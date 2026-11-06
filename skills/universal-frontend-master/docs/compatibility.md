# Compatibility

## Runtime
- Node.js `^22.23.4`, `^24.22.1`, or `>=26.12.1` (declared in `package.json` `engines`,
  pinned by `.nvmrc` to 24). The range is the intersection required by
  `selenium-webdriver@4.52`.
- `.npmrc` enables `engine-strict`, so installs fail fast on an unsupported Node.
- Direct dependencies: `selenium-webdriver`, `@axe-core/webdriverjs`, `lighthouse`
  (pinned `13.5.0`; `13.6.0` pulls a vulnerable `@sentry/node`/`glob` chain),
  `pngjs`, `pixelmatch`.
- Python 3.9+ for scripts; no third-party Python packages required.

## Platform
- Arch Linux (native Chromium + Firefox, Wayland/X11/headless) — the only supported platform.
- Install browsers: `sudo pacman -S chromium firefox`.
- Shell helpers use POSIX tools available on Arch Linux (`sha256sum`, `date -u`).

## Quality gate semantics
- Required checks (`--require`, or the `audit` preset) cannot PASS when SKIPPED.
  A skipped required check makes the overall status BLOCKED.
- A check that exits 0 without fresh, structurally valid evidence is FAIL.
- Overall precedence: FAIL > BLOCKED > PASS.
- Visual regression treats a missing current screenshot as a failure and reports
  first-run baseline creation as BLOCKED, not PASS.
- `UFME_CHROME_FLAGS` overrides Lighthouse's Chrome flags (default
  `--headless=new`); container/CI runners usually need
  `--headless=new --no-sandbox --disable-dev-shm-usage`.

## Browser engine
- Selenium WebDriver only (Chromium + Firefox).
- Selenium Manager resolves/caches drivers automatically.
- No Playwright. No WebKit requirement.

## Frontend stacks preserved (not forced)
React, Next.js, Vue, Nuxt, Svelte, SvelteKit, Astro, Angular, SolidJS, Qwik.
Build tools: Vite, etc. Styling: Tailwind, Bootstrap, CSS Modules, native CSS.
TypeScript and JavaScript.

## Backend stacks analyzed
Spring Boot, Express, Fastify, NestJS, Django, Flask, FastAPI, Laravel, Rails, ASP.NET,
Go HTTP services. API styles: REST, GraphQL, OpenAPI, Swagger, Postman, AsyncAPI.

## OpenCode
- OpenCode v2.2.3 compatible.
- Skill installed under `.opencode/skills/universal-frontend-master/`.
- Agents installed under `.opencode/agents/`.

## Dependencies
- Free and open-source only. No paid templates, premium component libraries, paid MCP
  servers, or mandatory paid APIs.
