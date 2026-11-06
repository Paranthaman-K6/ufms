# Fixes — audited defects

Each entry: what broke, the evidence, the root cause, the fix, and the regression check.
Status values: `fixed`, `open`, `wontfix`.

## F1 — Linter could not read React/Tailwind code

- **Evidence:** `detect-slop.py` scanned only `.html/.css`; the failure site is `.tsx`.
- **Root cause:** `iter_source_files()` filtered by `HTML_EXTS | CSS_EXTS`.
- **Fix:** scan `.jsx/.tsx/.vue/.svelte`; parse JSX brace props (`width={320}`) so expression
  props are not reported as missing.
- **Check:** `tests/quality/run.py` — "design slop scans component files and flags uniform motion".

## F2 — No rule for uniform entrance motion

- **Evidence:** the same `variants={slideUp}` on 7 components; every audit passed.
- **Root cause:** no rule existed.
- **Fix:** `uniform-entrance-motion` — the same `variants={X}` on 4+ components fails.
- **Check:** same test as F1.

## F3 — Canonical design system was never validated

- **Evidence:** `.ufme/DESIGN_SYSTEM.md` was the empty template while the real design lived in
  `.ufme/design/DESIGN_SYSTEM.md`; the gate passed.
- **Root cause:** path drift plus no completeness rule.
- **Fix:** `design-system-incomplete` validates the canonical file for `design direction`,
  typography, color, component, and animation sections; empty sections, template bullets, and a
  lone table header fail. `--design FILE` overrides, `--no-design` skips.
- **Check:** `tests/quality/run.py` — "quality gate fails an empty design system".

## F4 — Quality gate skipped the design check when the file was absent

- **Evidence:** `quality-check.py` passed `--design` only when
  `<slopPath>/.ufme/DESIGN_SYSTEM.md` existed, so a project without one passed silently.
- **Root cause:** conditional flag.
- **Fix:** always pass `--design`; `UFME_SLOP_SKIP_DESIGN=1` is the explicit escape hatch.
- **Check:** gate test with a missing design file.

## F5 — Visual audit could pass with an empty findings table

- **Evidence:** `.ufme/VISUAL_AUDIT.md` was a header-only table and the workflow reported PASS.
- **Root cause:** no acceptance rule on the audit artifact.
- **Fix:** `workflows/09-visual-audit.md`, `agents/auditor.md`, and `SKILL.md` state that an empty
  table is FAIL and name grid integrity, media legibility, dead controls, and motion variety as
  required checks.
- **Check:** doc assertions in `tests/auditor/run.py`.

## F6 — Design system template was not a gate

- **Evidence:** an untouched seed could be presented as a finished design.
- **Root cause:** the template's prompts were plain bullets with no values.
- **Fix:** the template keeps prompts inside an HTML comment; required sections are empty, so an
  untouched seed fails.
- **Check:** `tests/quality/run.py` empty-design test.

## F7 — `approve_package()` crashed on every approval

- **Evidence:** `re.sub(..., r"\1approved |", ...)` with no capture group raises
  `PatternError: invalid group reference 1`.
- **Root cause:** replacement string assumes a group that the pattern does not have.
- **Fix:** replace with a lambda that rewrites the status column; add a test.
- **Check:** `tests/quality/run.py` — "approve rewrites status without a regex crash".

## F8 — Motion section alternate heading mapping was inverted

- **Evidence:** `DESIGN_ALTERNATE_HEADINGS = {"motion": "animation"}` but the lookup is
  `get("animation")`, so a `## Motion` heading never matched.
- **Root cause:** map written backwards.
- **Fix:** `{"animation": "motion"}`.
- **Check:** design-system test with a `## Motion` heading.

## F9 — Installed skill references a source path that global install does not copy

- **Evidence:** `.opencode/skills/universal-frontend-master/SKILL.md` says
  `Run scripts from universal-frontend-master-source/scripts/`; global install copies only
  `SKILL.md`, so the scripts do not exist there.
- **Root cause:** the installed skill is a stub, not a self-contained package.
- **Fix:** install copies the whole skill directory (scripts, templates, workflows) into
  `~/.config/opencode/skills/universal-frontend-master/`; the SKILL.md resolves scripts relative
  to the skill directory and documents the project path.
- **Check:** `tests/install/run.sh` asserts `scripts/detect-slop.py` exists in the installed skill.

## F10 — Four skill directories, four naming schemes

- **Evidence:** `universal-frontend-master-source/`, `ufmw_seo_protocol_skill/`,
  `ufmw_frontend_design_skill/`, `skills/init-frontend/`.
- **Root cause:** incremental additions.
- **Fix:** one `skills/<kebab-name>/` root; one top-level `agents/` and `commands/`; a generated
  `CATALOG.md`.
- **Check:** `scripts/catalog.py --check`.

## F11 — Library registry could not be shared or updated remotely

- **Evidence:** registry lived only in `~/.config/ufme/LIBRARY_REGISTRY.md` and project
  `.ufme/LIBRARY_REGISTRY.md`.
- **Root cause:** no remote store.
- **Fix:** optional `registry-server/` (Vercel MCP, env-key auth, Vercel Blob) plus
  `registry-remote.py`; local files remain the default.
- **Check:** `node registry-server/test/run.mjs`.

## F12 — Registry seeded with low-value, unverified entries

- **Evidence:** eight hand-written rows, no star counts, no verified licenses, several stale.
- **Root cause:** no research pass.
- **Fix:** seed from live GitHub metadata (`registry-server/seed.json`) with stars, SPDX license,
  repo URL, npm package, and category.
- **Check:** `registry-server/test/run.mjs` validates every seed row.

## F13 — Repo docs describe a layout that no longer exists

- **Evidence:** README, install.sh comments, and docs reference the old paths.
- **Root cause:** rename without doc update.
- **Fix:** regenerate `README.md`, `AGENTS.md`, `CATALOG.md`, and install help from the new
  layout; `scripts/catalog.py --check` fails on drift.
- **Check:** `npm test` + `catalog.py --check`.
