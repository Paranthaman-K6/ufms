#!/usr/bin/env bash
# tests/e2e/run.sh — end-to-end proof from a real project install.
#
# Installs the skill into a clean directory (project scope, no network), then
# runs the installed gate against a seeded design template, a filled design
# system, and uniform motion. Proves the installed skill fails closed and that
# uninstall removes only managed paths.
#
# Usage: bash tests/e2e/run.sh
# Exit: 0 all pass, 1 failure.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BASE="$(mktemp -d "${TMPDIR:-/tmp}/ufme-e2e.XXXXXX")"
PROJ="$BASE/proj"
PASS=0
FAIL=0

cleanup() { rm -rf "$BASE"; }
trap cleanup EXIT

check() {
  local name="$1"; shift
  if "$@"; then PASS=$((PASS + 1)); echo "PASS: $name";
  else FAIL=$((FAIL + 1)); echo "FAIL: $name"; fi
}

mkdir -p "$PROJ"

# 1. Project-scope install from the local checkout, no network.
INSTALL_DIR="$PROJ" INSTALL_SCOPE=project UFME_SOURCE_DIR="$REPO" UFME_SKIP_NPM=1 \
  bash "$REPO/install.sh" >"$BASE/install.log" 2>&1
check "install exits 0" test $? -eq 0
check "installed agent" test -f "$PROJ/.opencode/agents/universal-frontend-master.md"
check "installed skill scripts" test -f "$PROJ/skills/universal-frontend-master/scripts/detect-slop.py"
check "installed design template" test -f "$PROJ/.ufme/DESIGN_SYSTEM.md"

GATE="$PROJ/skills/universal-frontend-master/scripts/detect-slop.py"
DESIGN="$PROJ/.ufme/DESIGN_SYSTEM.md"
SRC="$PROJ/src"
mkdir -p "$SRC"
cat > "$SRC/index.html" <<'HTML'
<!doctype html>
<html lang="en">
  <head><meta charset="utf-8"><link rel="stylesheet" href="style.css"><title>E2E</title></head>
  <body><main><h1>Work</h1><img src="a.png" alt="cover" width="320" height="200"></main></body>
</html>
HTML
cat > "$SRC/style.css" <<'CSS'
:root { --ink: #14130f; --paper: #f4efe6; --rust: #a3431f; }
html { font-family: 'Bricolage Grotesque', Georgia, serif; background: var(--paper); color: var(--ink); }
:focus-visible { outline: 2px solid var(--rust); outline-offset: 3px; }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
CSS

# 2. The seeded template is not a design: the gate must fail.
python3 "$GATE" --path "$SRC" --design "$DESIGN" >"$BASE/gate-seeded.log" 2>&1
check "seeded design system fails (exit 2)" test $? -eq 2
check "failure names design-system-incomplete" grep -q "design-system-incomplete" "$BASE/gate-seeded.log"

# 3. A filled, content-derived design system passes.
cat > "$DESIGN" <<'MD'
# Design System

## Design direction
- Tone: editorial, print-inspired
- Type pairing: Bricolage Grotesque for display, Source Serif for text
- Palette rationale: ink and paper neutrals from the printed portfolio
- Layout concept: filmstrip of work above a running index
- Motion hierarchy: hero mask reveal, list stagger, hover only on interactive rows

### Typography
Display: Bricolage Grotesque. Text: Source Serif.

### Color
Ink #14130f, paper #f4efe6, accent rust #a3431f.

## Components
Work card, index row, contact block; hover and focus states defined.

## Animation guidance
Hero mask reveal; list stagger; no section-wide fade.
MD
python3 "$GATE" --path "$SRC" --design "$DESIGN" >"$BASE/gate-filled.log" 2>&1
check "filled design system passes (exit 0)" test $? -eq 0

# 4. Uniform entrance motion on four components still fails.
for name in Hero About Work Contact; do
  cat > "$SRC/$name.tsx" <<'TSX'
const slideUp = { hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0 } };
export function Section() {
  return <motion.section variants={slideUp} initial="hidden" animate="show" />;
}
TSX
done
python3 "$GATE" --path "$SRC" --design "$DESIGN" >"$BASE/gate-motion.log" 2>&1
check "uniform motion fails (exit 2)" test $? -eq 2
check "failure names uniform-entrance-motion" grep -q "uniform-entrance-motion" "$BASE/gate-motion.log"

# 5. The installed skill renders the theme showcase for the project.
INSTALLED_SHOWCASE="$PROJ/skills/universal-frontend-master/scripts/theme-showcase.py"
python3 "$INSTALLED_SHOWCASE" --target "$PROJ" --quiet >"$BASE/showcase.log" 2>&1
check "installed theme showcase runs" test $? -eq 0
check "theme showcase PDF written" test -f "$PROJ/.ufme/theme-showcase.pdf"
check "theme showcase lists themes" grep -q "Midnight Ocean" "$PROJ/.ufme/theme-showcase.pdf"

# 6. Uninstall removes managed paths, keeps project memory.
INSTALL_DIR="$PROJ" bash "$REPO/uninstall.sh" --project-only >"$BASE/uninstall.log" 2>&1
check "uninstall exits 0" test $? -eq 0
check "agents removed" test ! -e "$PROJ/.opencode/agents/universal-frontend-master.md"
check "skills removed" test ! -e "$PROJ/skills/universal-frontend-master"
check "commands removed" test ! -e "$PROJ/.opencode/commands/ufme"
check "project memory preserved" test -f "$DESIGN"

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
