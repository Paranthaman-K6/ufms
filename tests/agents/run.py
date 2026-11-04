#!/usr/bin/env python3
"""tests/agents/run.py — agent structure, sync and discovery tests.

Verifies the six-agent contract without invoking a model:
  * exactly one primary agent (universal-frontend-master)
  * ufme-orchestrator is a subagent
  * source agents validate and match installed copies
  * every agent reference resolves to a real agent
  * OpenCode discovers all six agents (skipped when opencode is absent)
  * docs no longer describe two primary agents or "11 specialists"

Usage: python3 tests/agents/run.py
Exit: 0 all pass (skips allowed), 1 failure.
"""

import json
import re
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "universal-frontend-master-source" / "agents"
INSTALLED = ROOT / ".opencode" / "agents"
EVIDENCE = ROOT / ".ufme" / "evidence"

EXPECTED_MODES = {
    "universal-frontend-master": "primary",
    "ufme-orchestrator": "subagent",
    "ufme-designer": "subagent",
    "ufme-builder": "subagent",
    "ufme-backend-analyst": "subagent",
    "ufme-auditor": "subagent",
}
SOURCE_TO_INSTALLED = {
    "universal-frontend-master": "universal-frontend-master",
    "orchestrator": "ufme-orchestrator",
    "designer": "ufme-designer",
    "builder": "ufme-builder",
    "backend-analyst": "ufme-backend-analyst",
    "auditor": "ufme-auditor",
}

results = []


def test(name):
    def wrapper(fn):
        try:
            fn()
            results.append({"name": name, "status": "PASS"})
            print(f"PASS: {name}")
        except Exception as exc:  # noqa: BLE001 - test harness
            results.append({"name": name, "status": "FAIL", "error": str(exc)})
            print(f"FAIL: {name}: {exc}")
            traceback.print_exc()
        return fn

    return wrapper


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise AssertionError(f"{path.name}: missing frontmatter")
    block = text.split("---", 2)[1]
    fields, current = {}, None
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith(" ") and current:
            key, value = line.strip().split(":", 1)
            fields[current][key.strip()] = value.strip()
        elif ":" in line:
            key, value = line.split(":", 1)
            current = key.strip()
            value = value.strip()
            fields[current] = value if value else {}
    return fields, text.split("---", 2)[2]


@test("source agents exist")
def _():
    missing = [n for n in SOURCE_TO_INSTALLED if not (SOURCE / f"{n}.md").is_file()]
    assert not missing, f"missing source agents: {missing}"


@test("exactly one primary agent")
def _():
    primaries = []
    for source_name in SOURCE_TO_INSTALLED:
        fields, _ = parse_frontmatter(SOURCE / f"{source_name}.md")
        if fields.get("mode") == "primary":
            primaries.append(fields.get("name"))
    assert primaries == ["universal-frontend-master"], primaries


@test("orchestrator is a subagent")
def _():
    fields, _ = parse_frontmatter(SOURCE / "orchestrator.md")
    assert fields.get("mode") == "subagent", fields.get("mode")


@test("frontmatter valid for every agent")
def _():
    for source_name in SOURCE_TO_INSTALLED:
        fields, _ = parse_frontmatter(SOURCE / f"{source_name}.md")
        assert fields.get("name"), f"{source_name}: missing name"
        assert fields.get("description"), f"{source_name}: missing description"
        assert fields.get("mode") in {"primary", "subagent"}, fields.get("mode")
        perms = fields.get("permission")
        assert isinstance(perms, dict), f"{source_name}: missing permission block"
        for key, value in perms.items():
            assert key in {"read", "edit", "bash", "task"}, f"{source_name}: bad permission {key}"
            assert value in {"allow", "deny", "ask"}, f"{source_name}: bad value {value}"


@test("source and installed agents are in sync")
def _():
    for source_name, installed_name in SOURCE_TO_INSTALLED.items():
        source_file = SOURCE / f"{source_name}.md"
        installed_file = INSTALLED / f"{installed_name}.md"
        assert installed_file.is_file(), f"missing installed agent {installed_file}"
        assert source_file.read_text(encoding="utf-8") == installed_file.read_text(
            encoding="utf-8"
        ), f"{installed_name} drifted from source"


@test("build-agents.py --check passes")
def _():
    p = subprocess.run(
        [sys.executable, str(ROOT / "universal-frontend-master-source/scripts/build-agents.py"), "--check"],
        capture_output=True, text=True, timeout=120,
    )
    assert p.returncode == 0, (p.stdout + p.stderr).strip()


@test("agent references resolve")
def _():
    known = set(EXPECTED_MODES) | set(SOURCE_TO_INSTALLED)
    pattern = re.compile(r"@?(ufme-[a-z][a-z0-9-]*|universal-frontend-master)\b")
    for source_name in SOURCE_TO_INSTALLED:
        _, body = parse_frontmatter(SOURCE / f"{source_name}.md")
        for ref in sorted(set(pattern.findall(body))):
            assert ref in known, f"{source_name}: unknown agent reference {ref}"


@test("docs describe one primary and five subagents")
def _():
    docs = [
        ROOT / "README.md",
        ROOT / "universal-frontend-master-source/core/SYSTEM_ARCHITECTURE.md",
    ]
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        assert "11 specialist agents" not in text, f"{doc.name}: stale agent count"
        assert "ufme-orchestrator (primary" not in text, f"{doc.name}: stale orchestrator role"


@test("OpenCode discovers all six agents")
def _():
    if shutil.which("opencode") is None:
        raise AssertionError("SKIP: opencode not installed")
    p = subprocess.run(
        ["opencode", "debug", "agents"], capture_output=True, text=True, timeout=90
    )
    if p.returncode != 0:
        raise AssertionError(f"opencode debug agents failed: {(p.stderr or p.stdout)[:200]}")
    start = p.stdout.find("[")
    data = json.loads(p.stdout[start:]) if start >= 0 else []
    ids = {agent.get("id") for agent in data}
    missing = set(EXPECTED_MODES) - ids
    assert not missing, f"not discovered: {sorted(missing)}"


def main():
    failures = [r for r in results if r["status"] == "FAIL"]
    skips = [r for r in results if "SKIP" in r.get("error", "")]
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "agents-test.json").write_text(
        json.dumps(
            {
                "checks": len(results),
                "pass": len(results) - len(failures),
                "skipped": len(skips),
                "failed": len(failures),
                "results": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\n{len(results) - len(failures)} passed, {len(skips)} skipped, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
