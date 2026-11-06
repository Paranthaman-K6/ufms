#!/usr/bin/env python3
"""
seo-report.py — Generate comprehensive SEO audit report.

Combines crawl, analysis, plan, and verification results into a
final SEO_AUDIT_REPORT.md.

Usage:
  python3 skills/ufmw-seo-protocol/scripts/seo-report.py [evidenceDir]
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UFME = ROOT / ".ufme"
EVIDENCE = Path(os.environ.get("UFME_EVIDENCE_DIR") or (UFME / "evidence"))


def load_json(evidence_dir, filename):
    f = evidence_dir / filename
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return None


def main():
    evidence_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else EVIDENCE

    crawl = load_json(evidence_dir, "seo-crawl.json")
    results = load_json(evidence_dir, "seo-results.json")
    plan = load_json(evidence_dir, "seo-plan.json")
    verify = load_json(evidence_dir, "seo-verify.json")

    if not results:
        print(f"[seo-report] No seo-results.json found in {evidence_dir}")
        print("[seo-report] Run: python3 skills/ufmw-seo-protocol/scripts/seo-analyze.py")
        return 1

    md_lines = [
        "# SEO Audit Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        f"## Target: {results.get('startUrl', 'unknown')}",
        "",
    ]

    # Summary
    md_lines.append("## Summary")
    md_lines.append("")
    md_lines.append(f"- **Pages crawled**: {results.get('pagesCrawled', 0)}")
    md_lines.append(f"- **Total issues**: {results.get('totalIssues', 0)}")
    md_lines.append(f"- **Critical**: {results.get('issuesBySeverity', {}).get('critical', 0)}")
    md_lines.append(f"- **Major**: {results.get('issuesBySeverity', {}).get('major', 0)}")
    md_lines.append(f"- **Minor**: {results.get('issuesBySeverity', {}).get('minor', 0)}")
    md_lines.append("")

    # Verification
    if verify:
        md_lines.append("## Verification")
        md_lines.append("")
        md_lines.append(f"- **Issues before**: {verify.get('beforeIssues', 0)}")
        md_lines.append(f"- **Issues after**: {verify.get('afterIssues', 0)}")
        md_lines.append(f"- **Resolved**: {verify.get('resolved', 0)}")
        md_lines.append(f"- **Remaining**: {verify.get('remaining', 0)}")
        md_lines.append(f"- **All resolved**: {'Yes' if verify.get('allResolved') else 'No'}")
        md_lines.append("")

    # Top issues
    md_lines.append("## Top Issues")
    md_lines.append("")
    issues = results.get("issues", [])
    if issues:
        md_lines.append("| Severity | URL | Issue | Recommendation |")
        md_lines.append("|----------|-----|-------|----------------|")
        for issue in issues[:15]:
            md_lines.append(
                f"| {issue['severity'].title()} | {issue['url']} | {issue['issue']} | {issue['recommendation']} |"
            )
    else:
        md_lines.append("No issues found!")
    md_lines.append("")

    # Plan status
    if plan:
        md_lines.append("## Improvement Plan Status")
        md_lines.append("")
        p1 = len(plan.get("priority1", []))
        p2 = len(plan.get("priority2", []))
        p3 = len(plan.get("priority3", []))
        md_lines.append(f"- **Critical (P1)**: {p1}")
        md_lines.append(f"- **Major (P2)**: {p2}")
        md_lines.append(f"- **Minor (P3)**: {p3}")
        md_lines.append("")

    # Recommendations
    md_lines.append("## Recommendations")
    md_lines.append("")
    md_lines.append("1. Fix all critical issues first (server errors, noindex tags)")
    md_lines.append("2. Add missing titles, meta descriptions, and H1 tags")
    md_lines.append("3. Add alt text to all images")
    md_lines.append("4. Add canonical tags to prevent duplicate content")
    md_lines.append("5. Validate structured data (JSON-LD)")
    md_lines.append("6. Re-crawl after fixes to verify resolution")
    md_lines.append("")

    report = "\n".join(md_lines)

    evidence_dir.mkdir(parents=True, exist_ok=True)
    report_file = evidence_dir / "seo-report.json"
    report_file.write_text(json.dumps({
        "url": results.get("startUrl", ""),
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "totalIssues": results.get("totalIssues", 0),
        "issuesBySeverity": results.get("issuesBySeverity", {}),
        "verification": verify,
    }, indent=2), encoding="utf-8")

    md_path = UFME / "SEO_AUDIT_REPORT.md"
    UFME.mkdir(parents=True, exist_ok=True)
    md_path.write_text(report, encoding="utf-8")

    print(f"[seo-report] Report generated: {md_path}")
    print(f"[seo-report] Evidence: {report_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
