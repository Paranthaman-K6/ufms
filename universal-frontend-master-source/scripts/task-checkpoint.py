#!/usr/bin/env python3
"""
task-checkpoint.py — dependency-aware task state in .ufme/TASKS.md.

Usage:
  task-checkpoint.py list
  task-checkpoint.py status <id>
  task-checkpoint.py complete <id> [dep ...]
  task-checkpoint.py blocked <id> <reason>
  task-checkpoint.py add <id> <description>

Rules: a task can only be marked COMPLETE when every listed dependency is
COMPLETE, and the file change is re-read and verified before success is
reported. Writes are atomic.

Safety: reads/writes .ufme/TASKS.md only.
"""

import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / ".ufme" / "TASKS.md"

TASK_RE = re.compile(r"^- \[([ x])\] (T-?[0-9]+) (.*)$")
ID_RE = re.compile(r"^T-?[0-9]+$")


def log(msg):
    print(f"[task-checkpoint] {msg}")


def usage():
    print("Usage: task-checkpoint.py list | status <id> | complete <id> [dep ...]")
    print("       task-checkpoint.py blocked <id> <reason>")
    print("       task-checkpoint.py add <id> <description>")
    return 2


def read_lines():
    if not TASKS.exists():
        return []
    return TASKS.read_text(encoding="utf-8").splitlines()


def write_lines(lines):
    """Atomic replace so a crash never truncates TASKS.md."""
    TASKS.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(TASKS.parent), prefix=".TASKS.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + ("\n" if lines else ""))
        os.replace(tmp, TASKS)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def find(id_):
    for i, line in enumerate(read_lines()):
        m = TASK_RE.match(line)
        if m and m.group(2) == id_:
            return i, m
    return None, None


def status(id_):
    _, m = find(id_)
    if m is None:
        return "not_found"
    return "complete" if m.group(1) == "x" else "pending"


def require_id(id_):
    if not id_ or not ID_RE.match(id_):
        log(f"ERROR: Invalid task ID: {id_ or '(empty)'}")
        return False
    return True


def main(argv):
    cmd = argv[0] if argv else ""
    args = argv[1:]

    if cmd == "list":
        rows = [l for l in read_lines() if TASK_RE.match(l)]
        print("\n".join(rows) if rows else "(no tasks found)")
        return 0

    if cmd == "status":
        if not args:
            return usage()
        id_ = args[0]
        if not require_id(id_):
            return 1
        st = status(id_)
        if st == "not_found":
            print(f"task {id_} not found (no matching entry)")
            return 1
        print(f"task {id_}: {st}")
        return 0

    if cmd == "add":
        if not args:
            return usage()
        id_, desc = args[0], " ".join(args[1:]).strip()
        if not require_id(id_):
            return 1
        if not desc:
            log("ERROR: Task description required")
            return 1
        if find(id_)[1] is not None:
            log(f"ERROR: Task {id_} already exists")
            return 1
        lines = read_lines()
        lines.append(f"- [ ] {id_} {desc}")
        write_lines(lines)
        if find(id_)[1] is None:
            log(f"ERROR: Failed to add task {id_}")
            return 1
        log(f"added task {id_}: {desc}")
        return 0

    if cmd == "complete":
        if not args:
            return usage()
        id_, deps = args[0], args[1:]
        if not require_id(id_):
            return 1
        idx, m = find(id_)
        if m is None:
            log(f"ERROR: Task {id_} not found")
            return 1
        if m.group(1) == "x":
            log(f"Task {id_} already complete")
            return 0
        for dep in deps:
            if not require_id(dep):
                return 1
            dep_status = status(dep)
            if dep_status != "complete":
                log(f"BLOCKED: dependency {dep} is not complete (status: {dep_status})")
                return 1
        lines = read_lines()
        lines[idx] = f"- [x] {id_} {m.group(3)}"
        write_lines(lines)
        if status(id_) != "complete":
            log(f"ERROR: Modification verification failed for {id_}")
            return 1
        log(f"marked {id_} COMPLETE")
        return 0

    if cmd == "blocked":
        if not args:
            return usage()
        id_, reason = args[0], " ".join(args[1:]).strip()
        if not require_id(id_):
            return 1
        if not reason:
            log("ERROR: Block reason required")
            return 1
        if find(id_)[1] is not None:
            log(f"ERROR: Task {id_} already exists")
            return 1
        lines = read_lines()
        lines.append(f"- [ ] {id_} (BLOCKED: {reason})")
        write_lines(lines)
        if find(id_)[1] is None:
            log(f"ERROR: Failed to add blocked task {id_}")
            return 1
        log(f"marked {id_} BLOCKED: {reason}")
        return 0

    return usage()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
