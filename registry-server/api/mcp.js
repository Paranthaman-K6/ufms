// Stateless MCP JSON-RPC 2.0 endpoint for the UFME library registry.
// POST /mcp with `Authorization: Bearer $REGISTRY_API_KEY`.

import crypto from "node:crypto";
import { query, remove, upsert, validateEntry } from "../lib/registry.js";
import { readRegistry, writeRegistry } from "../lib/store.js";

const SERVER_INFO = { name: "ufme-library-registry", version: "1.0.0" };
const PROTOCOL_VERSION = "2024-11-05";

const TOOLS = [
  {
    name: "registry_list",
    description: "List library-registry entries, optionally filtered.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Match name, npm package, category or reason." },
        category: { type: "string" },
        status: { type: "string", enum: ["candidate", "researched", "approved", "rejected"] },
        limit: { type: "integer", minimum: 1 },
      },
    },
  },
  {
    name: "registry_get",
    description: "Get one library-registry entry by name.",
    inputSchema: {
      type: "object",
      properties: { name: { type: "string" } },
      required: ["name"],
    },
  },
  {
    name: "registry_upsert",
    description: "Create or merge one library-registry entry.",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string" },
        category: { type: "string" },
        site: { type: "string" },
        license: { type: "string" },
        commercial: { type: "string" },
        install: { type: "string" },
        reason: { type: "string" },
        status: { type: "string", enum: ["candidate", "researched", "approved", "rejected"] },
        npm: { type: "string" },
        stars: { type: "integer", minimum: 0 },
        theme: {
          type: "object",
          description: "Optional theme payload: bg, surface, text, muted, accent, accent_alt, display, body, mono.",
        },
      },
      required: ["name", "category", "site", "license", "commercial", "install", "reason"],
    },
  },
  {
    name: "registry_remove",
    description: "Delete one library-registry entry by name.",
    inputSchema: {
      type: "object",
      properties: { name: { type: "string" } },
      required: ["name"],
    },
  },
];

function send(res, status, body) {
  res.statusCode = status;
  res.setHeader("content-type", "application/json");
  res.setHeader("cache-control", "no-store");
  res.end(JSON.stringify(body));
}

function authorized(header, expected) {
  const provided = String(header || "").replace(/^Bearer\s+/i, "");
  const a = Buffer.from(provided);
  const b = Buffer.from(expected);
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

async function callTool(name, args) {
  if (name === "registry_list") {
    return query(await readRegistry(), args || {});
  }
  if (name === "registry_get") {
    const entries = await readRegistry();
    const entry = entries.find((item) => item.name === args?.name);
    if (!entry) throw new Error(`not found: ${args?.name}`);
    return entry;
  }
  if (name === "registry_upsert") {
    const result = upsert(await readRegistry(), args || {});
    await writeRegistry(result.entries);
    return { entry: result.entry, created: result.created };
  }
  if (name === "registry_remove") {
    const result = remove(await readRegistry(), args?.name);
    if (!result.removed) throw new Error(`not found: ${args?.name}`);
    await writeRegistry(result.entries);
    return { removed: args.name };
  }
  throw new Error(`unknown tool: ${name}`);
}

async function handle(message) {
  const { id, method, params } = message;
  if (method === "initialize") {
    return {
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: params?.protocolVersion || PROTOCOL_VERSION,
        capabilities: { tools: {} },
        serverInfo: SERVER_INFO,
      },
    };
  }
  if (method === "ping") return { jsonrpc: "2.0", id, result: {} };
  if (method === "tools/list") return { jsonrpc: "2.0", id, result: { tools: TOOLS } };
  if (method === "tools/call") {
    const name = params?.name;
    try {
      const result = await callTool(name, params?.arguments);
      return {
        jsonrpc: "2.0",
        id,
        result: { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] },
      };
    } catch (error) {
      return {
        jsonrpc: "2.0",
        id,
        result: {
          content: [{ type: "text", text: String(error.message || error) }],
          isError: true,
        },
      };
    }
  }
  return { jsonrpc: "2.0", id, error: { code: -32601, message: `method not found: ${method}` } };
}

export default async function handler(req, res) {
  if (req.method === "OPTIONS") {
    res.statusCode = 204;
    res.setHeader("access-control-allow-origin", "*");
    res.setHeader("access-control-allow-headers", "authorization, content-type");
    res.setHeader("access-control-allow-methods", "POST, OPTIONS");
    res.end();
    return;
  }
  if (req.method !== "POST") {
    send(res, 405, { error: "method not allowed" });
    return;
  }

  const expected = process.env.REGISTRY_API_KEY || "";
  if (!expected) {
    send(res, 503, { error: "REGISTRY_API_KEY is not configured" });
    return;
  }
  if (!authorized(req.headers.authorization, expected)) {
    send(res, 401, { error: "unauthorized" });
    return;
  }

  let message;
  try {
    message = typeof req.body === "string" ? JSON.parse(req.body) : req.body;
  } catch {
    send(res, 400, { jsonrpc: "2.0", id: null, error: { code: -32700, message: "parse error" } });
    return;
  }
  if (!message || typeof message !== "object") {
    send(res, 400, { jsonrpc: "2.0", id: null, error: { code: -32600, message: "invalid request" } });
    return;
  }

  // Notifications have no id and expect no body.
  if (message.id === undefined || message.id === null) {
    if (message.method === "notifications/initialized") {
      res.statusCode = 202;
      res.end();
      return;
    }
    send(res, 200, { jsonrpc: "2.0", id: null, result: {} });
    return;
  }

  send(res, 200, await handle(message));
}

export { TOOLS, validateEntry };
