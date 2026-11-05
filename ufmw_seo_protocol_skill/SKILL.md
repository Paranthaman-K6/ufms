---
name: ufmw-seo-protocol
description: Arch Linux-native autonomous SEO engineering skill for technical SEO, on-page optimization, structured data, internal linking, crawlability, indexing, keyword research, and Google Search Console integration.
license: MIT
compatibility: opencode
metadata:
  category: seo-engineering
  architecture: multi-agent
  scope: user
  depends_on:
    - ufmw-frontend-design
---

# ufmw-seo-protocol

## Trigger

Use `@ufmw-seo-protocol` when the task is to audit, optimize, or monitor a website for search engine optimization — technical SEO, on-page SEO, content optimization, structured data, internal linking, crawlability, indexing diagnostics, rendering analysis, redirects, sitemap validation, robots.txt analysis, keyword research, search-intent analysis, content-gap detection, or performance optimization for SEO.

## Hard Rules

1. Never fabricate search metrics. Report only measured data from crawl, Lighthouse, axe-core, or Google Search Console (when credentials are configured). Mock data must be clearly labeled as fixtures.
2. Preserve the existing website architecture. Inspect each target website before modifying it; use its existing framework, routing, components, and metadata implementation.
3. Apply only safe, non-destructive SEO fixes by default (meta tags, alt text, canonical tags, structured data, sitemap, robots.txt). Framework migrations or wholesale rewrites require explicit user approval.
4. Never run `sudo`, `pacman`, `systemctl`, `doas`, `pkexec`, or `su`; never install system packages; no Playwright, no containers; browser sandbox preserved.
5. Evidence-first SEO: read `.ufme/evidence/seo-results.json`, `seo-crawl.json`, `seo-plan.json` BEFORE making changes; verify fixes by re-crawling.

## Agent Router

| Need | @agent |
|------|--------|
| Start SEO session, plan, acceptance checks, memory | `@ufmw-seo-protocol` (entry) |
| Technical SEO — crawl, indexability, redirects, sitemap, robots.txt | `@ufmw-seo-technical` |
| On-page SEO — titles, meta descriptions, headings, content | `@ufmw-seo-content` |
| Keyword research, intent analysis, content-gap detection | `@ufmw-seo-analyst` |
| SEO audit from evidence JSON | `@ufmw-seo-auditor` |
| Delegate to design skill for source-code SEO fixes | `@ufmw-builder` (from ufmw-frontend-design) |

Invoke `@ufmw-seo-protocol` to start; it coordinates the SEO workflow across both skills.

## CLI Commands (ufmw/)

| Command | Purpose |
|---------|---------|
| `ufmw seo init` | Initialize SEO project memory |
| `ufmw seo crawl <url>` | Crawl website and extract SEO data |
| `ufmw seo analyze <url>` | Analyze crawl data for SEO issues |
| `ufmw seo plan <url>` | Generate prioritized SEO improvement plan |
| `ufmw seo fix <url> --apply-safe` | Apply safe automated SEO fixes |
| `ufmw seo verify <url>` | Re-crawl and verify fixes |
| `ufmw seo report <url>` | Generate SEO_AUDIT_REPORT.md |
| `ufmw seo run --profile autonomous --mode full --apply-safe` | Full autonomous SEO run |
| `ufmw seo monitor <url>` | Monitor SEO metrics over time |
| `ufmw seo gsc <url>` | Google Search Console integration |

## Primary Autonomous Command

```bash
ufmw seo run --profile autonomous --mode full --apply-safe
```

Executes the complete SEO workflow: discovery → crawl → analyze → plan → implement → verify → report → monitor.

## Compatibility

This skill depends on `ufmw_frontend_design_skill` for browser automation (Selenium), quality gate, and agent infrastructure. Both skills share the `.ufme/` project memory directory and the `ufmw/` CLI command namespace.
