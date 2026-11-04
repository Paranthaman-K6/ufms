#!/usr/bin/env python3
"""tests/profiles/run.py — execution profile enforcement tests.

Verifies that every profile is valid and that --enforce really rejects
over-limit, unauthorized, duplicate, parallel and over-depth delegations.
Evidence writes are redirected with UFME_EVIDENCE_DIR so tests stay hermetic.

Usage: python3 tests/profiles/run.py
Exit: 0 all pass, 1 failure.
"""

import json
import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "universal-frontend-master-source/scripts/execution-profiles.sh"
PROFILES = ROOT / "universal-frontend-master-source/profiles"
ALL_SIX = (
    "universal-frontend-master,ufme-orchestrator,ufme-designer,"
    "ufme-builder,ufme-backend-analyst,ufme-auditor"
)

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


def enforce(tmp, *args):
    env = os.environ.copy()
    evidence = tmp / "evidence"
    env["UFME_EVIDENCE_DIR"] = str(evidence)
    p = subprocess.run(
        ["bash", str(SCRIPT), "--enforce", *args, "--json"],
        cwd=ROOT, capture_output=True, text=True, timeout=60, env=env,
    )
    data = None
    report = evidence / "profile-enforcement.json"
    if report.exists():
        data = json.loads(report.read_text(encoding="utf-8"))
    return p, data


def assert_ok(p, data):
    assert p.returncode == 0, p.stderr
    assert data is not None, "evidence not written"
    assert data["status"] == "PASS", data["violations"]
    assert data["violations"] == [], data["violations"]
    assert data["mandatoryAcceptanceCriteria"] is True
    assert data["securityConstraints"].get("noSudo") is True


def assert_violation(p, data, fragment):
    assert p.returncode == 1, p.stderr
    assert data is not None, "evidence not written"
    assert data["status"] == "FAIL", data
    joined = " ".join(data["violations"])
    assert fragment in joined, joined


@test("every profile is valid JSON with the required fields")
def _():
    for name in ("lite", "standard", "advanced", "autonomous"):
        path = PROFILES / f"{name}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["name"] == name
        for key in (
            "maxAgents", "researchDepth", "allowedParallelism",
            "verificationDepth", "browserTestingLevel", "securityConstraints",
        ):
            assert key in data, f"{name}: missing {key}"
        assert data["securityConstraints"]["noSudo"] is True
        assert data["mandatoryAcceptanceCriteria"] is True


@test("show profile renders JSON")
def _():
    p = subprocess.run(
        ["bash", str(SCRIPT), "lite", "--json"],
        capture_output=True, text=True, timeout=30,
    )
    assert p.returncode == 0, p.stderr
    data = json.loads(p.stdout)
    assert data["name"] == "lite" and data["maxAgents"] == 2
    assert data["allowedParallelism"] is False


@test("lite accepts its two allowed agents")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(Path(raw), "lite", "--agents", "universal-frontend-master,ufme-orchestrator")
        assert_ok(p, data)
        assert data["activeAgents"] == ["universal-frontend-master", "ufme-orchestrator"]
        assert data["maxAgents"] == 2
        assert data["allowedParallelism"] is False


@test("lite rejects three active agents")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "lite",
            "--agents", "universal-frontend-master,ufme-orchestrator,ufme-designer",
        )
        assert_violation(p, data, "exceeds maxAgents 2")


@test("lite rejects an agent outside its allowed set")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "lite", "--agents", "universal-frontend-master,ufme-auditor",
        )
        assert_violation(p, data, "not allowed in profile 'lite'")


@test("lite rejects parallel execution")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "lite",
            "--agents", "universal-frontend-master,ufme-orchestrator", "--parallel",
        )
        assert_violation(p, data, "parallel execution is disabled")


@test("lite rejects deeper research than allowed")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "lite",
            "--agents", "universal-frontend-master,ufme-orchestrator",
            "--research", "deep",
        )
        assert_violation(p, data, "requested research 'deep' exceeds")


@test("duplicate agent names are rejected")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "standard",
            "--agents", "ufme-designer,ufme-designer",
        )
        assert_violation(p, data, "duplicate agent names")


@test("standard accepts designer and builder")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "standard",
            "--agents", "universal-frontend-master,ufme-orchestrator,ufme-designer,ufme-builder",
        )
        assert_ok(p, data)
        assert data["maxAgents"] == 4


@test("standard rejects backend-analyst and auditor")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(Path(raw), "standard", "--agents", ALL_SIX)
        joined = " ".join(data["violations"]) if data else ""
        assert p.returncode == 1, p.stderr
        assert "exceeds maxAgents 4" in joined, joined
        assert "not allowed in profile 'standard'" in joined, joined


@test("advanced accepts all six agents at its declared depth")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "advanced", "--agents", ALL_SIX,
            "--research", "deep", "--verify", "thorough",
            "--browser", "comprehensive", "--parallel",
        )
        assert_ok(p, data)
        assert len(data["activeAgents"]) == 6
        assert data["parallelRequested"] is True


@test("autonomous accepts exhaustive verification")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "autonomous", "--agents", ALL_SIX,
            "--research", "deep", "--verify", "exhaustive",
            "--browser", "comprehensive", "--parallel",
        )
        assert_ok(p, data)
        assert data["verificationDepth"] == "exhaustive"
        assert data["maxAgents"] == 12


@test("autonomous rejects invalid depth values")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "autonomous", "--agents", ALL_SIX,
            "--verify", "impossible",
        )
        assert_violation(p, data, "invalid verify level 'impossible'")


@test("unknown profile exits 2")
def _():
    p = subprocess.run(
        ["bash", str(SCRIPT), "turbo"], capture_output=True, text=True, timeout=30,
    )
    assert p.returncode == 2, p.stdout + p.stderr


@test("--enforce without agents exits 2")
def _():
    p = subprocess.run(
        ["bash", str(SCRIPT), "--enforce", "lite"], capture_output=True, text=True, timeout=30,
    )
    assert p.returncode == 2, p.stdout + p.stderr


def main():
    failures = [r for r in results if r["status"] == "FAIL"]
    evidence = ROOT / ".ufme" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "profiles-test.json").write_text(
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
