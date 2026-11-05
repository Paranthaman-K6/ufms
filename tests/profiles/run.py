#!/usr/bin/env python3
"""tests/profiles/run.py — execution profile enforcement tests.

Covers the schema (primaryAgent / allowedAgents / maxConcurrentDelegates),
the distinction between available roles and concurrently active delegates,
and the real delegation scenarios each profile is meant to support.

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
AGENTS_DIR = ROOT / "universal-frontend-master-source/agents"
PRIMARY = "universal-frontend-master"
SPECIALISTS = (
    "ufme-orchestrator",
    "ufme-designer",
    "ufme-builder",
    "ufme-backend-analyst",
    "ufme-auditor",
)
ALL_SIX = ",".join((PRIMARY,) + SPECIALISTS)

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


def enforce(tmp, *args, env_extra=None):
    env = os.environ.copy()
    evidence = tmp / "evidence"
    env["UFME_EVIDENCE_DIR"] = str(evidence)
    env.update(env_extra or {})
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


def load(name):
    return json.loads((PROFILES / f"{name}.json").read_text(encoding="utf-8"))


@test("every profile has the new schema and no legacy maxAgents")
def _():
    for name in ("lite", "standard", "advanced", "autonomous"):
        data = load(name)
        assert data["name"] == name
        assert data["primaryAgent"] == PRIMARY, name
        assert isinstance(data["maxConcurrentDelegates"], int), name
        assert data["maxConcurrentDelegates"] >= 1, name
        assert "maxAgents" not in data, f"{name}: legacy maxAgents still present"
        for key in (
            "allowedAgents", "researchDepth", "allowedParallelism",
            "verificationDepth", "browserTestingLevel", "securityConstraints",
        ):
            assert key in data, f"{name}: missing {key}"
        assert isinstance(data["allowedAgents"], list) and data["allowedAgents"], name
        assert PRIMARY in data["allowedAgents"], name
        assert data["securityConstraints"]["noSudo"] is True
        assert data["mandatoryAcceptanceCriteria"] is True


@test("lite exposes the builder so small tasks can be implemented")
def _():
    data = load("lite")
    assert "ufme-builder" in data["allowedAgents"], data["allowedAgents"]
    assert "ufme-orchestrator" not in data["allowedAgents"], data["allowedAgents"]
    assert data["maxConcurrentDelegates"] == 1


@test("standard exposes designer, builder, backend-analyst and auditor")
def _():
    data = load("standard")
    for role in ("ufme-designer", "ufme-builder", "ufme-backend-analyst", "ufme-auditor"):
        assert role in data["allowedAgents"], f"{role} missing from standard"
    assert "ufme-orchestrator" not in data["allowedAgents"], data["allowedAgents"]
    assert data["maxConcurrentDelegates"] == 2


@test("advanced and autonomous expose all six roles")
def _():
    for name in ("advanced", "autonomous"):
        assert set(load(name)["allowedAgents"]) == {PRIMARY, *SPECIALISTS}, name


@test("available roles exceed concurrent delegates where concurrency is capped")
def _():
    for name in ("standard", "advanced"):
        data = load(name)
        delegates = [a for a in data["allowedAgents"] if a != PRIMARY]
        assert data["maxConcurrentDelegates"] < len(delegates), (
            f"{name}: concurrency should cap a subset, not equal all roles")
    assert load("autonomous")["maxConcurrentDelegates"] == 5


@test("autonomous concurrency matches the real delegate role definitions")
def _():
    data = load("autonomous")
    defined = {p.stem for p in AGENTS_DIR.glob("*.md")}
    defined = {f"ufme-{n}" if n != "universal-frontend-master" else n for n in defined}
    real_delegates = defined - {PRIMARY}
    assert data["maxConcurrentDelegates"] == len(real_delegates), (
        f"advertised {data['maxConcurrentDelegates']} concurrent delegates but "
        f"{len(real_delegates)} delegate definitions exist: {sorted(real_delegates)}")
    assert set(data["allowedAgents"]) - {PRIMARY} == real_delegates


@test("show profile renders the new JSON schema")
def _():
    p = subprocess.run(
        ["bash", str(SCRIPT), "lite", "--json"],
        capture_output=True, text=True, timeout=30,
    )
    assert p.returncode == 0, p.stderr
    data = json.loads(p.stdout)
    assert data["name"] == "lite"
    assert data["maxConcurrentDelegates"] == 1
    assert data["primaryAgent"] == PRIMARY
    assert "maxAgents" not in data
    assert data["allowedParallelism"] is False


@test("lite accepts the primary alone and the builder alone")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(Path(raw), "lite", "--agents", PRIMARY)
        assert_ok(p, data)
        assert data["delegates"] == []
        assert data["delegateCount"] == 0

    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(Path(raw), "lite", "--delegates", "ufme-builder")
        assert_ok(p, data)
        assert data["activeAgents"] == [PRIMARY, "ufme-builder"]
        assert data["delegateCount"] == 1
        assert data["availableDelegateRoles"] == ["ufme-builder"]


@test("lite rejects a second concurrent delegate")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "lite", "--delegates", "ufme-builder,ufme-builder",
        )
        assert_violation(p, data, "duplicate agent names")


@test("lite rejects an agent outside its allowed set")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(Path(raw), "lite", "--delegates", "ufme-auditor")
        assert_violation(p, data, "not allowed in profile 'lite'")


@test("lite rejects parallel execution")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "lite", "--agents", f"{PRIMARY},ufme-builder", "--parallel",
        )
        assert_violation(p, data, "parallel execution is disabled")


@test("lite rejects deeper research than allowed")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "lite", "--delegates", "ufme-builder", "--research", "deep",
        )
        assert_violation(p, data, "requested research 'deep' exceeds")


@test("standard delegates design and backend integration in parallel")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "standard",
            "--delegates", "ufme-designer,ufme-backend-analyst", "--parallel",
        )
        assert_ok(p, data)
        assert data["delegates"] == ["ufme-designer", "ufme-backend-analyst"]
        assert data["delegateCount"] == 2
        assert data["maxConcurrentDelegates"] == 2
        assert data["parallelRequested"] is True


@test("standard delegates an independent audit")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(Path(raw), "standard", "--delegates", "ufme-auditor")
        assert_ok(p, data)
        assert data["delegates"] == ["ufme-auditor"]


@test("standard rejects a third concurrent delegate")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "standard",
            "--delegates", "ufme-designer,ufme-builder,ufme-auditor", "--parallel",
        )
        assert_violation(p, data, "concurrent delegates exceed maxConcurrentDelegates 2")


@test("standard rejects the orchestrator, which only advanced/autonomous use")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(Path(raw), "standard", "--delegates", "ufme-orchestrator")
        assert_violation(p, data, "not allowed in profile 'standard'")


@test("advanced accepts all five specialists sequentially at its declared depth")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "advanced", "--agents", ALL_SIX,
            "--research", "deep", "--verify", "thorough",
            "--browser", "comprehensive",
        )
        assert_ok(p, data)
        assert data["delegateCount"] == 5
        assert data["concurrentDelegates"] == 1
        assert data["maxConcurrentDelegates"] == 4
        assert data["parallelRequested"] is False


@test("advanced runs four specialists in parallel")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "advanced",
            "--delegates", "ufme-designer,ufme-builder,ufme-backend-analyst,ufme-auditor",
            "--parallel",
        )
        assert_ok(p, data)
        assert data["concurrentDelegates"] == 4
        assert data["delegateCount"] == 4


@test("advanced rejects five concurrent delegates")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "advanced", "--agents", ALL_SIX, "--parallel",
        )
        assert_violation(p, data, "concurrent delegates exceed maxConcurrentDelegates 4")


@test("autonomous accepts exhaustive verification with all five specialists")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "autonomous", "--delegates",
            "ufme-orchestrator,ufme-designer,ufme-builder,"
            "ufme-backend-analyst,ufme-auditor",
            "--research", "deep", "--verify", "exhaustive",
            "--browser", "comprehensive", "--parallel",
        )
        assert_ok(p, data)
        assert data["delegateCount"] == 5
        assert data["verificationDepth"] == "exhaustive"
        assert data["maxConcurrentDelegates"] == 5


@test("parallel with fewer than two delegates is rejected")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "standard", "--delegates", "ufme-builder", "--parallel",
        )
        assert_violation(p, data, "parallel execution requires at least two")


@test("primary is not counted as a delegate")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(Path(raw), "lite", "--agents", f"{PRIMARY},ufme-builder")
        assert_ok(p, data)
        assert data["delegateCount"] == 1
        assert data["activeAgents"] != data["delegates"]


@test("a missing primary is rejected")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(Path(raw), "standard", "--agents", "ufme-designer")
        assert_violation(p, data, "must include the primary agent")


@test("a duplicated primary is rejected")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "lite", "--agents", f"{PRIMARY},{PRIMARY}",
        )
        assert_violation(p, data, "duplicate agent names")


@test("--agents and --delegates cannot be combined")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "standard",
            "--agents", f"{PRIMARY},ufme-builder", "--delegates", "ufme-builder",
        )
        assert_violation(p, data, "use either --agents")


@test("profile schema is loaded from UFME_PROFILES_DIR, not hard-coded")
def _():
    import shutil
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        profiles = tmp / "profiles"
        shutil.copytree(PROFILES, profiles)
        lite = json.loads((profiles / "lite.json").read_text(encoding="utf-8"))
        lite["allowedAgents"].append("ufme-auditor")
        (profiles / "lite.json").write_text(json.dumps(lite), encoding="utf-8")
        p, data = enforce(
            tmp, "lite", "--delegates", "ufme-auditor",
            env_extra={"UFME_PROFILES_DIR": str(profiles)},
        )
        assert_ok(p, data)
        assert data["delegates"] == ["ufme-auditor"]


@test("a profile advertising more delegates than defined roles is rejected")
def _():
    import shutil
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        profiles = tmp / "profiles"
        shutil.copytree(PROFILES, profiles)
        lite = json.loads((profiles / "lite.json").read_text(encoding="utf-8"))
        lite["maxConcurrentDelegates"] = 9
        (profiles / "lite.json").write_text(json.dumps(lite), encoding="utf-8")
        p, data = enforce(
            tmp, "lite", "--agents", PRIMARY,
            env_extra={"UFME_PROFILES_DIR": str(profiles)},
        )
        assert_violation(p, data, "delegate roles exist")


@test("autonomous rejects invalid depth values")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p, data = enforce(
            Path(raw), "autonomous", "--agents", ALL_SIX, "--verify", "impossible",
        )
        assert_violation(p, data, "invalid verify level 'impossible'")


@test("evidence status always agrees with the exit code")
def _():
    cases = [
        (["--agents", f"{PRIMARY},ufme-builder"], 0),
        (["--agents", PRIMARY], 0),
        (["--delegates", "ufme-auditor"], 1),
    ]
    for args, expected in cases:
        with tempfile.TemporaryDirectory() as raw:
            p, data = enforce(Path(raw), "lite", *args)
            assert p.returncode == expected, (args, p.returncode, p.stderr)
            assert data is not None, args
            assert data["status"] == ("PASS" if expected == 0 else "FAIL"), (args, data)


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
