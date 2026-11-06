---
description: Scaffold new frontend project with design system
---
# ufmw init-frontend

Scaffold a new frontend project with a design system — structure, tokens, component library, responsive base, accessibility foundations, performance budget, and CI.

**Mandatory:** Run `skills/universal-frontend-master/scripts/init-project.py` first to answer all design questions. The scaffold script refuses to run unless `.ufme/DESIGN_SYSTEM.md` exists.

Usage:
  ufmw init-frontend <project-name> [type]

Arguments:
  project-name  Name of the project directory to create
  type          Template category: landing, portfolio, blog, ecommerce, dashboard, admin, saas, docs, restaurant, realestate, event, nonprofit, resume (default: landing)

Output:
  - <project-name>/ — project directory with full structure
  - .ufme/DESIGN_SYSTEM.md — design tokens and constraints (filled from your answers)
  - .ufme/ENVIRONMENT.md — environment notes
