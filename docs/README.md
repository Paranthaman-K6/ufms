# Documentation

Start here. The root [README](../README.md) is the pitch and the install path;
these pages are the reference.

| Doc | Read it when you want to… |
|-----|---------------------------|
| [README](../README.md) | Install it, see what it does, run the first session |
| [CATALOG](../CATALOG.md) | Look up any skill, agent, or command and its path |
| [Architecture](ARCHITECTURE.md) | Understand what is authored vs generated, the memory model, the evidence gate |
| [Development](DEVELOPMENT.md) | Set up the repo, run the checks, add a skill/agent/command, release |
| [Skills](SKILLS.md) | See what each of the four skills does, its scripts and commands |
| [Registry server](../registry-server/README.md) | Deploy the optional shared library registry |

## Skill docs

Each skill carries its own deeper notes:

| Skill | Docs |
|-------|------|
| `universal-frontend-master` | [Multi-agent usage](../skills/universal-frontend-master/docs/multi-agent-usage.md) · [Testing](../skills/universal-frontend-master/docs/testing.md) · [Compatibility](../skills/universal-frontend-master/docs/compatibility.md) · [Troubleshooting](../skills/universal-frontend-master/docs/troubleshooting.md) · [Installation notes](../skills/universal-frontend-master/docs/installation-arch-linux.md) |
| `ufmw-frontend-design` | [SKILL.md](../skills/ufmw-frontend-design/SKILL.md) |
| `ufmw-seo-protocol` | [SKILL.md](../skills/ufmw-seo-protocol/SKILL.md) |
| `init-frontend` | [DOCS.md](../skills/init-frontend/DOCS.md) |

## Rules of the repo

The short version; [Architecture § Invariants](ARCHITECTURE.md#11-invariants) has
the full list.

- `.opencode/` and `CATALOG.md` are generated — regenerate, never edit.
- An agent's frontmatter `name` equals its file stem.
- Skills stay self-contained; scripts resolve the repo root from their own path.
- Runtime state goes to `.ufme/`, never into the source tree.
- `detect-slop.py` is not weakened to make a site pass.

## Checks before a change is done

```bash
npm test
python3 scripts/catalog.py --check
python3 scripts/build-agents.py --check
node registry-server/test/run.mjs
```

[Development § Check matrix](DEVELOPMENT.md#4-check-matrix) explains what each one
covers.
