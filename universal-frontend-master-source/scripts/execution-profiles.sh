#!/usr/bin/env bash
# execution-profiles.sh
# Priority 9 — Execution Profiles: lite / standard / advanced / autonomous.
# Reads configuration from universal-frontend-master-source/profiles/<name>.json
# and outputs the profile configuration or enforces agent limits.
#
# Usage:
#   execution-profiles.sh [lite|standard|advanced|autonomous] [--json]
#   execution-profiles.sh --enforce <profile> --agents <comma-separated-agents>
#
# Exit codes: 0 = valid / compliant, non-zero = invalid profile, enforcement violation, or error.
#
# Safety: read-only; no system modification.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROFILES_DIR="$ROOT_DIR/universal-frontend-master-source/profiles"

ACTION="${1:-}"

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
  if ! python3 -c "
import json, sys
try:
    file_path = sys.argv[1]
    with open(file_path, 'r') as f:
        content = f.read()
        json.loads(content)
        sys.stdout.write(content)
except Exception as e:
    sys.stderr.write(str(e))
    sys.exit(1)
" "$file" 2>/dev/null; then
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

enforce_profile() {
  local profile="$1"
  local agents_csv="$2"

  if ! validate_profile_name "$profile"; then
    log "ERROR: Invalid profile for enforcement: $profile"
    return 1
  fi

  local profile_json
  profile_json="$(load_profile "$profile")" || return 1

  python3 - "$profile_json" "$agents_csv" <<'PYEOF'
import json, sys

profile = json.loads(sys.argv[1])
agents_csv = sys.argv[2]
max_agents = profile.get("maxAgents", 12)

agents = [a.strip() for a in agents_csv.split(",") if a.strip()]
count = len(agents)

print(f"[execution-profiles] Enforcing profile '{profile['name']}': maxAgents={max_agents}, provided agents={count} ({', '.join(agents)})")

if count > max_agents:
    print(f"ERROR: Agent count ({count}) exceeds maximum allowed ({max_agents}) for profile '{profile['name']}'.", file=sys.stderr)
    sys.exit(1)

allowed_sets = {
    "lite": {"universal-frontend-master", "ufme-orchestrator", "ufme-builder"},
    "standard": {"universal-frontend-master", "ufme-orchestrator", "ufme-designer", "ufme-builder", "ufme-backend-analyst"},
    "advanced": {"universal-frontend-master", "ufme-orchestrator", "ufme-designer", "ufme-builder", "ufme-backend-analyst", "ufme-auditor"},
    "autonomous": {"universal-frontend-master", "ufme-orchestrator", "ufme-designer", "ufme-builder", "ufme-backend-analyst", "ufme-auditor"},
}

profile_name = profile["name"]
allowed = allowed_sets.get(profile_name, set())
if allowed:
    unauthorized = [a for a in agents if a not in allowed and a != "universal-frontend-master" and a != "ufme-orchestrator"]
    if unauthorized:
        print(f"ERROR: Unauthorized agent(s) {unauthorized} not allowed in profile '{profile_name}'. Allowed: {sorted(allowed)}", file=sys.stderr)
        sys.exit(1)

print("[execution-profiles] Profile enforcement passed.")
PYEOF
}

main() {
  if [ -z "$ACTION" ]; then
    log "ERROR: No action or profile specified."
    echo "Usage: $0 [lite|standard|advanced|autonomous] [--json]"
    echo "       $0 --enforce <profile> --agents <agent1,agent2,...>"
    exit 1
  fi

  if [ "$ACTION" = "--enforce" ]; then
    local prof="${2:-}"
    local flag="${3:-}"
    local agents="${4:-}"
    if [ "$flag" != "--agents" ] || [ -z "$prof" ] || [ -z "$agents" ]; then
      log "ERROR: Usage: $0 --enforce <profile> --agents <agent1,agent2,...>"
      exit 1
    fi
    enforce_profile "$prof" "$agents"
    exit $?
  fi

  local PROFILE="$ACTION"
  local OUTPUT_JSON="${2:-}"

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
    echo "$profile_json"
  else
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
