# MCP Integration (optional)

universal-frontend-master supports optional Model Context Protocol (MCP) integration
for capability discovery. Native Selenium WebDriver and local scripts remain the
default fallbacks; MCP is never mandatory.

## Available MCP servers (as exposed by the OpenCode host)

| Server | Capabilities | Optional in UFME |
|--------|--------------|------------------|
| context7 | Library/documentation lookup (resolve-library-id, query-docs) | Yes — research |
| figma | Design files, components, design system tokens (Figma/FigJam/Slides) | Yes — design |
| firecrawl | Web search, scrape, parse (PDF, JSON) | Yes — research/assets |
| opencode | Session/worktree/agent management | Yes — orchestration |
| rea | Reverse-engineering of local binaries, browser pages, runtimes | No — not used |
| skillspector | Security scan of AI agent skills before install | Yes — supply chain |

## Integration rules
- Discover actual available tools and their documented interfaces; do not invent
  MCP tool names or schemas.
- MCP integrations are optional. If an MCP server is unavailable, the skill falls
  back to native Selenium + local scripts.
- Do not introduce Playwright as a mandatory dependency.
- No sudo/pacman/systemctl; MCP servers must not require root.

## How to use
MCP servers are configured by the OpenCode host, not by this skill. The skill
references them only as optional capability sources. The orchestrator decides
whether to use an MCP server or a local script for a given task.
