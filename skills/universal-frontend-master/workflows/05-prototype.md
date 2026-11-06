# 05 — Prototype

## Goal
Create the design system, wireframes, and component architecture from the PRD and API map.

## Steps
1. Read `.ufme/PRD.md`, `.ufme/API_MAP.md`, `.ufme/SITEMAP.md`, `.ufme/USER_FLOWS.md`,
   `.ufme/FEATURES.md`, and `.ufme/DESIGN_SYSTEM.md` (motion/animation/color/typography answers).
2. Create `.ufme/DESIGN_SYSTEM.md` (canonical path only — no `.ufme/design/` copy).
   Start with `## Design direction`: tone, two distinct type roles with real typefaces,
   palette rationale, layout concept, and motion hierarchy (at least two treatments).
   Then tokens (typography, spacing, color; component architecture; responsive rules;
   animation guidance; accessible UI patterns). Do not start implementation while
   `detect-slop.py --path <src> --design .ufme/DESIGN_SYSTEM.md` still reports
   `design-system-incomplete`.
   - Include motion graphics specification: entrance reveals, hover states, scroll animations,
     micro-interactions with easing curves and duration. Vary them by hierarchy.
   - Include animation palette: preferred easing (ease, ease-in, ease-out, ease-in-out, custom),
     duration ranges (fast 150-300ms, normal 300-500ms, slow 500-800ms), stagger delays.
3. Run `scripts/generate-prototype.py` to produce HTML/CSS prototype pages from the
   sitemap routes and design tokens; output isolated in `prototypes/`.
4. Produce wireframes (low-fidelity page layouts).
5. Record any new asset (font, icon, image) in `.ufme/DECISIONS.md`.
6. Run `scripts/discover-assets.py` to inventory project images/fonts/videos with license
   hints into `.ufme/ASSET_MANIFEST.md`.
7. Update `.ufme/TASKS.md` (T-06) and `.ufme/AGENT_STATE.md`.
8. Delegate next: frontend architecture.

## Output
- `.ufme/DESIGN_SYSTEM.md` (including motion graphics and animation palette)
- Wireframes
- Component architecture
