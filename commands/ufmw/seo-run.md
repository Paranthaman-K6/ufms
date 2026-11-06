---
description: Full autonomous SEO run
---
# ufmw seo run --profile autonomous --mode full --apply-safe

Execute the complete SEO workflow autonomously:

1. Project discovery — read .ufme/ memory, detect stack
2. Website crawling — deterministic HTTP crawl via seo-crawl.py
3. Technical SEO analysis — seo-analyze.py detects issues
4. Search/content analysis — keyword-to-page mapping, content gaps
5. Opportunity prioritization — seo-plan.py ranks by severity/effort/impact
6. Multi-agent coordination — delegates to builder for source-code fixes
7. Implementation — seo-fix.py applies safe fixes
8. Re-crawling — seo-verify.py confirms fixes
9. Independent verification — quality gate + visual diff
10. Automatic repair — re-delegates failed fixes
11. Reporting — seo-report.py generates SEO_AUDIT_REPORT.md
12. Monitoring — seo-monitor.py tracks metrics over time

Usage:
  ufmw seo run --profile autonomous --mode full --apply-safe

Example:
  ufmw seo run --profile autonomous --mode full --apply-safe
