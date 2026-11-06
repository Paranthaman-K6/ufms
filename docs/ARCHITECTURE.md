# Architecture

How the repository is put together: what is authored, what is generated, how a
session flows through it, and the invariants that keep the pieces in sync.

- **Audience:** contributors and anyone debugging install or generation drift.
- **Companion docs:** [Development](DEVELOPMENT.md) · [Skills](SKILLS.md) · [Catalog](../CATALOG.md)

---

## 1. System at a glance

```mermaid
flowchart TB
    subgraph Author["Authored (source of truth)"]
        A1["skills/&lt;name&gt;/"]
        A2["agents/*.md"]
        A3["commands/**/*.md"]
    end

    subgraph Generated["Generated (never hand-edited)"]
        G1[".opencode/skills/&lt;name&gt;/SKILL.md"]
        G2[".opencode/agents/*.md"]
        G3[".opencode/commands/**/*.md"]
        G4["CATALOG.md"]
    end

    subgraph Runtime["Runtime state"]
        R1[".ufme/ (per project)"]
        R2["~/.config/ufme/ (shared)"]
    end

    subgraph Install["Installed (user scope)"]
        I1["~/.config/opencode/agents/"]
        I2["~/.config/opencode/skills/"]
        I3["~/.config/opencode/commands/"]
        I4["~/.config/opencode/opencode.json"]
    end

    A1 --> G1
    A2 --> G2
    A3 --> G3
    A1 --> G4
    A2 --> G4
    A3 --> G4
    Author --> Install
    Author --> R1
    Author --> R2
```

Three things are **authored**: skills, agents, and commands. Everything under
`.opencode/` and `CATALOG.md` is **generated**. Anything in `.ufme/` is
**runtime state** produced by a session.

---

## 2. Source of truth and generated mirrors

| Thing | Author here | Generated here | Regenerate with |
|-------|-------------|----------------|-----------------|
| Skills | `skills/<name>/` | `.opencode/skills/<name>/SKILL.md` | `python3 scripts/catalog.py` |
| Agents | `agents/*.md` (flat, final names) | `.opencode/agents/*.md` | `python3 scripts/build-agents.py` |
| Commands | `commands/**/*.md` | `.opencode/commands/**/*.md` | `python3 scripts/catalog.py` |
| Catalog | — | `CATALOG.md` | `python3 scripts/catalog.py` |

Both generators support `--check`, which exits non-zero on drift. CI runs both,
so a hand-edited mirror or a stale catalog fails the build instead of shipping.

```mermaid
flowchart LR
    E["Edit skills/ agents/ commands/"] --> G["Run generators"]
    G --> C{"--check passes?"}
    C -- no --> F["Fix source or rerun generator"]
    F --> G
    C -- yes --> P["Commit + push"]
```

---

## 3. Repository map

```text
.
├── skills/                     # four self-contained skills
│   ├── universal-frontend-master/
│   ├── ufmw-frontend-design/
│   ├── ufmw-seo-protocol/
│   └── init-frontend/
├── agents/                     # 17 agent definitions, flat
├── commands/                   # slash commands: ufme/, ufmw/, profile/
├── scripts/                    # repo tooling only (build-agents, catalog)
├── tests/                      # 15 suites, run by npm test
├── registry-server/            # optional Vercel MCP registry
├── docs/                       # this documentation set
├── .opencode/                  # GENERATED mirror
├── .ufme/                      # runtime memory + evidence (gitignored)
├── install.sh / uninstall.sh   # scoped, idempotent
├── opencode.json               # permission policy
└── CATALOG.md                  # GENERATED catalog
```

`scripts/` at the repository root is **repo tooling**. The scripts a skill runs
live inside the skill (`skills/<name>/scripts/`), so an installed skill works
outside a checkout.

---

## 4. Skill anatomy

Every skill is self-contained: installing the folder installs everything it
needs. Optional directories appear only where a skill uses them.

```text
skills/<name>/
├── SKILL.md          # frontmatter + trigger + rules + routing (required)
├── core/             # long-form rules the agent loads on demand
├── workflows/        # numbered passes, e.g. 01-intake → 07-integration
├── scripts/          # deterministic helpers (bash / python / node)
├── templates/        # project-memory and document templates
├── profiles/         # lite / standard / advanced / autonomous JSON
├── browser/          # Selenium abstraction (main skill)
├── data/             # curated CSVs: palettes, fonts, styles, UX rules
├── integrations/     # optional MCP discovery helpers
└── examples/
```

| Directory | Purpose | Loaded when |
|-----------|---------|-------------|
| `SKILL.md` | Entry contract: trigger, hard rules, agent router | Always |
| `core/` | Safety, quality standards, orchestration, memory rules | Referenced by the agent |
| `workflows/` | Ordered passes of the engineering loop | Per session phase |
| `scripts/` | Anything that must be deterministic and repeatable | Invoked by the agent |
| `profiles/` | Delegation limits and allowed agents | Start of a run |
| `templates/` | Seed files for `.ufme/` | Install / first run |

---

## 5. Agents and delegation

All agents are **flat** in `agents/` under their final installed name, so the
file stem is the invocation name.

```mermaid
flowchart TB
    P1["@universal-frontend-master (primary)"]
    P2["@ufmw-frontend-design (primary)"]
    P3["@ufmw-seo-protocol (primary)"]
    P4["@init-frontend (primary)"]

    O1["ufme-orchestrator"]
    O2["ufmw-orchestrator"]

    S1["ufme-designer / ufme-backend-analyst / ufme-builder / ufme-auditor"]
    S2["ufmw-designer / ufmw-builder / ufmw-backend-analyst / ufmw-auditor"]
    S3["ufmw-seo-analyst / -technical / -content / -auditor"]

    P1 --> O1 --> S1
    P2 --> O2 --> S2
    P3 --> S3
    P3 -. source fixes .-> S2
```

The **orchestrator is profile-dependent**: `lite` and `standard` delegate
directly to specialists, while `advanced` and `autonomous` route through the
orchestrator. `scripts/execution-profiles.sh --enforce` validates a proposed
delegation against the active profile's allowed agents and concurrency cap.

Frontmatter contract, enforced by `scripts/build-agents.py`:

| Key | Rule |
|-----|------|
| `name` | Must equal the file stem |
| `mode` | `primary` or `subagent` |
| `description` | Non-empty |
| `permission` | Optional; keys limited to `read`, `edit`, `bash`, `task` with `allow` / `deny` / `ask` |

---

## 6. Commands

A command file at `commands/<namespace>/<name>.md` becomes `/<namespace>/<name>`.

| Namespace | Owner skill | Examples |
|-----------|-------------|----------|
| `ufme/` | universal-frontend-master | `/ufme/audit`, `/ufme/polish`, `/ufme/harden`, `/ufme/critique` |
| `ufmw/` | design, SEO, and init-frontend | `/ufmw/build`, `/ufmw/seo-run`, `/ufmw/init-frontend` |
| `profile/` | universal-frontend-master | `/profile/lite` … `/profile/autonomous` |

The full list is generated into [CATALOG.md](../CATALOG.md).

---

## 7. Memory model

```mermaid
flowchart LR
    T["skills/.../templates/"] -->|seed-project-memory.py| P[".ufme/"]
    P --> M["TASKS · DECISIONS · DESIGN_SYSTEM<br/>API_MAP · ARCHITECTURE · ..."]
    P --> E[".ufme/evidence/*.json"]
    S["~/.config/ufme/"] --> L["LIBRARY_REGISTRY.md + evidence"]
    L -->|search-libraries.py| P
```

| Location | Scope | Lifetime | Contents |
|----------|-------|----------|----------|
| `.ufme/` | One project | Committed by the user | Decisions, task state, design system, evidence JSON |
| `.ufme/evidence/` | One project | Regenerated per run | `a11y-results.json`, `perf-results.json`, `visual-diff.json`, `quality-report.json` |
| `~/.config/ufme/` | Whole machine | Survives reinstalls | Shared library registry, cross-project evidence |

Seeding never overwrites an existing file, so project memory survives reinstall.

---

## 8. Execution pipeline

The main skill runs the same seven phases in every profile; profiles change who
does the work, not the order.

```mermaid
flowchart LR
    A["01 Intake"] --> B["02 Research"]
    B --> C["03 Backend"]
    C --> D["04 Product"]
    D --> E["05 Prototype"]
    E --> F["06 Implement"]
    F --> G["07 Integrate"]
    G --> H{"Quality gate"}
    H -- findings --> F
    H -- pass --> I["Deliver"]
```

| Profile | Delegation | Use for |
|---------|-----------|---------|
| `lite` | Primary + builder | Small edits, quick prototypes |
| `standard` | Balanced, includes backend + audit | Typical projects |
| `advanced` | All roles, full audits | Complex projects |
| `autonomous` | All roles, exhaustive verification | Unattended runs |

---

## 9. Evidence and the quality gate

Audits do not report from screenshots or intuition; they read script output.

```mermaid
flowchart TB
    B["browser-test.sh"] --> J1["browser-results.json"]
    A["audit-a11y.js"] --> J2["a11y-results.json"]
    P["audit-perf.sh"] --> J3["perf-results.json"]
    V["visual-diff.js"] --> J4["visual-diff.json"]
    S["detect-slop.py"] --> J5["slop-results.json"]
    J1 & J2 & J3 & J4 & J5 --> Q["quality-check.py"]
    Q --> R["quality-report.json"]
    R --> D{"PASS / FAIL / SKIPPED / BLOCKED"}
```

| Status | Meaning |
|--------|---------|
| `PASS` | Check ran, evidence is fresh and within threshold |
| `FAIL` | Check ran and exceeded a threshold, or evidence was missing/stale |
| `SKIPPED` | Preconditions missing (no browser, no URL); never counts as a pass |
| `BLOCKED` | Required check could not run (for example, no visual baseline) |

A required check that is skipped or has stale evidence **blocks** the gate. The
design linter (`detect-slop.py`) is deliberately strict: fix the design, never
the linter.

---

## 10. Registry (optional)

`registry-server/` is a separate deployable: a Vercel function set that speaks
MCP over JSON-RPC and stores one shared library registry. It is optional — the
local Markdown registry is the default — and it fails closed: no configured key
means `503`, a wrong key means `401`.

See [registry-server/README.md](../registry-server/README.md) for endpoints,
storage, and deployment.

---

## 11. Invariants

These are the rules that keep the repository working. A change that breaks one
of them is a bug, not a style choice.

- [ ] `.opencode/` and `CATALOG.md` are never edited by hand.
- [ ] An agent's frontmatter `name` equals its file stem.
- [ ] Skills stay self-contained; an installed skill never reaches back into the repo.
- [ ] Scripts resolve the repo root from their own path, never from `$PWD`.
- [ ] Runtime state goes to `.ufme/`, never into the source tree.
- [ ] The registry fails closed.
- [ ] `detect-slop.py` is not weakened to make a site pass.
