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
import threading
import traceback
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
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


def gate(tmp, only, env_extra=None, report_name="report.json", target=None):
    evidence = tmp / "evidence"
    env = os.environ.copy()
    env["UFME_EVIDENCE_DIR"] = str(evidence)
    env.update(env_extra or {})
    report = tmp / report_name
    cmd = [sys.executable, str(QUALITY), "--only", only, "--report", str(report)]
    if target:
        cmd += ["--target", target]
    p = subprocess.run(
        cmd, cwd=ROOT, capture_output=True, text=True, timeout=120, env=env,
    )
    data = json.loads(report.read_text(encoding="utf-8")) if report.exists() else None
    return p, data, report


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):  # noqa: D401 - silence test server
        pass


def serve(directory):
    handler = partial(_QuietHandler, directory=str(directory))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}/"


def fake_browser(tmp):
    bindir = tmp / "bin"
    bindir.mkdir()
    binary = bindir / "chromium"
    binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    binary.chmod(0o755)
    return f"{bindir}{os.pathsep}{os.environ['PATH']}"


def fake_a11y(tmp):
    path = tmp / "a11y.js"
    path.write_text(
        "const fs = require('fs');\n"
        "const mode = process.env.FAKE_A11Y_MODE || 'valid';\n"
        "if (mode !== 'missing') {\n"
        "  const data = mode === 'invalid'\n"
        "    ? { status: 'RAN' }\n"
        "    : { status: 'RAN', totalViolations: Number(process.env.FAKE_TOTAL || 0),"
        " violationsByRule: [] };\n"
        "  fs.writeFileSync(process.env.UFME_A11Y_RESULTS, JSON.stringify(data));\n"
        "}\n"
        "process.exit(Number(process.env.FAKE_EXIT || 0));\n",
        encoding="utf-8",
    )
    return path


def fake_perf(tmp):
    path = tmp / "perf.sh"
    path.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s' \"${FAKE_PERF_JSON}\" > \"$UFME_PERF_RESULTS\"\n"
        "exit \"${FAKE_EXIT:-0}\"\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def fake_visual(tmp):
    path = tmp / "visual.js"
    path.write_text(
        "const fs = require('fs');\n"
        "fs.writeFileSync(process.env.UFME_VISUAL_RESULTS, process.env.FAKE_VISUAL_JSON);\n"
        "process.exit(Number(process.env.FAKE_EXIT || 0));\n",
        encoding="utf-8",
    )
    return path


def fake_slop(tmp):
    path = tmp / "slop.py"
    path.write_text(
        "import json, sys\n"
        "out = sys.argv[sys.argv.index('--json') + 1]\n"
        "open(out, 'w').write(json.dumps(json.loads(__import__('os').environ['FAKE_SLOP_JSON'])))\n"
        "sys.exit(int(__import__('os').environ.get('FAKE_EXIT', '0')))\n",
        encoding="utf-8",
    )
    return path


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
        browser = script(
            tmp / "browser.sh",
            'printf \'{"status":"PASS"}\\n\' > "$UFME_EVIDENCE_DIR/browser-results.json"\n'
            "exit 0\n",
        )
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


@test("browser exit 0 without PASS evidence is FAIL")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        check = script(tmp / "check.sh", "exit 0\n")
        browser = script(tmp / "browser.sh", "exit 0\n")
        p, data, _ = gate(
            tmp, "browser",
            {"UFME_BROWSER_CHECK_SCRIPT": str(check), "UFME_BROWSER_TEST_SCRIPT": str(browser)},
        )
        assert p.returncode == 1, p.stdout + p.stderr
        assert_report(data, "FAIL")
        assert "evidence missing" in data["checks"][0]["detail"]


@test("a required SKIPPED check BLOCKS the audit gate")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        missing = tmp / "absent"
        clean_slop = fake_slop(tmp)
        p, data, _ = gate(tmp, "audit", {
            "UFME_A11Y_SCRIPT": str(missing),
            "UFME_PERF_SCRIPT": str(missing),
            "UFME_VISUAL_SCRIPT": str(missing),
            "UFME_SLOP_SCRIPT": str(clean_slop),
            "FAKE_SLOP_JSON": '{"count": 0}',
        })
        assert p.returncode == 1, p.stdout + p.stderr
        assert data["overall"] == "BLOCKED", data["overall"]
        assert data["required"] == ["a11y", "perf", "slop", "visual"], data["required"]
        assert sorted(data["requiredNotPassed"]) == ["a11y", "perf", "visual"], data["requiredNotPassed"]
        statuses = {c["id"]: c["status"] for c in data["checks"]}
        assert statuses["slop"] == "PASS", statuses
        assert statuses["a11y"] == "SKIPPED", statuses


@test("invalid axe evidence is FAIL even with exit 0")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        www = tmp / "www"
        www.mkdir()
        httpd, url = serve(www)
        try:
            a11y = fake_a11y(tmp)
            p, data, _ = gate(tmp, "a11y", {
                "PATH": fake_browser(tmp),
                "UFME_A11Y_SCRIPT": str(a11y),
                "UFME_A11Y_RESULTS": str(tmp / "a11y-results.json"),
                "FAKE_A11Y_MODE": "invalid",
            }, target=url)
        finally:
            httpd.shutdown()
        assert p.returncode == 1, p.stdout + p.stderr
        assert_report(data, "FAIL")
        assert "invalid axe evidence" in data["checks"][0]["detail"]


@test("valid axe evidence with zero violations PASSes")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        www = tmp / "www"
        www.mkdir()
        httpd, url = serve(www)
        try:
            a11y = fake_a11y(tmp)
            p, data, _ = gate(tmp, "a11y", {
                "PATH": fake_browser(tmp),
                "UFME_A11Y_SCRIPT": str(a11y),
                "UFME_A11Y_RESULTS": str(tmp / "a11y-results.json"),
                "FAKE_A11Y_MODE": "valid",
            }, target=url)
        finally:
            httpd.shutdown()
        assert p.returncode == 0, p.stdout + p.stderr
        assert_report(data, "PASS")


@test("invalid lighthouse scores are FAIL even with exit 0")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        www = tmp / "www"
        www.mkdir()
        httpd, url = serve(www)
        try:
            perf = fake_perf(tmp)
            p, data, _ = gate(tmp, "perf", {
                "PATH": fake_browser(tmp),
                "UFME_PERF_SCRIPT": str(perf),
                "UFME_PERF_RESULTS": str(tmp / "perf-results.json"),
                "FAKE_PERF_JSON": '{"status":"RAN","scores":{}}',
            }, target=url)
        finally:
            httpd.shutdown()
        assert p.returncode == 1, p.stdout + p.stderr
        assert_report(data, "FAIL")
        assert "invalid lighthouse evidence" in data["checks"][0]["detail"]


def perf_case(json_body, exit_code, env_extra=None):
    """Run the perf gate against a reachable URL with scripted evidence."""
    raw = tempfile.mkdtemp()
    tmp = Path(raw)
    www = tmp / "www"
    www.mkdir()
    httpd, url = serve(www)
    try:
        perf = fake_perf(tmp)
        env = {
            "PATH": fake_browser(tmp),
            "UFME_PERF_SCRIPT": str(perf),
            "UFME_PERF_RESULTS": str(tmp / "perf-results.json"),
            "FAKE_PERF_JSON": json_body,
            "FAKE_EXIT": str(exit_code),
        }
        env.update(env_extra or {})
        return gate(tmp, "perf", env, target=url)
    finally:
        httpd.shutdown()


@test("valid lighthouse scores for all three categories PASS")
def _():
    p, data, _ = perf_case(
        '{"status":"RAN","scores":'
        '{"performance":95,"accessibility":100,"bestPractices":92}}', 0,
    )
    assert p.returncode == 0, p.stdout + p.stderr
    assert_report(data, "PASS")
    assert "best-practices=92" in data["checks"][0]["detail"]


@test("lighthouse SKIPPED (exit 5) stays SKIPPED, never PASS")
def _():
    p, data, _ = perf_case(
        '{"status":"SKIPPED","reason":"lighthouse not installed"}', 5,
    )
    assert p.returncode == 0, p.stdout + p.stderr
    check = data["checks"][0]
    assert check["status"] == "SKIPPED", check
    assert check["exitCode"] == 5, check


@test("lighthouse BLOCKED (exit 6) is BLOCKED and fails the gate")
def _():
    p, data, _ = perf_case(
        '{"status":"BLOCKED","reason":"no browser binary"}', 6,
    )
    assert p.returncode == 1, p.stdout + p.stderr
    assert_report(data, "BLOCKED")
    assert data["checks"][0]["exitCode"] == 6


@test("lighthouse FAIL (exit 4) is FAIL and fails the gate")
def _():
    p, data, _ = perf_case(
        '{"status":"FAIL","reason":"lighthouse crashed"}', 4,
    )
    assert p.returncode == 1, p.stdout + p.stderr
    assert_report(data, "FAIL")
    assert data["checks"][0]["exitCode"] == 4


@test("exit code contradicting lighthouse evidence is FAIL")
def _():
    p, data, _ = perf_case(
        '{"status":"FAIL","reason":"crashed"}', 0,
    )
    assert p.returncode == 1, p.stdout + p.stderr
    assert_report(data, "FAIL")
    assert "contradicts evidence status FAIL" in data["checks"][0]["detail"], \
        data["checks"][0]


@test("lighthouse evidence missing best-practices score is FAIL")
def _():
    p, data, _ = perf_case(
        '{"status":"RAN","scores":{"performance":90,"accessibility":95}}', 0,
    )
    assert p.returncode == 1, p.stdout + p.stderr
    assert_report(data, "FAIL")
    assert "invalid lighthouse evidence" in data["checks"][0]["detail"]


@test("lighthouse score below the minimum FAILs")
def _():
    p, data, _ = perf_case(
        '{"status":"RAN","scores":{"performance":90,"accessibility":95,'
        '"bestPractices":96}}', 0, {"UFME_LH_MIN_SCORE": "95"},
    )
    assert p.returncode == 1, p.stdout + p.stderr
    assert_report(data, "FAIL")
    assert "below minimum" in data["checks"][0]["detail"], data["checks"][0]


@test("an unreachable target URL is FAIL, not SKIPPED or BLOCKED")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        perf = fake_perf(tmp)
        p, data, _ = gate(tmp, "perf", {
            "PATH": fake_browser(tmp),
            "UFME_PERF_SCRIPT": str(perf),
            "UFME_PERF_RESULTS": str(tmp / "perf-results.json"),
            "FAKE_PERF_JSON": '{"status":"RAN","scores":{}}',
        }, target="http://127.0.0.1:1/")
        assert p.returncode == 1, p.stdout + p.stderr
        assert_report(data, "FAIL")
        assert "did not respond" in data["checks"][0]["detail"], data["checks"][0]


