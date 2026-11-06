# 11 — Performance Audit

## Goal
Measure Core Web Vitals-oriented lab metrics, bundle size, image optimization, caching,
network requests, and Lighthouse results.

## Steps
1. Build production bundle.
2. Serve production build locally.
3. Measure bundle size, image optimization, caching, network requests.
4. Run Lighthouse audit against the locally served production build when possible.
5. Record lab metrics and recommendations.
6. Return critical performance findings to builder via orchestrator.
7. Update `.ufme/TASKS.md` (T-15) and `.ufme/AGENT_STATE.md`.
8. Delegate next: security audit.

## Output
- Performance findings (lab metrics, bundle size, images, caching, network, Lighthouse)
