---
description: Apply safe automated SEO fixes
---
# ufmw seo fix <url> --apply-safe

Apply safe, non-destructive SEO fixes to source code:
- Add missing <title> tags (30-60 chars, unique per page)
- Add missing <meta name="description"> tags (50-160 chars)
- Ensure exactly one <h1> per page
- Add descriptive alt text to images
- Add canonical <link rel="canonical"> tags
- Add valid JSON-LD structured data
- Update sitemap.xml and robots.txt

Usage:
  ufmw seo fix <url> --apply-safe

Example:
  ufmw seo fix https://example.com --apply-safe
