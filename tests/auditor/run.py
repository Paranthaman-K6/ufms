#!/usr/bin/env python3
"""tests/auditor/run.py — auditor agent contract tests.

The auditor is evidence-first and read-only. These tests enforce that contract
without invoking a model:
  * mode is subagent with read/bash allow and edit/task deny
  * source and installed copies match
  * every script path referenced in the agent exists
  * every evidence JSON it reads is produced by the quality gate
  * the report table contract, severity vocabulary and status vocabulary are present
  * prohibited behaviour (invented numbers, storing secrets) is documented

Usage: python3 tests/auditor/run.py
Exit: 0 all pass, 1 failure.
"""

import json
import re
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "agents/ufme-auditor.md"
INSTALLED = ROOT / ".opencode/agents/ufme-auditor.md"
SCRIPTS = ROOT / "skills/universal-frontend-master/scripts"
EVIDENCE = ROOT / ".ufme" / "evidence"

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


def frontmatter(text):
    assert text.startswith("---"), "missing frontmatter"
    block = text.split("---", 2)[1]
    fields, current = {}, None
    for line in block.splitlines():
        if not line.strip():
            continue
        if line.startswith(" ") and current:
            key, value = line.strip().split(":", 1)
            fields[current][key.strip()] = value.strip()
        elif ":" in line:
            key, value = line.split(":", 1)
            current = key.strip()
            fields[current] = value.strip() if value.strip() else {}
    return fields


def text():
    return SOURCE.read_text(encoding="utf-8")


@test("auditor exists in source and installed copies")
def _():
    assert SOURCE.is_file(), "source auditor missing"
    assert INSTALLED.is_file(), "installed auditor missing"
    assert SOURCE.read_text(encoding="utf-8") == INSTALLED.read_text(encoding="utf-8"), "drift"


@test("auditor is a read-only subagent")
def _():
    fields = frontmatter(text())
    assert fields["name"] == "ufme-auditor"
    assert fields["mode"] == "subagent"
    assert fields["permission"]["read"] == "allow"
    assert fields["permission"]["bash"] == "allow"
    assert fields["permission"]["edit"] == "deny"
    assert fields["permission"]["task"] == "deny"


@test("every referenced script exists")
def _():
    body = text()
    refs = set(re.findall(r"skills/universal-frontend-master/scripts/([\w.-]+)", body))
    assert refs, "no script references found"
    missing = sorted(ref for ref in refs if not (SCRIPTS / ref).is_file())
    assert not missing, f"missing scripts: {missing}"


@test("every referenced evidence file is produced or documented")
def _():
    refs = set(re.findall(r"\.ufme/evidence/([\w.-]+\.json)", text()))
    assert refs, "no evidence references found"
    expected = {
        "a11y-results.json", "perf-results.json", "browser-results.json",
        "visual-diff.json", "slop-results.json", "quality-report.json",
    }
    assert expected <= refs, f"missing evidence references: {sorted(expected - refs)}"


@test("report table contract is documented")
def _():
    body = text()
    assert "Source | Severity | Location | Finding | Recommendation | Retest evidence" in body
    for source in ("visual", "a11y", "perf", "security", "slop"):
        assert source in body, f"missing source '{source}'"
    for severity in ("critical", "major", "minor"):
        assert severity in body, f"missing severity '{severity}'"
    for status in ("PASS", "FAIL", "SKIPPED", "BLOCKED"):
        assert status in body, f"missing status '{status}'"


@test("evidence-first rule and orchestrator write ownership are explicit")
def _():
    body = text()
    assert "Evidence first" in body
    assert "the orchestrator owns writes" in body
    assert "edit` permission is `deny" in body or "edit: deny" in body


@test("auditor warns against invented numbers and secret storage")
def _():
    body = text()
    assert "Never report unmeasured numbers" in body
    assert "Never store or log secrets" in body
    assert "client-side checks as authorization" in body


@test("quality gate writes the auditor's evidence files")
def _():
    gate = (SCRIPTS / "quality-check.py").read_text(encoding="utf-8")
    for name in ("a11y-results.json", "perf-results.json", "browser-results.json",
                 "visual-diff.json", "slop-results.json", "quality-report.json"):
        assert name in gate, f"quality-check.py does not reference {name}"


@test("ctx-pack maps every auditor evidence artifact")
def _():
    pack = (SCRIPTS / "ctx-pack.py").read_text(encoding="utf-8")
    for artifact in ("QUALITY_REPORT", "A11Y_RESULTS", "PERF_RESULTS",
                     "BROWSER_RESULTS", "VISUAL_DIFF", "SLOP_RESULTS", "AUDIT_REPORT"):
        assert f'"{artifact}"' in pack, f"ctx-pack.py missing {artifact}"


def main():
    failures = [r for r in results if r["status"] == "FAIL"]
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "auditor-test.json").write_text(
        json.dumps(
            {"checks": len(results), "pass": len(results) - len(failures),
             "failed": len(failures), "results": results},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\n{len(results) - len(failures)} passed, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
