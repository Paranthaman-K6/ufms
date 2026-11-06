# Remaster todo

Tickets are ordered by blocking edge. `[x]` done, `[~]` in progress, `[ ]` todo, `[!]` blocked.
Each ticket is self-contained: a fresh session can pick it up from the spec in
`docs/REMASTER_SPEC.md`.

## T1 — Freeze target tree and path contract
- [x] `docs/REMASTER_SPEC.md` written (decisions D1–D8, target tree, migration map)
- [x] `docs/OBJECTIVE.md` with measurable success criteria
- [x] `docs/FIXES.md` with evidence per defect
- **Blocks:** T2

## T2 — Move skills, agents, commands into the catalog layout
- [x] `git mv universal-frontend-master-source skills/universal-frontend-master`
- [x] `git mv ufmw_seo_protocol_skill skills/ufmw-seo-protocol`
- [x] `git mv ufmw_frontend_design_skill skills/ufmw-frontend-design`
- [x] Move every `*/agents/*.md` into `agents/` with final names (UFME five get `ufme-` prefix)
- [x] Move every command source into `commands/` (`ufme/`, `ufmw/`, `profile/`, root)
- [x] Remove now-empty `agents/`/`commands/` dirs from each skill
- **Blocked by:** T1 · **Blocks:** T3, T4

## T3 — Repair path resolution
- [x] Fix `parents[]` depth in `skills/*/scripts/*.py` and `*.sh`
- [x] Fix script/doc references from `universal-frontend-master-source/...` to `skills/...`
- [x] Confirm `detect-slop.py`, `quality-check.py`, `seed-project-memory.py`, `self-improve.py`,
      `search-libraries.py`, `build-agents.py` resolve the repo root correctly from the new depth
- **Blocked by:** T2 · **Blocks:** T5, T12

## T4 — Rewrite install/uninstall for the new layout
- [x] `install.sh` copies `agents/`, `commands/`, `skills/<name>/` (full, self-contained)
- [x] Global install of a skill includes `scripts/`, `templates/`, `workflows/`, `profiles/`
- [x] `uninstall.sh` removes the same paths, no strays
- [x] `tests/install/run.sh` and `tests/uninstall/run.sh` assert the new paths
- **Blocked by:** T2 · **Blocks:** T5, T12

## T5 — Generate the catalog and the `.opencode` mirror
- [x] `scripts/catalog.py` generates `CATALOG.md` from `skills/*/SKILL.md`, `agents/*.md`,
      `commands/**/*.md`; `--check` fails on drift
- [x] `scripts/build-agents.py` validates `agents/` and mirrors to `.opencode/agents/`
- [x] `.opencode/skills/<name>/SKILL.md` mirrored from source
- [x] `CATALOG.md` lists every skill, agent, and command with trigger + file path
- **Blocked by:** T3, T4 · **Blocks:** T11, T12

## T6 — Fix registry/design defects
- [x] F7: `approve_package()` regex crash → lambda rewrite, test
- [x] F8: inverted motion heading map → `{"animation": "motion"}`, test
- [x] F4: quality gate always passes `--design`; `UFME_SLOP_SKIP_DESIGN=1` escape hatch, test
- **Blocked by:** T1 · **Blocks:** T8, T12

## T7 — Seed the library registry from live GitHub metadata
- [x] `registry-server/seed.json` with repo, stars, SPDX license, npm package, category, reason
- [x] Includes the frontend references: shadcn/ui, radix, tailwind, headlessui, motion,
      react-bits, r3f, drei, zustand, react-spring, TanStack query/table, zod, react-hook-form,
      react-router, lucide, phosphor, tabler, recharts, chart.js, d3, lottie, GSAP, anime,
      lenis, barba, unocss, open-props, daisyui, heroui, mantine, chakra, MUI, antd, next, vite,
      astro, svelte, vue, nuxt, storybook, vitest, testing-library, axe-core, lighthouse,
      playwright, puppeteer, fontsource, google/fonts, anthropics/skills, MCP TS SDK, ECC
- [x] License column is the verified SPDX id; `NOASSERTION` is marked "verify"
- **Blocked by:** T6 · **Blocks:** T9

## T8 — Build the optional Vercel MCP registry server
- [x] `registry-server/api/mcp.js`: stateless MCP JSON-RPC, `initialize`, `tools/list`,
      `tools/call`, `ping`; 401/503 auth
- [x] `registry-server/lib/store.js`: Vercel Blob, local-file fallback
- [x] `registry-server/lib/registry.js`: validation, upsert, query
- [x] `registry-server/test/run.mjs`: auth, list, upsert, get, remove, seed validity
- [x] `vercel.json`, `package.json`, `.env.example`, `README.md`
- **Blocked by:** T7 · **Blocks:** T10

## T9 — Build the registry client and wire it in
- [x] `skills/universal-frontend-master/scripts/registry-remote.py` (list/get/search/upsert/remove/seed)
- [x] `search-libraries.py` reads remote first, falls back silently to local
- [x] `--select` upserts to remote when configured
- [x] Unset env → exit 3, local behaviour unchanged
- **Blocked by:** T8 · **Blocks:** T11

## T10 — Documentation
- [x] `README.md` describes the catalog layout, install scopes, registry server
- [x] `AGENTS.md` for agents working on this repo
- [x] `skills/*/SKILL.md` path wording matches the install contract
- [x] `docs/installation-arch-linux.md` updated
- **Blocked by:** T5, T9 · **Blocks:** T12

## T11 — Full verification
- [x] `npm test` green
- [x] `python3 scripts/catalog.py --check` green
- [x] `python3 scripts/build-agents.py --check` green
- [x] `node registry-server/test/run.mjs` green
- [x] Reference-site regression: linter rejects `/home/paranthaman/Project/test4`
- [x] `self-improve.py` green
- [x] No stale path strings remain
- **Blocked by:** T3–T10 · **Blocks:** T12

## T12 — End-to-end proof from a real install
- [x] Install project-scope into a clean directory from the local checkout (`INSTALL_SCOPE=project`, `UFME_SKIP_NPM=1`)
- [x] Installed agent, skill scripts, and seeded `.ufme/DESIGN_SYSTEM.md` exist
- [x] Seeded design template fails closed: `detect-slop.py` exits 2 with `design-system-incomplete`
- [x] Filled design system passes: `detect-slop.py` exits 0
- [x] Uniform entrance motion on four components fails: exit 2 with `uniform-entrance-motion`
- [x] `uninstall.sh --project-only` removes agents/skills/commands and keeps `.ufme/`
- **Evidence:** `14 passed, 0 failed` from `/tmp/opencode/t12-e2e.sh` (reproducible; not committed)
- **Blocked by:** T11

## T13 — Theme showcase PDF for every project
- [x] `data/palettes.csv` rows are complete themes (`bg`, `surface`, `text`, `muted`, `accent`, `accent_alt`, `font_pairing`)
- [x] `theme-showcase.py` renders one page per theme — swatches with hex, type specimen, applied sample — with no dependencies (base-14 fonts)
- [x] The project's choice from `.ufme/design-choices.json` is marked `YOUR PROJECT` and shown first
- [x] Registry themes (`category: theme` entries with a `theme` object) are appended when `UFME_REGISTRY_URL`/`UFME_REGISTRY_KEY` are set; silent local fallback otherwise
- [x] `init-project.py` generates `.ufme/theme-showcase.pdf` automatically; `/ufmw/theme` regenerates it
- [x] `tests/theme/run.py` (7 pass) and the e2e install proof (17 pass) cover generation, project marking, `--only`, and registry merge
- **Blocked by:** T11

## T14 — TUI installer with a recommended selection
- [x] Single TUI screen asks what to install: scope, skills, agents, commands, project memory, audit npm dependencies
- [x] Everything is selected by default (scope both) and labelled recommended; Enter installs, Space toggles, Left/Right changes scope, `q` cancels
- [x] Pure bash (ANSI + `read -rsn1`), no new dependency; restores the previous `EXIT` trap (tmp cleanup)
- [x] Works for `curl | bash` by reading keys from `/dev/tty` when stdin is the script
- [x] Scripted installs: `INSTALL_SCOPE`, `UFME_SKILLS`, `UFME_SKIP_AGENTS|COMMANDS|MEMORY|NPM`, `UFME_NONINTERACTIVE`; a non-interactive run with no scope installs everything
- [x] `tests/install/run.sh` covers env selection, skip flags, an unknown skill (exit 1), and the TUI via a pty (`script`) — 91 pass
- **Blocked by:** T11
