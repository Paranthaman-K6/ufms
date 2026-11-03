# 09 — Visual Audit

## Goal
Review actual Selenium screenshots; produce severity-ranked visual audit; verify fixes.

## Steps
1. Read screenshots in `.ufme/evidence/screenshots/`.
2. Create `.ufme/VISUAL_AUDIT.md` with table:
   ID | Page | Viewport | Screenshot | Severity | Issue | Likely cause | Suggested fix | Owner | Status | Retest evidence
3. Rank issues: critical / major / minor.
4. For critical/major issues, return to builder (via orchestrator) for fixes.
5. After fixes, capture fresh screenshots and update Status/Retest evidence.
6. Update `.ufme/TASKS.md` (T-13) and `.ufme/AGENT_STATE.md`.
7. Delegate next: accessibility audit.

## Output
- `.ufme/VISUAL_AUDIT.md`
- Fresh verification screenshots (on fix)
