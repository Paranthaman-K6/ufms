#!/usr/bin/env bash
# init-tokens.sh — Initialize design-token tier + Style Dictionary build.
#
# Usage:
#   init-tokens.sh [project-dir]
#
set -euo pipefail

log() { echo "[init-frontend tokens] $*"; }

PROJECT_DIR="${1:-$(pwd)}"
TOKENS_DIR="$PROJECT_DIR/src/tokens"

mkdir -p "$TOKENS_DIR"

# Style Dictionary config
cat > "$PROJECT_DIR/style-dictionary.config.js" <<'JS'
module.exports = {
  source: ['tokens/**/*.json'],
  platforms: {
    css: {
      transformGroup: 'css',
      buildPath: 'build/tokens/',
      files: [
        {
          destination: 'design-tokens.css',
          format: 'css/variables',
        },
      ],
    },
  },
};
JS

# Base token JSON files
cat > "$TOKENS_DIR/color.json" <<'JSON'
{
  "color": {
    "bg": { "value": "#ffffff", "type": "color" },
    "surface": { "value": "#f8fafc", "type": "color" },
    "text": { "value": "#0f172a", "type": "color" },
    "text-muted": { "value": "#64748b", "type": "color" },
    "primary": { "value": "#0f172a", "type": "color" },
    "primary-hover": { "value": "#334155", "type": "color" },
    "accent": { "value": "#0ea5e9", "type": "color" },
    "border": { "value": "#e2e8f0", "type": "color" },
    "focus-ring": { "value": "#0ea5e9", "type": "color" },
    "success": { "value": "#166534", "type": "color" },
    "warning": { "value": "#ca8a04", "type": "color" },
    "error": { "value": "#dc2626", "type": "color" }
  }
}
JSON

cat > "$TOKENS_DIR/typography.json" <<'JSON'
{
  "typography": {
    "fontSans": { "value": "system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif", "type": "fontFamily" },
    "fontMono": { "value": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace", "type": "fontFamily" },
    "text-xs": { "value": "0.75rem", "type": "fontSize" },
    "text-sm": { "value": "0.875rem", "type": "fontSize" },
    "text-base": { "value": "1rem", "type": "fontSize" },
    "text-lg": { "value": "1.125rem", "type": "fontSize" },
    "text-xl": { "value": "1.25rem", "type": "fontSize" },
    "text-2xl": { "value": "1.5rem", "type": "fontSize" },
    "text-3xl": { "value": "1.875rem", "type": "fontSize" },
    "text-4xl": { "value": "2.25rem", "type": "fontSize" },
    "line-height-tight": { "value": "1.25", "type": "lineHeight" },
    "line-height-normal": { "value": "1.5", "type": "lineHeight" },
    "line-height-relaxed": { "value": "1.75", "type": "lineHeight" },
    "font-weight-normal": { "value": "400", "type": "fontWeight" },
    "font-weight-medium": { "value": "500", "type": "fontWeight" },
    "font-weight-semibold": { "value": "600", "type": "fontWeight" }
  }
}
JSON

cat > "$TOKENS_DIR/spacing.json" <<'JSON'
{
  "spacing": {
    "0": { "value": "0", "type": "dimension" },
    "1": { "value": "0.25rem", "type": "dimension" },
    "2": { "value": "0.5rem", "type": "dimension" },
    "3": { "value": "0.75rem", "type": "dimension" },
    "4": { "value": "1rem", "type": "dimension" },
    "5": { "value": "1.25rem", "type": "dimension" },
    "6": { "value": "1.5rem", "type": "dimension" },
    "8": { "value": "2rem", "type": "dimension" },
    "10": { "value": "2.5rem", "type": "dimension" },
    "12": { "value": "3rem", "type": "dimension" },
    "16": { "value": "4rem", "type": "dimension" }
  }
}
JSON

log "Design tokens initialized in $TOKENS_DIR"
log "Style Dictionary config: $PROJECT_DIR/style-dictionary.config.js"
