# AGENTS.md — working on this repository

This repo is a catalog of OpenCode skills. Read `CATALOG.md` first; it lists every
skill, agent, and command with its path.

## Source of truth

| Thing | Source | Generated |
|-------|--------|-----------|
| Skills | `skills/<kebab-name>/` | `.opencode/skills/<name>/SKILL.md` |
| Agents | `agents/*.md` (flat, final names) | `.opencode/agents/*.md` |
| Commands | `commands/**/*.md` | `.opencode/commands/**/*.md` |
| Catalog | the tree above | `CATALOG.md` |

Never edit `.opencode/` or `CATALOG.md` by hand. After moving or renaming anything:

```bash
python3 scripts/build-agents.py
python3 scripts/catalog.py
```

Both have `--check` and fail on drift.

## Contracts

- An agent's frontmatter `name` must equal its file stem. Allowed keys:
  `name`, `mode`, `description`, `permission`; mode is `primary` or `subagent`;
  permissions are `read`, `edit`, `bash`, `task` with `allow|deny|ask`.
- Skill scripts resolve the repo root from `Path(__file__).resolve().parents[3]`
  (script → skill → skills → repo). Never resolve from `$PWD`.
- Installed skills must stay self-contained: `SKILL.md`, `scripts/`, `templates/`,
  `workflows/`, `profiles/`.
- Local registry is the default. The MCP server in `registry-server/` is optional and
  must fail closed: no `REGISTRY_API_KEY` → `503`, wrong key → `401`.

## Checks before a change is done

```bash
npm test
python3 scripts/catalog.py --check
python3 scripts/build-agents.py --check
node registry-server/test/run.mjs
```

The design gate is the reason this repo exists: an untouched design-system template,
uniform entrance motion, or an empty visual audit must fail, not pass. Do not weaken
`detect-slop.py` to make a site pass; fix the design.
