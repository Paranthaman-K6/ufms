#!/usr/bin/env python3
"""
seo-monitor.py — Monitor SEO metrics over time.

Records crawl results and compares against previous measurements to
track SEO progress.

Usage:
  python3 ufmw_seo_protocol_skill/scripts/seo-monitor.py <url> [evidenceDir]
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UFME = ROOT / ".ufme"
EVIDENCE = Path(os.environ.get("UFME_EVIDENCE_DIR") or (UFME / "evidence"))
METRICS_FILE = UFME / "SEO_METRICS.md"
METRICS_JSON = EVIDENCE / "seo-metrics.json"


def load_metrics_history():
    if METRICS_JSON.exists():
        return json.loads(METRICS_JSON.read_text(encoding="utf-8"))
    return {"measurements": []}


def save_metrics_history(history):
    UFME.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    METRICS_JSON.write_text(json.dumps(history, indent=2), encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 seo-monitor.py <url> [evidenceDir]")
        sys.exit(2)

    url = sys.argv[1]
    evidence_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else EVIDENCE

    # Run crawl
    crawl_script = ROOT / "ufmw_seo_protocol_skill" / "scripts" / "seo-crawl.py"
    print(f"[seo-monitor] Crawling {url}...")
    result = subprocess.run(
        [sys.executable, str(crawl_script), url],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        print(f"[seo-monitor] Crawl failed: {result.stderr}")
        return 1

    # Run analysis
    analyze_script = ROOT / "ufmw_seo_protocol_skill" / "scripts" / "seo-analyze.py"
    result2 = subprocess.run(
        [sys.executable, str(analyze_script), str(evidence_dir)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    # Load current results
    results_file = evidence_dir / "seo-results.json"
    if not results_file.exists():
        print("[seo-monitor] No results found after analysis.")
        return 1

    current = json.loads(results_file.read_text(encoding="utf-8"))

    # Load history
    history = load_metrics_history()

    # Add new measurement
    measurement = {
        "url": url,
        "measuredAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pagesCrawled": current.get("pagesCrawled", 0),
        "totalIssues": current.get("totalIssues", 0),
        "critical": current.get("issuesBySeverity", {}).get("critical", 0),
        "major": current.get("issuesBySeverity", {}).get("major", 0),
        "minor": current.get("issuesBySeverity", {}).get("minor", 0),
    }
    history["measurements"].append(measurement)

    # Keep only last 50 measurements
    history["measurements"] = history["measurements"][-50:]

    save_metrics_history(history)

    # Generate markdown
    md_lines = [
        "# SEO Metrics",
        "",
        f"- **Target URL**: {url}",
        f"- **Last measured**: {measurement['measuredAt']}",
        "",
        "## Historical Metrics",
        "",
        "| Date | Pages | Issues | Critical | Major | Minor |",
        "|------|-------|--------|----------|-------|-------|",
    ]

    for m in history["measurements"]:
        md_lines.append(
            f"| {m['measuredAt'][:10]} | {m['pagesCrawled']} | {m['totalIssues']} | "
            f"{m['critical']} | {m['major']} | {m['minor']} |"
        )

    md_lines.append("")
    md_lines.append("## Current Metrics")
    md_lines.append("")
    md_lines.append(f"- **Pages crawled**: {measurement['pagesCrawled']}")
    md_lines.append(f"- **Total issues**: {measurement['totalIssues']}")
    md_lines.append(f"- **Critical**: {measurement['critical']}")
    md_lines.append(f"- **Major**: {measurement['major']}")
    md_lines.append(f"- **Minor**: {measurement['minor']}")
    md_lines.append("")

    # Trend
    if len(history["measurements"]) > 1:
        prev = history["measurements"][-2]
        change = measurement["totalIssues"] - prev["totalIssues"]
        trend = "improving" if change < 0 else "worsening" if change > 0 else "stable"
        md_lines.append(f"## Trend: {trend} (change: {change:+d} issues)")

    METRICS_FILE.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"[seo-monitor] Measured: {measurement['totalIssues']} issues")
    print(f"[seo-monitor] History: {len(history['measurements'])} measurements")
    print(f"[seo-monitor] Report: {METRICS_FILE}")
    print(f"[seo-monitor] Data: {METRICS_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
