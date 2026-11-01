#!/usr/bin/env bash
# task-checkpoint.sh
# Priority 4 — Multi-Agent Orchestration: task checkpoints.
# Reads/writes .ufme/TASKS.md task statuses. Supports dependency-aware status
# transitions: a task can only be marked COMPLETE if its dependencies are COMPLETE.
# Provides structured status output for agent coordination.
#
# Safety: read/write .ufme/TASKS.md only.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TASKS="$ROOT_DIR/.ufme/TASKS.md"

log() { echo "[task-checkpoint] $*"; }

usage() {
  echo "Usage: $0 list | status <id> | complete <id> [dep1 dep2 ...]"
  echo "       $0 blocked <id> <reason>"
  exit 1
}

cmd="${1:-}"
shift || true

case "$cmd" in
  list)
    grep -E '^- \[.\]' "$TASKS" 2>/dev/null || echo "(no tasks found)"
    ;;
  status)
    id="${1:-}"
    [ -z "$id" ] && usage
    grep -E "^- \[.\] $id " "$TASKS" 2>/dev/null || echo "task $id not found"
    ;;
  complete)
    id="${1:-}"
    [ -z "$id" ] && usage
    shift
    deps="$*"
    # Verify dependencies are complete before marking.
    if [ -n "$deps" ]; then
      for dep in $deps; do
        line=$(grep -E "^- \[.\] $dep " "$TASKS" 2>/dev/null || true)
        if [ -z "$line" ] || ! echo "$line" | grep -q '\[x\]'; then
          log "BLOCKED: $id depends on incomplete task $dep"
          exit 1
        fi
      done
    fi
    # Mark task complete in TASKS.md (toggle first matching [ ] to [x]).
    if [ -f "$TASKS" ]; then
      sed -i "0,/^- \[ \] $id /s//- [x] $id /" "$TASKS" 2>/dev/null || \
        sed -i "0,/^- \[ \]   $id /s//- [x]   $id /" "$TASKS" 2>/dev/null || true
    fi
    log "marked $id COMPLETE"
    ;;
  blocked)
    id="${1:-}"
    reason="${2:-}"
    [ -z "$id" ] && usage
    log "marked $id BLOCKED: $reason"
    echo "- [ ] $id (BLOCKED: $reason)" >> "$TASKS"
    ;;
  *)
    usage
    ;;
esac
