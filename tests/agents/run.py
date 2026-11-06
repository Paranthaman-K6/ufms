#!/usr/bin/env python3
"""tests/agents/run.py — agent structure, sync and discovery tests.

Verifies the agent contract without invoking a model:
  * every agent in `agents/` is valid and named after its file stem
  * exactly four primaries: universal-frontend-master, ufmw-frontend-design,
    ufmw-seo-protocol, init-frontend; every other agent is a subagent
  * `.opencode/agents/` is an exact mirror of `agents/`
  * every `@agent-name` reference resolves to a real agent
  * OpenCode discovers the agents (skipped when opencode is absent)
  * docs no longer describe the old six-agent layout

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
SOURCE = ROOT / "agents"
INSTALLED = ROOT / ".opencode" / "agents"
EVIDENCE = ROOT / ".ufme" / "evidence"

EXPECTED_AGENTS = {
    "universal-frontend-master",
    "init-frontend",
    "ufme-orchestrator",
    "ufme-designer",
    "ufme-builder",
    "ufme-backend-analyst",
    "ufme-auditor",
    "ufmw-frontend-design",
    "ufmw-orchestrator",
    "ufmw-designer",
    "ufmw-builder",
    "ufmw-auditor",
    "ufmw-seo-protocol",
    "ufmw-seo-technical",
    "ufmw-seo-content",
    "ufmw-seo-analyst",
    "ufmw-seo-auditor",
}
PRIMARIES = {
    "universal-frontend-master",
    "ufmw-frontend-design",
    "ufmw-seo-protocol",
    "init-frontend",
}

results = []


def test(name):
    def wrapper(fn):
        try:
            fn()
            results.append({"name": name, "status": "PASS"})
            print(f"PASS: {name}")
        except Exception as exc:  # noqa: BLE001 - test harness
            if "SKIP" in str(exc):
                results.append({"name": name, "status": "SKIP", "error": str(exc)})
                print(f"SKIP: {name}: {exc}")
                return fn
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


def agents():
    return {path.stem: path for path in sorted(SOURCE.glob("*.md"))}


@test("the agent set matches the catalog")
def _():
    found = set(agents())
    assert found == EXPECTED_AGENTS, {
        "missing": sorted(EXPECTED_AGENTS - found),
        "unexpected": sorted(found - EXPECTED_AGENTS),
    }


@test("every agent name matches its file stem")
def _():
    for stem, path in agents().items():
        fields, _ = parse_frontmatter(path)
        assert fields.get("name") == stem, f"{path.name}: name is {fields.get('name')!r}"


@test("four primaries, every other agent a subagent")
def _():
    for stem, path in agents().items():
        fields, _ = parse_frontmatter(path)
        expected = "primary" if stem in PRIMARIES else "subagent"
        assert fields.get("mode") == expected, f"{stem}: mode is {fields.get('mode')!r}"


@test("frontmatter valid for every agent")
def _():
    for stem, path in agents().items():
        fields, _ = parse_frontmatter(path)
        assert fields.get("description"), f"{stem}: missing description"
        perms = fields.get("permission")
        assert isinstance(perms, dict), f"{stem}: missing permission block"
        for key, value in perms.items():
            assert key in {"read", "edit", "bash", "task"}, f"{stem}: bad permission {key}"
            assert value in {"allow", "deny", "ask"}, f"{stem}: bad value {value}"


@test("source and installed agents are in sync")
def _():
    for stem, source_file in agents().items():
        installed_file = INSTALLED / f"{stem}.md"
        assert installed_file.is_file(), f"missing installed agent {installed_file}"
        assert source_file.read_bytes() == installed_file.read_bytes(), f"{stem} drifted"
    installed = {p.stem for p in INSTALLED.glob("*.md")}
    assert installed == set(agents()), f"obsolete installed agents: {sorted(installed - set(agents()))}"


@test("scripts/build-agents.py --check passes")
def _():
    p = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build-agents.py"), "--check"],
        capture_output=True, text=True, timeout=120,
    )
    assert p.returncode == 0, (p.stdout + p.stderr).strip()


@test("agent references resolve")
def _():
    known = set(agents())
    pattern = re.compile(r"@([a-z][a-z0-9-]*)\b")
    for stem, path in agents().items():
        _, body = parse_frontmatter(path)
        for ref in sorted(set(pattern.findall(body))):
            assert ref in known, f"{stem}: unknown agent reference @{ref}"


@test("docs no longer describe the six-agent layout")
def _():
    docs = [
        ROOT / "README.md",
        ROOT / "skills/universal-frontend-master/core/SYSTEM_ARCHITECTURE.md",
    ]
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        assert "6-agent" not in text, f"{doc.name}: stale six-agent count"
        assert "six agents" not in text.lower(), f"{doc.name}: stale six-agent count"
        assert "11 specialist agents" not in text, f"{doc.name}: stale agent count"
        assert "ufme-orchestrator (primary" not in text, f"{doc.name}: stale orchestrator role"


@test("OpenCode discovers the agents")
def _():
    if shutil.which("opencode") is None:
        raise AssertionError("SKIP: opencode not installed")
    # --standalone runs a private server: the shared background service can be
    # busy or reloading config, and then returns a truncated JSON body.
    p = subprocess.run(
        ["opencode", "debug", "agents", "--standalone"],
        capture_output=True, text=True, timeout=120,
    )
    output = p.stderr + p.stdout
    if p.returncode != 0:
        if "ServiceUnavailable" in output or "did not finish activating" in output:
            raise AssertionError(f"SKIP: opencode agent service unavailable: {output[:160]}")
        raise AssertionError(f"opencode debug agents failed: {output[:200]}")
    start = p.stdout.find("[")
    if start < 0:
        raise AssertionError(f"opencode debug agents returned no JSON: {output[:200]}")
    try:
        data, _ = json.JSONDecoder().raw_decode(p.stdout[start:])
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"opencode debug agents returned invalid JSON: {exc}; "
            f"near {p.stdout[max(0, exc.pos - 80):exc.pos + 80]!r}"
        ) from exc
    ids = {agent.get("id") for agent in data}
    missing = EXPECTED_AGENTS - ids
    assert not missing, f"not discovered: {sorted(missing)}"


def main():
    failures = [r for r in results if r["status"] == "FAIL"]
    skips = [r for r in results if r["status"] == "SKIP"]
    passes = [r for r in results if r["status"] == "PASS"]
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "agents-test.json").write_text(
        json.dumps(
            {
                "checks": len(results),
                "pass": len(passes),
                "skipped": len(skips),
                "failed": len(failures),
                "results": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\n{len(passes)} passed, {len(skips)} skipped, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
