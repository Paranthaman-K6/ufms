#!/usr/bin/env bash
# task-checkpoint.sh
# Priority 4 — Multi-Agent Orchestration: task checkpoints.
# Reads/writes .ufme/TASKS.md task statuses with dependency-aware status
# transitions. A task can only be marked COMPLETE if its dependencies are
# COMPLETE AND the state change is verified after modification.
#
# Safety: read/write .ufme/TASKS.md only.
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TASKS="$ROOT_DIR/.ufme/TASKS.md"

log() { echo "[task-checkpoint] $*"; }

usage() {
  echo "Usage: $0 list | status <id> | complete <id> [dep1 dep2 ...]"
  echo "       $0 blocked <id> <reason>"
  echo "       $0 add <id> <description>"
  exit 1
}

# Validate task identifier: alphanumeric, hyphens, underscores only.
validate_task_id() {
  local id="$1"
  if [ -z "$id" ]; then
    return 1
  fi
  if ! echo "$id" | grep -qE '^[A-Za-z0-9][A-Za-z0-9_-]*$'; then
    return 1
  fi
  return 0
}

# Check if a task ID already exists in TASKS.md.
task_exists() {
  local id="$1"
  grep -qE "^- \[[ x]\] $id " "$TASKS" 2>/dev/null
}

# Get the current status of a task: [ ] or [x].
get_task_status() {
  local id="$1"
  local line
  line=$(grep -E "^- \[[ x]\] $id " "$TASKS" 2>/dev/null | head -1)
  if echo "$line" | grep -q '\[x\]'; then
    echo "complete"
  elif echo "$line" | grep -q '\[ \]'; then
    echo "pending"
  else
    echo "not_found"
  fi
}

# Check if all dependency task IDs are complete.
check_dependencies() {
  local deps="$*"
  for dep in $deps; do
    if ! validate_task_id "$dep"; then
      log "ERROR: Invalid dependency task ID: $dep"
      return 1
    fi
    local status
    status=$(get_task_status "$dep")
    if [ "$status" != "complete" ]; then
      log "BLOCKED: dependency $dep is not complete (status: $status)"
      return 1
    fi
  done
  return 0
}

# Verify that a modification to TASKS.md succeeded by re-reading the file.
verify_modification() {
  local id="$1" expected_status="$2"
  local actual
  actual=$(get_task_status "$id")
  if [ "$actual" != "$expected_status" ]; then
    log "ERROR: Modification verification failed for $id: expected $expected_status, got $actual"
    return 1
  fi
  return 0
}

cmd="${1:-}"
shift || true

case "$cmd" in
  list)
    if [ ! -f "$TASKS" ]; then
      echo "(no TASKS.md found)"
      exit 0
    fi
    grep -E '^- \[[ x]\]' "$TASKS" || echo "(no tasks found)"
    ;;
  status)
    id="${1:-}"
    [ -z "$id" ] && usage
    if ! validate_task_id "$id"; then
      log "ERROR: Invalid task ID: $id"
      exit 1
    fi
    if [ ! -f "$TASKS" ]; then
      echo "task $id not found (no TASKS.md)"
      exit 1
    fi
    status=$(get_task_status "$id")
    if [ "$status" = "not_found" ]; then
      echo "task $id not found"
      exit 1
    fi
    echo "task $id: $status"
    ;;
  add)
    id="${1:-}"
    shift || true
    desc="$*"
    [ -z "$id" ] && usage
    if ! validate_task_id "$id"; then
      log "ERROR: Invalid task ID: $id"
      exit 1
    fi
    if [ ! -f "$TASKS" ]; then
      log "ERROR: .ufme/TASKS.md not found"
      exit 1
    fi
    if task_exists "$id"; then
      log "ERROR: Task $id already exists"
      exit 1
    fi
    if [ -z "$desc" ]; then
      log "ERROR: Task description required"
      exit 1
    fi
    echo "- [ ] $id $desc" >> "$TASKS"
    # Verify the addition succeeded.
    if ! task_exists "$id"; then
      log "ERROR: Failed to add task $id to TASKS.md"
      exit 1
    fi
    log "added task $id: $desc"
    ;;
  complete)
    id="${1:-}"
    shift || true
    [ -z "$id" ] && usage
    if ! validate_task_id "$id"; then
      log "ERROR: Invalid task ID: $id"
      exit 1
    fi
    if [ ! -f "$TASKS" ]; then
      log "ERROR: .ufme/TASKS.md not found"
      exit 1
    fi
    if ! task_exists "$id"; then
      log "ERROR: Task $id not found"
      exit 1
    fi
    current=$(get_task_status "$id")
    if [ "$current" = "complete" ]; then
      log "Task $id already complete"
      exit 0
    fi
    # Check dependencies first (remaining args after task ID).
    deps="$*"
    if [ -n "$deps" ]; then
      if ! check_dependencies $deps; then
        exit 1
      fi
    fi
    # Mark task complete (toggle first matching [ ] to [x]).
    if sed -i "0,/^- \[ \] $id /s//- [x] $id /" "$TASKS" 2>/dev/null; then
      :
    elif sed -i "0,/^- \[ \]   $id /s//- [x]   $id /" "$TASKS" 2>/dev/null; then
      :
    else
      log "ERROR: Failed to modify TASKS.md for task $id"
      exit 1
    fi
    # Verify the modification succeeded.
    if ! verify_modification "$id" "complete"; then
      exit 1
    fi
    log "marked $id COMPLETE"
    ;;
  blocked)
    id="${1:-}"
    shift || true
    reason="$*"
    [ -z "$id" ] && usage
    if ! validate_task_id "$id"; then
      log "ERROR: Invalid task ID: $id"
      exit 1
    fi
    if [ ! -f "$TASKS" ]; then
      log "ERROR: .ufme/TASKS.md not found"
      exit 1
    fi
    if task_exists "$id"; then
      log "ERROR: Task $id already exists"
      exit 1
    fi
    if [ -z "$reason" ]; then
      log "ERROR: Block reason required"
      exit 1
    fi
    echo "- [ ] $id (BLOCKED: $reason)" >> "$TASKS"
    # Verify the addition succeeded.
    if ! task_exists "$id"; then
      log "ERROR: Failed to add blocked task $id to TASKS.md"
      exit 1
    fi
    log "marked $id BLOCKED: $reason"
    ;;
  *)
    usage
    ;;
esac
