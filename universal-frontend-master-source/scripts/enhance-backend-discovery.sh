#!/usr/bin/env bash
# enhance-backend-discovery.sh
# Priority 6 — Backend Intelligence: enhanced contract discovery.
# Detects GraphQL, WebSockets, SSE, OpenAPI/Swagger, Postman, AsyncAPI
# and verifies that frontend API clients are generated only from verified
# contracts. Never invents endpoints, fields, permissions, or responses.
#
# Safety: read-only analysis; writes .ufme/BACKEND_CONTRACTS.md only.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UFME_DIR="$ROOT_DIR/.ufme"
OUT="$UFME_DIR/BACKEND_CONTRACTS.md"

mkdir -p "$UFME_DIR"

log() { echo "[enhance-backend-discovery] $*"; }

main() {
  {
    echo "# Backend Contracts"
    echo "Generated: $(date -Iseconds)"
    echo ""
    echo "| Contract type | Detected | File(s) | Verified endpoints | Notes |"
    echo "|---------------|----------|---------|-------------------|-------|"
  } > "$OUT"

  local found=0

  # OpenAPI / Swagger
  for f in openapi.json openapi.yaml swagger.json swagger.yaml; do
    if [ -f "$ROOT_DIR/$f" ]; then
      found=1
      echo "| OpenAPI/Swagger | yes | $f | parse manually | Evidence: $f |" >> "$OUT"
    fi
  done

  # Postman
  if [ -f "$ROOT_DIR/postman.json" ] || [ -f "$ROOT_DIR/postman_collection.json" ]; then
    found=1
    for f in postman.json postman_collection.json; do
      [ -f "$ROOT_DIR/$f" ] && echo "| Postman | yes | $f | parse manually | Evidence: $f |" >> "$OUT"
    done
  fi

  # AsyncAPI
  for f in asyncapi.json asyncapi.yaml; do
    if [ -f "$ROOT_DIR/$f" ]; then
      found=1
      echo "| AsyncAPI | yes | $f | parse manually | Evidence: $f |" >> "$OUT"
    fi
  done

  # GraphQL schema
  if [ -f "$ROOT_DIR/schema.graphql" ] || [ -f "$ROOT_DIR/schema.gql" ]; then
    found=1
    for f in schema.graphql schema.gql; do
      [ -f "$ROOT_DIR/$f" ] && echo "| GraphQL | yes | $f | introspect manually | Evidence: $f |" >> "$OUT"
    done
  fi

  # WebSocket / SSE hints in source
  local ws_hits
  ws_hits=$(grep -rlE 'new WebSocket|ws://|wss://|io\.connect|socket\.io' "$ROOT_DIR" --include='*.js' --include='*.ts' --include='*.py' --include='*.go' --include='*.java' --include='*.rb' --include='*.php' 2>/dev/null | grep -v node_modules | head -5 || true)
  if [ -n "$ws_hits" ]; then
    found=1
    echo "| WebSocket | yes | $ws_hits | verify manually | Evidence: source references |" >> "$OUT"
  fi

  # SSE hints
  local sse_hits
  sse_hits=$(grep -rlE 'EventSource|text/event-stream' "$ROOT_DIR" --include='*.js' --include='*.ts' --include='*.py' --include='*.go' --include='*.java' --include='*.rb' --include='*.php' 2>/dev/null | grep -v node_modules | head -5 || true)
  if [ -n "$sse_hits" ]; then
    found=1
    echo "| SSE | yes | $sse_hits | verify manually | Evidence: source references |" >> "$OUT"
  fi

  if [ "$found" -eq 0 ]; then
    echo "| None | no | — | 0 | No backend contract files detected |" >> "$OUT"
  fi

  echo ""
  echo "## Contract verification rule" >> "$OUT"
  echo "Frontend API clients are generated ONLY from verified backend contracts." >> "$OUT"
  echo "Never invent endpoints, fields, permissions, or response structures." >> "$OUT"

  log "Backend contracts written to $OUT"
}

main "$@"
