# UFME Research Registry

**Purpose:** Track research needed to turn UFME's documented capabilities into reliable, tested runtime features.  
**Status convention:** NOT STARTED · IN PROGRESS · VERIFIED · DEFERRED  
**Last updated:** 2026-11-01  
**Related checklist:** [todo.md](todo.md)

> Research entries are questions and investigation tasks, not claims that a feature is implemented. Record findings, decisions, evidence, compatibility constraints, and a proof-of-concept before marking an entry VERIFIED.

## Research priorities

| ID | Priority | Area | Research question / deliverable | Status |
|---|---|---|---|---|
| R-001 | P0 | Selenium/CDP | Determine reliable Selenium 4 Chrome performance-log configuration and correct CDP events for failed requests, HTTP errors, request IDs, and methods. Produce a tested parser fixture set. | NOT STARTED |
| R-002 | P0 | Browser result semantics | Define severity policy for console errors, network failures, navigation failures, screenshot failures, and unsupported capabilities; map to PASS/FAIL/SKIPPED/BLOCKED and exit codes. | NOT STARTED |
| R-003 | P0 | Full-page screenshots | Compare Selenium-compatible approaches: Chrome DevTools full-page capture, scroll-and-stitch, and browser-specific alternatives. Document viewport/device-scale-factor behavior and limitations. | NOT STARTED |
| R-004 | P0 | Element screenshots | Identify the supported Selenium WebElement screenshot API and design a stable selector-based abstraction with tests. | NOT STARTED |
| R-005 | P0 | Theme verification | Research prefers-color-scheme emulation, app-level theme toggles, persistence/reset behavior, and a way to verify screenshot theme state rather than merely labeling it. | NOT STARTED |
| R-006 | P0 | Quality gates | Specify machine-readable quality report schema, required vs optional checks, blocked handling, aggregate status, and deterministic exit codes. | NOT STARTED |
| R-007 | P0 | Browser security | Audit all Chromium launch paths and document sandbox requirements for headless operation across supported environments. | NOT STARTED |
| R-008 | P1 | Functional testing | Choose a lightweight test strategy for Node scripts and shell scripts; add fixtures/mocks for browser logs, task transitions, quality results, sitemap parsing, and contract parsing. | NOT STARTED |
| R-009 | P1 | Sitemap/prototype generation | Define supported sitemap formats (Markdown table, YAML/JSON), safe route-to-filename mapping, navigation graph, accessible interactions, and realistic page templates. | NOT STARTED |
| R-010 | P1 | Design-token ingestion | Research robust token formats and extraction from design-system Markdown, CSS variables, JSON tokens, and common design-token conventions. Define precedence and validation. | NOT STARTED |
| R-011 | P1 | Asset discovery | Research local metadata extraction, duplicate detection, path-with-spaces handling, SVG safety, image dimensions, video metadata, optimization recommendations, and license verification workflow. | NOT STARTED |
| R-012 | P1 | Remote asset providers | Compare official APIs/providers for image/video search, authentication, attribution, usage restrictions, and rate limits. Only integrate sources with documented licensing/terms; never treat filename/domain heuristics as license proof. | NOT STARTED |
| R-013 | P1 | OpenAPI/Swagger | Select parser(s) and define extraction for paths, methods, parameters, request/response schemas, auth schemes, servers, errors, versioning, and validation. | NOT STARTED |
| R-014 | P1 | Postman | Research collection format versions and environment-variable handling; map requests to verified API operations without exposing secrets. | NOT STARTED |
| R-015 | P1 | GraphQL | Define schema discovery from SDL/introspection, operation extraction, auth/error conventions, and safe handling when introspection is disabled. | NOT STARTED |
| R-016 | P1 | AsyncAPI/WebSocket/SSE | Research contract parsing and source-code evidence for channels, messages, auth, reconnection, event schemas, and transport limitations. Separate verified contracts from inferred hints. | NOT STARTED |
| R-017 | P1 | MCP runtime integration | Determine what OpenCode exposes for MCP server/tool discovery and invocation at runtime; design capability negotiation, permission boundaries, audit trail, timeout handling, and native Selenium fallback. | NOT STARTED |
| R-018 | P1 | Execution profiles | Define a validated profile schema and prove that profile settings affect orchestration (agent selection, research depth, concurrency, verification, resource budgets) without weakening safety or acceptance criteria. | NOT STARTED |
| R-019 | P1 | Multi-agent orchestration | Research task DAG representation, dependency validation, concurrency limits, cancellation, retries, checkpoint persistence, conflict resolution, and agent handoff evidence. | NOT STARTED |
| R-020 | P1 | Skill/source synchronization | Define a single source-of-truth and deterministic deployment/check process for source agents, workflows, scripts, and installed OpenCode skill files. | NOT STARTED |
| R-021 | P1 | Platform support | Verify shell/runtime/browser prerequisites and path handling for Arch Linux, Ubuntu/Debian, Fedora, Windows/WSL, and macOS. Define platform-specific BLOCKED reasons. | NOT STARTED |
| R-022 | P1 | Accessibility | Compare axe-core integration approaches in browser automation; define WCAG 2.2 AA scope, rule configuration, false-positive review, and evidence format. | NOT STARTED |
| R-023 | P1 | Performance | Research Lighthouse CI/local invocation, Core Web Vitals collection, stable test conditions, project-local installation, and reporting thresholds. | NOT STARTED |
| R-024 | P1 | Security auditing | Define safe static checks for secrets, XSS sinks, dependency vulnerabilities, headers/CSP, auth flows, and test boundaries. Avoid active testing against systems without authorization. | NOT STARTED |
| R-025 | P1 | End-to-end validation | Build a small fixture website with routes, forms, loading/error states, an OpenAPI contract, assets, and responsive behavior; execute the entire UFME pipeline and capture evidence. | NOT STARTED |
| R-026 | P2 | CI | Research GitHub Actions matrix for Node/shell checks, browser installation strategy, artifact retention, and explicit handling of unavailable browsers. | NOT STARTED |
| R-027 | P2 | Report consistency | Define generated status model so TASKS, AGENT_STATE, SELF_IMPROVEMENT, UPGRADE_REPORT, and quality JSON cannot contradict each other. | NOT STARTED |
| R-028 | P2 | Dependency governance | Research project-local dependency policy, license/SBOM reporting, vulnerability scanning, update cadence, and reproducible lockfiles. | NOT STARTED |
| R-029 | P2 | Observability | Define structured logs, correlation/task IDs, redaction, failure diagnostics, and artifact naming for multi-agent runs. | NOT STARTED |
| R-030 | P2 | Resource-aware autonomy | Research safe budgets for tool calls, tokens, wall-clock time, browser sessions, retries, and user approval checkpoints. | NOT STARTED |

## Research record template

For each entry, add a dated subsection containing:

- **Question and scope**
- **Primary sources** (official docs/specifications first)
- **Alternatives considered**
- **Compatibility / platform notes**
- **Security, licensing, and privacy implications**
- **Decision and rationale**
- **Proof-of-concept or reproducible test**
- **Known limitations**
- **Follow-up TODO IDs**
- **Status and reviewer**

## Initial primary-source index

Use these as starting points; verify current versions and exact behavior during each investigation.

### Browser automation and protocol
- Selenium documentation: https://www.selenium.dev/documentation/
- Selenium WebDriver API: https://www.selenium.dev/selenium/docs/api/javascript/
- Chrome DevTools Protocol: https://chromedevtools.github.io/devtools-protocol/
- Chrome DevTools Protocol Viewer: https://chromedevtools.github.io/devtools-protocol/tot/
- WebDriver specification: https://www.w3.org/TR/webdriver/
- WebDriver BiDi specification: https://www.w3.org/TR/webdriver-bidi/

### API contracts
- OpenAPI Specification: https://spec.openapis.org/oas/latest.html
- Swagger documentation: https://swagger.io/specification/
- Postman collection format: https://schema.postman.com/
- GraphQL specification: https://spec.graphql.org/
- AsyncAPI specification: https://www.asyncapi.com/docs/reference/specification/latest
- JSON Schema: https://json-schema.org/

### Accessibility and performance
- axe-core: https://github.com/dequelabs/axe-core
- Lighthouse: https://developer.chrome.com/docs/lighthouse/overview
- Web Vitals: https://web.dev/articles/vitals
- WCAG 2.2: https://www.w3.org/TR/WCAG22/

### MCP and OpenCode
- Model Context Protocol: https://modelcontextprotocol.io/
- OpenCode documentation: https://opencode.ai/docs/
- OpenCode agents: https://opencode.ai/docs/agents/
- OpenCode MCP servers: https://opencode.ai/docs/mcp-servers/

### GitHub CI and dependency governance
- GitHub Actions documentation: https://docs.github.com/actions
- Dependency graph: https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-the-dependency-graph
- GitHub dependency review: https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review

## Research governance

1. Prefer official specifications and project documentation; use issue discussions only to supplement documented behavior.
2. Record exact versions, retrieval date, and tested environment for version-sensitive findings.
3. Separate **documented capability**, **prototype-tested behavior**, and **production-verified behavior**.
4. Never mark research VERIFIED from documentation alone when the item concerns runtime behavior; include a reproducible proof-of-concept or test.
5. Never claim license approval from a search result or metadata hint alone. Record the actual license and applicable terms.
6. Link implementation TODOs to research IDs and update both when a decision changes.
7. Do not mark a research item complete if the finding is inconclusive; use DEFERRED and document the blocker.
