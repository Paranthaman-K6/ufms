---
description: Google Search Console integration
---
# ufmw seo gsc <url>

Integrate with Google Search Console for actual impressions, clicks,
CTR, average position, query data, sitemap status, and URL inspection.

Requires GSC credentials (service account or OAuth). When credentials are
not available, uses clearly labeled mock fixtures.

Usage:
  ufmw seo gsc <url>

Example:
  ufmw seo gsc https://example.com

Output:
  - .ufme/evidence/seo-gsc.json — GSC data (or mock fixture)
  - .ufme/SEO_GSC_REPORT.md — human-readable GSC report
