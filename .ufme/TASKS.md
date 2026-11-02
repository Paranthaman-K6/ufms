# UFME Task State

Primary orchestrator maintains this file. Statuses: TODO, IN_PROGRESS, COMPLETE, BLOCKED.

## Intake
- [x] T-01 Project intake: classify project; detect stack; preserve architecture. (detect-stack.sh)
- [x] T-02 Read `.ufme/AGENT_STATE.md` and `.ufme/ENVIRONMENT.md` at session start.

## Research & intelligence
- [x] T-03 Research requirements, references, design inspiration, components, fonts, icons; verify licenses. (research-libraries.sh, LIBRARY_REGISTRY.md)
- [ ] T-04 Backend intelligence: produce API_MAP.md, BACKEND_CAPABILITIES.md, AUTHENTICATION_MAP.md, ERROR_HANDLING.md. (enhance-backend-discovery.sh, BACKEND_CONTRACTS.md) — PARTIAL: contract detection done, full parsing IN_PROGRESS
- [ ] T-05 Product intelligence: PRD.md, SITEMAP.md, USER_FLOWS.md, FEATURES.md. — TODO

## Design & architecture
- [x] T-06 Design system: DESIGN_SYSTEM.md, tokens, responsive rules. (generate-prototype.sh)
- [ ] T-07 Frontend architecture: folder structure, routing, state, testing strategy. — TODO

## Implementation
- [ ] T-08 Implement pages, components, navigation, forms, loading/error/empty states, responsive layouts. — PARTIAL: prototype generator creates HTML/CSS prototypes
- [ ] T-09 Integrate frontend to confirmed backend endpoints. — TODO

## Browser testing (native Selenium WebDriver)
- [x] T-10 Run check-native-browser.sh; Firefox READY. (check-native-browser.sh)
- [x] T-11 Run browser-test.sh; browser-results.json with PASS/FAIL/SKIPPED/BLOCKED.
- [x] T-12 screenshot.sh: mobile/tablet/laptop/desktop, dark + light themes.

## Audits
- [ ] T-13 Visual audit: VISUAL_AUDIT.md. — TODO
- [ ] T-14 Accessibility audit: WCAG 2.1 AA. — TODO (axe-core not installed)
- [ ] T-15 Performance audit: Core Web Vitals, Lighthouse where available. — TODO (Lighthouse not installed)
- [ ] T-16 Security audit: XSS, CSRF, CORS, CSP, secrets, deps. — TODO

## Quality & delivery
- [x] T-17 quality-check.sh: exit codes, PASS/FAIL/SKIPPED/BLOCKED, quality-report.json.
- [ ] T-18 Fix critical/major findings; retest. — TODO
- [x] T-19 Continuous improvement: self-improve.sh (69 PASS/0 FAIL), AGENT_STATE.md.
- [ ] T-20 Delivery. — TODO

## Additional (P0 defect fixes — COMPLETE)
- [x] Browser security: --no-sandbox removed from all launch paths
- [x] Network monitoring: Chromium CDP + Firefox BiDi adapters with shared schema
- [x] PASS/FAIL logic: calculated from individual check results
- [x] Screenshot correctness: full-page, section, dark mode modes
- [x] Quality report: .ufme/evidence/quality-report.json generated
- [x] Regression tests: tests/regression/run.js (5 pass, 0 fail, 3 skip)

## Additional (P1 implementation — IN PROGRESS)
- [ ] Asset intelligence: discover-assets.sh enhanced (dedup, dimensions, broken assets)
- [ ] Execution profiles: profile config files + execution-profiles.sh reads them
- [ ] Backend contract parsing: enhance-backend-discovery.sh parses OpenAPI/Swagger/Postman/GraphQL/AsyncAPI
- [ ] MCP integration: discover.js integration layer (optional, docs only)
- [ ] Prototype generator: consumes real project info from .ufme/ memory files
- [ ] Task checkpoint safety: verification after modification
- [ ] Documentation reconciliation: this file, UPGRADE_REPORT.md, SKILL_VALIDATION.md
