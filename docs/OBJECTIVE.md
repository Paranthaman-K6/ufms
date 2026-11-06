# Objective — UFMS Remaster

## What this repo is

A catalog of OpenCode skills for frontend engineering. One repo, many skills, one install.
`@universal-frontend-master` is the primary entry point; the SEO and init-frontend skills are
siblings that share the same project memory (`.ufme/`) and the same install contract.

## The problem being fixed

The skill passed its own audits and still produced a disappointing website
(`http://localhost:5174/`, project `/home/paranthaman/Project/test4`). That is the failure this
remaster exists to prevent:

- every section used the same `slideUp` variant;
- every card used the same `hoverScale`;
- the font stack was system-only, the accent was default violet;
- portfolio work sat behind a permanent scrim;
- a play button had no handler;
- the visual audit passed with an empty `VISUAL_AUDIT.md`;
- the canonical `.ufme/DESIGN_SYSTEM.md` was never validated, so a template shipped as a design.

The repo also accumulated four differently-named skill directories, duplicate agent copies, and
a registry that could not be shared across machines.

## Objective

Make UFMS a **catalog-shaped, evidence-gated multi-skill system** that:

1. produces distinctive, content-derived frontend design, not template output;
2. fails closed when the design direction, motion hierarchy, or visual audit is missing;
3. keeps every skill and agent discoverable from one place;
4. can read and update a shared library registry from any machine, with an env-key-protected
   Vercel MCP server;
5. installs and uninstalls cleanly from one repo.

## Success criteria (all must be true)

| # | Criterion | Evidence |
|---|-----------|----------|
| 1 | The reference failure site is rejected by the gate | `detect-slop.py` on `/home/paranthaman/Project/test4` exits 2 with `uniform-entrance-motion`, `font-stack-inter-or-arial-only`, `design-system-incomplete` |
| 2 | An empty or template-only design system fails | `tests/quality/run.py` design-system test passes |
| 3 | Uniform entrance motion fails | `tests/quality/run.py` component-scan test passes |
| 4 | One catalog lists every skill, agent, and command | `python3 scripts/catalog.py --check` exits 0 |
| 5 | No stale skill directory names remain | `rg "universal-frontend-master-source\|ufmw_seo_protocol_skill\|ufmw_frontend_design_skill"` returns nothing |
| 6 | Install and uninstall work from the new layout | `npm test` install/uninstall suites pass |
| 7 | Registry server works locally and fails closed | `node registry-server/test/run.mjs` exits 0; request without key returns 401 |
| 8 | Registry client falls back to local files | `registry-remote.py` exits 3 when `UFME_REGISTRY_URL` is unset and `search-libraries.py` still works |
| 9 | Full suite is green | `npm test` exits 0 |

## Non-goals

- Rewriting the Selenium browser runner.
- Changing the six-agent UFME contract (one primary, five subagents).
- Hosting the registry for the user. The server is optional; the local registry remains the
  default.
- Committing any secret. `REGISTRY_API_KEY` and `BLOB_READ_WRITE_TOKEN` live in Vercel env only.
