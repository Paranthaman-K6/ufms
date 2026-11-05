# Reference-Driven Design Workflow

## Workflows

### 01 — Reference Discovery

## Goal
Classify the project, detect the existing stack, and identify reference URLs for design inspiration.

## Steps
1. Read `.ufme/AGENT_STATE.md` and `.ufme/ENVIRONMENT.md`.
2. Run `scripts/detect-stack.sh` to detect frontend and backend frameworks/tools.
3. Run `scripts/detect-platform.sh` to record host OS/compatibility (Arch Linux required).
4. Create `.ufme/PROJECT_SPEC.md` from the brief, repo, screenshot, or reference site.
5. Create `.ufme/REFERENCES.md` to catalog reference URLs.
6. Record classification: new, frontend-only, backend-only, or full-stack.
7. Update `.ufme/TASKS.md` (T-01) and `.ufme/AGENT_STATE.md`.
8. Delegate next: reference analysis (if references exist) or backend intelligence.

## Output
- `.ufme/PROJECT_SPEC.md`
- `.ufme/REFERENCES.md`
- `.ufme/TASKS.md` (T-01 marked COMPLETE)

---

### 02 — Reference Analysis

## Goal
Analyze reference websites, identify individual UI elements, extract DOM structure and
computed styles.

## Steps
1. Read `.ufme/PROJECT_SPEC.md` and `.ufme/REFERENCES.md`.
2. For each reference URL, run `scripts/reference-inspect.js <url>` to load in Selenium
   and extract DOM structure, computed CSS styles, and element screenshots.
3. Run `scripts/reference-analyze.py` to group elements by type and generate
   `.ufme/ELEMENT_MAP.md`.
4. Ask user clarification questions for each element:
   - Which element to adapt? (nav, hero, cards, buttons, forms, etc.)
   - Where to implement? (homepage, existing header, product page, dashboard, replace component, add new section)
   - What aspects? (visual appearance, behavior, animations, layout, combination)
5. Record element-to-destination mapping in `.ufme/ELEMENT_MAP.md`.
6. Update `.ufme/TASKS.md` and `.ufme/AGENT_STATE.md`.
7. Delegate next: reference matching.

## Output
- `.ufme/REFERENCES.md` — reference catalog with element details
- `.ufme/ELEMENT_MAP.md` — element-to-location mapping with pending destinations/aspects

---

### 03 — Reference Matching

## Goal
Match each reference element to a destination in the target project and generate an
implementation plan.

## Steps
1. Read `.ufme/ELEMENT_MAP.md` with user-specified destinations and aspects.
2. Run `scripts/reference-match.py` to produce `.ufme/evidence/reference-match.json`.
3. Generate `.ufme/DESIGN_ADAPTATIONS.md` with adaptation rules per element.
4. Update `.ufme/TASKS.md` and `.ufme/AGENT_STATE.md`.
5. Delegate next: reference adaptation.

## Output
- `.ufme/evidence/reference-match.json` — machine-readable match plan
- `.ufme/DESIGN_ADAPTATIONS.md` — adaptation rules per element

---

### 04 — Reference Adaptation

## Goal
Adapt reference elements to the target project's design system and generate component code.

## Steps
1. Read `.ufme/evidence/reference-match.json`.
2. Run `scripts/reference-adapt.py` to generate CSS variables and component code.
3. Generate `.ufme/REFERENCE_IMPLEMENTATION.md` with HTML/CSS for each element.
4. CSS variables capture source colors, typography, spacing for consistent adaptation.
5. Update `.ufme/TASKS.md` and `.ufme/AGENT_STATE.md`.
6. Delegate next: implementation.

## Output
- `.ufme/evidence/reference-adapt.json` — machine-readable adaptation data
- `.ufme/REFERENCE_IMPLEMENTATION.md` — component code (HTML/CSS)

---

### 05 — Reference Implementation

## Goal
Implement adapted reference elements in the target project's source code.

## Steps
1. Read `.ufme/REFERENCE_IMPLEMENTATION.md`.
2. Delegate to `ufmw-builder` to implement each adapted element:
   - Adapt component to target project's framework and styling approach
   - Apply target project's design tokens (colors, typography, spacing)
   - Ensure responsive behavior (mobile/tablet/laptop/desktop)
   - Apply interactions (hover, active states, animations)
3. Update `.ufme/TASKS.md` via the orchestrator.
4. Delegate next: verification.

## Output
- Modified source files (pages, components, layouts)
- `.ufme/TASKS.md` updated

---

### 06 — Reference Verification

## Goal
Verify that implemented elements match the reference intent.

## Steps
1. Run `scripts/reference-verify.js <targetUrl> [referenceUrl]` to capture screenshots
   of implemented elements.
2. Compare computed styles against reference intent.
3. Report matches and mismatches in `.ufme/evidence/reference-verify.json`.
4. If mismatches found, delegate back to `ufmw-builder` for fixes.
5. Update `.ufme/TASKS.md` and `.ufme/AGENT_STATE.md`.
6. Delegate next: quality audit.

## Output
- `.ufme/evidence/reference-verify.json` — verification results
- `.ufme/evidence/reference-verify-screenshots/` — before/after screenshots

---

### 07 — Quality Audit

## Goal
Run full quality audit including reference-implementation verification.

## Steps
1. Run `scripts/quality-check.py` (a11y, perf, visual, security, slop).
2. `ufmw-auditor` reads `reference-verify.json` and includes findings in AUDIT_REPORT.md.
3. Fix critical/major findings, retest.
4. Update `.ufme/TASKS.md` and `.ufme/AGENT_STATE.md`.
5. Delegate next: continuous improvement.

## Output
- `.ufme/evidence/quality-report.json`
- `.ufme/AUDIT_REPORT.md`
