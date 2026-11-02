#!/usr/bin/env bash
# self-improve.sh
# Self-improvement: audits the universal-frontend-master skill itself and records findings
# so the skill can evolve. Run periodically or after a delivery to fold lessons back into
# the skill. Produces .ufme/SELF_IMPROVEMENT.md with PASS/FAIL/SKIPPED per check.
#
# Safety: read-only analysis of skill files; never sudo/pacman/systemctl. Project-local only.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_DIR="$ROOT_DIR/universal-frontend-master-source"
UFME_DIR="$ROOT_DIR/.ufme"
REPORT="$UFME_DIR/SELF_IMPROVEMENT.md"

mkdir -p "$UFME_DIR"

FAILURES=0
SKIPPED=0
PASSES=0

log() { echo "[self-improve] $*"; }

note() { # note <status> <label> [detail]
  local status="$1" label="$2" detail="${3:-}"
  case "$status" in
    PASS)   PASSES=$((PASSES+1)); log "PASS: $label${detail:+: $detail}";;
    FAIL)   FAILURES=$((FAILURES+1)); log "FAIL: $label${detail:+: $detail}";;
    SKIPPED) SKIPPED=$((SKIPPED+1)); log "SKIPPED: $label${detail:+: $detail}";;
  esac
}

check_file() { # check_file <path> <label> [check_type]
  local path="$1" label="$2" type="${3:-exists}"
  if [ ! -f "$path" ]; then
    note FAIL "$label" "missing"
    return 1
  fi
  case "$type" in
    exists)
      if [ -s "$path" ]; then note PASS "$label"; else note FAIL "$label" "empty"; fi
      ;;
    syntax)
      if [[ "$path" == *.py ]]; then
        if python3 -m py_compile "$path" 2>/dev/null; then note PASS "$label" "executable + syntax valid"; else note FAIL "$label" "syntax invalid"; fi
      elif [[ "$path" == *.js ]]; then
        if node --check "$path" 2>/dev/null; then note PASS "$label" "syntax valid"; else note FAIL "$label" "syntax invalid"; fi
      else
        if bash -n "$path" 2>/dev/null; then note PASS "$label" "executable + syntax valid"; else note FAIL "$label" "syntax invalid"; fi
      fi
      ;;
    exec)
      if [ -x "$path" ]; then note PASS "$label" "executable"; else note FAIL "$label" "not executable"; fi
      ;;
  esac
}

has_frontmatter() { # has_frontmatter <file>
  head -1 "$1" | grep -q '^---$'
}

get_frontmatter_field() { # get_frontmatter_field <file> <field>
  awk -v field="$2" '
    /^---$/ { if (started) exit; started=1; next }
    started && $0 ~ field ":" { sub(/^[^:]+: */, ""); print; exit }
  ' "$1"
}
{
  echo "# UFME Self-Improvement Report"
  echo "Generated: $(date -Iseconds)"
  echo ""

  echo "## Skill file audit (content validation)"
  for f in \
    "$SOURCE_DIR/core/MASTER_SKILL.md" \
    "$SOURCE_DIR/core/MULTI_AGENT_ORCHESTRATION.md" \
    "$SOURCE_DIR/core/AGENT_RULES.md" \
    "$SOURCE_DIR/core/PROJECT_MEMORY.md" \
    "$SOURCE_DIR/core/QUALITY_STANDARDS.md" \
    "$SOURCE_DIR/core/SAFETY.md" \
    "$SOURCE_DIR/core/ARCH_LINUX.md" \
    "$SOURCE_DIR/core/SYSTEM_ARCHITECTURE.md"; do
    check_file "$f" "$(basename "$f")"
  done

  echo ""
  echo "## Agent audit (frontmatter + mode)"
  for a in orchestrator researcher backend-analyst product-analyst designer frontend-architect implementer integrator visual-auditor accessibility-auditor performance-auditor security-auditor; do
    f="$SOURCE_DIR/agents/$a.md"
    if ! check_file "$f" "ufme-$a" exists; then
      continue
    fi
    if ! has_frontmatter "$f"; then
      note FAIL "ufme-$a" "no frontmatter"
      continue
    fi
    mode=$(get_frontmatter_field "$f" "mode")
    if [ -z "$mode" ]; then
      note FAIL "ufme-$a" "no mode field"
    else
      note PASS "ufme-$a" "mode=$mode"
    fi
  done

  echo ""
  echo "## Workflow audit (14 expected)"
  for i in 01 02 03 04 05 06 07 08 09 10 11 12 13 14; do
    match=$(ls "$SOURCE_DIR/workflows/${i}-"*.md 2>/dev/null | head -1)
    if [ -n "$match" ] && [ -s "$match" ]; then
      note PASS "workflow $i" "$(basename "$match")"
    else
      note FAIL "workflow $i" "missing or empty"
    fi
  done

  echo ""
  echo "## Script audit (executable + syntax-valid)"
  for s in detect-stack backend-discovery check-native-browser browser-test screenshot quality-check self-improve search-libraries.py detect-platform discover-assets execution-profiles enhance-backend-discovery generate-prototype.py task-checkpoint; do
    if [[ "$s" == *.py ]]; then
      f="$SOURCE_DIR/scripts/$s"
    else
      f="$SOURCE_DIR/scripts/$s.sh"
    fi
    check_file "$f" "$s" exec
    check_file "$f" "$s" syntax
  done

  echo ""
  echo "## Browser abstraction audit"
  for f in tests/browser/browser.js tests/browser/screenshot.js tests/browser/run.js tests/browser/validate.js; do
    check_file "$ROOT_DIR/$f" "$f" syntax
  done

  echo ""
  echo "## OpenCode install audit"
  SKILL="$ROOT_DIR/.opencode/skills/universal-frontend-master/SKILL.md"
  if [ ! -f "$SKILL" ]; then
    note FAIL "SKILL.md" "missing"
  elif ! has_frontmatter "$SKILL"; then
    note FAIL "SKILL.md" "no frontmatter"
  else
    sname=$(get_frontmatter_field "$SKILL" "name")
    sdesc=$(get_frontmatter_field "$SKILL" "description")
    if [ -z "$sname" ] || [ -z "$sdesc" ]; then
      note FAIL "SKILL.md" "missing name/description"
    else
      note PASS "SKILL.md" "name=$sname"
    fi
  fi
  if [ -f "$ROOT_DIR/opencode.json" ]; then
    if python3 -c "import json; json.load(open('$ROOT_DIR/opencode.json'))" 2>/dev/null; then
      note PASS "opencode.json" "valid JSON"
    else
      note FAIL "opencode.json" "invalid JSON"
    fi
  else
    note FAIL "opencode.json" "missing"
  fi
  for a in ufme-orchestrator ufme-researcher ufme-backend-analyst ufme-product-analyst ufme-designer ufme-frontend-architect ufme-implementer ufme-integrator ufme-visual-auditor ufme-accessibility-auditor ufme-performance-auditor ufme-security-auditor; do
    f="$ROOT_DIR/.opencode/agents/$a.md"
    if [ ! -f "$f" ]; then
      note FAIL "$a" "missing"
    elif ! has_frontmatter "$f"; then
      note FAIL "$a" "no frontmatter"
    else
      note PASS "$a" "frontmatter present"
    fi
  done

  echo ""
  echo "## Runtime memory audit"
  for f in TASKS.md ENVIRONMENT.md SKILL_VALIDATION.md; do
    if [ -f "$UFME_DIR/$f" ] && [ -s "$UFME_DIR/$f" ]; then
      note PASS "$f"
    else
      note FAIL "$f" "missing or empty"
    fi
  done

  echo ""
  echo "## Summary"
  echo "PASS: $PASSES"
  echo "FAIL: $FAILURES"
  echo "SKIPPED: $SKIPPED"
  if [ "$FAILURES" -gt 0 ]; then
    echo "Result: FAILED"
    exit 1
  else
    echo "Result: PASSED"
    exit 0
  fi
} > "$REPORT"

cat "$REPORT"
