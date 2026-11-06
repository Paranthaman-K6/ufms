# Remaster spec

## Decision summary

| # | Decision | Why |
|---|----------|-----|
| D1 | One repo, many skills under `skills/<kebab-name>/` | Removes four naming schemes |
| D2 | Every agent lives in top-level `agents/` with its final installed name | One place to find an agent; no rename map to drift |
| D3 | Every slash command lives in top-level `commands/`, namespaced | One place to find a command |
| D4 | `.opencode/` is a generated mirror, never hand-edited | OpenCode needs the convention; the source stays single |
| D5 | `CATALOG.md` is generated from the tree, and `--check` fails on drift | The "dictionary" cannot go stale |
| D6 | Local registry stays the default; the MCP server is optional | No forced hosting or secret |
| D7 | Design direction is a required, validated artifact | The failure was a design nobody decided |
| D8 | No new framework or dependency in the skill runtime | The skill must stay Python + Node stdlib |

## Target tree

```text
MySkill/
├── AGENTS.md                      # repo instructions for agents working on this repo
├── CATALOG.md                     # GENERATED dictionary: skills, agents, commands
├── README.md
├── todo.md                        # remaster tickets (this work)
├── install.sh
├── uninstall.sh
├── opencode.json
├── package.json
├── docs/
│   ├── OBJECTIVE.md
│   ├── REMASTER_SPEC.md
│   ├── FIXES.md
│   └── ...                        # existing install/architecture docs
├── skills/
│   ├── universal-frontend-master/ # was universal-frontend-master-source
│   │   ├── SKILL.md
│   │   ├── agents/                # REMOVED -> top-level agents/
│   │   ├── commands/              # REMOVED -> top-level commands/
│   │   ├── core/ workflows/ profiles/ templates/ scripts/ browser/
│   │   └── docs/ data/ examples/ integrations/
│   ├── ufmw-seo-protocol/         # was ufmw_seo_protocol_skill
│   ├── ufmw-frontend-design/      # was ufmw_frontend_design_skill
│   └── init-frontend/             # unchanged name, agents/commands moved out
├── agents/                        # ALL agents, flat, final names
│   ├── universal-frontend-master.md
│   ├── ufme-orchestrator.md  ufme-designer.md  ufme-builder.md
│   ├── ufme-backend-analyst.md  ufme-auditor.md
│   ├── ufmw-seo-protocol.md  ufmw-seo-technical.md  ufmw-seo-content.md
│   ├── ufmw-seo-analyst.md  ufmw-seo-auditor.md
│   ├── ufmw-frontend-design.md  ufmw-orchestrator.md
│   ├── ufmw-designer.md  ufmw-builder.md  ufmw-auditor.md
│   └── init-frontend.md
├── commands/
│   ├── ufme/                      # audit, critique, harden, polish
│   ├── ufmw/                      # seo-*, design-*, reference-*, init-frontend-*
│   ├── profile/                   # lite, standard, advanced, autonomous
│   └── lite.md standard.md advanced.md autonomous.md
├── scripts/                       # repo-level tooling only
│   ├── build-agents.py            # validate agents/ and mirror to .opencode/agents
│   └── catalog.py                 # generate + check CATALOG.md
├── tests/                         # unchanged suites, paths updated
├── registry-server/               # optional Vercel MCP registry
│   ├── api/{mcp,health,admin}.js
│   ├── lib/{store,registry,keys,limits}.js
│   ├── seed.json
│   ├── test/run.mjs
│   ├── package.json  vercel.json  README.md  .env.example
├── .opencode/                     # GENERATED mirror (agents, commands, skills/<name>/SKILL.md)
└── .ufme/                         # this repo's project memory (gitignored)
```

## Path contract

1. **Skill scripts** resolve the repo root from their own file location, never from `$PWD`.
2. **Docs and agents** refer to skills as `skills/<name>/...` from the repo root.
3. **Installed skill** is self-contained: `~/.config/opencode/skills/<name>/` holds `SKILL.md`,
   `scripts/`, `templates/`, `workflows/`, and `profiles/`. The SKILL.md says scripts are in
   `scripts/` relative to itself, and at `skills/<name>/scripts/` in a project checkout.
4. **Installed agents** are flat in `.opencode/agents/` (and `~/.config/opencode/agents/`).
5. **Installed commands** are flat or namespaced under `.opencode/commands/`.

## Install contract

| Scope | Writes |
|-------|--------|
| global | `~/.config/opencode/agents/*.md`, `~/.config/opencode/commands/**`, `~/.config/opencode/skills/<name>/` (full), `~/.config/ufme/` |
| project | `$TARGET/.opencode/agents/*.md`, `$TARGET/.opencode/commands/**`, `$TARGET/.opencode/skills/<name>/SKILL.md`, `$TARGET/skills/<name>/` (full), `$TARGET/.ufme/` |
| both | global + project |

`uninstall.sh` removes exactly those paths and nothing else.

## Registry protocol

Transport: MCP JSON-RPC 2.0 over HTTP `POST /mcp`, stateless, JSON responses
(`enableJsonResponse` semantics). One endpoint.

Auth: `Authorization: Bearer <key>`. The key is either `REGISTRY_API_KEY` or one
created in `/admin` (stored hashed). No bootstrap key and no stored keys → `503`.
Wrong key → `401`. Constant-time compare.

Bot protection: per-IP fixed-window rate limits on `/mcp` and admin login,
`429` + `retry-after` when exceeded; JSON body cap → `413`; non-JSON content
type → `415`; `x-robots-tag: noindex` on every response. Limits are in-memory
per instance; distributed protection is out of scope.

Ops endpoints: `GET /health` → `200` when configured, `503` when not;
`?deep=1` adds the registry entry count. `GET/POST /admin` is a password
(`REGISTRY_ADMIN_PASSWORD`) dashboard with an HMAC-signed HttpOnly
SameSite=Strict session, CSRF token, one-time key display, and revoke.

Tools:

| Tool | Input | Behaviour |
|------|-------|-----------|
| `registry_list` | `query?, category?, status?, limit?` | filtered list |
| `registry_get` | `name` | one entry or `isError` |
| `registry_upsert` | `name, category, site, license, commercial, install, reason, status?` | create or merge |
| `registry_remove` | `name` | delete |

Storage: one JSON array at `ufme/library-registry.json` and `{keys: []}` at
`ufme/admin-keys.json` in Vercel Blob (`access: public`, `allowOverwrite: true`,
`addRandomSuffix: false`). A connected store authenticates with OIDC and
`BLOB_STORE_ID`; `BLOB_READ_WRITE_TOKEN` is optional. No Blob store → local
`.data/library-registry.json` and `.data/admin-keys.json` for development and
tests; on Vercel that is ephemeral, so `/health` reports `degraded` and `/admin`
refuses to create keys.

Plan: the server fits the free Hobby plan (1 GB Blob, 10k reads, 2k writes,
300s functions, 3 WAF rules). Hobby is non-commercial use only.

Client: `skills/universal-frontend-master/scripts/registry-remote.py`, env
`UFME_REGISTRY_URL` + `UFME_REGISTRY_KEY`. Entries with `category: theme` may carry a
`theme` object; `theme-showcase.py` appends them to the local palette catalog. Unset → exit 3, and `search-libraries.py` silently
falls back to the local Markdown registry.

## Migration map

| From | To |
|------|-----|
| `universal-frontend-master-source/` | `skills/universal-frontend-master/` |
| `ufmw_seo_protocol_skill/` | `skills/ufmw-seo-protocol/` |
| `ufmw_frontend_design_skill/` | `skills/ufmw-frontend-design/` |
| `*/agents/orchestrator.md` | `agents/ufme-orchestrator.md` |
| `*/agents/designer.md` | `agents/ufme-designer.md` |
| `*/agents/builder.md` | `agents/ufme-builder.md` |
| `*/agents/backend-analyst.md` | `agents/ufme-backend-analyst.md` |
| `*/agents/auditor.md` | `agents/ufme-auditor.md` |
| `*/agents/universal-frontend-master.md` | `agents/universal-frontend-master.md` |
| other `*/agents/*.md` | `agents/<same-name>.md` |
| `.opencode/commands/ufme/*` | `commands/ufme/*` |
| `*/commands/ufmw/*` | `commands/ufmw/*` |
| `.opencode/commands/{profile/*,lite.md,standard.md,advanced.md,autonomous.md}` | `commands/...` |
| `.opencode/agents/*` | generated from `agents/` |
| `.opencode/skills/<name>/SKILL.md` | generated from `skills/<name>/SKILL.md` |

## Acceptance

- `python3 scripts/catalog.py --check` → 0
- `python3 scripts/build-agents.py --check` → 0
- `npm test` → 0
- `node registry-server/test/run.mjs` → 0
- `python3 skills/universal-frontend-master/scripts/detect-slop.py --path /home/paranthaman/Project/test4/src --design /home/paranthaman/Project/test4/.ufme/design/DESIGN_SYSTEM.md` → 2 with the three expected rules
- `rg "universal-frontend-master-source|ufmw_seo_protocol_skill|ufmw_frontend_design_skill"` → nothing
