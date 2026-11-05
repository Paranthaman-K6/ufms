---
description: Crawl website and extract SEO data
---
# ufmw seo crawl <url>

Crawl a website using deterministic HTTP requests and extract SEO data:
titles, meta descriptions, headings, links, images, canonical tags,
robots.txt, sitemap.xml, structured data, and status codes.

Usage:
  ufmw seo crawl <url>

Example:
  ufmw seo crawl https://example.com

Output:
  - .ufme/evidence/seo-crawl.json — machine-readable crawl data
  - .ufme/SEO_CRAWL.md — human-readable summary
