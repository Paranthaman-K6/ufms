#!/usr/bin/env bash
# backend-discovery.sh
# Enumerate backend endpoints, auth, and error formats from a repo or API specs.
# Read-only analysis. Outputs findings to stdout for the backend-analyst agent.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

log() { echo "[backend-discovery] $*"; }

detect_backend() {
  local found="no"
  if [ -f "$ROOT_DIR/pom.xml" ] || [ -f "$ROOT_DIR/build.gradle" ]; then log "Spring Boot / Java backend detected"; found="yes"; fi
  if [ -f "$ROOT_DIR/package.json" ] && grep -qE '"(express|fastify|nest)"' "$ROOT_DIR/package.json" 2>/dev/null; then log "Node backend (Express/Fastify/Nest) detected"; found="yes"; fi
  if [ -f "$ROOT_DIR/manage.py" ] || [ -f "$ROOT_DIR/settings.py" ]; then log "Django backend detected"; found="yes"; fi
  if [ -f "$ROOT_DIR/app.py" ] || grep -qE 'flask|FastAPI' "$ROOT_DIR/*.py" 2>/dev/null; then log "Flask/FastAPI backend detected"; found="yes"; fi
  if [ -f "$ROOT_DIR/composer.json" ]; then log "Laravel/PHP backend detected"; found="yes"; fi
  if [ -f "$ROOT_DIR/Gemfile" ]; then log "Rails backend detected"; found="yes"; fi
  if [ -f "$ROOT_DIR/*.csproj" ] 2>/dev/null || [ -f "$ROOT_DIR/Program.cs" ]; then log "ASP.NET backend detected"; found="yes"; fi
  if [ -f "$ROOT_DIR/go.mod" ]; then log "Go HTTP backend detected"; found="yes"; fi
  [ "$found" = "no" ] && log "No recognized backend framework detected."
}

detect_api_specs() {
  log "Checking for API specs..."
  for f in openapi.json openapi.yaml swagger.json swagger.yaml postman.json asyncapi.json asyncapi.yaml; do
    if [ -f "$ROOT_DIR/$f" ]; then log "Found API spec: $f"; fi
  done
}

main() {
  detect_backend
  detect_api_specs
}
main "$@"
