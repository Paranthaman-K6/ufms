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
QUALITY = ROOT / "skills/universal-frontend-master/scripts/quality-check.py"
EVIDENCE = ROOT / ".ufme" / "evidence"
FILLED_DESIGN = (
    "# Design System\n\n## Design direction\n"
    "- Tone: editorial, print-inspired\n"
    "- Type pairing: Bricolage Grotesque for display, Source Serif for text\n"
    "- Palette rationale: ink and paper neutrals from the printed portfolio\n"
    "- Layout concept: filmstrip of work above a running index\n"
    "- Motion hierarchy: hero mask reveal, list stagger, hover only on interactive rows\n"
    "\n### Typography\nDisplay: Bricolage Grotesque. Text: Source Serif.\n"
    "\n### Color\nInk #14130f, paper #f4efe6, accent rust #a3431f.\n"
    "\n## Components\nWork card, index row, contact block; hover and focus states defined.\n"
    "\n## Animation guidance\nHero mask reveal; list stagger; no section-wide fade.\n"
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
        (source / ".ufme").mkdir()
        (source / ".ufme" / "DESIGN_SYSTEM.md").write_text(FILLED_DESIGN, encoding="utf-8")
        p, data, _ = gate(tmp, "slop", {"UFME_SLOP_PATH": str(source)})
        assert p.returncode == 0, p.stdout + p.stderr
        assert_report(data, "PASS")


SLOP = ROOT / "skills/universal-frontend-master/scripts/detect-slop.py"


def run_slop(source, design=None):
    cmd = [sys.executable, str(SLOP), "--path", str(source)]
    if design:
        cmd += ["--design", str(design)]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)


def write_design(path, filled=True):
    if not filled:
        # The seeded template: every required section present but empty.
        body = (
            "# Design System\n\n## Design direction\n\n## Tokens\n"
            "### Typography\n### Color\n\n## Components\n## Animation guidance\n"
        )
    else:
        body = (
            "# Design System\n\n## Design direction\n"
            "- Tone: editorial, print-inspired\n"
            "- Type pairing: Bricolage Grotesque for display, Source Serif for text\n"
            "- Palette rationale: ink and paper neutrals from the printed portfolio\n"
            "- Layout concept: filmstrip of work above a running index\n"
            "- Motion hierarchy: hero mask reveal, list stagger, hover only on interactive rows\n"
            "\n### Typography\nDisplay: Bricolage Grotesque. Text: Source Serif.\n"
            "\n### Color\nInk #14130f, paper #f4efe6, accent rust #a3431f.\n"
            "\n## Components\nWork card, index row, contact block; hover and focus states defined.\n"
            "\n## Animation guidance\nHero mask reveal; list stagger; no section-wide fade.\n"
        )
    path.write_text(body, encoding="utf-8")


@test("design slop scans component files and flags uniform motion")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        source = tmp / "source"
        source.mkdir()
        (source / "style.css").write_text(
            "html { font-family: ui-sans-serif, system-ui, -apple-system, 'Segoe UI', "
            "Roboto, 'Helvetica Neue', Arial, sans-serif; }\n"
            ":focus-visible { outline: 2px solid #000; }\n"
            "@media (prefers-reduced-motion: reduce) { * { animation: none; } }\n",
            encoding="utf-8",
        )
        for name in ("Hero", "About", "Work", "Contact"):
            (source / f"{name}.tsx").write_text(
                f"export const {name} = () => <motion.section variants={{slideUp}} "
                '<img src={pic} alt={title} width={320} height={400} /></motion.section>;\n',
                encoding="utf-8",
            )
        design = tmp / "DESIGN_SYSTEM.md"
        write_design(design, filled=False)
        p = run_slop(source, design)
        out = p.stdout + p.stderr
        assert p.returncode == 2, out
        assert "uniform-entrance-motion" in out, out
        assert "font-stack-inter-or-arial-only" in out, out
        assert "design-system-incomplete" in out, out
        assert "img-missing" not in out, "JSX expression props are not missing attributes"


@test("design slop passes a distinctive component tree and filled design system")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        source = tmp / "source"
        source.mkdir()
        (source / "style.css").write_text(
            "html { font-family: 'Bricolage Grotesque', Georgia, serif; }\n"
            ":focus-visible { outline: 2px solid #a3431f; }\n"
            "@media (prefers-reduced-motion: reduce) { * { animation: none; } }\n",
            encoding="utf-8",
        )
        for name, variant in (
            ("Hero", "heroReveal"), ("About", "sectionReveal"),
            ("Work", "listStagger"), ("Contact", "supportingFade"),
        ):
            (source / f"{name}.tsx").write_text(
                f"export const {name} = () => <motion.section variants={{{variant}}} "
                '<img src={pic} alt={title} width={320} height={400} /></motion.section>;\n',
                encoding="utf-8",
            )
        design = tmp / "DESIGN_SYSTEM.md"
        write_design(design)
        p = run_slop(source, design)
        out = p.stdout + p.stderr
        assert p.returncode == 0, out
        assert "0 design finding(s)" in out, out


@test("quality gate fails an empty design system")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        source = tmp / "source"
        (source / ".ufme").mkdir(parents=True)
        (source / "style.css").write_text(
            ":focus-visible { outline: 2px solid #000; }\n"
            "@media (prefers-reduced-motion: reduce) { * { animation: none; } }\n",
            encoding="utf-8",
        )
        write_design(source / ".ufme" / "DESIGN_SYSTEM.md", filled=False)
        p, data, _ = gate(tmp, "slop", {"UFME_SLOP_PATH": str(source)})
        assert p.returncode == 1, p.stdout + p.stderr
        assert_report(data, "FAIL")


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
        (source / ".ufme").mkdir()
        (source / ".ufme" / "DESIGN_SYSTEM.md").write_text(FILLED_DESIGN, encoding="utf-8")
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




@test("a ## Motion heading satisfies the animation section")
def _():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        source = tmp / "source"
        source.mkdir()
        (source / "style.css").write_text(
            "html { font-family: 'Bricolage Grotesque', Georgia, serif; }\n"
            ":focus-visible { outline: 2px solid #000; }\n"
            "@media (prefers-reduced-motion: reduce) { * { animation: none; } }\n",
            encoding="utf-8",
        )
        design = tmp / "DESIGN_SYSTEM.md"
        write_design(design)
        design.write_text(
            design.read_text(encoding="utf-8").replace("## Animation guidance", "## Motion"),
            encoding="utf-8",
        )
        p = run_slop(source, design)
        out = p.stdout + p.stderr
        assert p.returncode == 0, out
        assert "missing 'animation' section" not in out, out


@test("approve rewrites the status cell without a regex crash")
def _():
    import importlib.util

    path = ROOT / "skills/universal-frontend-master/scripts/search-libraries.py"
    spec = importlib.util.spec_from_file_location("search_libraries", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        registry = tmp / "LIBRARY_REGISTRY.md"
        registry.write_text(
            "# Library Research Registry\n\n"
            "| Name | Category | Site | License | Commercial | Install | Reason | Status |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| zod | forms | https://zod.dev | MIT | yes | npm i zod | schemas | candidate |\n",
            encoding="utf-8",
        )
        module.REGISTRY_OUT = str(registry)
        module.DECISIONS = str(tmp / "DECISIONS.md")
        module.fetch_pkg_metadata = lambda pkg: None

        assert module.approve_package("zod") is True
        text = registry.read_text(encoding="utf-8")
        assert "| schemas | approved |" in text, text
        assert "candidate" not in text, text


@test("quality gate fails when the design system file is missing")
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
        p, data, _ = gate(tmp, "slop", {"UFME_SLOP_PATH": str(source)})
        assert p.returncode == 1, p.stdout + p.stderr
        assert_report(data, "FAIL")
        findings = (tmp / "evidence" / "slop-results.json").read_text(encoding="utf-8")
        assert "cannot read design system" in findings, findings


@test("UFME_SLOP_SKIP_DESIGN=1 skips the design-system check")
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
        p, data, _ = gate(tmp, "slop", {
            "UFME_SLOP_PATH": str(source),
            "UFME_SLOP_SKIP_DESIGN": "1",
        })
        assert p.returncode == 0, p.stdout + p.stderr
        assert_report(data, "PASS")


if __name__ == "__main__":
    failed = [r for r in results if r["status"] == "FAIL"]
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "quality-test.json").write_text(
        json.dumps({"checks": len(results), "failed": len(failed), "results": results}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
    sys.exit(1 if failed else 0)
