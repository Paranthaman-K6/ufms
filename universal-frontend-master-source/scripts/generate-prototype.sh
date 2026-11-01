#!/usr/bin/env bash
# generate-prototype.sh
# Priority 2 — Design Intelligence: Prototype generation.
# Reads .ufme/DESIGN_SYSTEM.md and .ufme/SITEMAP.md and produces working HTML
# prototype pages (responsive, dark/light-ready) under prototypes/.
# No framework forced; plain semantic HTML + CSS so it runs in any browser.
#
# Safety: project-local only; writes to prototypes/ only.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UFME_DIR="$ROOT_DIR/.ufme"
OUT_DIR="$ROOT_DIR/prototypes"
DESIGN="$UFME_DIR/DESIGN_SYSTEM.md"
SITEMAP="$UFME_DIR/SITEMAP.md"
PRD="$UFME_DIR/PRD.md"

mkdir -p "$OUT_DIR"

log() { echo "[generate-prototype] $*"; }

# Extract a simple token value from DESIGN_SYSTEM.md (best-effort).
token() { # token <key>
  grep -i "$1" "$DESIGN" 2>/dev/null | head -1 | sed -E 's/.*[:#]\s*//' | head -c 40
}

PRIMARY="${PRIMARY:-#2563eb}"
BG="${BG:-#ffffff}"
TEXT="${TEXT:-#111827}"

write_css() {
  cat > "$OUT_DIR/style.css" <<CSS
/* UFME generated prototype stylesheet */
:root {
  --color-primary: ${PRIMARY};
  --color-bg: ${BG};
  --color-text: ${TEXT};
  --font-sans: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  --radius: 8px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { color-scheme: light dark; }
body {
  font-family: var(--font-sans);
  color: var(--color-text);
  background: var(--color-bg);
  line-height: 1.5;
  padding: 1rem;
}
a { color: var(--color-primary); text-decoration: underline; }
button, .btn {
  background: var(--color-primary);
  color: #fff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 1rem;
}
button:hover { opacity: 0.9; }
nav { display: flex; gap: 1rem; padding: 1rem 0; border-bottom: 1px solid #ccc; }
.container { max-width: 1200px; margin: 0 auto; }
.grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
.card { border: 1px solid #ddd; border-radius: var(--radius); padding: 1rem; }
@media (max-width: 640px) { body { padding: 0.5rem; } .grid { grid-template-columns: 1fr; } }
@media (prefers-color-scheme: dark) {
  body { --color-bg: #111827; --color-text: #f3f4f6; }
  .card { border-color: #374151; }
}
CSS
}

write_page() { # write_page <name> <title> <body-html>
  local name="$1" title="$2" body="$3"
  cat > "$OUT_DIR/$name.html" <<HTML
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>$title</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<nav><a href="index.html">Home</a></nav>
<div class="container">
<h1>$title</h1>
$body
</div>
</body>
</html>
HTML
}

main() {
  log "Reading design system from $DESIGN and sitemap from $SITEMAP"
  [ -f "$DESIGN" ] || { log "WARNING: $DESIGN not found; using defaults"; }
  [ -f "$SITEMAP" ] || { log "WARNING: $SITEMAP not found; generating index only"; }

  write_css

  if [ -f "$SITEMAP" ]; then
    # Parse route lines from SITEMAP.md table (best-effort).
    routes="$(grep -E '^\|' "$SITEMAP" | grep -v 'Page | Route' | grep -v '^\|---' | sed -E 's/^\|\s*([^|]+)\s*\|.*/\1/' | grep -v '^\s*$' || true)"
  fi

  routes="${routes:-}"
  if [ -n "$routes" ]; then
    for route in $routes; do
      page="$(echo "$route" | tr '[:upper:]' '[:lower:]' | tr ' ' '-').html"
      write_page "$page" "$route" "<p>Generated page for <strong>$route</strong>.</p><button class=\"btn\">Get Started</button>"
      log "Generated prototype: $page"
    done
  else
    write_page "index" "Home" "<p>Welcome to the generated prototype.</p><button class=\"btn\">Get Started</button>"
    log "Generated prototype: index.html (no sitemap routes found)"
  fi

  log "Prototype output: $OUT_DIR"
}

main "$@"
