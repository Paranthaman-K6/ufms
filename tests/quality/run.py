#!/usr/bin/env python3
"""tests/quality/run.py — quality gate integration tests.

Exercises the gate without a real browser by overriding its browser scripts:
  * PASS / FAIL / BLOCKED / timeout browser outcomes
  * a blocked browser-setup probe never runs the suite
  * design-slop PASS and FAIL against fixture source trees
  * atomic report writes, per-check timing, counts matching checks

Usage: python3 tests/quality/run.py
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
QUALITY = ROOT / "universal-frontend-master-source/scripts/quality-check.py"
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


def script(path, body):
    path.write_text("#!/usr/bin/env bash\nset -u\n" + body, encoding="utf-8")
    path.chmod(0o755)
    return path


def gate(tmp, only, env_extra=None, report_name="report.json"):
    evidence = tmp / "evidence"
    env = os.environ.copy()
    env["UFME_EVIDENCE_DIR"] = str(evidence)
    env.update(env_extra or {})
    report = tmp / report_name
    p = subprocess.run(
        [sys.executable, str(QUALITY), "--only", only, "--report", str(report)],
        cwd=ROOT, capture_output=True, text=True, timeout=120, env=env,
    )
    data = json.loads(report.read_text(encoding="utf-8")) if report.exists() else None
    return p, data, report


def assert_report(data, status):
    assert data is not None, "report not written"
    assert data["overall"] == status, data["overall"]
    assert len(data["checks"]) == 1, data["checks"]
    check = data["checks"][0]
    assert check["status"] == status, check
    assert "startedAt" in check and "durationMs" in check, check
    assert check["durationMs"] >= 0
    assert sum(data["counts"].values()) == len(data["checks"])


@test("browser PASS")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        check = script(tmp / "check.sh", "exit 0\n")
        browser = script(tmp / "browser.sh", "exit 0\n")
        p, data, report = gate(
            tmp, "browser",
            {"UFME_BROWSER_CHECK_SCRIPT": str(check), "UFME_BROWSER_TEST_SCRIPT": str(browser)},
        )
        assert p.returncode == 0, p.stdout + p.stderr
        assert_report(data, "PASS")
        assert data["checks"][0]["id"] == "browser"
        assert not list(report.parent.glob(".quality-report.*.json")), "temp report left behind"


@test("browser FAIL")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        check = script(tmp / "check.sh", "exit 0\n")
        browser = script(
            tmp / "browser.sh",
            'printf \'{"status":"FAIL"}\\n\' > "$UFME_EVIDENCE_DIR/browser-results.json"\n'
            "exit 1\n",
        )
        p, data, _ = gate(
            tmp, "browser",
            {"UFME_BROWSER_CHECK_SCRIPT": str(check), "UFME_BROWSER_TEST_SCRIPT": str(browser)},
        )
        assert p.returncode == 1, p.stdout + p.stderr
        assert_report(data, "FAIL")
        assert data["checks"][0]["exitCode"] == 1


@test("browser BLOCKED from results status")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        check = script(tmp / "check.sh", "exit 0\n")
        browser = script(
            tmp / "browser.sh",
            'printf \'{"status":"BLOCKED"}\\n\' > "$UFME_EVIDENCE_DIR/browser-results.json"\n'
            "exit 1\n",
        )
        p, data, _ = gate(
            tmp, "browser",
            {"UFME_BROWSER_CHECK_SCRIPT": str(check), "UFME_BROWSER_TEST_SCRIPT": str(browser)},
        )
        assert p.returncode == 1
        assert_report(data, "BLOCKED")


@test("blocked browser setup never runs the suite")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        marker = tmp / "suite-ran"
        check = script(tmp / "check.sh", "exit 1\n")
        browser = script(tmp / "browser.sh", f"touch '{marker}'\nexit 0\n")
        p, data, _ = gate(
            tmp, "browser",
            {"UFME_BROWSER_CHECK_SCRIPT": str(check), "UFME_BROWSER_TEST_SCRIPT": str(browser)},
        )
        assert p.returncode == 1
        assert_report(data, "BLOCKED")
        assert not marker.exists(), "browser suite ran after setup failed"


@test("browser timeout is FAIL 124")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        check = script(tmp / "check.sh", "exit 0\n")
        browser = script(tmp / "browser.sh", "sleep 5\nexit 0\n")
        p, data, _ = gate(
            tmp, "browser",
            {
                "UFME_BROWSER_CHECK_SCRIPT": str(check),
                "UFME_BROWSER_TEST_SCRIPT": str(browser),
                "UFME_BROWSER_TIMEOUT": "1",
            },
        )
        assert p.returncode == 1
        assert_report(data, "FAIL")
        assert data["checks"][0]["exitCode"] == 124


@test("design slop FAIL on a bad fixture")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        source = tmp / "source"
        source.mkdir()
        (source / "index.html").write_text(
            '<!doctype html><html><body><a href="#">x</a><img src="a.png"></body></html>',
            encoding="utf-8",
        )
        p, data, _ = gate(tmp, "slop", {"UFME_SLOP_PATH": str(source)})
        assert p.returncode == 1, p.stdout + p.stderr
        assert_report(data, "FAIL")
        assert "findings" in data["checks"][0]["detail"]


@test("design slop PASS on a clean fixture")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        source = tmp / "source"
        source.mkdir()
        (source / "style.css").write_text(
            ":focus-visible { outline: 2px solid #000; }\n"
            "@media (prefers-reduced-motion: reduce) { * { animation: none; } }\n",
            encoding="utf-8",
        )
        (source / "index.html").write_text(
            '<!doctype html><html><head><link rel="stylesheet" href="style.css"></head>'
            '<body><img src="a.png" alt="dot" width="2" height="2"></body></html>',
            encoding="utf-8",
        )
        p, data, _ = gate(tmp, "slop", {"UFME_SLOP_PATH": str(source)})
        assert p.returncode == 0, p.stdout + p.stderr
        assert_report(data, "PASS")


@test("design slop threshold is configurable")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        source = tmp / "source"
        source.mkdir()
        (source / "index.html").write_text(
            '<!doctype html><html><body><a href="#">x</a></body></html>',
            encoding="utf-8",
        )
        evidence = tmp / "evidence"
        env = os.environ.copy()
        env["UFME_EVIDENCE_DIR"] = str(evidence)
        env["UFME_SLOP_PATH"] = str(source)
        report = tmp / "report.json"
        p = subprocess.run(
            [sys.executable, str(QUALITY), "--only", "slop",
             "--max-slop-findings", "1", "--report", str(report)],
            cwd=ROOT, capture_output=True, text=True, timeout=120, env=env,
        )
        data = json.loads(report.read_text(encoding="utf-8"))
        assert p.returncode == 0, p.stdout + p.stderr
        assert data["checks"][0]["status"] == "PASS"


@test("unknown --only id is rejected")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        p, _, _ = gate(tmp, "nonsense")
        assert p.returncode == 2, p.stdout + p.stderr


def main():
    failures = [r for r in results if r["status"] == "FAIL"]
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "quality-test.json").write_text(
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
