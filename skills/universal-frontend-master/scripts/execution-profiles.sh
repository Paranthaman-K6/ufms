#!/usr/bin/env bash
# execution-profiles.sh
# Priority 9 — Execution Profiles: lite / standard / advanced / autonomous.
#
# Reads skills/universal-frontend-master/profiles/<name>.json and either prints the
# configuration or enforces it for a proposed delegation set.
#
# Usage:
#   execution-profiles.sh [lite|standard|advanced|autonomous] [--json]
#   execution-profiles.sh --enforce <profile> --agents <csv> \
#       [--parallel] [--research <shallow|moderate|deep>] \
#       [--verify <basic|standard|thorough|exhaustive>] \
#       [--browser <basic|standard|comprehensive>] [--json]
#   execution-profiles.sh --enforce <profile> --delegates <csv> [...]  # primary added automatically
#
# Schema: profiles declare
#   primaryAgent            always active entry agent (never counted as a delegate)
#   allowedAgents           every role the profile may activate, including the primary
#   maxConcurrentDelegates  concurrent specialist slots (primary excluded)
#
# Enforcement checks:
#   * the primary agent is active exactly once
#   * every agent belongs to the profile's allowed set
#   * concurrent delegates <= maxConcurrentDelegates
#   * maxConcurrentDelegates never exceeds the real delegate role count
#   * parallelism is not requested when the profile forbids it or only one delegate is active
#   * requested research/verification/browser depth does not exceed the profile
#   * security constraints are always reported and never bypassed
#
# On --enforce the effective settings and any violations are recorded in
# .ufme/evidence/profile-enforcement.json. Exit 0 = compliant, 1 = violation,
# 2 = usage/config error.
#
# Safety: read-only; no system modification.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PROFILES_DIR="${UFME_PROFILES_DIR:-$ROOT_DIR/skills/universal-frontend-master/profiles}"
EVIDENCE_DIR="${UFME_EVIDENCE_DIR:-$ROOT_DIR/.ufme/evidence}"

log() { echo "[execution-profiles] $*"; }

usage() {
  echo "Usage: $0 [lite|standard|advanced|autonomous] [--json]"
  echo "       $0 --enforce <profile> (--agents <a,b,...> | --delegates <a,b,...>) [--parallel]"
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
for key in ("primaryAgent", "maxConcurrentDelegates", "allowedAgents", "researchDepth",
            "allowedParallelism", "verificationDepth", "resourceBudget",
            "browserTestingLevel", "selfImprovement"):
    print(f"  {key}: {p.get(key)}")
print("\n# Security constraints (never bypassed by any profile)")
for key, value in (p.get("securityConstraints") or {}).items():
    print(f"{key}={str(value).lower()}")
print(f"mandatoryAcceptanceCriteria={str(p.get('mandatoryAcceptanceCriteria', True)).lower()}")
PY
}

enforce_profile() {
  local profile="$1" agents="$2" delegates="$3" parallel="$4" research="$5" verify="$6" browser="$7" as_json="$8"
  local profile_json
  profile_json="$(load_profile "$profile")" || exit $?

  mkdir -p "$EVIDENCE_DIR"
  PROFILE_JSON="$profile_json" AGENTS="$agents" DELEGATES="$delegates" PARALLEL="$parallel" \
    RESEARCH="$research" VERIFY="$verify" BROWSER="$browser" AS_JSON="$as_json" \
    EVIDENCE="$EVIDENCE_DIR/profile-enforcement.json" \
    python3 - <<'PY'
import json, os, sys
from datetime import datetime, timezone

p = json.loads(os.environ["PROFILE_JSON"])
raw_agents = [a.strip() for a in os.environ["AGENTS"].split(",") if a.strip()]
delegate_arg = [a.strip() for a in os.environ["DELEGATES"].split(",") if a.strip()]
parallel = os.environ["PARALLEL"] == "1"
requested = {
    "research": os.environ["RESEARCH"],
    "verify": os.environ["VERIFY"],
    "browser": os.environ["BROWSER"],
}
as_json = os.environ["AS_JSON"] == "1"

name = p.get("name", "?")
primary = p.get("primaryAgent")
allowed = list(p.get("allowedAgents") or [])
max_delegates = p.get("maxConcurrentDelegates")
RANKS = {
    "research": ["shallow", "moderate", "deep"],
    "verify": ["basic", "standard", "thorough", "exhaustive"],
    "browser": ["basic", "standard", "comprehensive"],
}
FIELDS = {"research": "researchDepth", "verify": "verificationDepth",
          "browser": "browserTestingLevel"}

violations = []
if not isinstance(primary, str) or not primary:
    violations.append(f"profile '{name}' declares no primaryAgent")
if not isinstance(max_delegates, int) or isinstance(max_delegates, bool) or max_delegates < 1:
    violations.append(f"profile '{name}' declares no positive integer maxConcurrentDelegates")
if not allowed:
    violations.append(f"profile '{name}' declares no allowedAgents")
if primary and allowed and primary not in allowed:
    violations.append(f"primaryAgent '{primary}' is not in allowedAgents for profile '{name}'")

available_delegates = [a for a in allowed if a != primary]
if isinstance(max_delegates, int) and max_delegates > len(available_delegates):
    violations.append(
        f"profile '{name}' advertises {max_delegates} concurrent delegates but only "
        f"{len(available_delegates)} delegate roles exist")

if raw_agents and delegate_arg:
    violations.append("use either --agents (full set) or --delegates, not both")
if delegate_arg:
    agents = ([primary] if primary else []) + delegate_arg
else:
    agents = raw_agents

if not agents:
    violations.append("no active agents provided")
if primary and agents.count(primary) == 0:
    violations.append(f"active set must include the primary agent '{primary}'")
if primary and agents.count(primary) > 1:
    violations.append(f"primary agent '{primary}' listed more than once")
if len(set(agents)) != len(agents):
    violations.append("duplicate agent names in the active set")
unknown = sorted(set(agents) - set(allowed))
if unknown:
    violations.append(
        f"agents not allowed in profile '{name}': {unknown} (allowed: {sorted(allowed)})")

delegates = [a for a in agents if a != primary]
# --agents lists every role activated over the task; only parallel execution makes
# them concurrent. Sequential delegation is bounded by the role set, not by the
# concurrency cap.
concurrent = len(delegates) if parallel else (1 if delegates else 0)
if parallel and isinstance(max_delegates, int) and len(delegates) > max_delegates:
    violations.append(
        f"{len(delegates)} concurrent delegates exceed maxConcurrentDelegates "
        f"{max_delegates} for profile '{name}'")
if parallel and not p.get("allowedParallelism", False):
    violations.append(f"parallel execution is disabled for profile '{name}'")
if parallel and len(delegates) < 2:
    violations.append("parallel execution requires at least two concurrent delegates")
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
    "primaryAgent": primary,
    "activeAgents": agents,
    "delegates": delegates,
    "delegateCount": len(delegates),
    "concurrentDelegates": concurrent,
    "maxConcurrentDelegates": max_delegates,
    "availableAgents": sorted(allowed),
    "availableDelegateRoles": sorted(available_delegates),
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
    print(f"  Primary: {primary}")
    print(f"  Delegates ({len(delegates)}/{max_delegates}): {', '.join(delegates) or '(none)'}")
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
    local profile="${1:-}" agents="" delegates="" parallel="0" research="" verify="" browser="" as_json="0"
    shift || true
    while [ $# -gt 0 ]; do
      case "$1" in
        --agents) agents="${2:-}"; shift 2 ;;
        --agents=*) agents="${1#*=}"; shift ;;
        --delegates) delegates="${2:-}"; shift 2 ;;
        --delegates=*) delegates="${1#*=}"; shift ;;
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
    if ! validate_profile_name "$profile" || { [ -z "$agents" ] && [ -z "$delegates" ]; }; then
      log "ERROR: --enforce requires a valid profile and --agents <csv> or --delegates <csv>"
      usage >&2
      exit 2
    fi
    enforce_profile "$profile" "$agents" "$delegates" "$parallel" "$research" "$verify" "$browser" "$as_json"
    exit $?
  fi

  local as_json="0"
  if [ "${2:-}" = "--json" ]; then as_json="1"; fi
  show_profile "$action" "$as_json"
}

main "$@"
