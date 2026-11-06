#!/usr/bin/env python3
"""
seo-plan.py — Generate prioritized SEO improvement plan.

Reads .ufme/evidence/seo-results.json and produces:
  .ufme/evidence/seo-plan.json — machine-readable plan
  .ufme/SEO_PLAN.md — human-readable plan

Usage:
  python3 ufmw_seo_protocol_skill/scripts/seo-plan.py [evidenceDir]
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UFME = ROOT / ".ufme"
EVIDENCE = Path(os.environ.get("UFME_EVIDENCE_DIR") or (UFME / "evidence"))

SEVERITY_ORDER = {"critical": 0, "major": 1, "minor": 2}


def load_results(evidence_dir):
    results_file = evidence_dir / "seo-results.json"
    if not results_file.exists():
        return None
    return json.loads(results_file.read_text(encoding="utf-8"))


def plan(results):
    """Generate prioritized improvement plan from SEO results."""
    issues = results.get("issues", [])

    # Group issues by priority
    priority_1 = []  # Critical
    priority_2 = []  # Major
    priority_3 = []  # Minor

    for issue in issues:
        sev = issue["severity"]
        entry = {
            "url": issue["url"],
            "issue": issue["issue"],
            "fix": issue["recommendation"],
            "severity": sev,
            "category": issue["category"],
            "status": "pending",
        }
        if sev == "critical":
            priority_1.append(entry)
        elif sev == "major":
            priority_2.append(entry)
        else:
            priority_3.append(entry)

    # Estimate effort per issue type
    effort_map = {
        "Missing title tag": "low",
        "Missing meta description": "low",
        "Missing H1 tag": "low",
        "Missing alt text": "low",
        "Missing canonical tag": "low",
        "Duplicate title": "medium",
        "Duplicate meta description": "medium",
        "Title too short": "low",
        "Title too long": "low",
        "Meta description too short": "low",
        "Meta description too long": "low",
        "Multiple H1 tags": "low",
        "Server error": "high",
        "Client error": "medium",
        "noindex meta tag": "low",
        "Thin content": "high",
        "Duplicate canonical URL": "low",
    }

    for entry in priority_1 + priority_2 + priority_3:
        entry["effort"] = effort_map.get(entry["fix"], "medium")
        entry["impact"] = {
            "critical": "high",
            "major": "medium",
            "minor": "low",
        }.get(entry["severity"], "medium")

    return {
        "startUrl": results.get("startUrl", ""),
        "baseDomain": results.get("baseDomain", ""),
        "pagesCrawled": results.get("pagesCrawled", 0),
        "totalOpportunities": len(issues),
        "priority1": priority_1,
        "priority2": priority_2,
        "priority3": priority_3,
        "plannedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main():
    evidence_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else EVIDENCE

    results = load_results(evidence_dir)
    if not results:
        print(f"[seo-plan] No seo-results.json found in {evidence_dir}")
        print("[seo-analyze] Run: python3 ufmw_seo_protocol_skill/scripts/seo-analyze.py")
        return 1

    plan_data = plan(results)

    evidence_dir.mkdir(parents=True, exist_ok=True)
    plan_file = evidence_dir / "seo-plan.json"
    plan_file.write_text(json.dumps(plan_data, indent=2), encoding="utf-8")

    # Generate human-readable SEO_PLAN.md
    md_lines = [
        "# SEO Improvement Plan",
        "",
        f"- **Target URL**: {plan_data['startUrl']}",
        f"- **Base domain**: {plan_data['baseDomain']}",
        f"- **Pages crawled**: {plan_data['pagesCrawled']}",
        f"- **Total opportunities**: {plan_data['totalOpportunities']}",
        "",
    ]

    # Priority 1
    md_lines.append("## Priority 1 — Critical (fix immediately)")
    md_lines.append("")
    md_lines.append("| # | URL | Issue | Fix | Effort | Impact | Status |")
    md_lines.append("|---|-----|-------|-----|--------|--------|--------|")
    for i, item in enumerate(plan_data["priority1"], 1):
        md_lines.append(
            f"| {i} | {item['url']} | {item['issue']} | {item['fix']} | "
            f"{item['effort']} | {item['impact']} | {item['status']} |"
        )
    md_lines.append("")

    # Priority 2
    md_lines.append("## Priority 2 — Major (fix this sprint)")
    md_lines.append("")
    md_lines.append("| # | URL | Issue | Fix | Effort | Impact | Status |")
    md_lines.append("|---|-----|-------|-----|--------|--------|--------|")
    for i, item in enumerate(plan_data["priority2"], 1):
        md_lines.append(
            f"| {i} | {item['url']} | {item['issue']} | {item['fix']} | "
            f"{item['effort']} | {item['impact']} | {item['status']} |"
        )
    md_lines.append("")

    # Priority 3
    md_lines.append("## Priority 3 — Minor (fix next cycle)")
    md_lines.append("")
    md_lines.append("| # | URL | Issue | Fix | Effort | Impact | Status |")
    md_lines.append("|---|-----|-------|-----|--------|--------|--------|")
    for i, item in enumerate(plan_data["priority3"], 1):
        md_lines.append(
            f"| {i} | {item['url']} | {item['issue']} | {item['fix']} | "
            f"{item['effort']} | {item['impact']} | {item['status']} |"
        )
    md_lines.append("")

    # Acceptance criteria
    md_lines.append("## Acceptance Criteria")
    md_lines.append("")
    md_lines.append("- [ ] All critical issues resolved")
    md_lines.append("- [ ] All major issues resolved")
    md_lines.append("- [ ] All pages have unique titles and meta descriptions")
    md_lines.append("- [ ] All images have alt text")
    md_lines.append("- [ ] No broken internal links")
    md_lines.append("- [ ] Sitemap submitted and valid")
    md_lines.append("- [ ] Structured data validated")
    md_lines.append("")

    md_file = UFME / "SEO_PLAN.md"
    UFME.mkdir(parents=True, exist_ok=True)
    md_file.write_text("\n".join(md_lines), encoding="utf-8")

    p1 = len(plan_data["priority1"])
    p2 = len(plan_data["priority2"])
    p3 = len(plan_data["priority3"])
    print(f"[seo-plan] Generated plan: {p1} critical, {p2} major, {p3} minor")
    print(f"[seo-plan] Plan: {plan_file}")
    print(f"[seo-plan] Summary: {md_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
