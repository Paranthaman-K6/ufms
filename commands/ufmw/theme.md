---
description: Generate the theme showcase PDF for this project
---
# ufmw theme

Render every curated theme as a page — palette swatches with hex values, the
type pairing as a specimen, and a small applied sample — then mark the theme
this project already chose.

Usage:
  ufmw theme [--only NAME]

## Runs

```
python3 skills/universal-frontend-master/scripts/theme-showcase.py --target .
```

## Output

- `.ufme/theme-showcase.pdf` — one page per theme, project choice first

Themes come from the local catalog (`data/palettes.csv`). When
`UFME_REGISTRY_URL` and `UFME_REGISTRY_KEY` are set, registry entries with
category `theme` and a `theme` object are appended.
