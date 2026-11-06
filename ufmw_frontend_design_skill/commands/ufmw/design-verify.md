---
description: Verify implementation against reference intent
---
# ufmw design verify <targetUrl> [referenceUrl]

Verify that implemented elements match the reference intent by capturing
screenshots and comparing computed styles.

Usage:
  ufmw design verify <targetUrl> [referenceUrl]

Examples:
  ufmw design verify http://localhost:5173
  ufmw design verify http://localhost:5173 https://example.com

Output:
  - .ufme/evidence/reference-verify.json — verification results
  - .ufme/evidence/reference-verify-screenshots/ — before/after screenshots
