---
description: Prepare implementation briefs from validated reference mappings
---
# /ufmw/reference-adapt

Require .ufme/evidence/reference-match.json to have status MATCHED. Then run:
  python3 skills/universal-frontend-master/scripts/reference-adapt.py

Review .ufme/evidence/reference-adapt.json and .ufme/REFERENCE_IMPLEMENTATION.md. These are measured-style implementation briefs, not completed application code.

Implement the selected elements in the target project's existing framework, components, design tokens, responsive rules, and accessibility conventions. Modify actual source files and run project tests. Never claim that generic placeholder markup is a completed implementation.
