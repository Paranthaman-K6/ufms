# Quality Standards

## Code
- TypeScript strict where configured; ESLint + Prettier where configured.
- Semantic HTML5, ARIA landmarks, focus-visible styles, keyboard operability.
- Responsive breakpoints: mobile (390px), tablet (768px), laptop (1280px), desktop (1440px).
- Reusable components; props/TypeScript types; loading, error, and empty states on every data
  dependent view.

## Browser testing
- Native Selenium WebDriver (Chromium + Firefox). Headless by default.
- Screenshots at all four viewports, dark + light themes where applicable.
- Collect console errors, failed network requests, broken links, interaction failures.
- Machine-readable summary: `.ufme/evidence/browser-results.json`.

## Audits
- Visual: severity-ranked issues verified with fresh screenshots after fixes.
- Accessibility: axe-core where a browser is available; WCAG 2.1 AA target.
- Performance: Core Web Vitals-oriented lab metrics, bundle size, image optimization, caching,
  Lighthouse against a locally served production build when possible.
- Security: XSS, unsafe HTML, CSRF, CORS, CSP, cookies, token storage, exposed secrets,
  dependency audit, client-side authorization assumptions.

## Acceptance
- Critical and major findings fixed and retested.
- All acceptance criteria in PRD.md pass, or limitations explicitly documented in
  `.ufme/AUDIT_REPORT.md`.
