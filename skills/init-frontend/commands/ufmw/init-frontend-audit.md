---
description: Run quality gates: token audit, a11y, performance budget, responsive check
---
# ufmw init-frontend audit

Run quality gates: token audit, accessibility, performance budget, responsive check.

Usage:
  ufmw init-frontend audit

Output:
  - .ufme/evidence/audit-results.json — machine-readable audit results
  - .ufme/AUDIT_REPORT.md — human-readable audit report

Checks:
  - WCAG 2.2 AA compliance (static a11y gate via scripts/a11y.cjs)
  - Performance budgets (LCP, INP, CLS, input sizes)
  - Responsive breakpoints (390px / 768px / 1280px / 1440px)
  - Token consistency
