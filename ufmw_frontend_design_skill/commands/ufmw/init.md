---
description: Initialize UFMW reference-driven design project
---
# ufmw init

Initialize the current project for reference-driven website engineering.

Runs `scripts/init-project.py` interactively, which asks design-preference
questions and records the answers in `.ufme/`:

## Questions asked

- **Color palette** — choose from the curated palette list (or skip)
- **Font pairing** — choose heading + body font combination (or skip)
- **Visual style** — choose a design style (minimal, brutalism, glass, etc.) (or skip)
- **Reference websites** — paste reference URLs for design inspiration (blank line to finish)

## Creates

- `.ufme/DESIGN_SYSTEM.md` — design tokens (color, typography, style) filled from your answers
- `.ufme/REFERENCES.md` — catalog of reference URLs (if any provided)
- `.ufme/ELEMENT_MAP.md` — element-to-location mapping (empty template)
- `.ufme/DESIGN_ADAPTATIONS.md` — design adaptation rules (empty template)

Usage:
  ufmw init

Or directly:
  python3 universal-frontend-master-source/scripts/init-project.py [target-dir]
