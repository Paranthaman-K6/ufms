# init-frontend — Detailed Documentation

Initialize frontend projects with a design system — not just scaffolding. Sets up tokens, component architecture, responsive layout, accessibility foundations, performance budgets, and template selection based on project type.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Questions First — Mandatory Design Questionnaire](#questions-first--mandatory-design-questionnaire)
6. [Commands Reference](#commands-reference)
7. [Templates](#templates)
8. [Profiles (basic vs advanced)](#profiles-basic-vs-advanced)
9. [Design System & Anti-AI-Slop Rules](#design-system--anti-ai-slop-rules)
10. [Accessibility (WCAG 2.2 AA)](#accessibility-wcag-22-aa)
11. [Performance Budgets](#performance-budgets)
12. [Project Structure After Init](#project-structure-after-init)
13. [CI Integration](#ci-integration)
14. [Examples](#examples)
15. [Troubleshooting](#troubleshooting)
16. [Security & Safety](#security--safety)

---

## Overview

The `init-frontend` skill transforms a project brief into a complete, accessible, performant frontend project with a design system foundation. Unlike basic scaffolding tools that generate generic boilerplate, `init-frontend`:

- **Asks design questions first** — palette, typography, visual style, reference URLs (mandatory, not skippable)
- **Enforces constraints** — anti-AI-slop rules prevent generic, low-quality output
- **Builds a design system** — Style Dictionary tokens, semantic color/typography/spacing scales
- **Bakes in accessibility** — WCAG 2.2 AA from day one, axe-core verified
- **Enforces performance budgets** — LCP, INP, CLS, input size limits in CI
- **Supports templates** — 13 categories: landing, portfolio, blog, ecommerce, dashboard, admin, saas, docs, restaurant, realestate, event, nonprofit, resume

---

## Prerequisites

| Requirement | Minimum | Notes |
|-------------|---------|-------|
| Node.js | 18+ | For Vite, axe-core, Lighthouse |
| npm / pnpm / yarn | Any | Package manager of choice |
| Git | 2.0+ | For version control |
| OpenCode | Latest | The skill runs within OpenCode |
| `ufmw-frontend-design` skill | Installed | Listed as a dependency |

---

## Installation

The `init-frontend` skill is installed automatically when you run `install.sh` (scope: both or project+global). It installs to:

- **Global**: `~/.config/opencode/skills/init-frontend/` — available in every project
- **Project-local**: `<project>/.opencode/skills/init-frontend/` — project override

### Install from GitHub

```bash
# Global install (available in every project)
curl -fsSL https://raw.githubusercontent.com/Paranthaman-K6/ufms/main/install.sh | bash

# Project-local install only
INSTALL_SCOPE=project curl -fsSL https://raw.githubusercontent.com/Paranthaman-K6/ufms/main/install.sh | bash

# Check for installer updates
install.sh --check-update

# Self-update installer to latest main
install.sh --self-update
```

### Verify Installation

```bash
# Check the skill is installed
ls ~/.config/opencode/skills/init-frontend/

# Check commands are available
ls ~/.config/opencode/commands/ufmw/init-frontend*

# Check agent is installed
ls ~/.config/opencode/agents/init-frontend.md
```

**Important**: After installing a new skill, restart or reload OpenCode so it discovers the new agent and commands.

---

## Quick Start

### 1. Initialize a new project

```bash
# Interactive mode (prompts for project name, type, profile)
ufmw init-frontend my-saas-app saas

# Non-interactive with all defaults
ufmw init-frontend my-landing-page landing
```

### 2. Answer the design questions (mandatory)

The init flow asks three required questions:

| Question | Options | Example Choice |
|----------|---------|----------------|
| Color palette | 13 curated palettes (Tailwind Slate, GitHub Dim Dark, Stripe Gradient Blue, etc.) | Stripe Gradient Blue |
| Font pairing | 14 font combinations (Inter+JetBrains, Playfair+Source Sans, etc.) | IBM Plex Sans + Plex Mono |
| Visual style | 14 styles (Minimal Monochrome, Neo-Brutalism, Glassmorphism, etc.) | Minimal Monochrome |
| Reference URLs | Optional, paste any URLs (blank to finish) | https://stripe.com |

Pressing Enter without a valid choice re-prompts — these cannot be skipped.

### 3. Review generated files

```bash
cd my-saas-app
ls -la
# src/tokens/  src/components/  src/styles/  src/pages/
# perf-budget.json  .github/workflows/ci.yml  README.md
```

### 4. Install dependencies and run

```bash
npm install
npm run dev
```

### 5. Run the audit

```bash
ufmw init-frontend audit
```

---

## Questions First — Mandatory Design Questionnaire

**No code is written until every design question is answered.** The scaffold script (`init-frontend.sh`) checks for `.ufme/DESIGN_SYSTEM.md` and refuses to run if design questions haven't been answered.

### The Rule

```
Questions → .ufme/DESIGN_SYSTEM.md → Scaffold code → Tokens → Audit
     ↑                                                      │
     └──────────────────────────────────────────────────────┘
           Code only after all answers recorded
```

### Interactive Mode (terminal with TTY)

When run in an interactive terminal, `init-project.py` prompts you for each answer:

```bash
python3 universal-frontend-master-source/scripts/init-project.py .
```

You'll be asked:
1. **Project name** (required)
2. **Template type** (default: `landing`)
3. **Profile** (`basic` or `advanced`, default: `basic`)
4. **Color palette** (required — choose from 13 options)
5. **Font pairing** (required — choose from 14 options)
6. **Visual style** (required — choose from 14 options)
7. **Reference URLs** (optional — paste URLs, blank line to finish)

Each question is mandatory. Invalid choices re-prompt. Answers are saved to `.ufme/DESIGN_SYSTEM.md` and `.ufme/design-choices.json`.

### Non-Interactive Mode (OpenCode agent / CI / no TTY)

When there's no TTY (e.g. OpenCode agent context), pass answers via CLI flags:

```bash
python3 universal-frontend-master-source/scripts/init-project.py . \
  --project-name my-saas-app \
  --type saas \
  --profile advanced \
  --palette "Stripe Gradient Blue" \
  --font "IBM Plex Sans + Plex Mono" \
  --style "Minimal Monochrome" \
  --refs "https://stripe.com"
```

**All required flags must be provided.** If any are missing, the script prints all questions and exits with code 2 — no code is scaffolded.

List available options:
```bash
python3 init-project.py --list-palettes
python3 init-project.py --list-fonts  
python3 init-project.py --list-styles
```

### Step 2 — Scaffold (only after questions answered)

```bash
python3 universal-frontend-master-source/scripts/init-frontend.sh my-saas-app saas
# or:
ufmw init-frontend my-saas-app saas
```

The scaffold reads `.ufme/design-choices.json` to apply your chosen palette, font, style, and profile to the generated tokens and project structure.

---

## Commands Reference

### `ufmw init-frontend <project-name> [type]`

Scaffold a new frontend project with full design system.

**Arguments:**
- `project-name` — Directory name for the new project (required)
- `type` — Template category (default: `landing`)

**Valid types:**
`landing`, `portfolio`, `blog`, `ecommerce`, `dashboard`, `admin`, `saas`, `docs`, `restaurant`, `realestate`, `event`, `nonprofit`, `resume`

**What it creates:**
- Project directory with `src/{components,tokens,pages,styles,assets,utils}/`
- Design tokens (color, typography, spacing) as CSS variables + JSON
- Responsive base styles with focus-visible rings, 24px min touch targets
- `package.json` with Vite, Vitest, axe-core, Lighthouse
- `perf-budget.json` with Lighthouse CI budgets
- `.github/workflows/ci.yml` with build + a11y + perf gates
- `README.md` with project docs

**Example:**
```bash
ufmw init-frontend dashboard dashboard
ufmw init-frontend my-blog blog
ufmw init-frontend store ecommerce
```

---

### `ufmw init-frontend tokens`

Initialize the design-token tier with a Style Dictionary build pipeline.

**What it creates:**
- `src/tokens/color.json` — semantic color tokens
- `src/tokens/typography.json` — font families, sizes, weights, line heights
- `src/tokens/spacing.json` — spacing scale
- `style-dictionary.config.js` — Style Dictionary build config
- Updates `.ufme/DESIGN_SYSTEM.md` with token definitions

**Example:**
```bash
# Run inside your initialized project
ufmw init-frontend tokens

# Then build tokens
npx style-dictionary build
```

---

### `ufmw init-frontend component <name>`

Add a component with full state matrix, Storybook stories, and accessibility test.

**Arguments:**
- `name` — Component name in PascalCase (e.g. `Button`, `Card`, `Nav`)

**What it creates:**
- `src/components/<Name>/<Name>.jsx` — Component source
- `src/components/<Name>/<Name>.stories.jsx` — Storybook stories (Default + States)
- `src/components/<Name>/<Name>.a11y.test.jsx` — axe-core accessibility test
- `src/components/<Name>/<Name>.states.md` — State matrix documentation

**Example:**
```bash
ufmw init-frontend component Button
ufmw init-frontend component Card
ufmw init-frontend component Navigation
```

**Generated state matrix covers:** Default, Loading, Empty, Error states.

---

### `ufmw init-frontend template <category>`

Download/apply a template by category and re-apply init-frontend design-system principles.

**Arguments:**
- `category` — Template category (same list as init command)

**What it does:**
- Copies template files into the current project directory
- Records template source in `.ufme/REFERENCES.md`
- Re-applies init-frontend constraints (tokens, a11y, perf)

**Example:**
```bash
ufmw init-frontend template saas
ufmw init-frontend template ecommerce
```

---

### `ufmw init-frontend audit`

Run quality gates: token audit, accessibility, performance budget, responsive check.

**What it checks:**
- Design tokens exist (color, typography, spacing JSON)
- Base CSS has `focus-visible` rings
- Base CSS enforces 24px minimum touch targets
- Reduced-motion support in CSS
- Performance budget config exists

**Output:**
- `.ufme/evidence/audit-results.json` — machine-readable results
- `.ufme/AUDIT_REPORT.md` — human-readable pass/fail report

**Example:**
```bash
ufmw init-frontend audit
# Exit 0 = all pass, Exit 1 = failures present
```

---

## Templates

| Category | Description | Best For |
|----------|-------------|----------|
| `landing` | Marketing landing page | Product launches, SaaS marketing |
| `portfolio` | Personal portfolio | Designers, developers, artists |
| `blog` | Content blog | Writers, technical blogs |
| `ecommerce` | Online store | Retail, product sales |
| `dashboard` | Data dashboard | Admin panels, analytics |
| `admin` | Admin interface | CMS, internal tools |
| `saas` | SaaS application | Multi-tenant web apps |
| `docs` | Documentation site | API docs, knowledge bases |
| `restaurant` | Restaurant site | Food & beverage |
| `realestate` | Real estate listing | Property listings |
| `event` | Event page | Conferences, weddings |
| `nonprofit` | Nonprofit org | Charities, foundations |
| `resume` | Personal resume/CV | Job seekers |

Plus `examples/` — 12 example reference sites.

### Adding a New Template

1. Create `skills/init-frontend/templates/<category>/`
2. Add template files (HTML, CSS, JS, etc.)
3. Add entry to `skills/init-frontend/templates/README.md`
4. Reinstall the skill: `install.sh --self-update`

---

## Profiles: basic vs advanced

| Feature | basic | advanced |
|---------|-------|----------|
| Design tokens | ✅ | ✅ |
| Component library | ✅ | ✅ |
| Responsive base | ✅ | ✅ |
| Accessibility (WCAG 2.2 AA) | ✅ | ✅ |
| Performance budgets | ✅ | ✅ |
| CI configuration | ✅ | ✅ |
| Component state matrix | ❌ | ✅ |
| Storybook stories | ❌ | ✅ |
| CI-enforced perf budget | ❌ | ✅ |
| Words-first design direction | ❌ | ✅ |
| Coverage gates | ❌ | ✅ |

**Choose basic for:** Simple landing pages, marketing sites, prototypes
**Choose advanced for:** Dashboards, SaaS apps, production applications

---

## Design System & Anti-AI-Slop Rules

All init-frontend output enforces these constraints:

| Rule | What it means |
|------|---------------|
| **No Inter by default** | Choose typeface appropriate to project type (e.g. serif for editorial, mono for dev tools) |
| **No purple/blue gradients** | Avoid generic gradient backgrounds |
| **No hero+3-cards boilerplate** | No overused "hero section + three feature cards" layout |
| **No glassmorphism** | No frosted-glass backdrop-filter effects |
| **No sub-24px touch targets** | All interactive elements ≥ 24px × 24px |
| **No removed focus outlines** | `focus-visible` rings always preserved |
| **Words first** | Content hierarchy before decoration |
| **Constraints before options** | Encode limits, don't offer endless choice |

These rules are baked into the generated CSS and cannot be opted out of.

---

## Accessibility (WCAG 2.2 AA)

| Requirement | Implementation |
|-------------|----------------|
| Semantic HTML | `<header>`, `<nav>`, `<main>`, `<footer>`, `<section>`, `<article>` |
| Focus visible rings | `outline: 2px solid var(--color-focus-ring)` on `:focus-visible` |
| Real labels | Every `<input>`, `<select>`, `<textarea>` has associated `<label>` |
| Text contrast | ≥ 4.5:1 for normal text, ≥ 3:1 for UI components |
| Keyboard nav | All interactive elements reachable via Tab |
| Reduced motion | `@media (prefers-reduced-motion: reduce)` disables animations |
| Skip link | `.skip-link` for keyboard users to bypass navigation |
| Touch targets | Minimum 24px × 24px for all interactive elements |

Verified with **axe-core** via `npm run test:a11y`.

---

## Performance Budgets (P75, mobile + desktop)

| Metric | Budget | Tool |
|--------|--------|------|
| LCP | ≤ 2.5s | Lighthouse |
| INP | ≤ 200ms | Lighthouse |
| CLS | ≤ 0.1 | Lighthouse |
| Total input | ≤ 1.5MB | Lighthouse |
| JavaScript | ≤ 300KB | Lighthouse |
| CSS | ≤ 100KB | Lighthouse |
| LCP image | ≤ 200KB | Lighthouse |

Budgets are defined in `perf-budget.json` and enforced in CI via GitHub Actions + Lighthouse CI.

---

## Project Structure After Init

```
my-project/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI: build + a11y + perf
├── .ufme/                      # Project memory (gitignored)
│   ├── AGENT_STATE.md
│   ├── TASKS.md
│   ├── DESIGN_SYSTEM.md
│   └── evidence/
├── public/
├── src/
│   ├── components/             # Component library
│   ├── tokens/                 # Design tokens (color, typography, spacing)
│   ├── pages/                  # Page components
│   ├── styles/
│   │   └── base.css            # Reset, focus rings, responsive base
│   ├── assets/                 # Images, fonts, icons
│   └── utils/                  # Helper functions
├── perf-budget.json            # Lighthouse CI budgets
├── style-dictionary.config.js  # Token build config
├── package.json                # Vite, Vitest, axe-core, Lighthouse
└── README.md                   # Project documentation
```

---

## CI Integration

The generated `.github/workflows/ci.yml` runs on every push and PR:

```yaml
name: CI
on: [push, pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm run build
      - run: npm run test:a11y     # axe-core WCAG 2.2 AA
      - run: npm run test:perf     # Lighthouse performance budgets
```

Available npm scripts:

| Script | Purpose |
|--------|---------|
| `npm run dev` | Start Vite dev server |
| `npm run build` | Production build |
| `npm run preview` | Preview production build |
| `npm run test` | Run Vitest unit tests |
| `npm run test:a11y` | axe-core accessibility audit |
| `npm run test:perf` | Lighthouse performance budget check |

---

## Examples

### Landing page (basic profile)

```bash
ufmw init-frontend my-product landing
```

Generates: hero section, feature grid, CTA, responsive nav, footer. Design tokens: Tailwind Slate Classic palette, Inter+JetBrains Mono fonts.

### SaaS dashboard (advanced profile)

```bash
ufmw init-frontend saas-dashboard saas --profile advanced
```

Generates: dashboard layout, data tables, charts sidebar, user profile, settings. Component state matrix for all interactive elements. CI-enforced performance budgets.

### Ecommerce store

```bash
ufmw init-frontend store ecommerce
```

Generates: product grid, product detail, cart, checkout flow. Accessibility-focused forms with real labels.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ufmw: command not found` | Restart OpenCode after skill installation; verify `~/.config/opencode/commands/ufmw/init-frontend.md` exists |
| Design questions keep re-prompting | Enter a valid number from the list (1-N), not the option text |
| Skill not found in OpenCode | Run `install.sh --self-update` then restart OpenCode |
| Audit fails on contrast | Adjust `--color-text` or `--color-bg` tokens in `src/tokens/color.json` |
| Perf budget fails in CI | Optimize images, reduce JS bundle, inline critical CSS |
| `scripts/init-frontend.sh` not found | Reinstall skill: `install.sh --self-update` |

---

## Security & Safety

The skill follows strict safety rules:

- ❌ No `sudo`, `pacman`, `systemctl`, `doas`, `pkexec`, or `su`
- ❌ No system package installation
- ❌ No Playwright, no containers
- ❌ No removed focus outlines or sub-24px targets
- ❌ No Inter font by default
- ✅ Missing dependencies recorded in `.ufme/ENVIRONMENT.md`, user prompted, marked BLOCKED
- ✅ Existing project memory (`.ufme/`) never overwritten during repeat installs

---

## Support

- Skill definition: `skills/init-frontend/SKILL.md`
- Agent: `skills/init-frontend/agents/init-frontend.md`
- Scripts: `skills/init-frontend/scripts/`
- Commands: `skills/init-frontend/commands/ufmw/`
- Templates: `skills/init-frontend/templates/`
- Installer: `install.sh` (supports `--self-update`, `--check-update`, `INSTALL_SCOPE`)
