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
process.env.UFME_KEYS_FILE = path.join(TMP, "admin-keys.json");
delete process.env.BLOB_READ_WRITE_TOKEN;
process.env.REGISTRY_API_KEY = "test-key";
process.env.REGISTRY_ADMIN_PASSWORD = "admin-pass";
process.env.REGISTRY_ADMIN_SECRET = "test-secret";

const { default: handler } = await import("../api/mcp.js");
const { default: healthHandler } = await import("../api/health.js");
const { default: adminHandler } = await import("../api/admin.js");
const { resetLimits } = await import("../lib/limits.js");

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

async function call(target, { method = "GET", headers = {}, body, query } = {}) {
  const res = mockRes();
  await target({ method, headers, body, query }, res);
  return res;
}

function cookieValue(res, name) {
  for (const part of String(res.headers["set-cookie"] || "").split(";")) {
    const [key, ...rest] = part.trim().split("=");
    if (key === name) return rest.join("=");
  }
  return "";
}

async function adminSession() {
  const res = await call(adminHandler, {});
  const csrf = cookieValue(res, "ufme_csrf");
  return { csrf, cookie: `ufme_csrf=${csrf}` };
}

async function login() {
  const { csrf, cookie } = await adminSession();
  const res = await call(adminHandler, {
    method: "POST",
    headers: { cookie },
    body: { action: "login", password: "admin-pass", _csrf: csrf },
  });
  const session = cookieValue(res, "ufme_admin");
  return { status: res.statusCode, csrf, cookie: `${cookie}; ufme_admin=${session}` };
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

await test("mcp rejects a non-JSON content type", async () => {
  const res = await call(handler, {
    method: "POST",
    headers: { authorization: "Bearer test-key", "content-type": "text/plain" },
    body: { jsonrpc: "2.0", id: 1, method: "initialize", params: {} },
  });
  assert.equal(res.statusCode, 415);
});

await test("mcp rejects an oversized body", async () => {
  process.env.UFME_MAX_BODY_BYTES = "80";
  const res = await call(handler, {
    method: "POST",
    headers: { authorization: "Bearer test-key", "content-type": "application/json" },
    body: { jsonrpc: "2.0", id: 1, method: "initialize", params: { pad: "x".repeat(200) } },
  });
  delete process.env.UFME_MAX_BODY_BYTES;
  assert.equal(res.statusCode, 413);
});

await test("mcp rate limits per IP", async () => {
  process.env.UFME_MCP_RATE_MAX = "2";
  resetLimits();
  const headers = { authorization: "Bearer test-key", "content-type": "application/json" };
  const body = { jsonrpc: "2.0", id: 1, method: "initialize", params: {} };
  await call(handler, { method: "POST", headers, body });
  await call(handler, { method: "POST", headers, body });
  const blocked = await call(handler, { method: "POST", headers, body });
  delete process.env.UFME_MCP_RATE_MAX;
  resetLimits();
  assert.equal(blocked.statusCode, 429);
  assert.ok(blocked.headers["retry-after"]);
});

await test("admin is disabled without REGISTRY_ADMIN_PASSWORD", async () => {
  const saved = process.env.REGISTRY_ADMIN_PASSWORD;
  delete process.env.REGISTRY_ADMIN_PASSWORD;
  const res = await call(adminHandler, {});
  process.env.REGISTRY_ADMIN_PASSWORD = saved;
  assert.equal(res.statusCode, 503);
});

await test("admin serves the login page with a csrf cookie", async () => {
  const { csrf } = await adminSession();
  assert.ok(csrf);
  const res = await call(adminHandler, {});
  assert.equal(res.statusCode, 200);
  assert.match(res.body, /name="password"/);
  assert.equal(res.headers["x-robots-tag"], "noindex");
});

await test("admin rejects a POST without csrf", async () => {
  const res = await call(adminHandler, {
    method: "POST",
    body: { action: "login", password: "admin-pass" },
  });
  assert.equal(res.statusCode, 403);
});

await test("admin rejects a wrong password", async () => {
  const { csrf, cookie } = await adminSession();
  const res = await call(adminHandler, {
    method: "POST",
    headers: { cookie },
    body: { action: "login", password: "nope", _csrf: csrf },
  });
  assert.equal(res.statusCode, 401);
});

await test("admin rate limits login attempts", async () => {
  const { csrf, cookie } = await adminSession();
  process.env.UFME_LOGIN_RATE_MAX = "1";
  resetLimits();
  const body = { action: "login", password: "nope", _csrf: csrf };
  await call(adminHandler, { method: "POST", headers: { cookie }, body });
  const blocked = await call(adminHandler, { method: "POST", headers: { cookie }, body });
  delete process.env.UFME_LOGIN_RATE_MAX;
  resetLimits();
  assert.equal(blocked.statusCode, 429);
});

let createdKey = "";
let createdId = "";

await test("admin logs in and creates a key that works on /mcp", async () => {
  const { status, csrf, cookie } = await login();
  assert.equal(status, 303);

  const session = await call(adminHandler, { query: { action: "session" }, headers: { cookie } });
  assert.equal(JSON.parse(session.body).authenticated, true);

  const res = await call(adminHandler, {
    method: "POST",
    headers: { cookie },
    body: { action: "create", label: "test-laptop", _csrf: csrf },
  });
  assert.equal(res.statusCode, 200);
  createdKey = res.body.match(/ufme_[A-Za-z0-9_-]{20,}/)[0];
  createdId = res.body.match(/name="id" value="([^"]+)"/)[1];

  const used = await rpc("initialize", {}, { key: createdKey });
  assert.equal(used.status, 200);
});

await test("admin revokes the key and the root key still works", async () => {
  const { csrf, cookie } = await login();
  const res = await call(adminHandler, {
    method: "POST",
    headers: { cookie },
    body: { action: "revoke", id: createdId, _csrf: csrf },
  });
  assert.equal(res.statusCode, 200);

  const revoked = await rpc("initialize", {}, { key: createdKey });
  assert.equal(revoked.status, 401);

  const root = await rpc("initialize", {}, { key: "test-key" });
  assert.equal(root.status, 200);
});

await test("health reports ok and entry count when deep", async () => {
  const res = await call(healthHandler, { query: { deep: "1" } });
  assert.equal(res.statusCode, 200);
  const body = JSON.parse(res.body);
  assert.equal(body.status, "ok");
  assert.equal(body.storage, "local");
  assert.equal(body.entries, (await tool("registry_list", {})).data.length);
  assert.equal(res.headers["x-robots-tag"], "noindex");
});

await test("health reports degraded on Vercel without Blob", async () => {
  process.env.VERCEL = "1";
  const res = await call(healthHandler, {});
  delete process.env.VERCEL;
  assert.equal(res.statusCode, 503);
  const body = JSON.parse(res.body);
  assert.equal(body.status, "degraded");
  assert.equal(body.storage, "local");
});

await test("admin refuses to create ephemeral keys on Vercel", async () => {
  const { csrf, cookie } = await login();
  process.env.VERCEL = "1";
  const res = await call(adminHandler, {
    method: "POST",
    headers: { cookie },
    body: { action: "create", label: "ephemeral", _csrf: csrf },
  });
  delete process.env.VERCEL;
  assert.equal(res.statusCode, 503);
  assert.match(res.body, /lost when the instance recycles/);
});

await test("health returns 503 when nothing is configured", async () => {
  const savedKey = process.env.REGISTRY_API_KEY;
  const keysFile = path.join(TMP, "admin-keys.json");
  const savedKeys = fs.readFileSync(keysFile, "utf8");
  fs.writeFileSync(keysFile, JSON.stringify({ keys: [] }));
  delete process.env.REGISTRY_API_KEY;
  const res = await call(healthHandler, {});
  process.env.REGISTRY_API_KEY = savedKey;
  fs.writeFileSync(keysFile, savedKeys);
  assert.equal(res.statusCode, 503);
  assert.equal(JSON.parse(res.body).status, "unconfigured");
});

fs.rmSync(TMP, { recursive: true, force: true });

console.log(`\n${passed} passed, ${failures.length} failed`);
process.exit(failures.length ? 1 : 0);
