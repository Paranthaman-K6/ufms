# 02 — Research

## Goal
Research requirements, references, design inspiration, components, templates, fonts, icons,
images, and videos. Verify licenses and commercial-use permissions.

## Steps
1. Read `.ufme/PROJECT_SPEC.md` and any reference website/screenshot.
2. **Ask the user design-direction questions** (record answers in `.ufme/DESIGN_SYSTEM.md`):
   - What is the primary visual tone? (minimal, bold, playful, corporate, elegant, retro, futuristic)
   - Which motion graphics style? (none/subtle, entrance reveals, hover transitions, page-scroll animations, micro-interactions)
   - What animation palette? (soft/ease, bouncy/spring, sharp/linear, custom cubic-bezier, physics-based)
   - Preferred color palette? (brand colors, monochrome, gradient, pastel, neon, dark-first)
   - Typography direction? (serif, sans-serif, display, mono, custom brand font)
   - Are there brand assets to reference? (logo, existing website, brand guidelines)
3. Render the theme showcase so the user can see the palettes side by side:
   `scripts/theme-showcase.py --target .` → `.ufme/theme-showcase.pdf` (their current
   choice is marked and shown first).
4. Identify needed assets (fonts, icons, images, templates, components).
5. For each asset, verify license and commercial-use status.
6. Record asset decisions (name, repo/site, license, commercial-use, install method, reason)
   in `.ufme/DECISIONS.md` via the orchestrator.
7. Update `.ufme/TASKS.md` (T-03) and `.ufme/AGENT_STATE.md`.
8. Delegate next: backend intelligence (if backend) or product intelligence.

## Output
- Research notes
- Asset decisions in `.ufme/DECISIONS.md`
- Design-direction answers in `.ufme/DESIGN_SYSTEM.md` (motion, animation, color, typography, brand assets)
- `.ufme/theme-showcase.pdf` — every curated theme rendered for review
- `.ufme/TASKS.md` (T-03 COMPLETE)
