# 10 — Accessibility Audit

## Goal
Check semantic HTML, landmarks, headings, labels, focus visibility, keyboard operation,
contrast, touch targets, reduced motion, screen-reader semantics. Target WCAG 2.1 AA.

## Steps
1. Read frontend source and `.ufme/VISUAL_AUDIT.md`.
2. Run axe-core accessibility checks where a browser is available.
3. Record findings (semantic HTML, landmarks, headings, labels, focus, keyboard, contrast,
   touch targets, reduced motion, screen-reader semantics).
4. Return critical/major a11y findings to builder via orchestrator.
5. Update `.ufme/TASKS.md` (T-14) and `.ufme/AGENT_STATE.md`.
6. Delegate next: performance audit.

## Output
- Accessibility findings (WCAG 2.1 AA)
- `.ufme/TASKS.md` updated
