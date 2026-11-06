#!/usr/bin/env bash
# init-template.sh — Download template by category, re-apply init-frontend principles.
#
# Usage:
#   init-template.sh <category> [project-dir]
#
set -euo pipefail

log() { echo "[init-frontend template] $*"; }

CATEGORY="${1:-}"
PROJECT_DIR="${2:-$(pwd)}"

VALID_CATEGORIES="landing portfolio blog ecommerce dashboard admin saas docs restaurant realestate event nonprofit resume"

if [ -z "$CATEGORY" ]; then
  echo "Usage: $0 <category> [project-dir]" >&2
  echo "Categories: $VALID_CATEGORIES" >&2
  exit 2
fi

# Check if template exists locally
TEMPLATES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/templates"

if [ -d "$TEMPLATES_DIR/$CATEGORY" ]; then
  log "Applying local template: $CATEGORY"
  cp -R "$TEMPLATES_DIR/$CATEGORY/." "$PROJECT_DIR/"
else
  log "No local template for '$CATEGORY' — applying base structure only"
fi

# Record template source
mkdir -p "$PROJECT_DIR/.ufme"
cat > "$PROJECT_DIR/.ufme/REFERENCES.md" <<MD
# References

- Template: $CATEGORY
- Source: skills/init-frontend/templates/$CATEGORY
- Applied via: ufmw init-frontend template
MD

log "Template '$CATEGORY' applied to $PROJECT_DIR"
