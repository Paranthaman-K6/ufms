---
description: Add component with state matrix, stories, a11y test
---
# ufmw init-frontend component

Add a component with full state matrix, stories, and accessibility test.

Usage:
  ufmw init-frontend component <name>

Arguments:
  name  Component name (PascalCase, e.g. Button, Card, Nav)

Output:
  - components/<name>/ — component directory
  - components/<name>/<name>.jsx — component source
  - components/<name>/<name>.stories.jsx — Storybook stories
  - components/<name>/<name>.a11y.test.jsx — accessibility test
  - components/<name>/<name>.states.md — state matrix
