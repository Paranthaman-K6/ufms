---
description: Analyze crawl data for SEO issues
---
# ufmw seo analyze <url>

Analyze crawl data for SEO issues: missing/duplicate titles, meta
descriptions, H1 issues, missing alt text, broken links, missing canonical,
thin content, orphan pages.

Usage:
  ufmw seo analyze <url>

Example:
  ufmw seo analyze https://example.com

Output:
  - .ufme/evidence/seo-results.json — machine-readable analysis
  - .ufme/SEO_AUDIT.md — human-readable findings
