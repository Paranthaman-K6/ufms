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
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UFME = ROOT / ".ufme"
EVIDENCE = UFME / "evidence"
REPORT = EVIDENCE / "quality-report.json"
BROWSER_RESULTS = EVIDENCE / "browser-results.json"

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

    # No axe/lighthouse runner is bundled; never report PASS without executing.
    if BROWSER_RESULTS.exists():
        try:
            browser_ok = json.loads(BROWSER_RESULTS.read_text()).get("status") == "PASS"
        except (OSError, ValueError):
            browser_ok = False
    else:
        browser_ok = False
    reason = "no browser available" if not browser_ok else "no runner configured"
    record("SKIPPED", "Accessibility (axe-core)", 0, reason)
    record("SKIPPED", "Performance (Lighthouse)", 0, reason)

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
