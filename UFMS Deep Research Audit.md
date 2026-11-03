# UFMS (Universal Frontend Master) — Deep Research Audit

Repo: https://github.com/Paranthaman-K6/ufms (1 commit, `f557cbc`, audited 3 Nov 2026)
Method: cloned the repo, ran `npm test`, `self-improve.py`, `generate-prototype.py`, `detect-stack.sh`, ran `install.sh` into an empty project, and compared against the most-starred frontend/design skill repos.

---

## 1. Verdict in one paragraph

UFMS has strong engineering bones — honest PASS/FAIL/SKIPPED/BLOCKED reporting, a real safety boundary, evidence-based backend parsing, and a Selenium layer with network capture. But it is built as a **heavy process framework** (12 agents, 14 workflows, 20 templates, ~25 memory artifacts) with **almost no design intelligence** and **no token-saving mechanics**. The top repos win the opposite way: small always-loaded instructions, data/rules pulled on demand by scripts, and deterministic checkers that return short findings instead of making the model read screenshots and files. There is also one blocking bug: **browser testing cannot work in any installed project** (see 3.1).

---

## 2. What is in the repo (scripts and programs)

### Scripts (`universal-frontend-master-source/scripts/`)

| Script | What it does | Token impact today |
|---|---|---|
| `detect-stack.sh` / `backend-discovery.sh` | Detect frameworks, build tools, API specs | Good — replaces manual file reading |
| `enhance-backend-discovery.py` | Parses OpenAPI/Swagger/Postman/GraphQL/AsyncAPI → `BACKEND_CONTRACTS.md` | Good, but output is a full markdown dump (no `--summary` / per-endpoint query) |
| `check-native-browser.sh` | Verifies Chromium/Firefox + Selenium Manager | Neutral |
| `browser-test.sh` → `tests/browser/run.js` | Visits URL, collects console/network errors, screenshots | **Costly**: full-page screenshots at 4 viewports × 2 themes |
| `screenshot.sh` → `tests/browser/screenshot.js` | Resizes window to full `scrollHeight` and captures | **Most expensive part of the skill** — tall PNGs fed to the visual auditor |
| `quality-check.py` | tsc, eslint, prettier, test, build, browser, npm audit → JSON | Good — but a11y (axe) and perf (Lighthouse) are hard-coded `SKIPPED` |
| `search-libraries.py` | User/project registry + npm search, select/approve | Good pattern (script-side search) |
| `discover-assets.py` | Image/font/video inventory, hash dedupe | Good |
| `generate-prototype.py` | HTML/CSS prototype from `.ufme/` files | Generic output; no design-system reasoning |
| `task-checkpoint.py` | Dependency-aware TASKS.md updates | Good — avoids re-writing the whole file |
| `execution-profiles.sh` + `profiles/*.json` | lite/standard/advanced/autonomous | **Profiles are not enforced** anywhere; nothing reads `maxAgents` |
| `self-improve.py` | Audits the skill's own files (265 checks) | Fails on a clean clone (3 FAIL: missing seeded memory) |
| `detect-platform.sh` | OS/distro detection | Arch-specific value only |
| `integrations/mcp/discover.js` | Lists "known" MCP servers | Hard-coded list (`rea`, `skillspector`…); doesn't actually query the host |

### Tests
`npm test` passes (validate + security + regression: 5 pass, 3 skipped). Real-browser tests only run with `--real-browser`, and there is no CI (`.github/` is absent).

---

## 3. Things to fix (prioritized)

### 3.1 Critical — broken on install
1. **`install.sh` does not copy `tests/browser/`**, but `browser-test.sh` and `screenshot.sh` call `$ROOT_DIR/tests/browser/run.js`. Verified: after install into an empty dir, `tests/` does not exist. Browser testing, screenshots, and the mandatory visual auditor all fail in every real project.
   Fix: move the browser runner into `universal-frontend-master-source/browser/` (or the skill folder) and reference it relative to the script.
2. **`selenium-webdriver` is not installed into the target project.** Install only copies files. Add an opt-in `npm i -D selenium-webdriver` step or make `check-native-browser.sh` print it (it does print it, but the flow stays BLOCKED).
3. **Invalid OpenCode permission keys.** Agents use `write:` and `subagent:` under `permission`. OpenCode's valid keys are `read, edit, glob, grep, list, bash, task, webfetch, websearch, skill, …`; `write` is gated by `edit`, and `subagent` is a *mode*, not a permission ([OpenCode Agents docs](https://opencode.ai/docs/agents/)). Result: your "deny write" on auditors does nothing, and the orchestrator's delegation permission should be `task`.
4. **Non-standard agent frontmatter** (`inputs`, `outputs`, `role_definition`, `prohibited_actions`, `escalation_rules`, `source`) is ignored by OpenCode (documented fields: `description, mode, model, prompt, temperature, steps, permission, hidden, …`) ([OpenCode Agents docs](https://opencode.ai/docs/agents/)) — but it still costs tokens if the file body is sent as the prompt.

### 3.2 High — correctness and drift
5. **Agents are defined twice**: in `opencode.json` (with `prompt: {file:…}`) and as `.opencode/agents/*.md`. Pick one. `install.sh` doesn't copy `opencode.json`, so installed projects get only the markdown version.
6. **Source vs installed drift**: `universal-frontend-master-source/agents/designer.md` differs from `.opencode/agents/ufme-designer.md` (verified with `diff`). Generate `.opencode/` from source with a build script and test for drift in CI.
7. **Portfolio-specific rules leaked into a "universal" skill**: SKILL.md mandates staggered reveal animations on every section, hover animation on every card, a theme toggle, an initial "P" avatar placeholder, GitHub stats, degrees/certifications. These are from one portfolio project and push every site toward the generic "AI look" — Anthropic's own skill explicitly calls fade-and-slide-up on each section and hover transitions on every card "the generic default" that "read as AI-generated" ([anthropics/skills frontend-design](https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md)).
8. **`self-improve.py` fails on a fresh clone** (missing `.ufme/TASKS.md`, `ENVIRONMENT.md`, `SKILL_VALIDATION.md`); there is no `SKILL_VALIDATION.md` template, so `install.sh` writes a stub.
9. **Profiles are decorative**: `lite.json` says `maxAgents: 2`, but SKILL.md forces an 11-step delegation chain with two "MANDATORY" agents.
10. **a11y/perf gates always SKIPPED** — the README promises WCAG and Core Web Vitals audits, but no axe-core or Lighthouse runner exists. The auditors therefore "audit" by reading code/screenshots (expensive and unreliable).
11. `package.json` name is `myskills`; `keywords` empty; Arch-Linux framing limits adoption.

### 3.3 Medium — security/safety gaps
12. The bash deny list blocks `rm -rf /` and `rm -rf ~` literally, but not `rm -rf ~/`, `rm -rf $HOME`, `rm -rf *`, `git reset --hard`, `curl … | bash`. Prefer an allow-list for the implementer, and `ask` for destructive git.
13. `curl | bash` install with no pinned tag/checksum.

---

## 4. Token audit — where UFMS spends tokens

Measured file sizes (≈ chars ÷ 4 = tokens):

| Item | Size | ≈ Tokens | When loaded |
|---|---|---|---|
| `SKILL.md` | 14.2 KB | ~3,500 | Every activation |
| 12 agent prompts (`.opencode/agents`) | 26.8 KB | ~6,700 | Each subagent call loads its own (~550 each), orchestrator ~800 |
| Agent descriptions in `opencode.json` | ~4 KB | ~1,000 | Listed to the orchestrator for delegation |
| `core/` docs | 16.8 KB | ~4,200 | If the agent follows references |
| `workflows/` (14) | 12.1 KB | ~3,000 | Per phase |
| `.ufme/` memory (grows) | unbounded | 5k–50k+ | Every agent "reads" several artifacts at start |
| Screenshots: 4 viewports × 2 themes, **full-page height** | 8 images/run | typically thousands of tokens per run, repeated on every audit loop | Visual auditor |

The real multipliers are structural, not file size:
- **11 sequential subagents** each start cold, re-read `AGENT_STATE`, `TASKS`, `DECISIONS`, `PRD`, `API_MAP`, `DESIGN_SYSTEM`… The same context is paid for 11 times per loop.
- **Audit → fix → retest loops** repeat the full screenshot set each iteration.
- **Duplicate text**: each agent file says its role 3 times (frontmatter description, `role_definition`, body). SKILL.md re-lists the 12 agents, the 11-step chain, and the 14 scripts that the README and MASTER_SKILL.md also list.
- **Markdown memory with no size cap** — DECISIONS/TASKS only grow.

---

## 5. Comparison with the highest-starred repos

| Repo | Stars | Core idea | How it saves tokens | What UFMS lacks vs it |
|---|---|---|---|---|
| [obra/superpowers](https://github.com/topics/superpowers?o=desc&s=stars) | ~309k | Methodology skills (brainstorm → plan → TDD → review) | Many tiny, single-purpose skills loaded only when triggered | Focused skills instead of one mega-skill |
| [anthropics/skills — frontend-design](https://www.skills.sh/anthropics/skills/frontend-design) | ~186k (repo) | One short SKILL.md on design taste | ~1 page; plan tokens → self-review → build; "a picture is worth 1000 tokens" — screenshot only to critique ([SKILL.md](https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md)) | Anti-"AI-look" guidance, a brief→token-plan step, copywriting rules |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://www.star-history.com/nextlevelbuilder/ui-ux-pro-max-skill/) | ~144k | Design intelligence database + BM25 search | Data lives in CSVs; `search.py` returns only top-N matches by domain/stack, truncates fields at 300 chars, persists `MASTER.md` + per-page overrides ([README](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)) | Any design knowledge base (styles, palettes, fonts, UX rules), design-system generator, per-page override memory |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | ~100k | Design vocabulary + 24 commands + deterministic detector | 62 rules run by CLI with no LLM; exit code 2 on findings; post-edit hook pushes short findings; `PRODUCT.md`/`DESIGN.md` context ([README](https://github.com/pbakaus/impeccable)); even trimmed its description from 119 → 45 words ([PR #426](https://github.com/pbakaus/impeccable/pull/426)) | A slop/quality detector, edit hooks, steer commands (bolder/quieter/polish/harden) |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills/) | ~33k | `web-design-guidelines` (100+ rules), `react-best-practices` (40+ rules, impact-ranked) | Rules are a review checklist, loaded only for review | A concrete rule set for audits (forms, focus, i18n, dark mode meta, touch) |
| [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser/blob/main/docs/content/docs/index.mdx) | ~23k+ | Browser CLI for agents | Accessibility snapshot with `@e1` refs: ~200–400 tokens vs ~3,000–5,000 for full DOM ([snapshot-refs](https://github.com/vercel-labs/agent-browser/blob/main/skill-data/core/references/snapshot-refs.md)) | Text-first page inspection instead of screenshots |

**Pattern across all of them:** keep the always-loaded part small; move knowledge into data + scripts; let deterministic tools produce compact findings; use images only for final visual critique.

---

## 6. Essentials missing in UFMS

1. **Design intelligence** — no style/palette/typography/UX-rule database, no product-type → style reasoning. `designer.md` is ~2 KB of role text. This is the #1 reason output will look generic.
2. **Anti-pattern ("AI slop") detector** — nothing checks for overused fonts, purple gradients, nested cards, `href="#"`, missing focus styles, low contrast.
3. **Real a11y + perf runners** — axe-core via Selenium (`@axe-core/webdriverjs`) and Lighthouse CLI are both promised but missing.
4. **Text-first page snapshot** — no accessibility-tree/DOM-summary output; the only way the agent "sees" the page is via images.
5. **Visual diff** — no baseline/compare, so every loop re-reviews every screenshot.
6. **Context budget enforcement** — profiles exist but nothing caps agents, memory size, or screenshot count.
7. **Edit hooks** — no post-edit check that feeds short findings back automatically.
8. **Steer commands** — no `polish / harden / critique / bolder / quieter` style entry points; one giant "build everything" command.
9. **Multi-host support** — OpenCode only; top repos ship Claude Code, Cursor, Codex, Gemini CLI, etc. ([ui-ux-pro-max README](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)).
10. **CI** — no GitHub Actions running `npm test`, drift checks, or `bash -n`.
11. **Examples** — `examples/README.md` only; no before/after showcase.
12. **UX writing guidance** — CTA naming, error/empty-state copy (covered in Anthropic's skill and impeccable).

---

## 7. Scripts/programs to add for token reduction

Ordered by savings per effort.

### 7.1 `page-snapshot.js` — text instead of screenshots (biggest win)
Run in the existing Selenium session; return a compact outline the model can read in a few hundred tokens:
```js
// returns e.g.  "@e3 [button] 'Sign in' 44x44 focus:none contrast:3.1"
const outline = await driver.executeScript(() => {
  const out = []; let i = 0;
  for (const el of document.querySelectorAll('h1,h2,h3,a,button,input,select,textarea,img,[role]')) {
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const s = getComputedStyle(el);
    const name = (el.getAttribute('aria-label') || el.alt || el.innerText || el.placeholder || '').trim().slice(0, 40);
    out.push(`@e${++i} [${el.tagName.toLowerCase()}] "${name}" ${Math.round(r.width)}x${Math.round(r.height)}`
      + (r.right > innerWidth ? ' OVERFLOW-X' : '') + (s.fontSize < '12px' ? ' TINY-TEXT' : ''));
  }
  return out.join('\n');
});
```
Policy: auditors read the snapshot + findings first; request a screenshot only for a specific section that the text flags.

### 7.2 Screenshot budget in `screenshot.js`
- Default to **viewport-only** (above the fold) at 390 and 1440 only; full-page and tablet/laptop only on `--full`.
- Downscale to ≤1280 px long edge and save as JPEG/WebP q≈70.
- Section crops (`element.takeScreenshot()`) for flagged elements instead of whole pages.
- Dark theme only if the site actually has `prefers-color-scheme` rules or a theme toggle.

### 7.3 `visual-diff.js` — only review what changed
Store `.ufme/evidence/baseline/`, compare with `pixelmatch` (small npm dep), and pass the auditor only images whose diff exceeds a threshold, plus a one-line summary per viewport.

### 7.4 `audit-a11y.js` — axe-core through Selenium
Use `@axe-core/webdriverjs`; output only `rule-id | impact | count | first selector`. 50–100 tokens instead of an LLM reading code for WCAG issues. Wire it into `quality-check.py` so the gate stops being SKIPPED.

### 7.5 `audit-perf.sh` — Lighthouse CLI, summarized
`npx lighthouse $URL --only-categories=performance,accessibility,best-practices --output=json --quiet --chrome-flags=--headless` → a Python one-pager that prints just scores + top 5 opportunities.

### 7.6 `detect-slop.py` — deterministic design linter
Regex/AST rules over HTML/CSS/JSX: `href="#"`, Inter/Arial-only font stacks, purple→pink gradients, `rgba(0,0,0,.1)` shadow everywhere, nested cards, missing `:focus-visible`, missing `prefers-reduced-motion`, `<img>` without width/height/alt, emoji used as icons. Exit 2 on findings, print one line each. (Or simply integrate `npx impeccable detect` ([impeccable](https://github.com/pbakaus/impeccable)).)

### 7.7 `ctx-pack.py` — one compact brief per subagent
Instead of each agent reading 5–8 `.ufme` files, the orchestrator runs `ctx-pack.py --for implementer --task T12` which emits ≤1,500 tokens: current task, acceptance criteria, relevant tokens from DESIGN_SYSTEM, only the endpoints this task touches from API_MAP, and the last 5 decisions. Add `--max-tokens` and summarize/rotate old DECISIONS into `DECISIONS.archive.md`.

### 7.8 `design-search.py` + `data/*.csv` — design knowledge on demand
Copy the ui-ux-pro-max pattern: CSVs for styles, palettes, font pairings, UX rules, landing patterns; BM25 or simple TF-IDF search returning top 3 with fields truncated. Persist `design-system/MASTER.md` + `pages/<page>.md` overrides ([ui-ux-pro-max README](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)).

### 7.9 `api-query.py` — slice the backend contract
`api-query.py --tag auth` or `--path /users` returns only matching endpoints from `BACKEND_CONTRACTS.md` instead of the whole map.

### 7.10 `build-agents.py` — generate, dedupe, and validate prompts
Builds `.opencode/agents/*.md` from source with only valid frontmatter, strips `role_definition` duplicates, fails CI on drift or on prompts above a size budget.

---

## 8. Restructure for token efficiency

| Change | Effect |
|---|---|
| Cut `SKILL.md` to ≤150 lines: trigger, 5 hard rules, a router table ("for X read `reference/x.md`"), script list | ~3.5k → ~1.2k tokens per activation |
| Remove `role_definition`/`inputs`/`outputs` from frontmatter; keep one body per agent | ~40% smaller agent prompts |
| Merge 12 agents → 5: orchestrator, designer (research + product + design), builder (architect + implementer + integrator), backend-analyst, auditor (visual + a11y + perf + security, driven by script outputs) | Far fewer cold starts per loop |
| Make the chain conditional: skip backend-analyst when no backend; skip product-analyst for single-page/edit tasks; `lite` profile = orchestrator + builder + script audits | Small tasks stop paying for the full pipeline |
| Auditors consume JSON from scripts, not raw files/images | Findings in hundreds of tokens, not thousands |
| Delete the portfolio-specific rules (animations everywhere, "P" avatar, degrees, GitHub stats) and replace with an anti-generic design section | Better quality and fewer tokens |
| Add steer commands: `/ufme polish`, `/ufme harden`, `/ufme critique`, `/ufme audit` | Targeted runs instead of full rebuilds |

---

## 9. Suggested roadmap

**Week 1 (fix):** ship `tests/browser` with install; fix permission keys (`edit`, `task`); single agent definition source + `build-agents.py`; seed missing templates; add GitHub Actions for `npm test` + drift check.
**Week 2 (token cuts):** `page-snapshot.js`, screenshot budget, `ctx-pack.py`, slim SKILL.md, conditional pipeline, enforce profiles.
**Week 3 (quality):** axe-core + Lighthouse runners, `detect-slop.py` (or impeccable integration), design CSV + `design-search.py`, `MASTER.md` + page overrides.
**Week 4 (reach):** steer commands, visual diff, Claude Code/Cursor/Codex install targets, before/after examples.
