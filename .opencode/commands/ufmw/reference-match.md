---
description: Validate selected reference elements and create a target mapping plan
---
# /ufmw/reference-match

Read .ufme/ELEMENT_MAP.md. Match only elements the user selected by supplying both a destination and intended aspects. Untouched placeholder rows are not selected.

Run:
  python3 skills/universal-frontend-master/scripts/reference-match.py

The matcher must resolve every selected element to its actual source evidence, preserving its own reference URL, selector, and computed styles. Invalid or unresolved selections remain pending and are not reported as matched.

Review .ufme/evidence/reference-match.json. Continue only when its status is MATCHED. When no elements are selected, ask which element to adapt and its destination/aspects.
