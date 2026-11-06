---
description: Initialize UFMW reference-driven design project
---
# ufmw init

Initialize the current project for reference-driven website engineering.

**Mandatory:** run `scripts/init-project.py` and require answers to every
design question. Do not skip or defer the questionnaire.

## Runs

```
python3 universal-frontend-master-source/scripts/init-project.py [target-dir]
```

## Questions asked (all required)

- **Color palette** — must choose one from the curated palette list
- **Font pairing** — must choose one heading + body font combination
- **Visual style** — must choose one design style (minimal, brutalism, glass, etc.)
- **Reference websites** — paste reference URLs for design inspiration (blank line to finish; optional)

## Creates

- `.ufme/DESIGN_SYSTEM.md` — design tokens (color, typography, style) filled from your answers
- `.ufme/REFERENCES.md` — catalog of reference URLs (if any provided)
- `.ufme/ELEMENT_MAP.md` — element-to-location mapping (empty template)
- `.ufme/DESIGN_ADAPTATIONS.md` — design adaptation rules (empty template)

Usage:
  ufmw init
