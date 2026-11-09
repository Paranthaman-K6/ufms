---
name: ufmw-frontend-design
description: Autonomous multi-agent frontend engineering with reference-driven design, implementation, visual auditing, accessibility, performance, security, and production readiness.
license: MIT
compatibility: opencode
metadata:
  category: frontend-engineering
  architecture: multi-agent
  scope: user
  depends_on:
    - universal-frontend-master
---

# ufmw-frontend-design

## Trigger

Use @ufmw-frontend-design to build, improve, redesign, integrate, or audit a website frontend from a brief, repository, API documentation, screenshots, or one or more live design references. Users may select individual elements from reference sites and specify where and how to adapt them.

## Core Rules

1. Never invent backend endpoints, fields, or roles. Implement only capabilities confirmed by the project's API and authentication contracts.
2. Preserve the existing stack. Record a justified decision before changing frameworks, build tools, or architecture.
3. Never run sudo, pacman, systemctl, doas, pkexec, or su. Never install system packages. Do not use Playwright or containers for this skill.
4. Preserve browser sandboxing. Explicit CI flags may differ when configured by the workflow.
5. Verify asset and library licenses before adding dependencies. Record material decisions and new dependencies.
6. Base audits on fresh evidence. Missing prerequisites must remain BLOCKED or SKIPPED, never silently pass.
7. Do not treat generated reference notes as completed application implementation. Implement in the target project's actual framework and component architecture.

## Agent Collaboration

The primary agent decides how to collaborate based on the task. It may work directly, use the orchestrator, invoke any useful specialist, use available MCP servers, research, tools, and parallel execution. Do not impose a fixed agent roster, mandatory sequence, delegation count, concurrency cap, or allowlist.

Profiles in profiles/ are advisory guidance for research depth, verification depth, browser coverage, and resource intensity. They never restrict collaboration, agent selection, tools, MCP servers, delegation, or parallelism. Safety requirements remain in force.

Available specialists include ufmw-orchestrator, ufmw-designer, ufmw-builder, ufme-backend-analyst, and ufmw-auditor. They are options, not required roles.

## Shared Script Dependency

This skill depends on universal-frontend-master for its shared scripts, browser runner, quality gates, templates, and evidence helpers. The installer must resolve this dependency when this skill is selected. In a checkout, helpers live in skills/universal-frontend-master/scripts/; after global installation they live in the corresponding OpenCode skill directory.

## Reference-Driven Design

1. Collect reference URLs supplied by the user. Do not require a reference for unrelated frontend work.
2. Inspect each URL with reference-inspect.js. Evidence is retained per URL and screenshots are stored separately.
3. Run reference-analyze.py to create or update REFERENCES.md and ELEMENT_MAP.md. Re-analysis must preserve existing element selections and mappings.
4. Let the user select only elements they want. Record the intended destination and aspects (visual appearance, behavior, animation, layout, or a combination). Untouched placeholders are not selected mappings.
5. Run reference-match.py. A mapping is matched only when it resolves to real source evidence and contains a destination and intended aspects.
6. Run reference-adapt.py to prepare an implementation brief from measured source styles. The script does not edit application source code; implement the adaptation in the target framework, component conventions, design tokens, semantics, and responsive behavior.
7. Run reference-verify.js with the target URL after implementation. It inspects both pages and compares selected selectors, using each element's own reference URL. Style comparison does not prove behavior or animation; those require interaction-specific checks and must be reported separately.

## Shared Helpers

The scripts are provided by universal-frontend-master:

| Script | Purpose |
|---|---|
| reference-inspect.js | Inspect a live reference and capture DOM, computed styles, and unique element selectors/screenshots |
| reference-analyze.py | Build or update the reference catalog, stable element IDs, and mapping file |
| reference-match.py | Validate selected elements and create a match plan across references |
| reference-adapt.py | Produce a measured-style implementation brief |
| reference-verify.js | Compare selected reference and target elements |
| element-catalog.py | Maintain reusable reference-element records |
| detect-stack.sh | Detect the existing frontend stack and project scripts |
| browser-test.sh | Run native Selenium browser checks |
| audit-a11y.js | Run axe-core accessibility checks |
| audit-perf.sh | Run Lighthouse performance checks |
| visual-diff.js | Compare browser screenshots |
| quality-check.py | Combine test and audit evidence into a quality report |
| self-improve.py | Review skill source and installed copies |

## OpenCode Commands

These are OpenCode slash commands, not a standalone uFMW shell executable:

| Command | Purpose |
|---|---|
| /ufmw/reference-add | Add a reference URL |
| /ufmw/reference-analyze | Inspect/analyze reference URLs and generate the element map |
| /ufmw/reference-inspect | Inspect a selected element |
| /ufmw/reference-list | List known references |
| /ufmw/reference-match | Validate selected mappings |
| /ufmw/reference-adapt | Prepare implementation briefs |
| /ufmw/reference-verify | Verify implemented reference elements |
| /profile/lite, /profile/standard, /profile/advanced, /profile/autonomous | Select advisory execution depth |

## Quality and Delivery

- Implement selected elements rather than stopping at analysis or generated notes.
- Preserve accessible semantics, keyboard behavior, responsive layouts, reduced-motion preferences, and existing project contracts.
- Run relevant project tests, browser checks, accessibility/performance/visual audits, and security checks.
- Fix findings and repeat affected checks.
- Record what was actually run, failures, blocked checks, and remaining limitations.

## Compatibility

This skill uses the shared universal-frontend-master helpers and is compatible with ufmw-seo-protocol. Both use the project .ufme memory directory. The installer resolves declared skill dependencies automatically.
