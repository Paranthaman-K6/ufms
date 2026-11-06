#!/usr/bin/env bash
# init-frontend.sh — Scaffold a new frontend project with a design system.
#
# Usage:
#   init-frontend.sh <project-name> [type]
#
#   project-name  Name of the project directory to create
#   type          Template category (default: landing)
#
# Creates project structure with design tokens, component library,
# responsive base, accessibility foundations, performance budgets, and CI.
#
set -euo pipefail

log() { echo "[init-frontend] $*"; }

PROJECT_NAME="${1:-}"
TYPE="${2:-landing}"

if [ -z "$PROJECT_NAME" ]; then
  echo "Usage: $0 <project-name> [type]" >&2
  echo "  type: landing, portfolio, blog, ecommerce, dashboard, admin, saas, docs, restaurant, realestate, event, nonprofit, resume" >&2
  exit 2
fi

PROJECT_DIR="$(pwd)/$PROJECT_NAME"
TEMPLATES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/skills/init-frontend/templates"

log "Creating project: $PROJECT_NAME (type: $TYPE)"

# Create project directory structure
mkdir -p "$PROJECT_DIR"/{src/{components,tokens,pages,styles,assets,utils},public,tests/{a11y,perf,responsive},.github/workflows}

# Copy template files if they exist
if [ -d "$TEMPLATES_DIR/$TYPE" ]; then
  log "Applying template: $TYPE"
  cp -R "$TEMPLATES_DIR/$TYPE/." "$PROJECT_DIR/"
else
  log "No template files for '$TYPE' — creating base structure"
fi

# Design tokens
mkdir -p "$PROJECT_DIR/src/tokens"
cat > "$PROJECT_DIR/src/tokens/colors.css" <<'CSS'
:root {
  --color-bg: #ffffff;
  --color-surface: #f8fafc;
  --color-text: #0f172a;
  --color-text-muted: #64748b;
  --color-primary: #0f172a;
  --color-primary-hover: #334155;
  --color-accent: #0ea5e9;
  --color-border: #e2e8f0;
  --color-focus-ring: #0ea5e9;
  --color-success: #166534;
  --color-warning: #ca8a04;
  --color-error: #dc2626;
}
CSS

cat > "$PROJECT_DIR/src/tokens/typography.css" <<'CSS'
:root {
  --font-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  --text-4xl: 2.25rem;
  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
}
CSS

cat > "$PROJECT_DIR/src/tokens/spacing.css" <<'CSS'
:root {
  --space-0: 0;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  --space-16: 4rem;
  --space-20: 5rem;
  --space-24: 6rem;
}
CSS

# Responsive base
cat > "$PROJECT_DIR/src/styles/base.css" <<'CSS'
/* Reset */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  line-height: 1.5;
  -webkit-text-size-adjust: 100%;
  -moz-tab-size: 4;
  tab-size: 4;
}

body {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  line-height: var(--line-height-normal);
  color: var(--color-text);
  background: var(--color-bg);
}

/* Focus visible rings — never remove */
:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
}

/* Responsive containers */
.container {
  width: 100%;
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 var(--space-4);
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* Touch targets — minimum 24px */
button, a, [role="button"], input, select, textarea {
  min-height: 24px;
  min-width: 24px;
}

/* Skip link */
.skip-link {
  position: absolute;
  top: -10000px;
  left: 0;
  z-index: 1000;
}
.skip-link:focus-visible {
  top: var(--space-2);
  left: var(--space-2);
}
CSS

# Package.json
cat > "$PROJECT_DIR/package.json" <<JSON
{
  "name": "$PROJECT_NAME",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:a11y": "axe-core-cli http://localhost:5173",
    "test:perf": "lighthouse http://localhost:5173 --preset=desktop --budget-path=./perf-budget.json"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "vitest": "^1.0.0",
    "axe-core": "^4.8.0",
    "lighthouse": "^11.0.0"
  }
}
JSON

# Performance budget
cat > "$PROJECT_DIR/perf-budget.json" <<'JSON'
[
  { "path": "/*", "timings": [ { "metric": "largest-contentful-paint", "budget": 2500 } ] },
  { "path": "/*", "timings": [ { "metric": "interaction-to-next-paint", "budget": 200 } ] },
  { "path": "/*", "timings": [ { "metric": "cumulative-layout-shift", "budget": 0.1 } ] },
  { "path": "/*", "resourceSizes": [ { "resourceType": "script", "budget": 300 } ] },
  { "path": "/*", "resourceSizes": [ { "resourceType": "stylesheet", "budget": 100 } ] },
  { "path": "/*", "resourceSizes": [ { "resourceType": "image", "budget": 200 } ] }
]
JSON

# CI workflow
cat > "$PROJECT_DIR/.github/workflows/ci.yml" <<'YAML'
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
      - run: npm run test:a11y
      - run: npm run test:perf
YAML

# README
cat > "$PROJECT_DIR/README.md" <<MD
# $PROJECT_NAME

Frontend project initialized with \`init-frontend\` (type: $TYPE).

## Design System

- Tokens: \`src/tokens/\` (color, typography, spacing)
- Base styles: \`src/styles/base.css\`
- Components: \`src/components/\`

## Accessibility

WCAG 2.2 AA — semantic HTML, focus-visible rings, real labels, contrast ratios, keyboard nav, reduced motion.

## Performance Budgets (P75)

- LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1
- JS ≤ 300KB, CSS ≤ 100KB, images ≤ 200KB

## Scripts

- \`npm run dev\` — start dev server
- \`npm run build\` — production build
- \`npm run test:a11y\` — axe-core accessibility audit
- \`npm run test:perf\` — Lighthouse performance budget check
MD

log "Project created at $PROJECT_DIR"
log "Next steps:"
log "  1. cd $PROJECT_NAME"
log "  2. npm install"
log "  3. ufmw init-frontend tokens"
log "  4. ufmw init-frontend audit"
