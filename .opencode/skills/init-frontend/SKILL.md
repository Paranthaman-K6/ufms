---
name: init-frontend
description: Initialize frontend projects with a design system — tokens, component architecture, responsive layout, accessibility foundations, performance budgets, and template selection based on project type. Asks ALL design questions before writing any code.
license: MIT
compatibility: opencode
metadata:
  category: frontend-initialization
  architecture: single-agent
  scope: project
  depends_on:
    - ufmw-frontend-design
---

# init-frontend — Master Skill

## Trigger

Use `@init-frontend` when the task is to initialize a new frontend project with a design system — not just scaffolding. Triggers: "init frontend", "frontend init", "scaffold frontend", "new frontend project", "design system init", "frontend setup".

**Golden Rule: Questions First, Code Second.** No code is written until ALL design questions are answered.

## Commands (`ufmw/`)

| Command | Purpose |
|---------|---------|
| `ufmw init-frontend <project-name> [type]` | Scaffold new project (structure, tokens, component library, responsive base, a11y, perf budget, CI) |
| `ufmw init-frontend tokens` | Initialize design-token tier + Style Dictionary build |
| `ufmw init-frontend component <name>` | Add component with full state matrix, stories, a11y test |
| `ufmw init-frontend template <category>` | Download template by category, re-apply init-frontend principles |
| `ufmw init-frontend audit` | Run quality gates: token audit, static a11y, performance budget, responsive check |

Template categories: landing, portfolio, blog, ecommerce, dashboard, admin, saas, docs, restaurant, realestate, event, nonprofit, resume, plus examples/ (12 example sites).

## Profiles

| Profile | Constraints |
|---------|-------------|
| basic | Tokens, component library, responsive base, a11y, perf budget, CI |
| advanced | All basic + state matrix per component, stories, CI-enforced perf budget, words-first design direction, coverage gates |

## Mandatory Question-First Flow (before any code)

The agent asks ALL of these via chat. No code is written until every question is answered:

1. **Project name** (required)
2. **Template type** (default: landing) — landing, portfolio, blog, ecommerce, dashboard, admin, saas, docs, restaurant, realestate, event, nonprofit, resume, or custom
3. **Profile** (default: basic) — basic or advanced
4. **Background** (choose one or more): solid color, gradient, background image, background video, dark theme, light theme, system preference, brand primary color, brand accent color, none
5. **Animation** (choose one or more): fade-in on load, slide-up on scroll, parallax scrolling, hover effects, page transitions, loading spinner/skeleton, staggered list reveals, none
6. **Reference websites** (optional): URLs you like — researched before design decisions
7. **Interactivity** (choose one or more): hover state changes, click/tap behaviors, form validation, modal dialogs, carousel/slider, mobile hamburger menu, sticky navigation, scroll-to-top button, none
8. **Content sections** (choose one or more): hero, about, services, portfolio/work, testimonials, contact, pricing, FAQ, blog/news, none/custom
9. **Typography**: 14 font pairings or custom or system fonts only
10. **Color palette**: 13 curated palettes or custom colors or none/defaults

Each question has multiple choices + "none" / "custom" option. Nothing is assumed.

## Research Phase (before design decisions)

Reference URLs provided are researched via `ask-matt` subagent before design decisions:
- Extracts color schemes, typography, layout patterns, interaction styles
- Findings feed into design token choices
- You approve or adjust before scaffold

## Anti-AI-Slop Rules

1. No Inter by default — choose a typeface appropriate to the project type.
2. No purple/blue gradients.
3. No hero+3-cards boilerplate.
4. No glassmorphism.
5. No sub-24px touch targets.
6. No removed focus outlines.
7. Words first — content and hierarchy before decoration.
8. Constraints before options — encode limits, don't offer endless choice.

## Accessibility (WCAG 2.2 AA)

- Semantic HTML throughout.
- `focus-visible` rings on all interactive elements.
- Real labels for every input (never placeholder-only).
- ≥4.5:1 text contrast / ≥3:1 UI contrast.
- Full keyboard navigation.
- Reduced-motion support.
- Verified with static a11y gate (scripts/a11y.cjs).

## Performance Budgets (P75, mobile + desktop)

- LCP ≤ 2.5s
- INP ≤ 200ms
- CLS ≤ 0.1
- Input budget total ≤ 1.5MB
- JS ≤ 300KB
- CSS ≤ 100KB
- LCP image ≤ 200KB

## Workflow

1. Read `.ufme/AGENT_STATE.md`, `.ufme/TASKS.md`, `.ufme/ENVIRONMENT.md`.
2. Ask ALL design questions via chat (background, animation, references, interactivity, content, typography, color).
3. Research reference URLs (if provided) via `ask-matt`.
4. Run `scripts/init-project.py` to record answers in `.ufme/DESIGN_SYSTEM.md` and `.ufme/design-choices.json`.
5. Run `scripts/init-frontend.sh <project-name> [type]` to scaffold (only after questions answered).
6. Initialize design tokens (`ufmw init-frontend tokens`).
7. Configure CI with perf budget and a11y gates.
8. Run `ufmw init-frontend audit` to verify WCAG 2.2 AA + performance budgets.
9. Update `.ufme/AGENT_STATE.md` and `.ufme/TASKS.md` after each step.

## Prohibited

- Do not run `sudo`, `pacman`, `systemctl`, `doas`, `pkexec`, or `su`.
- Do not install system packages.
- No Playwright, no containers.
- No removed focus outlines, no sub-24px targets, no Inter by default.
- Do not silently bypass missing dependencies — record in `.ufme/ENVIRONMENT.md`, prompt the user, mark BLOCKED.
- Do NOT scaffold before design questions are answered.

## Delegation

- No sub-agents by default (single-agent architecture). For complex multi-template projects, delegate to `@ufmw-frontend-design` for reference-driven design work.
