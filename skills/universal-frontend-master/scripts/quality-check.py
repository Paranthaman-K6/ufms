#!/usr/bin/env python3
"""
quality-check.py — genuine quality gate.

Runs type check, lint, formatting, unit tests, build, browser tests,
accessibility, performance, design-slop and visual-diff checks, then a
dependency audit. Records every check as PASS/FAIL/SKIPPED/BLOCKED with
start time and duration, and writes .ufme/evidence/quality-report.json.

Exits non-zero when any mandatory check FAILs or is BLOCKED. Required checks
(--require, or the audit preset) never PASS on SKIPPED or invalid evidence.

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

ROOT = Path(__file__).resolve().parents[3]
UFME = ROOT / ".ufme"
EVIDENCE = Path(os.environ.get("UFME_EVIDENCE_DIR") or (UFME / "evidence"))
REPORT = EVIDENCE / "quality-report.json"
BROWSER_RESULTS = EVIDENCE / "browser-results.json"

SCRIPTS_DIR = ROOT / "skills/universal-frontend-master" / "scripts"
A11Y_SCRIPT = Path(os.environ.get("UFME_A11Y_SCRIPT") or (SCRIPTS_DIR / "audit-a11y.js"))
A11Y_RESULTS = Path(os.environ.get("UFME_A11Y_RESULTS") or (EVIDENCE / "a11y-results.json"))
PERF_SCRIPT = Path(os.environ.get("UFME_PERF_SCRIPT") or (SCRIPTS_DIR / "audit-perf.sh"))
PERF_RESULTS = Path(os.environ.get("UFME_PERF_RESULTS") or (EVIDENCE / "perf-results.json"))
SLOP_SCRIPT = Path(os.environ.get("UFME_SLOP_SCRIPT") or (SCRIPTS_DIR / "detect-slop.py"))
SLOP_RESULTS = Path(os.environ.get("UFME_SLOP_RESULTS") or (EVIDENCE / "slop-results.json"))
VISUAL_SCRIPT = Path(os.environ.get("UFME_VISUAL_SCRIPT") or (SCRIPTS_DIR / "visual-diff.js"))
VISUAL_RESULTS = Path(os.environ.get("UFME_VISUAL_RESULTS") or (EVIDENCE / "visual-diff.json"))
BROWSER_CHECK_SCRIPT = Path(
    os.environ.get("UFME_BROWSER_CHECK_SCRIPT")
    or (SCRIPTS_DIR / "check-native-browser.sh")
)
BROWSER_TEST_SCRIPT = Path(
    os.environ.get("UFME_BROWSER_TEST_SCRIPT")
    or (SCRIPTS_DIR / "browser-test.sh")
)

SEO_CRAWL_SCRIPT = Path(
    os.environ.get("UFME_SEO_CRAWL_SCRIPT")
    or (ROOT / "skills/ufmw-seo-protocol" / "scripts" / "seo-crawl.py")
)
SEO_ANALYZE_SCRIPT = Path(
    os.environ.get("UFME_SEO_ANALYZE_SCRIPT")
    or (ROOT / "skills/ufmw-seo-protocol" / "scripts" / "seo-analyze.py")
)
SEO_RESULTS = Path(os.environ.get("UFME_SEO_RESULTS") or (EVIDENCE / "seo-results.json"))

TARGET_URL = os.environ.get("UFME_AUDIT_URL") or "http://localhost:5173"

CHECKS = []
COUNTS = {"PASS": 0, "FAIL": 0, "SKIPPED": 0, "BLOCKED": 0}
REQUIRED = set()

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
OPTIONS["minPerfScore"] = int(
    os.environ.get("UFME_LH_MIN_SCORE") or os.environ.get("UFME_PERF_MIN_SCORE") or 0
)
try:
    OPTIONS["maxVisualDiff"] = float(os.environ.get("UFME_VISUAL_MAX_DIFF", 0.001))
except ValueError:
    pass

CHECK_IDS = [
    "typescript", "lint", "format", "unit", "build",
    "browser", "a11y", "perf", "slop", "visual", "deps", "seo",
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
    started = time.time()
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
    data, problem = read_evidence(BROWSER_RESULTS, started)
    if p.returncode == 0:
        if problem or data.get("status") != "PASS":
            record("FAIL", label, 0, problem or f"exit 0 without PASS evidence (status={data.get('status')})")
            return
        record("PASS", label, 0)
        return
    blocked = (data or {}).get("status") == "BLOCKED"
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


def read_evidence(path, started=None):
    """Return (data, problem). Evidence must exist, parse, and be written by this run."""
    if not path.exists():
        return None, f"evidence missing: {path}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, f"evidence is not valid JSON: {path}"
    if not isinstance(data, dict):
        return None, f"evidence is not a JSON object: {path}"
    if started is not None and path.stat().st_mtime < started - 2:
        return data, f"evidence is stale (not written by this run): {path}"
    return data, None


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


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
    started = time.time()
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
    if rc in (0, 1):
        data, problem = read_evidence(A11Y_RESULTS, started)
        total = (data or {}).get("totalViolations")
        if problem:
            record("FAIL", label, rc, problem)
        elif (data.get("status") != "RAN"
              or not isinstance(total, int) or isinstance(total, bool)
              or not isinstance(data.get("violationsByRule"), list)):
            record("FAIL", label, rc, "invalid axe evidence: expected status=RAN, "
                                      "integer totalViolations and violationsByRule[]")
        elif rc == 0 and total != 0:
            record("FAIL", label, rc, f"exit 0 but evidence reports {total} violations")
        elif rc == 1 and total == 0:
            record("FAIL", label, rc, "exit 1 but evidence reports 0 violations")
        else:
            limit = OPTIONS["maxA11yViolations"]
            status = "PASS" if total <= limit else "FAIL"
            record(status, label, rc,
                   f"{total} axe violations (allowed {limit}) — results: {A11Y_RESULTS}")
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
            "FAIL", label, 0,
            f"target URL did not respond: {OPTIONS['target']} — the site under test is unreachable",
        )
        return
    log(f"Running lighthouse audit against {OPTIONS['target']}")
    started = time.time()
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
    data, problem = read_evidence(PERF_RESULTS, started)
    reason = json_field(PERF_RESULTS, "reason") if data else ""
    expected = {0: "RAN", 4: "FAIL", 5: "SKIPPED", 6: "BLOCKED"}.get(rc)
    if expected is None:
        first = (p.stderr or p.stdout or "").strip().splitlines()
        record("FAIL", label, rc, first[0][:200] if first else "")
        return
    status = (data or {}).get("status")
    if status != expected:
        record("FAIL", label, rc,
               f"exit {rc} contradicts evidence status {status or 'missing'}")
        return
    if rc == 5:
        record("SKIPPED", label, rc, reason or "lighthouse unavailable")
        return
    if rc == 6:
        record("BLOCKED", label, rc, reason or "browser environment unsupported")
        return
    if rc == 4:
        record("FAIL", label, rc, reason or "lighthouse audit failed")
        return
    scores = (data or {}).get("scores")
    required = ("performance", "accessibility", "bestPractices")
    if problem or not isinstance(scores, dict) or any(
        not is_number(scores.get(key)) or not 0 <= scores.get(key) <= 100
        for key in required
    ):
        record("FAIL", label, rc,
               problem or "invalid lighthouse evidence: expected RAN and numeric "
               "performance/accessibility/best-practices scores in 0-100")
        return
    detail = (
        f"perf={scores.get('performance')} a11y={scores.get('accessibility')}"
        f" best-practices={scores.get('bestPractices')}"
    )
    minimum = OPTIONS["minPerfScore"]
    below = [f"{key}={scores[key]}" for key in required if minimum and scores[key] < minimum]
    if below:
        record("FAIL", label, 0, f"{detail}; below minimum {minimum}: {', '.join(below)}")
    else:
        record("PASS", label, 0, detail)


def run_slop_gate():
    label = "Design slop (detect-slop)"
    if not SLOP_SCRIPT.exists():
        record("SKIPPED", label, 0, "detect-slop.py missing")
        return
    started = time.time()
    cmd = [sys.executable, str(SLOP_SCRIPT),
           "--path", OPTIONS["slopPath"], "--json", str(SLOP_RESULTS)]
    if os.environ.get("UFME_SLOP_SKIP_DESIGN") == "1":
        cmd += ["--no-design"]
    else:
        # Always pass the path: a missing design system is a failure, not a skip.
        cmd += ["--design", str(Path(OPTIONS["slopPath"]) / ".ufme" / "DESIGN_SYSTEM.md")]
    try:
        p = subprocess.run(
            cmd,
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        record("FAIL", label, 124, "detect-slop timed out")
        return
    except OSError as e:
        record("FAIL", label, 1, str(e))
        return
    if p.returncode in (0, 2):
        data, problem = read_evidence(SLOP_RESULTS, started)
        count = (data or {}).get("count")
        if problem:
            record("FAIL", label, p.returncode, problem)
            return
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            record("FAIL", label, p.returncode,
                   "invalid slop evidence: expected an integer count")
            return
        if p.returncode == 0 and count != 0:
            record("FAIL", label, 0, f"exit 0 but evidence reports {count} findings")
            return
        limit = OPTIONS["maxSlopFindings"]
        record(
            "PASS" if count <= limit else "FAIL", label, p.returncode,
            f"{count} findings (allowed {limit}) — see {SLOP_RESULTS}",
        )
        return
    record("FAIL", label, p.returncode, (p.stderr or p.stdout or "").strip()[:200])


def run_visual_gate():
    label = "Visual regression (pixelmatch)"
    if not VISUAL_SCRIPT.exists():
        record("SKIPPED", label, 0, "visual-diff.js missing")
        return
    started = time.time()
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
    if p.returncode in (0, 1):
        data, problem = read_evidence(VISUAL_RESULTS, started)
        ratio = (data or {}).get("maxDiffRatio")
        if problem:
            record("FAIL", label, p.returncode, problem)
        elif data.get("status") == "BASELINE_CREATED":
            record("BLOCKED", label, p.returncode,
                   "baseline was auto-created; inspect it, commit it, then rerun")
        elif p.returncode == 0 and data.get("status") != "PASS":
            record("FAIL", label, 0, f"exit 0 with status={data.get('status')}")
        elif not is_number(ratio):
            record("FAIL", label, p.returncode, "invalid visual evidence: maxDiffRatio missing")
        elif p.returncode == 0 and ratio > OPTIONS["maxVisualDiff"]:
            record("FAIL", label, 0, f"maxDiffRatio={ratio} exceeds {OPTIONS['maxVisualDiff']}")
        elif p.returncode == 1 and ratio <= OPTIONS["maxVisualDiff"]:
            record("FAIL", label, 1, "exit 1 but maxDiffRatio is within threshold")
        else:
            record("PASS" if p.returncode == 0 else "FAIL", label, p.returncode,
                   f"maxDiffRatio={ratio} (threshold {OPTIONS['maxVisualDiff']})")
    elif p.returncode == 3:
        reason = json_field(VISUAL_RESULTS, "reason") or "no screenshots"
        record("SKIPPED", label, 3, reason)
    elif p.returncode == 4:
        reason = json_field(VISUAL_RESULTS, "reason") or "baseline missing"
        record("BLOCKED", label, 4, f"no visual baseline: {reason}")
    elif p.returncode == 2:
        first = (p.stderr or p.stdout or "").strip().splitlines()
        record("FAIL", label, 2, first[0][:200] if first else "invalid visual invocation")
    else:
        record("FAIL", label, p.returncode, (p.stderr or p.stdout or "").strip()[:200])


def run_seo_gate():
    label = "SEO audit"
    if not SEO_CRAWL_SCRIPT.exists() or not SEO_ANALYZE_SCRIPT.exists():
        record("SKIPPED", label, 0, "SEO crawl/analyze scripts not found")
        return
    if not url_responds(OPTIONS["target"]):
        record(
            "SKIPPED", label, 0,
            f"target URL did not respond: {OPTIONS['target']} — start the dev server and re-run",
        )
        return
    log(f"Running SEO crawl against {OPTIONS['target']}")
    started = time.time()
    try:
        p = subprocess.run(
            [sys.executable, str(SEO_CRAWL_SCRIPT), OPTIONS["target"], "50"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        record("FAIL", label, 124, "SEO crawl timed out after 300s")
        return
    except OSError as e:
        record("FAIL", label, 1, str(e))
        return
    if p.returncode != 0:
        record("FAIL", label, p.returncode, (p.stderr or p.stdout or "").strip()[:200])
        return
    # Run analysis
    try:
        p2 = subprocess.run(
            [sys.executable, str(SEO_ANALYZE_SCRIPT), str(EVIDENCE)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        record("FAIL", label, 124, "SEO analyze timed out after 60s")
        return
    except OSError as e:
        record("FAIL", label, 1, str(e))
        return
    if p2.returncode != 0:
        record("FAIL", label, p2.returncode, (p2.stderr or p2.stdout or "").strip()[:200])
        return
    data, problem = read_evidence(SEO_RESULTS, started)
    if problem:
        record("FAIL", label, 0, problem)
        return
    total = (data or {}).get("totalIssues", 0)
    if not isinstance(total, int) or isinstance(total, bool):
        record("FAIL", label, 0, "invalid SEO evidence: expected integer totalIssues")
        return
    issues_by_sev = (data or {}).get("issuesBySeverity", {})
    critical = issues_by_sev.get("critical", 0)
    major = issues_by_sev.get("major", 0)
    minor = issues_by_sev.get("minor", 0)
    record(
        "PASS" if total == 0 else "FAIL", label, 0,
        f"{total} SEO issues (critical={critical}, major={major}, minor={minor}) — results: {SEO_RESULTS}"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--only", default="",
                        help=f"comma-separated check ids or preset ({', '.join(PRESETS)})")
    parser.add_argument("--require", default="",
                        help="comma-separated check ids or preset that must PASS; "
                             "a skipped required check BLOCKS the gate")
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
        ("seo", run_seo_gate),
    ]


def main():
    args = parse_args()
    try:
        selected = selected_ids(args.only)
        require_value = args.require or os.environ.get("UFME_REQUIRE_CHECKS", "")
        required = selected_ids(require_value) if require_value else set()
    except ValueError as exc:
        log(f"ERROR: {exc}")
        return 2
    if not required and selected == set(PRESETS["audit"]):
        required = set(PRESETS["audit"])
    REQUIRED.update(required)
    if selected and not required <= selected:
        log(f"ERROR: required checks not selected: {', '.join(sorted(required - selected))}")
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
    required_not_passed = [
        c["id"] for c in CHECKS if c["id"] in REQUIRED and c["status"] != "PASS"
    ]
    if counts["fail"]:
        overall = "FAIL"
    elif counts["blocked"] or required_not_passed:
        overall = "BLOCKED"
    else:
        overall = "PASS"
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
        "required": sorted(REQUIRED),
        "requiredNotPassed": sorted(set(required_not_passed)),
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
