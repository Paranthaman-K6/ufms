#!/usr/bin/env bash
# execution-profiles.sh
# Priority 9 — Execution Profiles: lite / standard / advanced / autonomous.
# Reads configuration from universal-frontend-master-source/profiles/<name>.json
# and outputs the profile configuration. Profiles are consumed by the orchestrator
# to control agent count, research depth, parallel execution, verification depth,
# and resource budgets. Security constraints are never bypassed.
#
# Usage: execution-profiles.sh [lite|standard|advanced|autonomous] [--json]
# Exit codes: 0 = valid profile, non-zero = invalid profile or error.
#
# Safety: read-only; no system modification.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROFILES_DIR="$ROOT_DIR/universal-frontend-master-source/profiles"

PROFILE="${1:-}"
OUTPUT_JSON="${2:-}"

log() { echo "[execution-profiles] $*"; }

validate_profile_name() {
  local name="$1"
  case "$name" in
    lite|standard|advanced|autonomous) return 0 ;;
    *) return 1 ;;
  esac
}

load_profile() {
  local name="$1"
  local file="$PROFILES_DIR/$name.json"
  if [ ! -f "$file" ]; then
    log "ERROR: Profile configuration not found: $file"
    return 1
  fi
  # Read the file once, validate JSON, and output the raw content safely
  if ! python3 -c "
import json, sys
try:
    with open('$file') as f:
        content = f.read()
        json.loads(content)  # Validate
        sys.stdout.write(content)  # Output raw content
except Exception as e:
    sys.stderr.write(str(e))
    sys.exit(1)
" 2>/dev/null; then
    log "ERROR: Invalid JSON in profile: $file"
    return 1
  fi
  return 0
}

print_security_constraints() {
  cat <<'CFG'
# Security constraints (never bypassed by any profile)
no_sudo=true
no_pacman=true
no_systemctl=true
no_playwright=true
no_containers=true
project_local_npm_only=true
mandatory_acceptance_criteria=true
CFG
}

main() {
  if [ -z "$PROFILE" ]; then
    log "ERROR: No profile specified."
    echo "Usage: $0 [lite|standard|advanced|autonomous] [--json]"
    exit 1
  fi

  if ! validate_profile_name "$PROFILE"; then
    log "ERROR: Invalid profile: $PROFILE"
    echo "Valid profiles: lite, standard, advanced, autonomous"
    exit 1
  fi

  local profile_json
  if ! profile_json="$(load_profile "$PROFILE")"; then
    exit 1
  fi

  if [ "$OUTPUT_JSON" = "--json" ]; then
    # Output valid JSON only: profile JSON already includes securityConstraints.
    echo "$profile_json"
  else
    # Human-readable output
    local name research_depth parallel verification budget browser self_improve max_agents
    name=$(echo "$profile_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['name'])" 2>/dev/null)
    max_agents=$(echo "$profile_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['maxAgents'])" 2>/dev/null)
    research_depth=$(echo "$profile_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['researchDepth'])" 2>/dev/null)
    parallel=$(echo "$profile_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['allowedParallelism'])" 2>/dev/null)
    verification=$(echo "$profile_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['verificationDepth'])" 2>/dev/null)
    budget=$(echo "$profile_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['resourceBudget'])" 2>/dev/null)
    browser=$(echo "$profile_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['browserTestingLevel'])" 2>/dev/null)
    self_improve=$(echo "$profile_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['selfImprovement'])" 2>/dev/null)

    echo "Profile: $name"
    echo "  Max agents: $max_agents"
    echo "  Research depth: $research_depth"
    echo "  Allowed parallelism: $parallel"
    echo "  Verification depth: $verification"
    echo "  Resource budget: $budget"
    echo "  Browser testing level: $browser"
    echo "  Self-improvement: $self_improve"
    echo ""
    print_security_constraints
    echo ""
    log "Profile '$PROFILE' loaded. Security constraints always enforced."
  fi

  exit 0
}

main "$@"
