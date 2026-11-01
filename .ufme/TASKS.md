# UFME Task State

Primary orchestrator maintains this file. Statuses: TODO, IN_PROGRESS, COMPLETE, BLOCKED.

## Intake
- [x] T-01 Project intake: classify project; detect stack; preserve architecture. (detect-stack.sh)
- [x] T-02 Read `.ufme/AGENT_STATE.md` and `.ufme/ENVIRONMENT.md` at session start.

## Research & intelligence
- [x] T-03 Research requirements, references, design inspiration, components, fonts, icons; verify licenses. (research-libraries.sh, LIBRARY_REGISTRY.md)
- [ ] T-04 Backend intelligence: produce API_MAP.md, BACKEND_CAPABILITIES.md, AUTHENTICATION_MAP.md, ERROR_HANDLING.md. (enhance-backend-discovery.sh, BACKEND_CONTRACTS.md)
- [ ] T-05 Product intelligence: PRD.md, SITEMAP.md, USER_FLOWS.md, FEATURES.md.

## Design & architecture
- [x] T-06 Design system: DESIGN_SYSTEM.md, tokens, responsive rules. (generate-prototype.sh)
- [ ] T-07 Frontend architecture: folder structure, routing, state, testing strategy.

## Implementation
- [ ] T-08 Implement pages, components, navigation, forms, loading/error/empty states, responsive layouts. (generate-prototype.sh creates prototypes/)
- [ ] T-09 Integrate frontend to confirmed backend endpoints.

## Browser testing (native Selenium WebDriver)
- [x] T-10 Run check-native-browser.sh; Firefox READY. (check-native-browser.sh)
- [x] T-11 Run browser-test.sh; browser-results.json with PASS/FAIL/SKIPPED/BLOCKED.
- [x] T-12 screenshot.sh: mobile/tablet/laptop/desktop, dark + light themes.

## Audits
- [ ] T-13 Visual audit: VISUAL_AUDIT.md.
- [ ] T-14 Accessibility audit: WCAG 2.1 AA.
- [ ] T-15 Performance audit: Core Web Vitals, Lighthouse where available.
- [ ] T-16 Security audit: XSS, CSRF, CORS, CSP, secrets, deps.

## Quality & delivery
- [x] T-17 quality-check.sh: exit codes, PASS/FAIL/SKIPPED, no silent suppression.
- [ ] T-18 Fix critical/major findings; retest.
- [x] T-19 Continuous improvement: self-improve.sh (69 PASS/0 FAIL), DECISIONS.md, AGENT_STATE.md.
- [ ] T-20 Delivery.

## Additional (all priorities)
- [x] Asset intelligence: discover-assets.sh, ASSET_MANIFEST.md
- [x] Execution profiles: execution-profiles.sh (lite/standard/advanced/autonomous)
- [x] Platform support: detect-platform.sh (Arch, Ubuntu/Debian, Fedora, WSL, macOS)
- [x] MCP integration: docs/mcp-integration.md (optional)
- [x] Task checkpoints: task-checkpoint.sh (dependency-aware)
