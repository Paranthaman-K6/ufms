#!/usr/bin/env bash
# execution-profiles.sh
# Priority 9 — Execution Profiles: lite / standard / advanced / autonomous.
#
# Reads universal-frontend-master-source/profiles/<name>.json and either prints the
# configuration or enforces it for a proposed delegation set.
#
# Usage:
#   execution-profiles.sh [lite|standard|advanced|autonomous] [--json]
#   execution-profiles.sh --enforce <profile> --agents <csv> \
#       [--parallel] [--research <shallow|moderate|deep>] \
#       [--verify <basic|standard|thorough|exhaustive>] \
#       [--browser <basic|standard|comprehensive>] [--json]
#
# Enforcement checks:
#   * active agent count <= profile maxAgents
#   * every agent belongs to the profile's allowed set
#   * parallelism is not requested when the profile forbids it
#   * requested research/verification/browser depth does not exceed the profile
#   * security constraints are always reported and never bypassed
#
# On --enforce the effective settings and any violations are recorded in
# .ufme/evidence/profile-enforcement.json. Exit 0 = compliant, 1 = violation,
# 2 = usage/config error.
#
# Safety: read-only; no system modification.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROFILES_DIR="$ROOT_DIR/universal-frontend-master-source/profiles"
EVIDENCE_DIR="${UFME_EVIDENCE_DIR:-$ROOT_DIR/.ufme/evidence}"

log() { echo "[execution-profiles] $*"; }

usage() {
  echo "Usage: $0 [lite|standard|advanced|autonomous] [--json]"
  echo "       $0 --enforce <profile> --agents <a,b,...> [--parallel]"
  echo "          [--research <shallow|moderate|deep>] [--verify <basic|standard|thorough|exhaustive>]"
  echo "          [--browser <basic|standard|comprehensive>] [--json]"
}

validate_profile_name() {
  case "$1" in
    lite|standard|advanced|autonomous) return 0 ;;
    *) return 1 ;;
  esac
}

load_profile() {
  local file="$PROFILES_DIR/$1.json"
  if [ ! -f "$file" ]; then
    log "ERROR: Profile configuration not found: $file"
    return 2
  fi
  if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$file" 2>/dev/null; then
    log "ERROR: Invalid JSON in profile: $file"
    return 2
  fi
  cat "$file"
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

# Pretty-print a profile without enforcement.
show_profile() {
  local profile="$1" as_json="$2" profile_json
  profile_json="$(load_profile "$profile")" || exit $?
  if [ "$as_json" = "1" ]; then
    echo "$profile_json"
    return 0
  fi
  python3 - "$profile_json" <<'PY'
import json, sys
p = json.loads(sys.argv[1])
print(f"Profile: {p['name']}")
for key in ("maxAgents", "researchDepth", "allowedParallelism", "verificationDepth",
            "resourceBudget", "browserTestingLevel", "selfImprovement"):
    print(f"  {key}: {p.get(key)}")
print("\n# Security constraints (never bypassed by any profile)")
for key, value in (p.get("securityConstraints") or {}).items():
    print(f"{key}={str(value).lower()}")
print(f"mandatoryAcceptanceCriteria={str(p.get('mandatoryAcceptanceCriteria', True)).lower()}")
PY
}

enforce_profile() {
  local profile="$1" agents="$2" parallel="$3" research="$4" verify="$5" browser="$6" as_json="$7"
  local profile_json
  profile_json="$(load_profile "$profile")" || exit $?

  mkdir -p "$EVIDENCE_DIR"
  PROFILE_JSON="$profile_json" AGENTS="$agents" PARALLEL="$parallel" \
    RESEARCH="$research" VERIFY="$verify" BROWSER="$browser" AS_JSON="$as_json" \
    EVIDENCE="$EVIDENCE_DIR/profile-enforcement.json" \
    python3 - <<'PY'
import json, os, sys
from datetime import datetime, timezone

p = json.loads(os.environ["PROFILE_JSON"])
agents = [a.strip() for a in os.environ["AGENTS"].split(",") if a.strip()]
parallel = os.environ["PARALLEL"] == "1"
requested = {
    "research": os.environ["RESEARCH"],
    "verify": os.environ["VERIFY"],
    "browser": os.environ["BROWSER"],
}
as_json = os.environ["AS_JSON"] == "1"

ALLOWED = {
    "lite": {"universal-frontend-master", "ufme-orchestrator"},
    "standard": {"universal-frontend-master", "ufme-orchestrator",
                 "ufme-designer", "ufme-builder"},
    "advanced": {"universal-frontend-master", "ufme-orchestrator",
                 "ufme-designer", "ufme-builder", "ufme-backend-analyst", "ufme-auditor"},
    "autonomous": {"universal-frontend-master", "ufme-orchestrator",
                   "ufme-designer", "ufme-builder", "ufme-backend-analyst", "ufme-auditor"},
}
RANKS = {
    "research": ["shallow", "moderate", "deep"],
    "verify": ["basic", "standard", "thorough", "exhaustive"],
    "browser": ["basic", "standard", "comprehensive"],
}
FIELDS = {"research": "researchDepth", "verify": "verificationDepth",
          "browser": "browserTestingLevel"}

name = p["name"]
max_agents = int(p.get("maxAgents", 0))
violations = []

if not agents:
    violations.append("no active agents provided")
if len(agents) > max_agents:
    violations.append(
        f"agent count {len(agents)} exceeds maxAgents {max_agents} for profile '{name}'")
if len(set(agents)) != len(agents):
    violations.append("duplicate agent names in --agents")
unknown = sorted(set(agents) - ALLOWED.get(name, set()))
if unknown:
    violations.append(
        f"agents not allowed in profile '{name}': {unknown} "
        f"(allowed: {sorted(ALLOWED.get(name, set()))})")
if parallel and not p.get("allowedParallelism", False):
    violations.append(f"parallel execution is disabled for profile '{name}'")
for key, value in requested.items():
    if not value:
        continue
    allowed_values = RANKS[key]
    effective = p.get(FIELDS[key])
    if value not in allowed_values:
        violations.append(f"invalid {key} level '{value}'")
    elif effective in allowed_values and allowed_values.index(value) > allowed_values.index(effective):
        violations.append(
            f"requested {key} '{value}' exceeds profile '{name}' level '{effective}'")

effective = {
    "profile": name,
    "activeAgents": agents,
    "maxAgents": max_agents,
    "researchDepth": p.get(FIELDS["research"]),
    "allowedParallelism": bool(p.get("allowedParallelism", False)),
    "verificationDepth": p.get(FIELDS["verify"]),
    "browserTestingLevel": p.get(FIELDS["browser"]),
    "selfImprovement": bool(p.get("selfImprovement", False)),
    "resourceBudget": p.get("resourceBudget"),
    "securityConstraints": p.get("securityConstraints", {}),
    "mandatoryAcceptanceCriteria": bool(p.get("mandatoryAcceptanceCriteria", True)),
    "requested": {k: v for k, v in requested.items() if v},
    "parallelRequested": parallel,
    "violations": violations,
    "status": "FAIL" if violations else "PASS",
    "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
}
with open(os.environ["EVIDENCE"], "w", encoding="utf-8") as fh:
    json.dump(effective, fh, indent=2)
    fh.write("\n")

if as_json:
    print(json.dumps(effective, indent=2))
else:
    print(f"[execution-profiles] Profile: {name}")
    print(f"  Active agents ({len(agents)}/{max_agents}): {', '.join(agents) or '(none)'}")
    print(f"  Research: {effective['researchDepth']} | "
          f"Parallel: {effective['allowedParallelism']} | "
          f"Verification: {effective['verificationDepth']} | "
          f"Browser: {effective['browserTestingLevel']} | "
          f"Self-improvement: {effective['selfImprovement']}")
    if violations:
        for v in violations:
            print(f"[execution-profiles] VIOLATION: {v}", file=sys.stderr)
    else:
        print("[execution-profiles] Profile enforcement passed.")
print(f"[execution-profiles] Evidence: {os.environ['EVIDENCE']}", file=sys.stderr)
sys.exit(1 if violations else 0)
PY
}

main() {
  local action="${1:-}"
  if [ -z "$action" ]; then
    usage >&2
    exit 2
  fi
  if ! validate_profile_name "$action"; then
    if [ "$action" != "--enforce" ]; then
      log "ERROR: Invalid profile: $action"
      usage >&2
      exit 2
    fi
    shift
    local profile="${1:-}" agents="" parallel="0" research="" verify="" browser="" as_json="0"
    shift || true
    while [ $# -gt 0 ]; do
      case "$1" in
        --agents) agents="${2:-}"; shift 2 ;;
        --agents=*) agents="${1#*=}"; shift ;;
        --parallel) parallel="1"; shift ;;
        --research) research="${2:-}"; shift 2 ;;
        --research=*) research="${1#*=}"; shift ;;
        --verify) verify="${2:-}"; shift 2 ;;
        --verify=*) verify="${1#*=}"; shift ;;
        --browser) browser="${2:-}"; shift 2 ;;
        --browser=*) browser="${1#*=}"; shift ;;
        --json) as_json="1"; shift ;;
        *) log "ERROR: unknown option: $1"; usage >&2; exit 2 ;;
      esac
    done
    if ! validate_profile_name "$profile" || [ -z "$agents" ]; then
      log "ERROR: --enforce requires a valid profile and --agents <csv>"
      usage >&2
      exit 2
    fi
    enforce_profile "$profile" "$agents" "$parallel" "$research" "$verify" "$browser" "$as_json"
    exit $?
  fi

  local as_json="0"
  if [ "${2:-}" = "--json" ]; then as_json="1"; fi
  show_profile "$action" "$as_json"
}

main "$@"
