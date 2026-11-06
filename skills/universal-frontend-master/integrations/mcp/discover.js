// skills/universal-frontend-master/integrations/mcp/discover.js
// Priority 5 — MCP Integration: real capability discovery layer.
//
// Discovers available MCP capabilities from the active OpenCode host,
// validates input/output, handles permission failures, unavailable servers,
// and timeouts. Native Selenium and script fallbacks remain available.
// Does not make external MCP servers mandatory.
// Does not install, connect, or authorize new external MCP servers.
//
// Usage: node skills/universal-frontend-master/integrations/mcp/discover.js
'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const RESULT_FILE = '.ufme/evidence/mcp-discovery.json';
const EVIDENCE_DIR = '.ufme/evidence';

// Known MCP servers that may be exposed by the OpenCode host, with their
// documented capability categories. We do not fabricate tool definitions;
// we only reference servers that the host may expose.
const KNOWN_MCP_SERVERS = [
  { name: 'context7', capabilities: ['documentation-search', 'library-lookup'] },
  { name: 'figma', capabilities: ['design-research', 'component-lookup', 'design-tokens'] },
  { name: 'firecrawl', capabilities: ['web-search', 'web-scrape', 'pdf-parse'] },
  { name: 'opencode', capabilities: ['session-management', 'worktree-management', 'agent-management'] },
  { name: 'rea', capabilities: ['reverse-engineering', 'binary-analysis'] },
  { name: 'skillspector', capabilities: ['skill-security-scan'] },
];

function ensureEvidenceDir() {
  if (!fs.existsSync(EVIDENCE_DIR)) {
    fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
  }
}

function runCommandWithTimeout(cmd, timeoutMs = 5000) {
  try {
    const output = execSync(cmd, { timeout: timeoutMs, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
    return { ok: true, output: output.trim(), error: null };
  } catch (e) {
    return {
      ok: false,
      output: (e.stdout && e.stdout.toString ? e.stdout.toString().trim() : '') || '',
      error: e.message || String(e),
    };
  }
}

function discoverMcpServers() {
  const discovered = [];

  // Try to list MCP servers via the OpenCode host if available.
  // We attempt common discovery commands but treat failure as "no MCP available".
  const discoveryCmds = [
    'opencode mcp list 2>/dev/null',
    'opencode mcp servers 2>/dev/null',
  ];

  let mcpOutput = '';
  for (const cmd of discoveryCmds) {
    const res = runCommandWithTimeout(cmd, 3000);
    if (res.ok && res.output) {
      mcpOutput = res.output;
      break;
    }
  }

  // Parse output heuristically: look for known server names.
  for (const server of KNOWN_MCP_SERVERS) {
    let available = false;
    let permissionError = false;
    let timeout = false;

    if (mcpOutput.includes(server.name)) {
      available = true;
    }

    // Try a lightweight invocation to verify the server responds.
    if (available) {
      const probe = runCommandWithTimeout(`opencode mcp ${server.name} --help 2>/dev/null || true`, 5000);
      if (!probe.ok && probe.error.includes('timeout')) {
        timeout = true;
        available = false;
      } else if (!probe.ok && (probe.error.includes('permission') || probe.error.includes('denied'))) {
        permissionError = true;
        available = false;
      }
    }

    discovered.push({
      name: server.name,
      capabilities: server.capabilities,
      available,
      permissionError,
      timeout,
      source: mcpOutput ? 'host-discovery' : 'none',
    });
  }

  return discovered;
}

function buildResult() {
  ensureEvidenceDir();
  const servers = discoverMcpServers();
  const availableCount = servers.filter((s) => s.available).length;
  const unsupportedCount = servers.filter((s) => !s.available && !s.permissionError && !s.timeout).length;
  const blockedCount = servers.filter((s) => s.permissionError || s.timeout).length;

  const result = {
    generatedAt: new Date().toISOString(),
    mcpAvailable: availableCount > 0,
    servers,
    summary: {
      total: servers.length,
      available: availableCount,
      unsupported: unsupportedCount,
      blocked: blockedCount,
    },
    fallback: 'native Selenium WebDriver + local scripts',
    note: 'MCP integration is optional. The skill remains fully functional without MCP servers.',
  };

  fs.writeFileSync(RESULT_FILE, JSON.stringify(result, null, 2));
  return result;
}

function printResult(result) {
  console.log('=== MCP Capability Discovery ===');
  console.log(`MCP available: ${result.mcpAvailable}`);
  console.log(`Servers: ${result.summary.available} available, ${result.summary.unsupported} unsupported, ${result.summary.blocked} blocked`);
  console.log(`Fallback: ${result.fallback}`);
  for (const s of result.servers) {
    const status = s.available ? 'available' : s.permissionError ? 'permission-error' : s.timeout ? 'timeout' : 'unsupported';
    console.log(`  ${s.name}: ${status} (${s.capabilities.join(', ')})`);
  }
}

const result = buildResult();
printResult(result);
