#!/usr/bin/env python3
"""tests/context/run.py — token-budgeted context pack tests.

Builds a fixture .ufme tree and exercises ctx-pack.py end to end:
  * all five agents produce a brief within 500 and 1500 tokens
  * missing artifacts are named explicitly, not silently dropped
  * --task appears in the brief
  * JSON evidence is summarized to decision-relevant fields
  * oversized artifacts are truncated or skipped, never over budget
  * --archive rotates old DECISIONS entries into DECISIONS.archive.md
  * usage/argument errors exit 2, a missing .ufme dir exits 1

Usage: python3 tests/context/run.py
Exit: 0 all pass, 1 failure.
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "universal-frontend-master-source/scripts/ctx-pack.py"
EVIDENCE = ROOT / ".ufme" / "evidence"
AGENTS = ["orchestrator", "designer", "builder", "backend-analyst", "auditor"]

spec = importlib.util.spec_from_file_location("ctx_pack", SCRIPT)
ctx_pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ctx_pack)

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


def make_ufme(tmp):
    ufme = tmp / ".ufme"
    (ufme / "evidence").mkdir(parents=True)
    files = {
        "AGENT_STATE.md": "# Agent State\n- phase: build\n- status: running\n",
        "TASKS.md": "# Tasks\n- [ ] hero\n- [ ] nav\n",
        "DECISIONS.md": (
            "# Decisions\n\n| Decision | Choice |\n|---|---|\n"
            "| font | Source Serif 4 |\n| hero layout | asymmetric |\n| API base | /api |\n"
        ),
        "ENVIRONMENT.md": "# Environment\n- node: 20\n",
        "PROJECT_SPEC.md": "# Project Spec\nPortfolio for a studio.\n",
        "PRD.md": "# PRD\nOne page with three sections.\n",
        "ARCHITECTURE.md": "# Architecture\nStatic HTML and CSS.\n",
        "DESIGN_SYSTEM.md": "# Design System\n- type: serif\n- color: warm\n",
        "API_MAP.md": "# API Map\n- GET /api/projects\n",
        "BACKEND_CAPABILITIES.md": "# Backend\nRead-only JSON.\n",
        "AUTHENTICATION_MAP.md": "# Auth\nNone.\n",
        "ERROR_HANDLING.md": "# Errors\n404 page.\n",
        "AUDIT_REPORT.md": "# Audit Report\nNo findings.\n",
    }
    for name, text in files.items():
        (ufme / name).write_text(text, encoding="utf-8")
    (ufme / "evidence" / "quality-report.json").write_text(
        json.dumps(
            {"overall": "FAIL", "counts": {"fail": 2, "pass": 4, "skipped": 1},
             "checks": [1, 2, 3], "project": {"name": "fixture"}}
        ),
        encoding="utf-8",
    )
    (ufme / "evidence" / "a11y-results.json").write_text(
        json.dumps({"totalViolations": 3, "violationsByRule": [{"id": "label"}]}),
        encoding="utf-8",
    )
    return ufme


def pack(ufme, agent, *extra, out=None):
    cmd = [sys.executable, str(SCRIPT), "--agent", agent, "--ufme-dir", str(ufme), *extra]
    if out:
        cmd += ["--out", str(out)]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)


@test("all five agents stay within 500 and 1500 tokens")
def _():
    with tempfile.TemporaryDirectory() as raw:
        ufme = make_ufme(Path(raw))
        for budget in (500, 1500):
            for agent in AGENTS:
                p = pack(ufme, agent, "--max-tokens", str(budget))
                assert p.returncode == 0, (agent, p.stderr)
                brief = (ufme / "evidence" / f"ctx-{agent}.md").read_text(encoding="utf-8")
                assert ctx_pack.estimate_tokens(brief) <= budget, (agent, budget)
                assert f"# Ctx pack: ufme-{agent}" in brief
                assert "Tokenizer:" in brief
                assert "Missing artifacts:" in brief


@test("missing artifacts are named explicitly")
def _():
    with tempfile.TemporaryDirectory() as raw:
        ufme = Path(raw) / ".ufme"
        ufme.mkdir()
        (ufme / "TASKS.md").write_text("# Tasks\n- [ ] one\n", encoding="utf-8")
        p = pack(ufme, "orchestrator", "--max-tokens", "500")
        assert p.returncode == 0, p.stderr
        brief = (ufme / "evidence" / "ctx-orchestrator.md").read_text(encoding="utf-8")
        missing = brief.split("Missing artifacts:", 1)[1].splitlines()[0]
        for name in ("AGENT_STATE", "DECISIONS", "ENVIRONMENT"):
            assert name in missing, (name, missing)
        assert "TASKS" not in missing.split("Truncated")[0], missing


@test("--task is recorded in the header")
def _():
    with tempfile.TemporaryDirectory() as raw:
        ufme = make_ufme(Path(raw))
        p = pack(ufme, "builder", "--max-tokens", "800",
                 "--task", "Implement the pricing page hero")
        assert p.returncode == 0, p.stderr
        brief = (ufme / "evidence" / "ctx-builder.md").read_text(encoding="utf-8")
        assert "- Task: Implement the pricing page hero" in brief


@test("JSON evidence is summarized")
def _():
    with tempfile.TemporaryDirectory() as raw:
        ufme = make_ufme(Path(raw))
        p = pack(ufme, "auditor", "--max-tokens", "1500")
        assert p.returncode == 0, p.stderr
        brief = (ufme / "evidence" / "ctx-auditor.md").read_text(encoding="utf-8")
        assert "overall=FAIL" in brief
        assert "counts: fail=2, pass=4, skipped=1" in brief
        assert "axeViolations=3" in brief


@test("oversized artifacts are truncated or skipped within budget")
def _():
    with tempfile.TemporaryDirectory() as raw:
        ufme = make_ufme(Path(raw))
        (ufme / "TASKS.md").write_text(
            "# Tasks\n" + "\n".join(f"- [ ] task {i} " + "x" * 80 for i in range(500)),
            encoding="utf-8",
        )
        p = pack(ufme, "builder", "--max-tokens", "300")
        assert p.returncode == 0, p.stderr
        brief = (ufme / "evidence" / "ctx-builder.md").read_text(encoding="utf-8")
        assert ctx_pack.estimate_tokens(brief) <= 300, ctx_pack.estimate_tokens(brief)
        truncated = brief.split("Truncated sections:", 1)[1].splitlines()[0]
        skipped = brief.split("Skipped for budget:", 1)[1].splitlines()[0]
        assert truncated != "none" or skipped != "none", brief


@test("--archive rotates old DECISIONS entries")
def _():
    with tempfile.TemporaryDirectory() as raw:
        ufme = make_ufme(Path(raw))
        rows = "\n".join(
            f"| row {i} | " + "y" * 40 + " |" for i in range(200)
        )
        (ufme / "DECISIONS.md").write_text(
            "# Decisions\n\n| Decision | Choice |\n|---|---|\n" + rows + "\n",
            encoding="utf-8",
        )
        before = (ufme / "DECISIONS.md").read_text(encoding="utf-8")
        p = pack(ufme, "designer", "--max-tokens", "300", "--archive")
        assert p.returncode == 0, p.stderr
        archive = ufme / "DECISIONS.archive.md"
        assert archive.exists(), "archive not created"
        after = (ufme / "DECISIONS.md").read_text(encoding="utf-8")
        assert "row 0" in archive.read_text(encoding="utf-8")
        assert "row 0" not in after
        assert len(after) < len(before)


@test("designer keeps only design-relevant decision rows")
def _():
    with tempfile.TemporaryDirectory() as raw:
        ufme = make_ufme(Path(raw))
        p = pack(ufme, "designer", "--max-tokens", "1500")
        assert p.returncode == 0, p.stderr
        brief = (ufme / "evidence" / "ctx-designer.md").read_text(encoding="utf-8")
        assert "Source Serif 4" in brief
        assert "| API base |" not in brief


@test("default output path is the evidence directory")
def _():
    with tempfile.TemporaryDirectory() as raw:
        ufme = make_ufme(Path(raw))
        p = pack(ufme, "backend-analyst")
        assert p.returncode == 0, p.stderr
        assert (ufme / "evidence" / "ctx-backend-analyst.md").is_file()


@test("unknown agent exits 2")
def _():
    with tempfile.TemporaryDirectory() as raw:
        ufme = make_ufme(Path(raw))
        p = pack(ufme, "wizard")
        assert p.returncode == 2, p.stdout + p.stderr


@test("non-positive budget exits 2")
def _():
    with tempfile.TemporaryDirectory() as raw:
        ufme = make_ufme(Path(raw))
        p = pack(ufme, "builder", "--max-tokens", "0")
        assert p.returncode == 2, p.stderr


@test("missing .ufme directory exits 1")
def _():
    with tempfile.TemporaryDirectory() as raw:
        p = pack(Path(raw) / "absent", "builder")
        assert p.returncode == 1, p.stderr


def main():
    failures = [r for r in results if r["status"] == "FAIL"]
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "context-test.json").write_text(
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
