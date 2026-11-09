---
description: Inspect a design reference URL and list its visible UI elements
---
# /ufmw/reference-inspect

Use the URL already associated with the selected reference. If none is known, ask the user.

Run:
  node skills/universal-frontend-master/scripts/reference-inspect.js <url>

The inspector records the source URL, stable reference ID, visible candidate elements, computed styles, unique CSS selectors, and screenshots under .ufme/evidence/. It reports EMPTY or FAIL when valid element evidence cannot be obtained.

Analyze the corresponding per-reference JSON and show candidates. Discovery alone does not mean an element has been selected or implemented.
