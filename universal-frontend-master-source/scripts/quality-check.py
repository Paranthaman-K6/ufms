#!/usr/bin/env python3
"""
quality-check.py — genuine quality gate.

Runs type check, lint, formatting, unit tests, build, browser tests,
accessibility/performance notes, and a dependency audit. Records every check
as PASS/FAIL/SKIPPED/BLOCKED and writes .ufme/evidence/quality-report.json.

Exits non-zero when any mandatory check FAILs or is BLOCKED.

Safety: project-local only; never sudo/pacman/systemctl.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UFME = ROOT / ".ufme"
EVIDENCE = UFME / "evidence"
REPORT = EVIDENCE / "quality-report.json"
BROWSER_RESULTS = EVIDENCE / "browser-results.json"
SCRIPTS_DIR = ROOT / "universal-frontend-master-source" / "scripts"
A11Y_SCRIPT = SCRIPTS_DIR / "audit-a11y.js"
A11Y_RESULTS = EVIDENCE / "a11y-results.json"
PERF_SCRIPT = SCRIPTS_DIR / "audit-perf.sh"
PERF_RESULTS = EVIDENCE / "perf-results.json"

# Target URL served by the app under test (browser-test.sh default).
TARGET_URL = os.environ.get("UFME_AUDIT_URL") or "http://localhost:5173"

CHECKS = []
COUNTS = {"PASS": 0, "FAIL": 0, "SKIPPED": 0, "BLOCKED": 0}


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def log(msg):
    print(f"[quality-check] {msg}", flush=True)


def record(status, label, rc=0, detail=""):
    CHECKS.append({"status": status, "label": label, "exitCode": rc, "detail": detail})
    COUNTS[status] += 1
    log(f"{status}: {label}{(': ' + detail) if detail else ''}")


def run(label, cmd, timeout=300):
    if not cmd or shutil.which(cmd[0]) is None:
        record("SKIPPED", label, 0, f"{cmd[0] if cmd else 'command'} not available")
        return
    log(f"Running: {label}")
    try:
        p = subprocess.run(
            cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        record("FAIL", label, 124, f"timed out after {timeout}s")
        return
    except OSError as e:
        record("FAIL", label, 1, str(e))
        return
    detail = (p.stderr or p.stdout or "").strip().splitlines()
    detail = detail[0][:200] if detail else ""
    record("PASS" if p.returncode == 0 else "FAIL", label, p.returncode, detail)


def package_json():
    path = ROOT / "package.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def package_manager():
    if (ROOT / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (ROOT / "yarn.lock").exists():
        return "yarn"
    return "npm" if (ROOT / "package.json").exists() else "none"


def has_eslint(pkg):
    names = [".eslintrc", ".eslintrc.js", ".eslintrc.json"]
    return (
        any((ROOT / n).exists() for n in names)
        or any(ROOT.glob("eslint.config.*"))
        or "eslint" in pkg.get("devDependencies", {})
    )


def has_prettier(pkg):
    names = [".prettierrc", ".prettierrc.js", ".prettierrc.json"]
    return (
        any((ROOT / n).exists() for n in names)
        or "prettier" in pkg.get("devDependencies", {})
    )


def run_browser_tests():
    check = ROOT / "universal-frontend-master-source/scripts/check-native-browser.sh"
    browser = ROOT / "universal-frontend-master-source/scripts/browser-test.sh"
    if not check.exists() or not browser.exists():
        record("SKIPPED", "Browser tests", 0, "browser scripts not found")
        return
    try:
        probe = subprocess.run(
            ["bash", str(check)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        record("BLOCKED", "Browser tests", 124, "browser setup check timed out")
        return
    if probe.returncode != 0:
        record("BLOCKED", "Browser tests", 1, "Selenium WebDriver not available")
        return
    try:
        p = subprocess.run(
            ["bash", str(browser)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        record("FAIL", "Browser tests", 124, "browser tests timed out")
        return
    if p.returncode == 0:
        record("PASS", "Browser tests", 0)
        return
    blocked = False
    if BROWSER_RESULTS.exists():
        try:
            blocked = json.loads(BROWSER_RESULTS.read_text()).get("status") == "BLOCKED"
        except (OSError, ValueError):
            blocked = False
record(
        "BLOCKED" if blocked else "FAIL",
        "Browser tests",
        p.returncode,
        "browser setup blocked" if blocked else "browser tests failed",
    )


def browser_binary_available():
    for name in (
        "chromium",
        "chromium-browser",
        "google-chrome-stable",
        "google-chrome",
        "chrome",
        "firefox",
        "firefox-developer-edition",
    ):
        if shutil.which(name):
            return True
    return False


def url_responds(url):
    """True when something answered over HTTP (any status counts)."""
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status is not None
    except urllib.error.HTTPError:
        return True
    except (urllib.error.URLError, OSError, ValueError):
        return False


def json_field(path, field):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8")).get(field)
    except (OSError, ValueError):
        return None


def run_a11y_gate():
    label = "Accessibility (axe-core)"
    if not A11Y_SCRIPT.exists() or not (
        ROOT / "node_modules" / "@axe-core" / "webdriverjs"
    ).exists():
        record(
            "SKIPPED", label, 0,
            "Missing dependency — run: npm i -D @axe-core/webdriverjs",
        )
        return
    if not (ROOT / "node_modules" / "selenium-webdriver" / "index.js").exists():
        record("SKIPPED", label, 0, "Missing dependency — run: npm i -D selenium-webdriver")
        return
    if not browser_binary_available():
        record(
            "BLOCKED", label, 0,
            "no Chromium/Chrome or Firefox binary found — install a system browser (sudo required, user action)",
        )
        return
    if not url_responds(TARGET_URL):
        record(
            "SKIPPED", label, 0,
            f"target URL did not respond: {TARGET_URL} — start the dev server and re-run",
        )
        return
    log(f"Running axe-core audit against {TARGET_URL}")
    try:
        p = subprocess.run(
            ["node", str(A11Y_SCRIPT), TARGET_URL, "--timeout", "180000"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        record("FAIL", label, 124, "axe-core audit timed out after 300s")
        return
    except OSError as e:
        record("FAIL", label, 1, str(e))
        return
    rc = p.returncode
    if rc == 0:
        record("PASS", label, 0, "no axe-core violations")
    elif rc == 1:
        total = json_field(A11Y_RESULTS, "totalViolations")
        record(
            "FAIL", label, rc,
            f"{total if total is not None else 'violations'} axe violations found"
            " (results: .ufme/evidence/a11y-results.json)",
        )
    elif rc == 3:
        reason = json_field(A11Y_RESULTS, "reason") or p.stdout.strip() or ""
        record("SKIPPED", label, rc, reason or "Missing dependency — run: npm i -D @axe-core/webdriverjs")
    elif rc == 5:
        brokered = json_field(A11Y_RESULTS, "reason") or "browser/runtime failure"
        record("BLOCKED", label, rc, f"browser could not launch: {brokered}")
    else:
        record("FAIL", label, rc, (p.stderr or p.stdout or "").strip()[:200])


def run_perf_gate():
    label = "Performance (Lighthouse)"
    if not PERF_SCRIPT.exists():
        record("SKIPPED", label, 0, "audit-perf.sh missing")
        return
    if not (ROOT / "node_modules" / "lighthouse" / "package.json").exists():
        record("SKIPPED", label, 0, "Missing dependency — run: npm i -D lighthouse")
        return
    if not browser_binary_available():
        record(
            "BLOCKED", label, 0,
            "no Chromium/Chrome binary found — install a system browser (sudo required, user action)",
        )
        return
    if not url_responds(TARGET_URL):
        record(
            "SKIPPED", label, 0,
            f"target URL did not respond: {TARGET_URL} — start the dev server and re-run",
        )
        return
    log(f"Running lighthouse audit against {TARGET_URL}")
    try:
        p = subprocess.run(
            ["bash", str(PERF_SCRIPT), TARGET_URL],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        record("FAIL", label, 124, "lighthouse audit timed out after 600s")
        return
    except OSError as e:
        record("FAIL", label, 1, str(e))
        return
    rc = p.returncode
    if rc == 0:
        scores = json_field(PERF_RESULTS, "scores") or {}
        record(
            "PASS", label, 0,
            f"perf={scores.get('performance')} a11y={scores.get('accessibility')}"
            f" best-practices={scores.get('bestPractices')}",
        )
    elif rc == 5:
        reason = json_field(PERF_RESULTS, "reason") or "lighthouse unavailable or failed"
        record("SKIPPED", label, rc, reason)
    else:
        record("FAIL", label, rc, (p.stderr or p.stdout or "").strip().splitlines()[0][:200])


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    exec_id = f"ufme-quality-{int(time.time())}"
    started = now()
    pkg = package_json()
    scripts = pkg.get("scripts", {}) if isinstance(pkg.get("scripts"), dict) else {}
    project_name = pkg.get("name") or "unknown"

    if (ROOT / "tsconfig.json").exists():
        run("TypeScript check", ["npx", "tsc", "--noEmit"])
    else:
        record("SKIPPED", "TypeScript check", 0, "no tsconfig.json")

    run("Lint", ["npx", "eslint", ".", "--ext", ".js,.ts,.jsx,.tsx"]) if has_eslint(pkg) \
        else record("SKIPPED", "Lint", 0, "not configured")

    run("Formatting", ["npx", "prettier", "--check", "."]) if has_prettier(pkg) \
        else record("SKIPPED", "Formatting", 0, "not configured")

    run("Unit tests", ["npm", "test"]) if "test" in scripts \
        else record("SKIPPED", "Unit tests", 0, "no test script")

    run("Production build", ["npm", "run", "build"]) if "build" in scripts \
        else record("SKIPPED", "Production build", 0, "no build script")

    run_browser_tests()

    run_a11y_gate()
    run_perf_gate()

    run("Dependency audit", ["npm", "audit", "--audit-level=moderate"]) if (ROOT / "package.json").exists() \
        else record("SKIPPED", "Dependency audit", 0, "no package.json")

    overall = "FAIL" if COUNTS["FAIL"] or COUNTS["BLOCKED"] else "PASS"
    report = {
        "executionId": exec_id,
        "startTime": started,
        "finishTime": now(),
        "project": {
            "name": project_name,
            "packageManager": package_manager(),
            "root": str(ROOT),
        },
        "overall": overall,
        "counts": {
            "pass": COUNTS["PASS"],
            "fail": COUNTS["FAIL"],
            "skipped": COUNTS["SKIPPED"],
            "blocked": COUNTS["BLOCKED"],
        },
        "checks": CHECKS,
    }

    fd, tmp = tempfile.mkstemp(dir=str(EVIDENCE), prefix=".quality-report.", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
            f.write("\n")
        os.replace(tmp, REPORT)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

    print("---- Quality check summary ----")
    print(
        f"PASS: {COUNTS['PASS']}, FAIL: {COUNTS['FAIL']}, "
        f"SKIPPED: {COUNTS['SKIPPED']}, BLOCKED: {COUNTS['BLOCKED']}"
    )
    print(f"Overall: {overall}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
