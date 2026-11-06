#!/usr/bin/env python3
"""
seo-analyze.py — Analyze crawl data for SEO issues.

Reads .ufme/evidence/seo-crawl.json and produces:
  .ufme/evidence/seo-results.json — machine-readable analysis
  .ufme/SEO_AUDIT.md — human-readable findings

Usage:
  python3 ufmw_seo_protocol_skill/scripts/seo-analyze.py [evidenceDir]
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


def load_crawl(evidence_dir):
    crawl_file = evidence_dir / "seo-crawl.json"
    if not crawl_file.exists():
        return None
    return json.loads(crawl_file.read_text(encoding="utf-8"))


def analyze(crawl_data):
    """Analyze crawl data and return SEO issues."""
    issues = []
    pages = crawl_data.get("pages", [])

    # Track titles and meta descriptions for duplicate detection
    titles = {}
    meta_descs = {}
    canonicals = {}

    for p in pages:
        url = p.get("url", "")
        status = p.get("status", 0)

        # Status code issues
        if status >= 500:
            issues.append({
                "severity": "critical",
                "category": "technical",
                "url": url,
                "issue": f"Server error (HTTP {status})",
                "recommendation": "Fix server configuration or application errors",
            })
        elif status >= 400:
            issues.append({
                "severity": "major",
                "category": "technical",
                "url": url,
                "issue": f"Client error (HTTP {status})",
                "recommendation": "Fix broken links or remove dead pages",
            })
        elif status >= 300:
            issues.append({
                "severity": "minor",
                "category": "technical",
                "url": url,
                "issue": f"Redirect (HTTP {status})",
                "recommendation": "Ensure redirects point to final destination",
            })

        # Title issues
        title = p.get("title", "").strip()
        if not title:
            issues.append({
                "severity": "major",
                "category": "on-page",
                "url": url,
                "issue": "Missing title tag",
                "recommendation": "Add a unique, descriptive title (30-60 chars)",
            })
        else:
            if title in titles:
                issues.append({
                    "severity": "major",
                    "category": "on-page",
                    "url": url,
                    "issue": f"Duplicate title: '{title}'",
                    "recommendation": "Make each page title unique",
                })
            else:
                titles[title] = url
            if len(title) < 30:
                issues.append({
                    "severity": "minor",
                    "category": "on-page",
                    "url": url,
                    "issue": f"Title too short ({len(title)} chars)",
                    "recommendation": "Expand title to 30-60 chars",
                })
            elif len(title) > 60:
                issues.append({
                    "severity": "minor",
                    "category": "on-page",
                    "url": url,
                    "issue": f"Title too long ({len(title)} chars)",
                    "recommendation": "Shorten title to 30-60 chars",
                })

        # Meta description issues
        meta_desc = p.get("metaDescription", "").strip()
        if not meta_desc:
            issues.append({
                "severity": "major",
                "category": "on-page",
                "url": url,
                "issue": "Missing meta description",
                "recommendation": "Add a unique meta description (50-160 chars)",
            })
        else:
            if meta_desc in meta_descs:
                issues.append({
                    "severity": "major",
                    "category": "on-page",
                    "url": url,
                    "issue": f"Duplicate meta description",
                    "recommendation": "Make each meta description unique",
                })
            else:
                meta_descs[meta_desc] = url
            if len(meta_desc) < 50:
                issues.append({
                    "severity": "minor",
                    "category": "on-page",
                    "url": url,
                    "issue": f"Meta description too short ({len(meta_desc)} chars)",
                    "recommendation": "Expand to 50-160 chars",
                })
            elif len(meta_desc) > 160:
                issues.append({
                    "severity": "minor",
                    "category": "on-page",
                    "url": url,
                    "issue": f"Meta description too long ({len(meta_desc)} chars)",
                    "recommendation": "Shorten to 50-160 chars",
                })

        # H1 issues
        headings = p.get("headings", {})
        h1s = headings.get("h1", [])
        if len(h1s) == 0:
            issues.append({
                "severity": "major",
                "category": "on-page",
                "url": url,
                "issue": "Missing H1 tag",
                "recommendation": "Add exactly one H1 per page",
            })
        elif len(h1s) > 1:
            issues.append({
                "severity": "minor",
                "category": "on-page",
                "url": url,
                "issue": f"Multiple H1 tags ({len(h1s)})",
                "recommendation": "Use only one H1 per page",
            })

        # Canonical issues
        canonical = p.get("canonical", "").strip()
        if not canonical:
            issues.append({
                "severity": "minor",
                "category": "technical",
                "url": url,
                "issue": "Missing canonical tag",
                "recommendation": "Add canonical URL to prevent duplicate content",
            })
        else:
            if canonical in canonicals:
                issues.append({
                    "severity": "minor",
                    "category": "technical",
                    "url": url,
                    "issue": "Duplicate canonical URL",
                    "recommendation": "Ensure each page has a unique canonical",
                })
            else:
                canonicals[canonical] = url

        # Meta robots issues
        robots = p.get("metaRobots", "").strip().lower()
        if "noindex" in robots:
            issues.append({
                "severity": "critical",
                "category": "technical",
                "url": url,
                "issue": "Page has noindex meta tag",
                "recommendation": "Remove noindex if page should be indexed",
            })

        # Image alt text issues
        for img in p.get("images", []):
            if not img.get("alt"):
                issues.append({
                    "severity": "minor",
                    "category": "on-page",
                    "url": url,
                    "issue": f"Missing alt text: {img.get('src', '')}",
                    "recommendation": "Add descriptive alt text to images",
                })

        # Broken internal links (404)
        for link in p.get("links", []):
            if link.get("rel") == "external":
                continue
            # We don't have per-link status codes from this crawler,
            # but we can flag links to pages that returned 404
            pass

    # Thin content detection
    for p in pages:
        word_count = p.get("wordCount", 0)
        if word_count < 300 and p.get("status") == 200:
            issues.append({
                "severity": "minor",
                "category": "content",
                "url": p.get("url", ""),
                "issue": f"Thin content ({word_count} words)",
                "recommendation": "Expand content to at least 300 words",
            })

    # Sort by severity
    issues.sort(key=lambda x: SEVERITY_ORDER.get(x["severity"], 99))

    # Count by severity
    counts = {"critical": 0, "major": 0, "minor": 0}
    for issue in issues:
        counts[issue["severity"]] += 1

    # Count by category
    categories = {}
    for issue in issues:
        cat = issue["category"]
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "startUrl": crawl_data.get("startUrl", ""),
        "baseDomain": crawl_data.get("baseDomain", ""),
        "pagesCrawled": crawl_data.get("pagesCrawled", 0),
        "totalIssues": len(issues),
        "issuesBySeverity": counts,
        "issuesByCategory": categories,
        "issues": issues,
        "analyzedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main():
    evidence_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else EVIDENCE

    crawl_data = load_crawl(evidence_dir)
    if not crawl_data:
        print(f"[seo-analyze] No seo-crawl.json found in {evidence_dir}")
        print("[seo-analyze] Run: python3 ufmw_seo_protocol_skill/scripts/seo-crawl.py <url>")
        return 1

    result = analyze(crawl_data)

    evidence_dir.mkdir(parents=True, exist_ok=True)
    results_file = evidence_dir / "seo-results.json"
    results_file.write_text(json.dumps(result, indent=2), encoding="utf-8")

    # Generate human-readable SEO_AUDIT.md
    md_lines = [
        "# SEO Audit Findings",
        "",
        f"- **Target URL**: {result['startUrl']}",
        f"- **Base domain**: {result['baseDomain']}",
        f"- **Pages crawled**: {result['pagesCrawled']}",
        f"- **Total issues**: {result['totalIssues']}",
        f"- **Critical**: {result['issuesBySeverity']['critical']}",
        f"- **Major**: {result['issuesBySeverity']['major']}",
        f"- **Minor**: {result['issuesBySeverity']['minor']}",
        "",
    ]

    # Issues by category
    for cat, count in sorted(result["issuesByCategory"].items()):
        md_lines.append(f"### {cat.title()} ({count})")
        md_lines.append("")
        cat_issues = [i for i in result["issues"] if i["category"] == cat]
        for issue in cat_issues:
            sev = issue["severity"]
            md_lines.append(
                f"- **{sev.upper()}** | {issue['url']} | {issue['issue']} | "
                f"{issue['recommendation']}"
            )
        md_lines.append("")

    md_file = UFME / "SEO_AUDIT.md"
    UFME.mkdir(parents=True, exist_ok=True)
    md_file.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"[seo-analyze] Found {result['totalIssues']} issues across {result['pagesCrawled']} pages")
    print(f"[seo-analyze] Critical: {result['issuesBySeverity']['critical']}, "
          f"Major: {result['issuesBySeverity']['major']}, "
          f"Minor: {result['issuesBySeverity']['minor']}")
    print(f"[seo-analyze] Results: {results_file}")
    print(f"[seo-analyze] Summary: {md_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
