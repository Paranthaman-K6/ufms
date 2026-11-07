---
description: Compare implemented elements with their live design references
---
# /ufmw/reference-verify

Use the known running target URL. Ask for it only when it is not already available. The reference URL defaults to each selected element's stored source URL.

Run:
  node skills/universal-frontend-master/scripts/reference-verify.js <targetUrl> [referenceUrl]

The verifier loads both pages, inspects the mapped unique selectors, compares requested measurable visual/layout properties, saves screenshots, and writes .ufme/evidence/reference-verify.json.

A missing selector is BLOCKED. A measurable mismatch is FAIL. Unsupported behavior/animation checks are PARTIAL until separate interaction tests exist. Only a complete comparison with every required check passing may be reported as PASS.
