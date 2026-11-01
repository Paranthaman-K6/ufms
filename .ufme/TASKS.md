# UFME Task State

Primary orchestrator maintains this file. One coherent task at a time; parallel only when
tasks do not modify the same files. Statuses: TODO, IN_PROGRESS, COMPLETE, BLOCKED.

## Intake
- [ ] T-01 Project intake: classify project as new / frontend-only / backend-only / full-stack; detect stack; preserve existing architecture. (detect-stack.sh)
- [ ] T-02 Read `.ufme/AGENT_STATE.md` and `.ufme/ENVIRONMENT.md` at session start.

## Research & intelligence
- [ ] T-03 Research requirements, references, design inspiration, components, fonts, icons; verify licenses.
- [ ] T-04 Backend intelligence: analyze backend/API specs; produce evidence-based API_MAP.md, BACKEND_CAPABILITIES.md, AUTHENTICATION_MAP.md, ERROR_HANDLING.md. Never invent endpoints.
- [ ] T-05 Product intelligence: PRD.md, SITEMAP.md, USER_FLOWS.md, FEATURES.md, acceptance criteria; map every confirmed backend capability to a frontend feature.

## Design & architecture
- [ ] T-06 Design system: DESIGN_SYSTEM.md, tokens, typography, spacing, color, component architecture, responsive rules, accessible UI patterns.
- [ ] T-07 Frontend architecture: select/preserve architecture; folder structure, routing, state, data fetching, component boundaries, error boundaries, testing strategy. No forced framework change without justification.

## Implementation
- [ ] T-08 Implement pages, components, navigation, forms, loading/error/empty states, responsive layouts, auth where supported, PWA readiness where justified.
- [ ] T-09 Integrate frontend to confirmed backend endpoints: typed API client, auth flows, authorization-aware UI, validation, retries, network failure states.

## Browser testing (native Selenium WebDriver, Chromium + Firefox)
- [ ] T-10 Run check-native-browser.sh; detect Chromium/Firefox; confirm Selenium Manager + selenium-webdriver.
- [ ] T-11 Run browser-test.sh against local dev server; capture screenshots at mobile/tablet/laptop/desktop; collect console errors, failed requests, broken links, interaction failures; save browser-results.json.
- [ ] T-12 screenshot.sh: full-page + section screenshots at 390x844, 768x1024, 1280x800, 1440x900; dark + light theme where applicable.

## Audits
- [ ] T-13 Visual audit: review Selenium screenshots; severity-ranked VISUAL_AUDIT.md; verify fixes with fresh screenshots.
- [ ] T-14 Accessibility audit: semantic HTML, landmarks, headings, labels, focus, keyboard, contrast, touch targets, reduced motion, screen-reader semantics.
- [ ] T-15 Performance audit: Core Web Vitals-oriented lab metrics, bundle size, image optimization, caching, Lighthouse where possible.
- [ ] T-16 Security audit: XSS, unsafe HTML, CSRF, CORS, CSP, cookies, token storage, exposed secrets, dependency vulnerabilities, client-side auth assumptions.

## Quality & delivery
- [ ] T-17 quality-check.sh: type check, lint, unit tests, production build, Selenium tests, axe-core where browser available, Lighthouse, dependency audit.
- [ ] T-18 Fix critical and major findings; retest; repeat until acceptance criteria pass or limitations documented.
- [ ] T-19 Continuous improvement: DECISIONS.md, AGENT_STATE.md updates; DEPLOYMENT.md.
- [ ] T-20 Delivery: hand off complete, tested, production-ready website.
