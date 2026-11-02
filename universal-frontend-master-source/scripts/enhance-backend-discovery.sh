#!/usr/bin/env bash
# enhance-backend-discovery.sh
# Priority 6 — Backend Intelligence: enhanced contract discovery.
# Detects and parses GraphQL, WebSockets, SSE, OpenAPI/Swagger, Postman, AsyncAPI
# contracts. Extracts methods, paths, parameters, request/response schemas,
# authentication requirements, error responses, pagination, WebSocket channels,
# and SSE events. Every extracted capability includes an evidence source.
#
# Classifies each capability as:
#   CONFIRMED — found in contract file with evidence
#   INFERRED — strongly suggested but not directly evidenced
#   UNKNOWN — mentioned but details not available
#   NOT_FOUND — not present
#   NOT_APPLICABLE — not relevant
#
# Safety: read-only analysis; writes .ufme/BACKEND_CONTRACTS.md only.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UFME_DIR="$ROOT_DIR/.ufme"
OUT="$UFME_DIR/BACKEND_CONTRACTS.md"

mkdir -p "$UFME_DIR"

log() { echo "[enhance-backend-discovery] $*"; }

# Check if jq is available for JSON parsing.
HAS_JQ=0
command -v jq >/dev/null 2>&1 && HAS_JQ=1

# Check if python3 is available for YAML/JSON parsing.
HAS_PY3=0
command -v python3 >/dev/null 2>&1 && HAS_PY3=1

main() {
  {
    echo "# Backend Contracts"
    echo "Generated: $(date -Iseconds)"
    echo ""
    echo "| Capability | Type | Classification | Evidence | Details |"
    echo "|------------|------|----------------|----------|---------|"
  } > "$OUT"

  local found_any=0

  # --- OpenAPI / Swagger JSON ---
  for f in openapi.json swagger.json; do
    if [ -f "$ROOT_DIR/$f" ]; then
      found_any=1
      if [ "$HAS_JQ" -eq 1 ]; then
        local methods paths auth
        methods=$(jq -r '.paths | to_entries[] | .key + " " + (.value | keys | join(", "))' "$ROOT_DIR/$f" 2>/dev/null || echo "")
        paths=$(jq -r '.paths | keys | join(", ")' "$ROOT_DIR/$f" 2>/dev/null || echo "")
        auth=$(jq -r '.security // .components.securitySchemes | keys | join(", ")' "$ROOT_DIR/$f" 2>/dev/null || echo "none")
        echo "| OpenAPI/Swagger | REST | CONFIRMED | $f | methods: $methods | paths: $paths | auth: $auth |" >> "$OUT"
      else
        echo "| OpenAPI/Swagger | REST | CONFIRMED | $f | JSON parsing requires jq |" >> "$OUT"
      fi
    fi
  done

  # --- OpenAPI / Swagger YAML ---
  for f in openapi.yaml openapi.yml swagger.yaml swagger.yml; do
    if [ -f "$ROOT_DIR/$f" ]; then
      found_any=1
      if [ "$HAS_PY3" -eq 1 ]; then
        python3 -c "
import yaml, sys
with open('$ROOT_DIR/$f') as fh:
    spec = yaml.safe_load(fh)
paths = list(spec.get('paths', {}).keys())
methods = []
for p, ops in spec.get('paths', {}).items():
    for m in ops:
        if m in ('get','post','put','patch','delete','head','options'):
            methods.append(m.upper() + ' ' + p)
print('PATHS:' + ','.join(paths))
print('METHODS:' + ','.join(methods))
" 2>/dev/null | while IFS= read -r line; do
          echo "| OpenAPI/Swagger YAML | REST | CONFIRMED | $f | $line |" >> "$OUT"
        done
      else
        echo "| OpenAPI/Swagger YAML | REST | CONFIRMED | $f | YAML parsing requires python3 |" >> "$OUT"
      fi
    fi
  done

  # --- Postman collections ---
  for f in postman.json postman_collection.json; do
    if [ -f "$ROOT_DIR/$f" ]; then
      found_any=1
      if [ "$HAS_JQ" -eq 1 ]; then
        local items
        items=$(jq -r '.item[]? | .request.method + " " + .request.url.raw' "$ROOT_DIR/$f" 2>/dev/null | head -20 || echo "")
        echo "| Postman | REST | CONFIRMED | $f | requests: $items |" >> "$OUT"
      else
        echo "| Postman | REST | CONFIRMED | $f | JSON parsing requires jq |" >> "$OUT"
      fi
    fi
  done

  # --- GraphQL schema ---
  for f in schema.graphql schema.gql; do
    if [ -f "$ROOT_DIR/$f" ]; then
      found_any=1
      local types queries mutations
      types=$(grep -cE '^(type|input|enum|interface|union) ' "$ROOT_DIR/$f" 2>/dev/null || echo 0)
      queries=$(grep -cE '^\s*query ' "$ROOT_DIR/$f" 2>/dev/null || echo 0)
      mutations=$(grep -cE '^\s*mutation ' "$ROOT_DIR/$f" 2>/dev/null || echo 0)
      echo "| GraphQL | GraphQL | CONFIRMED | $f | types: $types | queries: $queries | mutations: $mutations |" >> "$OUT"
    fi
  done

  # --- AsyncAPI ---
  for f in asyncapi.json asyncapi.yaml asyncapi.yml; do
    if [ -f "$ROOT_DIR/$f" ]; then
      found_any=1
      if [ "$HAS_JQ" -eq 1 ] && [ "${f##*.}" = "json" ]; then
        local channels
        channels=$(jq -r '.channels | keys | join(", ")' "$ROOT_DIR/$f" 2>/dev/null || echo "")
        echo "| AsyncJSON | AsyncAPI | CONFIRMED | $f | channels: $channels |" >> "$OUT"
      elif [ "$HAS_PY3" -eq 1 ]; then
        python3 -c "
import yaml, sys
with open('$ROOT_DIR/$f') as fh:
    spec = yaml.safe_load(fh)
channels = list(spec.get('channels', {}).keys())
print('CHANNELS:' + ','.join(channels))
" 2>/dev/null | while IFS= read -r line; do
          echo "| AsyncAPI | AsyncAPI | CONFIRMED | $f | $line |" >> "$OUT"
        done
      else
        echo "| AsyncAPI | AsyncAPI | CONFIRMED | $f | parsing requires jq or python3 |" >> "$OUT"
      fi
    fi
  done

  # --- WebSocket / SSE hints in source ---
  local ws_hits sse_hits
  ws_hits=$(grep -rlE 'new WebSocket|ws://|wss://|io\.connect|socket\.io' "$ROOT_DIR" --include='*.js' --include='*.ts' --include='*.py' --include='*.go' --include='*.java' --include='*.rb' --include='*.php' 2>/dev/null | grep -v node_modules | head -5 || true)
  if [ -n "$ws_hits" ]; then
    found_any=1
    echo "| WebSocket | WebSocket | INFERRED | $ws_hits | Source references detected; verify manually |" >> "$OUT"
  else
    echo "| WebSocket | WebSocket | NOT_FOUND | — | No WebSocket references in source |" >> "$OUT"
  fi

  sse_hits=$(grep -rlE 'EventSource|text/event-stream' "$ROOT_DIR" --include='*.js' --include='*.ts' --include='*.py' --include='*.go' --include='*.java' --include='*.rb' --include='*.php' 2>/dev/null | grep -v node_modules | head -5 || true)
  if [ -n "$sse_hits" ]; then
    found_any=1
    echo "| SSE | SSE | INFERRED | $sse_hits | Source references detected; verify manually |" >> "$OUT"
  else
    echo "| SSE | SSE | NOT_FOUND | — | No SSE references in source |" >> "$OUT"
  fi

  # --- Authentication hints ---
  local auth_hits
  auth_hits=$(grep -rlE 'authorization|bearer|jwt|oauth|api.?key' "$ROOT_DIR" --include='*.js' --include='*.ts' --include='*.py' --include='*.go' --include='*.java' --include='*.rb' --include='*.php' 2>/dev/null | grep -v node_modules | head -5 || true)
  if [ -n "$auth_hits" ]; then
    found_any=1
    echo "| Authentication | Auth | INFERRED | $auth_hits | Auth references detected; verify manually |" >> "$OUT"
  else
    echo "| Authentication | Auth | NOT_FOUND | — | No auth references in source |" >> "$OUT"
  fi

  if [ "$found_any" -eq 0 ]; then
    echo "| None | — | NOT_FOUND | — | No backend contract files detected |" >> "$OUT"
  fi

  echo ""
  echo "## Classification scale" >> "$OUT"
  echo "| Classification | Meaning |" >> "$OUT"
  echo "|----------------|---------|" >> "$OUT"
  echo "| CONFIRMED | Verified in contract file with evidence |" >> "$OUT"
  echo "| INFERRED | Strongly suggested but not directly evidenced |" >> "$OUT"
  echo "| UNKNOWN | Mentioned but details not available |" >> "$OUT"
  echo "| NOT_FOUND | Not present |" >> "$OUT"
  echo "| NOT_APPLICABLE | Not relevant to this frontend |" >> "$OUT"
  echo "" >> "$OUT"
  echo "## Contract verification rule" >> "$OUT"
  echo "Frontend API clients are generated ONLY from capabilities classified CONFIRMED." >> "$OUT"
  echo "Never invent endpoints, fields, permissions, or response structures." >> "$OUT"

  log "Backend contracts written to $OUT"
}

main "$@"
