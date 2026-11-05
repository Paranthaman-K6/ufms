#!/usr/bin/env python3
"""
seo-verify.py — Re-crawl website and verify SEO fixes.

Compares before/after crawl data to verify that issues have been resolved.

Usage:
  python3 ufmw_seo_protocol_skill/scripts/seo-verify.py <url> [evidenceDir]
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UFME = ROOT / ".ufme"
EVIDENCE = Path(os.environ.get("UFME_EVIDENCE_DIR") or (UFME / "evidence"))


def load_json(evidence_dir, filename):
    f = evidence_dir / filename
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return None


def verify(evidence_dir=EVIDENCE, url=None):
    """Verify SEO fixes by comparing crawl results."""
    # Run a fresh crawl
    import subprocess
    crawl_script = ROOT / "ufmw_seo_protocol_skill" / "scripts" / "seo-crawl.py"
    print(f"[seo-verify] Re-crawling {url}...")
    result = subprocess.run(
        [sys.executable, str(crawl_script), url],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        print(f"[seo-verify] Crawl failed: {result.stderr}")
        return 1

    # Load before and after
    before = load_json(evidence_dir, "seo-results.json")
    after_crawl = load_json(evidence_dir, "seo-crawl.json")

    if not before:
        print("[seo-verify] No previous seo-results.json found. Cannot compare.")
        print("[seo-verify] Run seo-analyze.py first to establish baseline.")
        return 1

    if not after_crawl:
        print("[seo-verify] No new crawl data found.")
        return 1

    # Re-run analysis on new crawl
    analyze_script = ROOT / "ufmw_seo_protocol_skill" / "scripts" / "seo-analyze.py"
    result2 = subprocess.run(
        [sys.executable, str(analyze_script), str(evidence_dir)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    after = load_json(evidence_dir, "seo-results.json")
    if not after:
        print("[seo-verify] Failed to analyze new crawl.")
        return 1

    # Compare
    before_issues = before.get("totalIssues", 0)
    after_issues = after.get("totalIssues", 0)
    resolved = before_issues - after_issues

    before_by_sev = before.get("issuesBySeverity", {})
    after_by_sev = after.get("issuesBySeverity", {})

    verification = {
        "url": url,
        "verifiedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "beforeIssues": before_issues,
        "afterIssues": after_issues,
        "resolved": resolved,
        "remaining": after_issues,
        "bySeverity": {
            "critical": {
                "before": before_by_sev.get("critical", 0),
                "after": after_by_sev.get("critical", 0),
                "resolved": before_by_sev.get("critical", 0) - after_by_sev.get("critical", 0),
            },
            "major": {
                "before": before_by_sev.get("major", 0),
                "after": after_by_sev.get("major", 0),
                "resolved": before_by_sev.get("major", 0) - after_by_sev.get("major", 0),
            },
            "minor": {
                "before": before_by_sev.get("minor", 0),
                "after": after_by_sev.get("minor", 0),
                "resolved": before_by_sev.get("minor", 0) - after_by_sev.get("minor", 0),
            },
        },
        "pagesCrawledBefore": before.get("pagesCrawled", 0),
        "pagesCrawledAfter": after.get("pagesCrawled", 0),
        "allResolved": after_issues == 0,
    }

    evidence_dir.mkdir(parents=True, exist_ok=True)
    verify_file = evidence_dir / "seo-verify.json"
    verify_file.write_text(json.dumps(verification, indent=2), encoding="utf-8")

    # Generate markdown
    md_lines = [
        "# SEO Verification Results",
        "",
        f"- **Target URL**: {url}",
        f"- **Verified**: {verification['verifiedAt']}",
        f"- **Issues before fix**: {before_issues}",
        f"- **Issues after fix**: {after_issues}",
        f"- **Issues resolved**: {resolved}",
        f"- **Issues remaining**: {after_issues}",
        f"- **All resolved**: {'Yes' if verification['allResolved'] else 'No'}",
        "",
        "## By Severity",
        "",
        "| Severity | Before | After | Resolved |",
        "|----------|--------|-------|----------|",
    ]

    for sev in ("critical", "major", "minor"):
        b = verification["bySeverity"][sev]["before"]
        a = verification["bySeverity"][sev]["after"]
        r = verification["bySeverity"][sev]["resolved"]
        md_lines.append(f"| {sev.title()} | {b} | {a} | {r} |")

    md_lines.append("")
    md_lines.append("## Remaining Issues")
    md_lines.append("")
    remaining = [i for i in after.get("issues", [])]
    if remaining:
        for issue in remaining[:10]:
            md_lines.append(f"- **{issue['severity'].upper()}** | {issue['url']} | {issue['issue']}")
    else:
        md_lines.append("- None — all issues resolved!")

    md_file = UFME / "SEO_RESULTS.md"
    UFME.mkdir(parents=True, exist_ok=True)
    md_file.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"[seo-verify] Before: {before_issues} issues, After: {after_issues} issues, Resolved: {resolved}")
    print(f"[seo-verify] Results: {verify_file}")
    print(f"[seo-verify] Summary: {md_file}")
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 seo-verify.py <url> [evidenceDir]")
        sys.exit(2)

    url = sys.argv[1]
    evidence_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else EVIDENCE
    sys.exit(verify(evidence_dir, url))


if __name__ == "__main__":
    sys.exit(main())
