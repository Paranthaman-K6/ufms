#!/usr/bin/env bash
# init-frontend.sh — Scaffold a new frontend project with a design system.
#
# REQUIRES: design questions answered first (init-project.py run, .ufme/DESIGN_SYSTEM.md exists).
# No code is scaffolded until the user has answered all design questions.
#
# Usage:
#   init-frontend.sh <project-name> [type]
#
#   project-name  Name of the project directory to create
#   type          Template category (default: landing)
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

# ------------------------------------------------------------------
# 0. Guard: design questions MUST be answered before any code is written.
# ------------------------------------------------------------------
ROOT_DIR="$(pwd)"
UFME_DIR="$ROOT_DIR/.ufme"
CHOICES_FILE="$UFME_DIR/design-choices.json"
DESIGN_SYSTEM_FILE="$UFME_DIR/DESIGN_SYSTEM.md"

if [ ! -f "$DESIGN_SYSTEM_FILE" ]; then
  echo "ERROR: Design questions not answered yet." >&2
  echo "" >&2
  echo "Run the design questionnaire first, then scaffold:" >&2
  echo "  python3 universal-frontend-master-source/scripts/init-project.py $ROOT_DIR" >&2
  echo "  (or pass --palette/--font/--style/--profile/--project-name non-interactively)" >&2
  echo "" >&2
  echo "No code is scaffolded until all design questions are answered." >&2
  exit 3
fi

if [ ! -f "$CHOICES_FILE" ]; then
  echo "ERROR: Design choices not recorded ($CHOICES_FILE missing)." >&2
  echo "Re-run init-project.py to answer the design questions." >&2
  exit 3
fi

# ------------------------------------------------------------------
# 1. Read design choices (palette, font, style, profile, refs)
# ------------------------------------------------------------------
PALETTE_NAME=$(python3 -c "import json;print(json.load(open('$CHOICES_FILE')).get('palette',''))" 2>/dev/null || echo "")
FONT_NAME=$(python3 -c "import json;print(json.load(open('$CHOICES_FILE')).get('font',''))" 2>/dev/null || echo "")
STYLE_NAME=$(python3 -c "import json;print(json.load(open('$CHOICES_FILE')).get('style',''))" 2>/dev/null || echo "")
PROFILE=$(python3 -c "import json;print(json.load(open('$CHOICES_FILE')).get('profile','basic'))" 2>/dev/null || echo "basic")

log "Creating project: $PROJECT_NAME (type: $TYPE, profile: $PROFILE)"
log "Design: palette=$PALETTE_NAME font=$FONT_NAME style=$STYLE_NAME"

PROJECT_DIR="$ROOT_DIR/$PROJECT_NAME"
TEMPLATES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/skills/init-frontend/templates"

# ------------------------------------------------------------------
# 2. Resolve color scheme from palette name
# ------------------------------------------------------------------
resolve_colors() {
  local name="$1"
  name_lower="$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]')"
  case "$name_lower" in
    *stripe*gradient*blue*|*stripe*)
      echo '#0f172a #f8fafc #64748b #0f172a #334155 #0ea5e9 #e2e8f0 #0ea5e9 #166534 #ca8a04 #dc2626'
      ;;
    *github*dim*dark*|*github*)
      echo '#0d1117 #161b22 #c9d1d9 #0d1117 #21262d #58a6ff #30363d #58a6ff #3fb950 #d29922 #f85149'
      ;;
    *notion*warm*paper*|*notion*)
      echo '#fafaf9 #f3f4f6 #37352f #37352f #787774 #a16207 #e7e8ea #a16207 #166534 #ca8a04 #dc2626'
      ;;
    *tailwind*slate*classic*|*tailwind*slate*)
      echo '#0f172a #f8fafc #64748b #0f172a #334155 #6366f1 #e2e8f0 #6366f1 #166534 #ca8a04 #dc2626'
      ;;
    *monochrome*red*signal*|*monochrome*red*)
      echo '#ffffff #f8fafc #0f172a #0f172a #334155 #dc2626 #e2e8f0 #dc2626 #166534 #ca8a04 #dc2626'
      ;;
    *forest*sustainability*|*forest*)
      echo '#fefce0 #f3f4f6 #166534 #166534 #374151 #15803d #e5e7eb #15803d #166534 #ca8a04 #dc2626'
      ;;
    *cyberpunk*neon*purple*|*cyberpunk*)
      echo '#050507 #0f0a17 #a78bfa #050507 #1e1b4b #d8b4fe #1f2937 #d8b4fe #166534 #ca8a04 #dc2626'
      ;;
    *apple*light*minimal*|*apple*)
      echo '#ffffff #f5f5f7 #1d1d1f #1d1d1f #86868b #0066cc #d2d2d7 #0066cc #166534 #ca8a04 #dc2626'
      ;;
    *midnight*ocean*|*midnight*)
      echo '#0f172a #1e293b #94a3b8 #0f172a #334155 #22d3ee #334155 #22d3ee #166534 #ca8a04 #dc2626'
      ;;
    *sunrise*warm*light*|*sunrise*)
      echo '#fff7ed #fef3c7 #f59e0b #f59e0b #b45309 #f97316 #fed7aa #f97316 #166534 #ca8a04 #dc2626'
      ;;
    *gunmetal*concrete*|*gunmetal*)
      echo '#e5e7eb #d1d5db #374151 #374151 #6b7280 #ef4444 #9ca3af #ef4444 #166534 #ca8a04 #dc2626'
      ;;
    *inter*stripe*analog*|*inter*stripe*)
      echo '#f5f0e8 #fefce0 #37352f #37352f #787774 #a16207 #e7e8ea #a16207 #166534 #ca8a04 #dc2626'
      ;;
    *telegram*blue*pop*|*telegram*)
      echo '#f0f0f0 #e8e8e8 #000000 #000000 #4d4d4d #0088cc #cccccc #0088cc #166534 #ca8a04 #dc2626'
      ;;
    *)
      # Default fallback: clean light theme
      echo '#0f172a #f8fafc #64748b #0f172a #334155 #0ea5e9 #e2e8f0 #0ea5e9 #166534 #ca8a04 #dc2626'
      ;;
  esac
}

COLORS="$(resolve_colors "$PALETTE_NAME")"
read -r COLOR_BG COLOR_SURFACE COLOR_TEXT COLOR_TEXT_MUTED COLOR_PRIMARY COLOR_PRIMARY_HOOK COLOR_ACCENT COLOR_BORDER COLOR_FOCUS_RING COLOR_SUCCESS COLOR_WARNING COLOR_ERROR <<< "$COLORS"

# ------------------------------------------------------------------
# 2. Create project directory structure
# ------------------------------------------------------------------
mkdir -p "$PROJECT_DIR"/{src/{components,tokens,pages,styles,assets,utils},public,tests/{a11y,perf,responsive},.github/workflows}

# Copy template files if they exist
if [ -d "$TEMPLATES_DIR/$TYPE" ]; then
  log "Applying template: $TYPE"
  cp -R "$TEMPLATES_DIR/$TYPE/." "$PROJECT_DIR/"
else
  log "No template files for '$TYPE' — creating base structure"
fi

# ------------------------------------------------------------------
# 3. Design tokens (from answered palette/font/style)
# ------------------------------------------------------------------
mkdir -p "$PROJECT_DIR/src/tokens"
cat > "$PROJECT_DIR/src/tokens/colors.css" <<CSS
:root {
  --color-bg: $COLOR_BG;
  --color-surface: $COLOR_SURFACE;
  --color-text: $COLOR_TEXT;
  --color-text-muted: $COLOR_TEXT_MUTED;
  --color-primary: $COLOR_PRIMARY;
  --color-primary-hover: $COLOR_PRIMARY_HOOK;
  --color-accent: $COLOR_ACCENT;
  --color-border: $COLOR_BORDER;
  --color-focus-ring: $COLOR_FOCUS_RING;
  --color-success: $COLOR_SUCCESS;
  --color-warning: $COLOR_WARNING;
  --color-error: $COLOR_ERROR;
}
CSS

cat > "$PROJECT_DIR/src/tokens/typography.css" <<CSS
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

cat > "$PROJECT_DIR/src/tokens/spacing.css" <<CSS
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

# ------------------------------------------------------------------
# 4. Responsive base
# ------------------------------------------------------------------
cat > "$PROJECT_DIR/src/styles/base.css" <<CSS
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

# ------------------------------------------------------------------
# 5. Package.json
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# 6. Performance budget
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# 7. CI workflow
# ------------------------------------------------------------------
cat > "$PROJECT_DIR/.github/workflows/ci.yml" <<YAML
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

# ------------------------------------------------------------------
# 8. README
# ------------------------------------------------------------------
cat > "$PROJECT_DIR/README.md" <<MD
# $PROJECT_NAME

Frontend project initialized with \`init-frontend\` (type: $TYPE, profile: $PROFILE).

Design: palette=$PALETTE_NAME font=$FONT_NAME style=$STYLE_NAME

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
log "Design questions answered before any code was written."
log "Next steps:"
log "  1. cd $PROJECT_NAME"
log "  2. npm install"
log "  3. ufmw init-frontend tokens"
log "  4. ufmw init-frontend audit"
