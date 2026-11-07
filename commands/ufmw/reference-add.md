---
description: Add and inspect one or more website design references
---
# /ufmw/reference-add

Use the URLs already supplied by the user. Ask for a URL only when none was provided and reference-driven design is relevant.

For each URL:
1. Validate HTTP or HTTPS.
2. Run: node skills/universal-frontend-master/scripts/reference-inspect.js <url>
3. Analyze its per-reference evidence: python3 skills/universal-frontend-master/scripts/reference-analyze.py .ufme/evidence reference-inspect-<referenceId>.json
4. Preserve separate evidence and prior user mappings.
5. Present candidate elements and ask which ones to adapt, their destination in the target project, and the intended aspects.

Do not implement every discovered candidate automatically. Missing browsers or dependencies must be reported as blockers; never fabricate inspection evidence.
