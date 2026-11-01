#!/usr/bin/env bash
# self-improve.sh
# Self-improvement: audits the universal-frontend-master skill itself (templates, agents,
# scripts, docs) and records findings so the skill can evolve. Run periodically or after a
# delivery to fold lessons back into the skill.
#
# Safety: read-only analysis of skill files; never sudo/pacman/systemctl. Project-local only.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_DIR="$ROOT_DIR/universal-frontend-master-source"
UFME_DIR="$ROOT_DIR/.ufme"
REPORT="$UFME_DIR/SELF_IMPROVEMENT.md"

mkdir -p "$UFME_DIR"

log() { echo "[self-improve] $*"; }

check_file() { # check_file <path> <label>
  local f="$1" label="$2"
  if [ -f "$f" ]; then
    echo "OK: $label ($f)"
  else
    echo "MISSING: $label ($f)"
  fi
}

{
  echo "# UFME Self-Improvement Report"
  echo "Generated: $(date -Iseconds)"
  echo ""
  echo "## Skill file audit"
  check_file "$SOURCE_DIR/core/MASTER_SKILL.md" "MASTER_SKILL.md"
  check_file "$SOURCE_DIR/core/MULTI_AGENT_ORCHESTRATION.md" "MULTI_AGENT_ORCHESTRATION.md"
  check_file "$SOURCE_DIR/core/AGENT_RULES.md" "AGENT_RULES.md"
  check_file "$SOURCE_DIR/core/PROJECT_MEMORY.md" "PROJECT_MEMORY.md"
  check_file "$SOURCE_DIR/core/QUALITY_STANDARDS.md" "QUALITY_STANDARDS.md"
  check_file "$SOURCE_DIR/core/SAFETY.md" "SAFETY.md"
  check_file "$SOURCE_DIR/core/ARCH_LINUX.md" "ARCH_LINUX.md"
  check_file "$SOURCE_DIR/core/SYSTEM_ARCHITECTURE.md" "SYSTEM_ARCHITECTURE.md"
  echo ""
  echo "## Agent audit (12 expected)"
  for a in orchestrator researcher backend-analyst product-analyst designer frontend-architect implementer integrator visual-auditor accessibility-auditor performance-auditor security-auditor; do
    check_file "$SOURCE_DIR/agents/$a.md" "ufme-$a"
  done
  echo ""
  echo "## Workflow audit (14 expected)"
  for i in 01 02 03 04 05 06 07 08 09 10 11 12 13 14; do
    match=$(ls "$SOURCE_DIR/workflows/${i}-"*.md 2>/dev/null | head -1)
    if [ -n "$match" ]; then
      echo "OK: workflow $i ($match)"
    else
      echo "MISSING: workflow $i (${i}-*.md)"
    fi
  done
  echo ""
  echo "## Script audit (all executable + syntax-valid)"
  for s in detect-stack backend-discovery check-native-browser browser-test screenshot quality-check self-improve; do
    f="$SOURCE_DIR/scripts/$s.sh"
    if [ -f "$f" ] && [ -x "$f" ] && bash -n "$f" 2>/dev/null; then
      echo "OK: $s.sh (executable, syntax valid)"
    else
      echo "ISSUE: $s.sh"
    fi
  done
  echo ""
  echo "## OpenCode install audit"
  check_file "$ROOT_DIR/.opencode/skills/universal-frontend-master/SKILL.md" "SKILL.md"
  check_file "$ROOT_DIR/opencode.json" "opencode.json"
  for a in ufme-orchestrator ufme-researcher ufme-backend-analyst ufme-product-analyst ufme-designer ufme-frontend-architect ufme-implementer ufme-integrator ufme-visual-auditor ufme-accessibility-auditor ufme-performance-auditor ufme-security-auditor; do
    check_file "$ROOT_DIR/.opencode/agents/$a.md" "$a"
  done
  echo ""
  echo "## Runtime memory audit"
  check_file "$UFME_DIR/TASKS.md" "TASKS.md"
  check_file "$UFME_DIR/ENVIRONMENT.md" "ENVIRONMENT.md"
  check_file "$UFME_DIR/SKILL_VALIDATION.md" "SKILL_VALIDATION.md"
  echo ""
  echo "## Improvement recommendations"
  echo "- Review any MISSING/ISSUE items above and restore them."
  echo "- After each delivery, append lessons learned to this report and update the affected"
  echo "  source files under universal-frontend-master-source/."
  echo "- Re-run this script to confirm regressions are fixed."
} > "$REPORT"

log "Self-improvement report written to $REPORT"
cat "$REPORT"
