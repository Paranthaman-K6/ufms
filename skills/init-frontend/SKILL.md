---
name: init-frontend
description: Initialize frontend projects with a design system — tokens, component architecture, responsive layout, accessibility foundations, performance budgets, and template selection based on project type.
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

## Commands (`ufmw/`)

| Command | Purpose |
|---------|---------|
| `ufmw init-frontend <project-name> [type]` | Scaffold new project (structure, tokens, component library, responsive base, a11y, perf budget, CI) |
| `ufmw init-frontend tokens` | Initialize design-token tier + Style Dictionary build |
| `ufmw init-frontend component <name>` | Add component with full state matrix, stories, a11y test |
| `ufmw init-frontend template <category>` | Download template by category, re-apply init-frontend principles |
| `ufmw init-frontend audit` | Run quality gates: token audit, a11y, performance budget, responsive check |

Template categories: landing, portfolio, blog, ecommerce, dashboard, admin, saas, docs, restaurant, realestate, event, nonprofit, resume, plus examples/ (12 example sites).

## Profiles

| Profile | Constraints |
|---------|-------------|
| basic | Tokens, component library, responsive base, a11y, perf budget, CI |
| advanced | All basic + state matrix per component, stories, CI-enforced perf budget, words-first design direction, coverage gates |

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
- Verified with axe-core.

## Performance (P75, mobile + desktop)

- LCP ≤ 2.5s
- INP ≤ 200ms
- CLS ≤ 0.1
- Input budget total ≤ 1.5MB
- JS ≤ 300KB
- CSS ≤ 100KB
- LCP image ≤ 200KB

## Workflow

1. Read `.ufme/AGENT_STATE.md`, `.ufme/TASKS.md`, `.ufme/ENVIRONMENT.md`.
2. Ask project type and template category (default: landing).
3. Run `scripts/init-frontend.sh <project-name> [type]`.
4. Initialize design tokens (`tokens` command).
5. Scaffold responsive base + component library.
6. Configure CI with perf budget and a11y gates.
7. Run `audit` to verify WCAG 2.2 AA + performance budgets.
8. Update `.ufme/AGENT_STATE.md` and `.ufme/TASKS.md`.

## Prohibited

- Do not run `sudo`, `pacman`, `systemctl`, `doas`, `pkexec`, or `su`.
- Do not install system packages.
- No Playwright, no containers.
- No removed focus outlines, no sub-24px targets, no Inter by default.
- Do not silently bypass missing dependencies — record in `.ufme/ENVIRONMENT.md`, prompt the user, mark BLOCKED.
