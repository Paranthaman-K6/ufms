// Registry server tests: auth, MCP handshake, tool calls, seed validity.
// Run: node test/run.mjs

import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, "..");
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "ufme-registry-"));
const DATA = path.join(TMP, "library-registry.json");

process.env.UFME_REGISTRY_FILE = DATA;
delete process.env.BLOB_READ_WRITE_TOKEN;
process.env.REGISTRY_API_KEY = "test-key";

const { default: handler } = await import("../api/mcp.js");

let passed = 0;
const failures = [];

async function test(name, fn) {
  try {
    await fn();
    passed += 1;
    console.log(`PASS: ${name}`);
  } catch (error) {
    failures.push({ name, error });
    console.log(`FAIL: ${name}: ${error.message}`);
  }
}

function mockRes() {
  return {
    statusCode: 0,
    headers: {},
    body: undefined,
    setHeader(key, value) {
      this.headers[key.toLowerCase()] = value;
    },
    end(payload) {
      this.body = payload;
    },
  };
}

async function rpc(method, params, { key = "test-key", id = 1 } = {}) {
  const req = {
    method: "POST",
    headers: key === null ? {} : { authorization: `Bearer ${key}` },
    body: { jsonrpc: "2.0", id, method, params },
  };
  const res = mockRes();
  await handler(req, res);
  return { status: res.statusCode, json: res.body ? JSON.parse(res.body) : undefined };
}

async function tool(name, args, options) {
  const { status, json } = await rpc("tools/call", { name, arguments: args }, options);
  assert.equal(status, 200);
  const text = json.result.content[0].text;
  return { isError: Boolean(json.result.isError), data: json.result.isError ? text : JSON.parse(text) };
}

function seed() {
  return JSON.parse(fs.readFileSync(path.join(ROOT, "seed.json"), "utf8"));
}

await test("seed has at least 40 valid entries", () => {
  const entries = seed();
  assert.ok(entries.length >= 40, `only ${entries.length} entries`);
  for (const entry of entries) {
    for (const field of ["name", "category", "site", "license", "commercial", "install", "reason"]) {
      assert.ok(entry[field], `${entry.name || "?"} missing ${field}`);
    }
    assert.match(entry.site, /^https:\/\//, `${entry.name} site`);
    assert.ok(Number.isInteger(entry.stars) && entry.stars >= 0, `${entry.name} stars`);
    assert.ok(["yes", "verify", "no"].includes(entry.commercial), `${entry.name} commercial`);
  }
});

await test("missing server key returns 503", async () => {
  const saved = process.env.REGISTRY_API_KEY;
  delete process.env.REGISTRY_API_KEY;
  const { status } = await rpc("initialize", {});
  process.env.REGISTRY_API_KEY = saved;
  assert.equal(status, 503);
});

await test("wrong key returns 401", async () => {
  const { status } = await rpc("initialize", {}, { key: "nope" });
  assert.equal(status, 401);
});

await test("initialize reports server info", async () => {
  const { status, json } = await rpc("initialize", { protocolVersion: "2025-03-26" });
  assert.equal(status, 200);
  assert.equal(json.result.protocolVersion, "2025-03-26");
  assert.equal(json.result.serverInfo.name, "ufme-library-registry");
  assert.ok(json.result.capabilities.tools);
});

await test("tools/list exposes the four registry tools", async () => {
  const { json } = await rpc("tools/list", {});
  const names = json.result.tools.map((entry) => entry.name).sort();
  assert.deepEqual(names, ["registry_get", "registry_list", "registry_remove", "registry_upsert"]);
});

await test("registry_list returns the seed", async () => {
  const { isError, data } = await tool("registry_list", {});
  assert.equal(isError, false);
  assert.equal(data.length, seed().length);
});

await test("registry_list filters by query and category", async () => {
  const { data } = await tool("registry_list", { query: "motion", category: "animation" });
  assert.ok(data.length >= 1);
  assert.ok(data.every((entry) => entry.category === "animation"));
});

await test("registry_upsert creates then merges", async () => {
  const entry = {
    name: "acme/ui",
    category: "ui",
    site: "https://example.com/acme-ui",
    license: "MIT",
    commercial: "yes",
    install: "npm i @acme/ui",
    reason: "test entry",
    status: "candidate",
  };
  const created = await tool("registry_upsert", entry);
  assert.equal(created.isError, false);
  assert.equal(created.data.created, true);

  const merged = await tool("registry_upsert", { name: "acme/ui", status: "approved" });
  assert.equal(merged.data.created, false);
  assert.equal(merged.data.entry.status, "approved");
  assert.equal(merged.data.entry.license, "MIT");
  assert.ok(fs.existsSync(DATA));
});

await test("registry_upsert keeps a theme payload", async () => {
  const theme = {
    bg: "#0a1929", surface: "#102a43", text: "#e6f0f5",
    muted: "#829ab1", accent: "#2d8b8b", accent_alt: "#64d2d2",
    display: "IBM Plex Sans", body: "IBM Plex Sans", mono: "IBM Plex Mono",
  };
  const created = await tool("registry_upsert", {
    name: "theme/midnight-ocean",
    category: "theme",
    site: "https://github.com/anthropics/skills",
    license: "Apache-2.0",
    commercial: "yes",
    install: "built-in",
    reason: "curated theme",
    theme,
  });
  assert.equal(created.isError, false);
  const fetched = await tool("registry_get", { name: "theme/midnight-ocean" });
  assert.deepEqual(fetched.data.theme, theme);
  await tool("registry_remove", { name: "theme/midnight-ocean" });
});

await test("registry_upsert rejects an invalid entry", async () => {
  const { isError, data } = await tool("registry_upsert", { name: "broken" });
  assert.equal(isError, true);
  assert.match(data, /missing 'category'/);
});

await test("registry_get returns the stored entry", async () => {
  const { isError, data } = await tool("registry_get", { name: "acme/ui" });
  assert.equal(isError, false);
  assert.equal(data.name, "acme/ui");
});

await test("registry_remove deletes the entry", async () => {
  const { isError, data } = await tool("registry_remove", { name: "acme/ui" });
  assert.equal(isError, false);
  assert.equal(data.removed, "acme/ui");
  const after = await tool("registry_get", { name: "acme/ui" });
  assert.equal(after.isError, true);
});

await test("unknown method returns JSON-RPC error", async () => {
  const { json } = await rpc("nope", {});
  assert.equal(json.error.code, -32601);
});

await test("unknown tool returns an MCP tool error", async () => {
  const { isError, data } = await tool("registry_nope", {});
  assert.equal(isError, true);
  assert.match(data, /unknown tool/);
});

fs.rmSync(TMP, { recursive: true, force: true });

console.log(`\n${passed} passed, ${failures.length} failed`);
process.exit(failures.length ? 1 : 0);
