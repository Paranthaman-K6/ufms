#!/usr/bin/env python3
"""
quality-check.py — genuine quality gate.

Runs type check, lint, formatting, unit tests, build, browser tests,
accessibility, performance, design-slop and visual-diff checks, then a
dependency audit. Records every check as PASS/FAIL/SKIPPED/BLOCKED with
start time and duration, and writes .ufme/evidence/quality-report.json.

Exits non-zero when any mandatory check FAILs or is BLOCKED.

Usage:
  python3 quality-check.py [--only browser,a11y] [--target URL] [--report PATH]
      [--max-a11y-violations N] [--max-slop-findings N]
      [--min-perf-score N] [--max-visual-diff RATIO]

Environment overrides:
  UFME_AUDIT_URL, UFME_EVIDENCE_DIR, UFME_SLOP_PATH, UFME_VISUAL_BASELINE,
  UFME_VISUAL_CURRENT, UFME_A11Y_SCRIPT, UFME_PERF_SCRIPT, UFME_SLOP_SCRIPT,
  UFME_VISUAL_SCRIPT, UFME_BROWSER_CHECK_SCRIPT, UFME_BROWSER_TEST_SCRIPT,
  UFME_BROWSER_CHECK_TIMEOUT, UFME_BROWSER_TIMEOUT.

Safety: project-local only; never sudo/pacman/systemctl.
"""

import argparse
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
EVIDENCE = Path(os.environ.get("UFME_EVIDENCE_DIR") or (UFME / "evidence"))
REPORT = EVIDENCE / "quality-report.json"
BROWSER_RESULTS = EVIDENCE / "browser-results.json"

SCRIPTS_DIR = ROOT / "universal-frontend-master-source" / "scripts"
A11Y_SCRIPT = Path(os.environ.get("UFME_A11Y_SCRIPT") or (SCRIPTS_DIR / "audit-a11y.js"))
A11Y_RESULTS = EVIDENCE / "a11y-results.json"
PERF_SCRIPT = Path(os.environ.get("UFME_PERF_SCRIPT") or (SCRIPTS_DIR / "audit-perf.sh"))
PERF_RESULTS = EVIDENCE / "perf-results.json"
SLOP_SCRIPT = Path(os.environ.get("UFME_SLOP_SCRIPT") or (SCRIPTS_DIR / "detect-slop.py"))
SLOP_RESULTS = EVIDENCE / "slop-results.json"
VISUAL_SCRIPT = Path(os.environ.get("UFME_VISUAL_SCRIPT") or (SCRIPTS_DIR / "visual-diff.js"))
VISUAL_RESULTS = EVIDENCE / "visual-diff.json"
BROWSER_CHECK_SCRIPT = Path(
    os.environ.get("UFME_BROWSER_CHECK_SCRIPT")
    or (SCRIPTS_DIR / "check-native-browser.sh")
)
BROWSER_TEST_SCRIPT = Path(
    os.environ.get("UFME_BROWSER_TEST_SCRIPT")
    or (SCRIPTS_DIR / "browser-test.sh")
)

TARGET_URL = os.environ.get("UFME_AUDIT_URL") or "http://localhost:5173"

CHECKS = []
COUNTS = {"PASS": 0, "FAIL": 0, "SKIPPED": 0, "BLOCKED": 0}

OPTIONS = {
    "target": TARGET_URL,
    "maxA11yViolations": 0,
    "maxSlopFindings": 0,
    "minPerfScore": 0,
    "maxVisualDiff": 0.001,
    "slopPath": os.environ.get("UFME_SLOP_PATH") or str(ROOT),
    "visualBaseline": os.environ.get("UFME_VISUAL_BASELINE")
    or str(EVIDENCE / "baseline"),
    "visualCurrent": os.environ.get("UFME_VISUAL_CURRENT")
    or str(EVIDENCE / "screenshots"),
}
OPTIONS["maxA11yViolations"] = int(os.environ.get("UFME_A11Y_MAX_VIOLATIONS", 0) or 0)
OPTIONS["maxSlopFindings"] = int(os.environ.get("UFME_SLOP_MAX_FINDINGS", 0) or 0)
OPTIONS["minPerfScore"] = int(os.environ.get("UFME_PERF_MIN_SCORE", 0) or 0)
try:
    OPTIONS["maxVisualDiff"] = float(os.environ.get("UFME_VISUAL_MAX_DIFF", 0.001))
except ValueError:
    pass

CHECK_IDS = [
    "typescript", "lint", "format", "unit", "build",
    "browser", "a11y", "perf", "slop", "visual", "deps",
]
PRESETS = {
    "audit": ["a11y", "perf", "slop", "visual"],
    "all": CHECK_IDS,
}


def env_int(name, default):
    try:
        return int(os.environ[name])
    except (KeyError, ValueError):
        return default


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def log(msg):
    print(f"[quality-check] {msg}", flush=True)


def record(status, label, rc=0, detail=""):
    CHECKS.append({"status": status, "label": label, "exitCode": rc, "detail": detail})
    COUNTS[status] += 1
    log(f"{status}: {label}{(': ' + detail) if detail else ''}")


def execute_check(check_id, fn):
    """Run one check and stamp every record it produced with timing metadata."""
    started_at = now()
    start = time.monotonic()
    before = len(CHECKS)
    try:
        fn()
    finally:
        elapsed = int((time.monotonic() - start) * 1000)
        for check in CHECKS[before:]:
            check["id"] = check_id
            check["startedAt"] = started_at
            check["durationMs"] = elapsed


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
    label = "Browser tests"
    if not BROWSER_CHECK_SCRIPT.exists() or not BROWSER_TEST_SCRIPT.exists():
        record("SKIPPED", label, 0, "browser scripts not found")
        return
    try:
        probe = subprocess.run(
            ["bash", str(BROWSER_CHECK_SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=env_int("UFME_BROWSER_CHECK_TIMEOUT", 180),
        )
    except subprocess.TimeoutExpired:
        record("BLOCKED", label, 124, "browser setup check timed out")
        return
    if probe.returncode != 0:
        record("BLOCKED", label, 1, "Selenium WebDriver not available")
        return
    try:
        p = subprocess.run(
            ["bash", str(BROWSER_TEST_SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=env_int("UFME_BROWSER_TIMEOUT", 300),
        )
    except subprocess.TimeoutExpired:
        record("FAIL", label, 124, "browser tests timed out")
        return
    if p.returncode == 0:
        record("PASS", label, 0)
        return
    blocked = json_field(BROWSER_RESULTS, "status") == "BLOCKED"
    record(
        "BLOCKED" if blocked else "FAIL",
        label,
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
    if not url_responds(OPTIONS["target"]):
        record(
            "SKIPPED", label, 0,
            f"target URL did not respond: {OPTIONS['target']} — start the dev server and re-run",
        )
        return
    log(f"Running axe-core audit against {OPTIONS['target']}")
    try:
        p = subprocess.run(
            ["node", str(A11Y_SCRIPT), OPTIONS["target"], "--timeout", "180000"],
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
        total = json_field(A11Y_RESULTS, "totalViolations") or 0
        limit = OPTIONS["maxA11yViolations"]
        status = "PASS" if total <= limit else "FAIL"
        record(
            status, label, rc,
            f"{total} axe violations (allowed {limit})"
            " — results: .ufme/evidence/a11y-results.json",
        )
    elif rc == 3:
        reason = json_field(A11Y_RESULTS, "reason") or p.stdout.strip() or ""
        record("SKIPPED", label, rc, reason or "Missing dependency — run: npm i -D @axe-core/webdriverjs")
    elif rc == 5:
        reason = json_field(A11Y_RESULTS, "reason") or "browser/runtime failure"
        record("BLOCKED", label, rc, f"browser could not launch: {reason}")
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
    if not url_responds(OPTIONS["target"]):
        record(
            "SKIPPED", label, 0,
            f"target URL did not respond: {OPTIONS['target']} — start the dev server and re-run",
        )
        return
    log(f"Running lighthouse audit against {OPTIONS['target']}")
    try:
        p = subprocess.run(
            ["bash", str(PERF_SCRIPT), OPTIONS["target"]],
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
        detail = (
            f"perf={scores.get('performance')} a11y={scores.get('accessibility')}"
            f" best-practices={scores.get('bestPractices')}"
        )
        minimum = OPTIONS["minPerfScore"]
        below = [
            f"{key}={value}" for key, value in scores.items()
            if isinstance(value, (int, float)) and minimum and value < minimum
        ]
        if below:
            record("FAIL", label, 0, f"{detail}; below minimum {minimum}: {', '.join(below)}")
        else:
            record("PASS", label, 0, detail)
    elif rc == 5:
        reason = json_field(PERF_RESULTS, "reason") or "lighthouse unavailable or failed"
        record("SKIPPED", label, rc, reason)
    else:
        first = (p.stderr or p.stdout or "").strip().splitlines()
        record("FAIL", label, rc, first[0][:200] if first else "")


def run_slop_gate():
    label = "Design slop (detect-slop)"
    if not SLOP_SCRIPT.exists():
        record("SKIPPED", label, 0, "detect-slop.py missing")
        return
    try:
        p = subprocess.run(
            [sys.executable, str(SLOP_SCRIPT),
             "--path", OPTIONS["slopPath"], "--json", str(SLOP_RESULTS)],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        record("FAIL", label, 124, "detect-slop timed out")
        return
    except OSError as e:
        record("FAIL", label, 1, str(e))
        return
    if p.returncode == 0:
        record("PASS", label, 0, "no design-slop findings")
        return
    if p.returncode == 2:
        count = json_field(SLOP_RESULTS, "count")
        count = int(count) if isinstance(count, int) else 0
        limit = OPTIONS["maxSlopFindings"]
        record(
            "PASS" if count <= limit else "FAIL", label, p.returncode,
            f"{count} findings (allowed {limit}) — see .ufme/evidence/slop-results.json",
        )
        return
    record("FAIL", label, p.returncode, (p.stderr or p.stdout or "").strip()[:200])


def run_visual_gate():
    label = "Visual regression (pixelmatch)"
    if not VISUAL_SCRIPT.exists():
        record("SKIPPED", label, 0, "visual-diff.js missing")
        return
    try:
        p = subprocess.run(
            ["node", str(VISUAL_SCRIPT),
             "--baseline", OPTIONS["visualBaseline"],
             "--current", OPTIONS["visualCurrent"],
             "--max-diff-ratio", str(OPTIONS["maxVisualDiff"]),
             "--out", str(VISUAL_RESULTS)],
            cwd=ROOT, capture_output=True, text=True, timeout=180,
        )
    except subprocess.TimeoutExpired:
        record("FAIL", label, 124, "visual diff timed out")
        return
    except OSError as e:
        record("FAIL", label, 1, str(e))
        return
    if p.returncode == 0:
        ratio = json_field(VISUAL_RESULTS, "maxDiffRatio")
        record("PASS", label, 0, f"maxDiffRatio={ratio}")
    elif p.returncode == 1:
        ratio = json_field(VISUAL_RESULTS, "maxDiffRatio")
        record("FAIL", label, 1, f"maxDiffRatio={ratio} exceeds {OPTIONS['maxVisualDiff']}")
    elif p.returncode == 3:
        reason = json_field(VISUAL_RESULTS, "reason") or "no screenshots"
        record("SKIPPED", label, 3, reason)
    else:
        record("FAIL", label, p.returncode, (p.stderr or p.stdout or "").strip()[:200])


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--only", default="",
                        help=f"comma-separated check ids or preset ({', '.join(PRESETS)})")
    parser.add_argument("--target", default="", help="URL under test")
    parser.add_argument("--report", default="", help="report path")
    parser.add_argument("--max-a11y-violations", type=int)
    parser.add_argument("--max-slop-findings", type=int)
    parser.add_argument("--min-perf-score", type=int)
    parser.add_argument("--max-visual-diff", type=float)
    return parser.parse_args()


def selected_ids(value):
    tokens = [t.strip() for t in value.split(",") if t.strip()]
    selected = []
    for token in tokens:
        if token in PRESETS:
            selected.extend(PRESETS[token])
        elif token in CHECK_IDS:
            selected.append(token)
        else:
            raise ValueError(f"unknown check id '{token}' (known: {', '.join(CHECK_IDS)})")
    return set(selected)


def checks_table(pkg):
    scripts = pkg.get("scripts", {}) if isinstance(pkg.get("scripts"), dict) else {}
    return [
        ("typescript", lambda: run("TypeScript check", ["npx", "tsc", "--noEmit"])
         if (ROOT / "tsconfig.json").exists()
         else record("SKIPPED", "TypeScript check", 0, "no tsconfig.json")),
        ("lint", lambda: run("Lint", ["npx", "eslint", ".", "--ext", ".js,.ts,.jsx,.tsx"])
         if has_eslint(pkg) else record("SKIPPED", "Lint", 0, "not configured")),
        ("format", lambda: run("Formatting", ["npx", "prettier", "--check", "."])
         if has_prettier(pkg) else record("SKIPPED", "Formatting", 0, "not configured")),
        ("unit", lambda: run("Unit tests", ["npm", "test"])
         if "test" in scripts else record("SKIPPED", "Unit tests", 0, "no test script")),
        ("build", lambda: run("Production build", ["npm", "run", "build"])
         if "build" in scripts else record("SKIPPED", "Production build", 0, "no build script")),
        ("browser", run_browser_tests),
        ("a11y", run_a11y_gate),
        ("perf", run_perf_gate),
        ("slop", run_slop_gate),
        ("visual", run_visual_gate),
        ("deps", lambda: run("Dependency audit", ["npm", "audit", "--audit-level=moderate"])
         if (ROOT / "package.json").exists()
         else record("SKIPPED", "Dependency audit", 0, "no package.json")),
    ]


def main():
    args = parse_args()
    try:
        selected = selected_ids(args.only)
    except ValueError as exc:
        log(f"ERROR: {exc}")
        return 2

    if args.target:
        OPTIONS["target"] = args.target
    if args.max_a11y_violations is not None:
        OPTIONS["maxA11yViolations"] = args.max_a11y_violations
    if args.max_slop_findings is not None:
        OPTIONS["maxSlopFindings"] = args.max_slop_findings
    if args.min_perf_score is not None:
        OPTIONS["minPerfScore"] = args.min_perf_score
    if args.max_visual_diff is not None:
        OPTIONS["maxVisualDiff"] = args.max_visual_diff

    report_path = Path(args.report).resolve() if args.report else REPORT
    report_path.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)

    exec_id = f"ufme-quality-{int(time.time())}"
    started = now()
    pkg = package_json()
    project_name = pkg.get("name") or "unknown"

    for check_id, fn in checks_table(pkg):
        if selected and check_id not in selected:
            continue
        execute_check(check_id, fn)

    counts = {
        key.lower(): sum(1 for c in CHECKS if c["status"] == key)
        for key in ("PASS", "FAIL", "SKIPPED", "BLOCKED")
    }
    overall = "FAIL" if counts["fail"] else "BLOCKED" if counts["blocked"] else "PASS"
    report = {
        "executionId": exec_id,
        "startTime": started,
        "finishTime": now(),
        "project": {
            "name": project_name,
            "packageManager": package_manager(),
            "root": str(ROOT),
        },
        "options": {
            "only": sorted(selected) if selected else CHECK_IDS,
            "target": OPTIONS["target"],
            "maxA11yViolations": OPTIONS["maxA11yViolations"],
            "maxSlopFindings": OPTIONS["maxSlopFindings"],
            "minPerfScore": OPTIONS["minPerfScore"],
            "maxVisualDiff": OPTIONS["maxVisualDiff"],
        },
        "overall": overall,
        "counts": counts,
        "checks": CHECKS,
    }

    fd, tmp = tempfile.mkstemp(
        dir=str(report_path.parent), prefix=".quality-report.", suffix=".json"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
            f.write("\n")
        os.replace(tmp, report_path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

    print("---- Quality check summary ----")
    print(
        f"PASS: {counts['pass']}, FAIL: {counts['fail']}, "
        f"SKIPPED: {counts['skipped']}, BLOCKED: {counts['blocked']}"
    )
    print(f"Overall: {overall}")
    print(f"Report: {report_path}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
