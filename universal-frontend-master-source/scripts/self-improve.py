#!/usr/bin/env python3
"""
self-improve.py — audit the UFME skill itself.

Checks core docs, agent frontmatter, workflows, every script (exists,
executable, syntax-valid), the browser abstraction, the OpenCode install, and
runtime memory. Writes .ufme/SELF_IMPROVEMENT.md and exits non-zero on FAIL.

Safety: read-only analysis; never sudo/pacman/systemctl.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "universal-frontend-master-source"
UFME = ROOT / ".ufme"
REPORT = UFME / "SELF_IMPROVEMENT.md"

PASSES = FAILS = SKIPPED = 0
LINES = []

CORE_DOCS = [
    "MASTER_SKILL.md", "MULTI_AGENT_ORCHESTRATION.md", "AGENT_RULES.md",
    "PROJECT_MEMORY.md", "QUALITY_STANDARDS.md", "SAFETY.md",
    "ARCH_LINUX.md", "SYSTEM_ARCHITECTURE.md",
]
AGENTS = [
    "orchestrator", "researcher", "backend-analyst", "product-analyst", "designer",
    "frontend-architect", "implementer", "integrator", "visual-auditor",
    "accessibility-auditor", "performance-auditor", "security-auditor",
]
RUNTIME_MEMORY = ["TASKS.md", "ENVIRONMENT.md", "SKILL_VALIDATION.md"]


def log(kind, label, detail=""):
    suffix = f": {detail}" if detail else ""
    print(f"{kind}: {label}{suffix}", flush=True)
    LINES.append(f"- {kind}: {label}{suffix}")


def heading(text):
    print(f"## {text}", flush=True)
    LINES.extend(["", f"## {text}"])


def note(kind, label, detail=""):
    global PASSES, FAILS, SKIPPED
    if kind == "PASS":
        PASSES += 1
    elif kind == "FAIL":
        FAILS += 1
    else:
        SKIPPED += 1
    log(kind, label, detail)


def frontmatter(path):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {}
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    fields = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields


def check_file(path, label, kind="exists"):
    if not path.is_file():
        note("FAIL", label, "missing")
        return False
    if path.stat().st_size == 0:
        note("FAIL", label, "empty")
        return False
    if kind == "exists":
        note("PASS", label)
    elif kind == "exec":
        if os.access(path, os.X_OK):
            note("PASS", label, "executable")
        else:
            note("FAIL", label, "not executable")
    elif kind == "syntax":
        suffix = path.suffix.lower()
        if suffix == ".py":
            ok = subprocess.run(
                [sys.executable, "-m", "py_compile", str(path)],
                capture_output=True,
            ).returncode == 0
        elif suffix == ".js":
            ok = subprocess.run(
                ["node", "--check", str(path)], capture_output=True
            ).returncode == 0
        else:
            ok = subprocess.run(
                ["bash", "-n", str(path)], capture_output=True
            ).returncode == 0
        note("PASS" if ok else "FAIL", label, "syntax valid" if ok else "syntax invalid")
    return True


def main():
    UFME.mkdir(parents=True, exist_ok=True)

    heading("Skill file audit (content validation)")
    for name in CORE_DOCS:
        check_file(SOURCE / "core" / name, name)

    heading("Agent audit (frontmatter + mode)")
    for name in AGENTS:
        path = SOURCE / "agents" / f"{name}.md"
        if not check_file(path, f"ufme-{name}"):
            continue
        fields = frontmatter(path)
        if not fields:
            note("FAIL", f"ufme-{name}", "no frontmatter")
        elif not fields.get("mode"):
            note("FAIL", f"ufme-{name}", "no mode field")
        else:
            note("PASS", f"ufme-{name}", f"mode={fields['mode']}")

    heading("Workflow audit (14 expected)")
    for i in range(1, 15):
        matches = sorted((SOURCE / "workflows").glob(f"{i:02d}-*.md"))
        match = matches[0] if matches else None
        if match and match.stat().st_size > 0:
            note("PASS", f"workflow {i:02d}", match.name)
        else:
            note("FAIL", f"workflow {i:02d}", "missing or empty")

    heading("Script audit (exists + executable + syntax)")
    for path in sorted((SOURCE / "scripts").glob("*")):
        if path.suffix not in {".sh", ".py", ".js"} or not path.is_file():
            continue
        check_file(path, path.name, "exec")
        check_file(path, path.name, "syntax")

    heading("Browser abstraction audit")
    for rel in [
        "tests/browser/browser.js", "tests/browser/viewport.js",
        "tests/browser/screenshot.js", "tests/browser/run.js",
        "tests/browser/engines/chromium.js", "tests/browser/engines/firefox.js",
        "tests/browser/engines/schema.js", "tests/browser/validate.js",
        "tests/browser/security.js", "tests/regression/run.js",
    ]:
        check_file(ROOT / rel, rel, "syntax")

    heading("OpenCode install audit")
    skill = ROOT / ".opencode/skills/universal-frontend-master/SKILL.md"
    fields = frontmatter(skill)
    if not skill.exists():
        note("FAIL", "SKILL.md", "missing")
    elif not fields:
        note("FAIL", "SKILL.md", "no frontmatter")
    elif not fields.get("name") or not fields.get("description"):
        note("FAIL", "SKILL.md", "missing name/description")
    else:
        note("PASS", "SKILL.md", f"name={fields['name']}")

    opencode = ROOT / "opencode.json"
    if opencode.exists():
        try:
            json.loads(opencode.read_text(encoding="utf-8"))
            note("PASS", "opencode.json", "valid JSON")
        except (OSError, ValueError):
            note("FAIL", "opencode.json", "invalid JSON")
    else:
        note("FAIL", "opencode.json", "missing")

    for name in AGENTS:
        path = ROOT / ".opencode/agents" / f"ufme-{name}.md"
        if not path.exists():
            note("FAIL", f"ufme-{name}", "missing")
        elif not frontmatter(path):
            note("FAIL", f"ufme-{name}", "no frontmatter")
        else:
            note("PASS", f"ufme-{name}", "frontmatter present")

    heading("Runtime memory audit")
    for name in RUNTIME_MEMORY:
        path = UFME / name
        if path.is_file() and path.stat().st_size > 0:
            note("PASS", name)
        else:
            note("FAIL", name, "missing or empty")

    overall = "FAILED" if FAILS else "PASSED"
    body = [
        "# UFME Self-Improvement Report",
        f"Generated: {__import__('datetime').datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        *LINES,
        "",
        "## Summary",
        f"PASS: {PASSES}",
        f"FAIL: {FAILS}",
        f"SKIPPED: {SKIPPED}",
        f"Result: {overall}",
    ]
    fd, tmp = tempfile.mkstemp(dir=str(UFME), prefix=".self-improvement.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(body) + "\n")
        os.replace(tmp, REPORT)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

    print("\n".join(body))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
