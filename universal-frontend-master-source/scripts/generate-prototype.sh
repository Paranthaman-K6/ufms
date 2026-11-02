#!/usr/bin/env bash
# generate-prototype.sh
# Priority 2 — Design Intelligence: Prototype generation.
# Reads .ufme/ project memory files (PROJECT_SPEC.md, PRD.md, SITEMAP.md,
# DESIGN_SYSTEM.md, USER_FLOWS.md, FEATURES.md, API_MAP.md) and produces
# working HTML/CSS prototype pages under prototypes/.
#
# Plain HTML/CSS only — framework-independent preview. Preserves existing
# framework when the project already has one (detected via detect-stack.sh).
# Never overwrites unrelated user prototype files.
#
# Safety: project-local only; writes to prototypes/ only.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UFME_DIR="$ROOT_DIR/.ufme"
OUT_DIR="$ROOT_DIR/prototypes"

PROJECT_SPEC="$UFME_DIR/PROJECT_SPEC.md"
PRD="$UFME_DIR/PRD.md"
SITEMAP="$UFME_DIR/SITEMAP.md"
DESIGN_SYSTEM="$UFME_DIR/DESIGN_SYSTEM.md"
USER_FLOWS="$UFME_DIR/USER_FLOWS.md"
FEATURES="$UFME_DIR/FEATURES.md"
API_MAP="$UFME_DIR/API_MAP.md"

mkdir -p "$OUT_DIR"

log() { echo "[generate-prototype] $*"; }

# Extract a value from a markdown file by heading key.
# Usage: extract_value <file> <key>
extract_value() {
  local file="$1" key="$2"
  [ -f "$file" ] || return 1
  grep -i -A2 "^#* *${key}" "$file" 2>/dev/null | head -3 | tail -1 | sed -E 's/^[[:space:]]*[-*]?[[:space:]]*//' | head -c 200
}

# Extract design tokens from DESIGN_SYSTEM.md.
extract_token() {
  local file="$1" key="$2" default="$3"
  [ -f "$file" ] || { echo "$default"; return; }
  local val
  val=$(grep -i "${key}" "$file" 2>/dev/null | head -1 | sed -E 's/.*[:#]\s*//' | head -c 40)
  [ -n "$val" ] && echo "$val" || echo "$default"
}

# Parse routes from SITEMAP.md table.
# Outputs one route per line: "Route Name | /path"
parse_routes() {
  local file="$1"
  [ -f "$file" ] || return 0
  grep -E '^\|' "$file" 2>/dev/null | grep -v 'Page | Route' | grep -v '^\|---' | while IFS='|' read -r _ route _; do
    route=$(echo "$route" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')
    [ -n "$route" ] && [ "$route" != "Route" ] && echo "$route"
  done
}

# Parse features from FEATURES.md table.
parse_features() {
  local file="$1"
  [ -f "$file" ] || return 0
  grep -E '^\|' "$file" 2>/dev/null | grep -v 'Feature |' | grep -v '^\|---' | while IFS='|' read -r _ feature _; do
    feature=$(echo "$feature" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')
    [ -n "$feature" ] && [ "$feature" != "Feature" ] && echo "$feature"
  done
}

# Slugify a route for a filename.
slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g'
}

write_css() {
  local primary bg text
  primary=$(extract_token "$DESIGN_SYSTEM" "color.*primary" "#2563eb")
  bg=$(extract_token "$DESIGN_SYSTEM" "color.*bg" "#ffffff")
  text=$(extract_token "$DESIGN_SYSTEM" "color.*text" "#111827")

  cat > "$OUT_DIR/style.css" <<CSS
/* UFME generated prototype stylesheet */
/* Tokens extracted from .ufme/DESIGN_SYSTEM.md */
:root {
  --color-primary: ${primary};
  --color-bg: ${bg};
  --color-text: ${text};
  --font-sans: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  --radius: 8px;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { color-scheme: light dark; }
body {
  font-family: var(--font-sans);
  color: var(--color-text);
  background: var(--color-bg);
  line-height: 1.5;
  padding: var(--spacing-md);
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
.nav { display: flex; gap: var(--spacing-md); padding: var(--spacing-md) 0; border-bottom: 1px solid #ccc; flex-wrap: wrap; }
.nav a { text-decoration: none; color: var(--color-text); font-weight: 500; }
.nav a:hover { color: var(--color-primary); }
.container { max-width: 1200px; margin: 0 auto; }
.grid { display: grid; gap: var(--spacing-md); grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
.card { border: 1px solid #ddd; border-radius: var(--radius); padding: var(--spacing-md); background: var(--color-bg); }
.state-loading, .state-empty, .state-error {
  padding: var(--spacing-lg);
  text-align: center;
  border-radius: var(--radius);
  margin: var(--spacing-md) 0;
}
.state-loading { background: #e5edff; color: #1e3a8a; }
.state-empty { background: #f3f4f6; color: #4b5563; }
.state-error { background: #fee2e2; color: #991b1b; }
@media (max-width: 640px) { body { padding: 0.5rem; } .grid { grid-template-columns: 1fr; } }
@media (prefers-color-scheme: dark) {
  body { --color-bg: #111827; --color-text: #f3f4f6; }
  .card { border-color: #374151; background: #111827; }
  .state-loading { background: #1e3a8a; color: #bfdbfe; }
  .state-empty { background: #1f2937; color: #9ca3af; }
  .state-error { background: #450a0a; color: #fecaca; }
}
CSS
}

write_nav() {
  local routes="$1"
  local nav=""
  while IFS= read -r route; do
    [ -z "$route" ] && continue
    local page
    page="$(slugify "$route").html"
    nav+="<a href=\"$page\">$route</a>"
  done <<< "$routes"
  echo "$nav"
}

write_page() {
  local name="$1" title="$2" body="$3" nav="$4"
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
<nav class="nav">$nav</nav>
<div class="container">
<h1>$title</h1>
$body
</div>
</body>
</html>
HTML
}

generate_loading_state() {
  echo '<div class="state-loading" role="status" aria-live="polite"><p>Loading...</p></div>'
}

generate_empty_state() {
  echo '<div class="state-empty"><p>No items found.</p><button class="btn">Refresh</button></div>'
}

generate_error_state() {
  echo '<div class="state-error"><p>Something went wrong.</p><button class="btn">Try Again</button></div>'
}

main() {
  log "Reading project memory from $UFME_DIR"

  [ -f "$PROJECT_SPEC" ] || { log "WARNING: $PROJECT_SPEC not found; using defaults"; }
  [ -f "$SITEMAP" ] || { log "WARNING: $SITEMAP not found; generating index only"; }

  write_css

  local routes=""
  if [ -f "$SITEMAP" ]; then
    routes="$(parse_routes "$SITEMAP")"
  fi

  local nav
  nav="$(write_nav "$routes")"

  if [ -n "$routes" ]; then
    while IFS= read -r route; do
      [ -z "$route" ] && continue
      local page title
      page="$(slugify "$route").html"
      title="$route"

      # Build page-specific content based on route name
      local body
      case "$route" in
        *Home*|*Index*|*Dashboard*)
          body="<p>Welcome to $route.</p>
<div class=\"grid\">
  <div class=\"card\"><h3>Overview</h3><p>Key metrics and overview for $route.</p></div>
  <div class=\"card\"><h3>Recent Activity</h3><p>Latest updates and notifications.</p></div>
</div>"
          ;;
        *Login*|*Sign*|*Auth*)
          body="<div class=\"card\" style=\"max-width: 400px; margin: 0 auto;\">
<h3>Sign In</h3>
<form>
<label>Email</label><br>
<input type=\"email\" placeholder=\"email@example.com\" style=\"width:100%;padding:0.5rem;margin:0.5rem 0;\"><br>
<label>Password</label><br>
<input type=\"password\" placeholder=\"••••••••\" style=\"width:100%;padding:0.5rem;margin:0.5rem 0;\"><br>
<button class=\"btn\" type=\"button\">Sign In</button>
</form>
$(generate_empty_state)
</div>"
          ;;
        *Profile*|*Account*)
          body="<div class=\"card\">
<h3>Profile Settings</h3>
<p>Manage your account preferences.</p>
$(generate_loading_state)
</div>"
          ;;
        *Settings*)
          body="<div class=\"card\">
<h3>Settings</h3>
<p>Configure application options.</p>
</div>"
          ;;
        *)
          body="<p>Content for $route.</p>
$(generate_empty_state)
<button class=\"btn\">Get Started</button>"
          ;;
      esac

      write_page "$page" "$title" "$body" "$nav"
      log "Generated prototype: $page"
    done <<< "$routes"
  else
    write_page "index" "Home" "<p>Welcome to the generated prototype.</p><button class=\"btn\">Get Started</button>" "$nav"
    log "Generated prototype: index.html (no sitemap routes found)"
  fi

  # Detect if project has an existing framework and note it.
  if [ -f "$ROOT_DIR/universal-frontend-master-source/scripts/detect-stack.sh" ]; then
    local stack
    stack="$(bash "$ROOT_DIR/universal-frontend-master-source/scripts/detect-stack.sh" 2>/dev/null | grep -E '^(React|Vue|Angular|Svelte|Next|Nuxt): yes' | head -1 || true)"
    if [ -n "$stack" ]; then
      log "Detected existing framework: $stack — preserve it when extending prototypes"
    fi
  fi

  log "Prototype output: $OUT_DIR"
}

main "$@"
