#!/usr/bin/env bash
# detect-stack.sh
# Detect frontend and backend frameworks/tools present in the project.
# Outputs findings to stdout for intake. Read-only.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

log() { echo "[detect-stack] $*"; }

echo "--- Frontend ---"
if [ -f package.json ]; then
  PKG="$(cat package.json)"
  echo "$PKG" | grep -q '"react"' && echo "React: yes"
  echo "$PKG" | grep -q '"next"' && echo "Next.js: yes"
  echo "$PKG" | grep -q '"vue"' && echo "Vue: yes"
  echo "$PKG" | grep -q '"nuxt"' && echo "Nuxt: yes"
  echo "$PKG" | grep -q '"svelte"' && echo "Svelte: yes"
  echo "$PKG" | grep -q '"@sveltejs/kit"' && echo "SvelteKit: yes"
  echo "$PKG" | grep -q '"astro"' && echo "Astro: yes"
  echo "$PKG" | grep -q '"@angular/core"' && echo "Angular: yes"
  echo "$PKG" | grep -q '"solid-js"' && echo "SolidJS: yes"
  echo "$PKG" | grep -q '"@builder.io/qwik"' && echo "Qwik: yes"
  echo "$PKG" | grep -q '"vite"' && echo "Vite: yes"
  echo "$PKG" | grep -q '"tailwindcss"' && echo "Tailwind CSS: yes"
  echo "$PKG" | grep -q '"bootstrap"' && echo "Bootstrap: yes"
  echo "$PKG" | grep -q '"typescript"' && echo "TypeScript: yes"
fi
[ -d node_modules ] && echo "node_modules: present" || echo "node_modules: absent"

echo "--- Backend ---"
bash "$ROOT_DIR/universal-frontend-master-source/scripts/backend-discovery.sh"

echo "--- API specs ---"
for f in openapi.json openapi.yaml swagger.json swagger.yaml postman.json asyncapi.json asyncapi.yaml; do
  [ -f "$ROOT_DIR/$f" ] && echo "API spec: $f"
done
