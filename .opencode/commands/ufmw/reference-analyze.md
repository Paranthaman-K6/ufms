---
description: Analyze stored design-reference inspections and update the element map
---
# /ufmw/reference-analyze

Analyze stored inspection evidence without re-opening pages unless fresh evidence is required.

For each .ufme/evidence/reference-inspect-<referenceId>.json, run:
  python3 skills/universal-frontend-master/scripts/reference-analyze.py .ufme/evidence reference-inspect-<referenceId>.json

If no per-reference evidence exists, use the compatibility file:
  python3 skills/universal-frontend-master/scripts/reference-analyze.py .ufme/evidence

Review .ufme/REFERENCES.md and .ufme/ELEMENT_MAP.md. Re-analysis must upsert each reference section and preserve the user's existing destination, aspects, and target selector.

Do not treat placeholder rows as selected elements. Ask the user to select elements and specify destination and intended aspects before matching.
