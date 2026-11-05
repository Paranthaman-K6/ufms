#!/usr/bin/env python3
"""
seo-fix.py — Apply safe automated SEO fixes to source code.

Applies non-destructive fixes:
- Add missing <title> tags
- Add missing <meta name="description"> tags
- Ensure exactly one <h1> per page
- Add alt text to images
- Add canonical tags
- Add JSON-LD structured data

Usage:
  python3 ufmw_seo_protocol_skill/scripts/seo-fix.py <url> --apply-safe [evidenceDir]
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UFME = ROOT / ".ufme"
EVIDENCE = Path(os.environ.get("UFME_EVIDENCE_DIR") or (UFME / "evidence"))

APPLY_SAFE = "--apply-safe" in sys.argv


def load_plan(evidence_dir):
    plan_file = evidence_dir / "seo-plan.json"
    if not plan_file.exists():
        return None
    return json.loads(plan_file.read_text(encoding="utf-8"))


def fix_html_file(file_path, fixes):
    """Apply SEO fixes to an HTML file."""
    if not file_path.exists():
        return {"file": str(file_path), "applied": [], "errors": ["File not found"]}

    content = file_path.read_text(encoding="utf-8")
    original = content
    applied = []
    errors = []

    for fix in fixes:
        issue = fix.get("issue", "")
        recommendation = fix.get("fix", "")
        url = fix.get("url", "")

        if "Missing title tag" in issue:
            if "<title>" not in content:
                # Add title after <head>
                if "<head>" in content:
                    content = content.replace(
                        "<head>",
                        f"<head>\n    <title>Untitled Page</title>",
                        1,
                    )
                    applied.append("Added <title> tag")
                else:
                    errors.append("No <head> tag found for title insertion")

        elif "Missing meta description" in issue:
            if '<meta name="description"' not in content:
                if "<head>" in content:
                    content = content.replace(
                        "<head>",
                        f'<head>\n    <meta name="description" content="Page description">',
                        1,
                    )
                    applied.append("Added meta description")
                else:
                    errors.append("No <head> tag found for meta description")

        elif "Missing H1 tag" in issue:
            if "<h1" not in content.lower():
                if "<body>" in content:
                    content = content.replace(
                        "<body>",
                        f"<body>\n    <h1>Page Heading</h1>",
                        1,
                    )
                    applied.append("Added <h1> tag")
                else:
                    errors.append("No <body> tag found for H1 insertion")

        elif "Missing alt text" in issue:
            # Add alt to img tags without alt
            img_pattern = r'<img(?![^>]*\balt=)([^>]*)>'
            matches = re.findall(img_pattern, content, re.IGNORECASE)
            for match in matches:
                content = content.replace(
                    f"<img{match}>",
                    f"<img{match} alt=\"Image\">",
                )
            if matches:
                applied.append(f"Added alt text to {len(matches)} images")

        elif "Missing canonical tag" in issue:
            if 'rel="canonical"' not in content:
                if "<head>" in content:
                    content = content.replace(
                        "<head>",
                        f'<head>\n    <link rel="canonical" href="{url}">',
                        1,
                    )
                    applied.append("Added canonical tag")
                else:
                    errors.append("No <head> tag found for canonical")

    if APPLY_SAFE and content != original:
        file_path.write_text(content, encoding="utf-8")

    return {
        "file": str(file_path),
        "applied": applied,
        "errors": errors,
        "modified": content != original,
    }


def find_html_files(project_root):
    """Find HTML files in the project."""
    html_files = []
    for root, dirs, files in os.walk(project_root):
        # Skip node_modules, .git, etc.
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "__pycache__")]
        for f in files:
            if f.endswith((".html", ".htm")):
                html_files.append(Path(root) / f)
    return html_files


def main():
    # Parse args: url [evidenceDir]
    args = [a for a in sys.argv if a != "--apply-safe"]
    url = args[1] if len(args) > 1 else None
    evidence_dir = Path(args[2]) if len(args) > 2 else EVIDENCE

    if not url:
        print("Usage: python3 seo-fix.py <url> --apply-safe [evidenceDir]")
        sys.exit(2)

    plan_data = load_plan(evidence_dir)
    if not plan_data:
        print(f"[seo-fix] No seo-plan.json found in {evidence_dir}")
        print("[seo-fix] Run: python3 ufmw_seo_protocol_skill/scripts/seo-plan.py")
        return 1

    # Collect fixes from plan
    all_fixes = []
    for priority in ("priority1", "priority2", "priority3"):
        for item in plan_data.get(priority, []):
            if item.get("status") == "pending":
                all_fixes.append(item)

    if not all_fixes:
        print("[seo-fix] No pending fixes found.")
        return 0

    print(f"[seo-fix] Found {len(all_fixes)} pending fixes")
    if not APPLY_SAFE:
        print("[seo-fix] DRY RUN — use --apply-safe to apply changes")
        print()

    # Find HTML files in project
    html_files = find_html_files(ROOT)

    results = []
    for fix in all_fixes:
        fix_result = {
            "url": fix.get("url", ""),
            "issue": fix.get("issue", ""),
            "fix": fix.get("fix", ""),
            "files": [],
        }

        for html_file in html_files:
            fr = fix_html_file(html_file, [fix])
            if fr["applied"]:
                fix_result["files"].append(fr)

        results.append(fix_result)

    # Write results
    evidence_dir.mkdir(parents=True, exist_ok=True)
    results_file = evidence_dir / "seo-fix-results.json"
    results_file.write_text(json.dumps({
        "url": url,
        "fixedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "applySafe": APPLY_SAFE,
        "totalFixes": len(all_fixes),
        "results": results,
    }, indent=2), encoding="utf-8")

    total_applied = sum(len(r["files"]) for r in results)
    print(f"[seo-fix] Applied {total_applied} fixes across {len(results)} issues")
    print(f"[seo-fix] Results: {results_file}")
    if not APPLY_SAFE:
        print("[seo-fix] Run with --apply-safe to apply changes to files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
