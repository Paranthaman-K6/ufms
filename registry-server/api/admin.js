// GET/POST / — password-protected dashboard for registry API keys.
// Keys are stored hashed and shown once, right after creation.

import crypto from "node:crypto";
import { createKey, createSession, revokeKey, safeEqual, verifySession } from "../lib/keys.js";
import { clientIp, intFromEnv, rateLimit } from "../lib/limits.js";
import { readKeys, storageMode, writeKeys } from "../lib/store.js";

const SESSION_COOKIE = "ufme_admin";
const CSRF_COOKIE = "ufme_csrf";
const COOKIE_PATH = "/";
const SESSION_MAX_AGE = 12 * 60 * 60;

const STYLE = `
:root{color-scheme:light dark;font-family:ui-sans-serif,system-ui,sans-serif}
*{box-sizing:border-box}
body{margin:0;padding:2rem 1rem;background:#0f172a;color:#e2e8f0}
main{max-width:56rem;margin:0 auto}
h1{font-size:1.4rem;margin:0 0 .25rem}
p{margin:.5rem 0}
.muted{color:#94a3b8}
.row{display:flex;gap:.75rem;flex-wrap:wrap;align-items:end;margin:1rem 0}
label{display:flex;flex-direction:column;gap:.3rem;font-size:.85rem}
input{font:inherit;padding:.5rem .6rem;border:1px solid #334155;border-radius:.4rem;background:#1e293b;color:inherit;min-width:14rem}
button{font:inherit;padding:.5rem .9rem;border:0;border-radius:.4rem;background:#38bdf8;color:#082f49;font-weight:600;cursor:pointer}
button.danger{background:#f87171;color:#450a0a}
table{width:100%;border-collapse:collapse;margin-top:1rem;font-size:.9rem}
th,td{text-align:left;padding:.5rem;border-bottom:1px solid #334155;vertical-align:middle}
code{font-family:ui-monospace,monospace;font-size:.85em}
.key{margin:1rem 0;padding:.75rem 1rem;border:1px solid #22c55e;border-radius:.5rem;background:#052e16}
.key code{display:block;margin-top:.4rem;word-break:break-all;color:#86efac}
.error{color:#fca5a5}
.card{border:1px solid #334155;border-radius:.6rem;padding:1rem 1.25rem;margin-top:1rem}
form{display:inline}
`;

function esc(value) {
  return String(value).replace(/[&<>"']/g, (char) => {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
  });
}

function secureFlag(req) {
  return req.headers?.["x-forwarded-proto"] === "https" ? "; Secure" : "";
}

function cookie(req, name) {
  for (const part of String(req.headers?.cookie || "").split(";")) {
    const [key, ...rest] = part.trim().split("=");
    if (key === name) return rest.join("=");
  }
  return "";
}

function csrfToken(req, res) {
  const existing = cookie(req, CSRF_COOKIE);
  if (existing) return existing;
  const token = crypto.randomBytes(18).toString("base64url");
  res.setHeader(
    "set-cookie",
    `${CSRF_COOKIE}=${token}; Path=${COOKIE_PATH}; HttpOnly; SameSite=Strict${secureFlag(req)}`,
  );
  return token;
}

function formBody(req) {
  const body = req.body;
  if (body && typeof body === "object") return body;
  return Object.fromEntries(new URLSearchParams(String(body || "")).entries());
}

function sendHtml(res, status, html, headers = {}) {
  res.statusCode = status;
  res.setHeader("content-type", "text/html; charset=utf-8");
  res.setHeader("cache-control", "no-store");
  res.setHeader("x-robots-tag", "noindex");
  res.setHeader("x-frame-options", "DENY");
  res.setHeader("x-content-type-options", "nosniff");
  res.setHeader("referrer-policy", "no-referrer");
  res.setHeader(
    "content-security-policy",
    "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
  );
  for (const [key, value] of Object.entries(headers)) res.setHeader(key, value);
  res.end(html);
}

function sendJson(res, status, body) {
  res.statusCode = status;
  res.setHeader("content-type", "application/json");
  res.setHeader("cache-control", "no-store");
  res.setHeader("x-robots-tag", "noindex");
  res.end(JSON.stringify(body));
}

function page(title, content) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>${esc(title)}</title><style>${STYLE}</style></head><body><main>${content}</main></body></html>`;
}

function loginPage(csrf, error = "") {
  return page(
    "UFME registry admin",
    `<h1>UFME registry admin</h1>
<p class="muted">Sign in to create and revoke registry API keys.</p>
${error ? `<p class="error">${esc(error)}</p>` : ""}
<div class="card"><form method="post" action="/">
<input type="hidden" name="_csrf" value="${esc(csrf)}">
<input type="hidden" name="action" value="login">
<label>Password<input type="password" name="password" autocomplete="current-password" required autofocus></label>
<div class="row"><button type="submit">Sign in</button></div>
</form></div>`,
  );
}

function dashboard(keys, csrf, newKey = "", notice = "") {
  const rows = keys.length
    ? keys
        .map(
          (key) => `<tr>
<td>${esc(key.label)}</td>
<td><code>${esc(key.prefix)}…</code></td>
<td>${esc(key.createdAt)}</td>
<td><form method="post" action="/">
<input type="hidden" name="_csrf" value="${esc(csrf)}">
<input type="hidden" name="action" value="revoke">
<input type="hidden" name="id" value="${esc(key.id)}">
<button class="danger" type="submit">Revoke</button>
</form></td>
</tr>`,
        )
        .join("")
    : `<tr><td colspan="4" class="muted">No keys yet. Create one below.</td></tr>`;

  return page(
    "UFME registry admin",
    `<h1>UFME registry admin</h1>
<p class="muted">${keys.length} active key${keys.length === 1 ? "" : "s"} · MCP endpoint <code>/mcp</code></p>
${notice ? `<p class="error">${esc(notice)}</p>` : ""}
${newKey ? `<div class="key"><strong>New key — copy it now, it is not shown again.</strong><code>${esc(newKey)}</code></div>` : ""}
<div class="card">
<h2>Create a key</h2>
<form method="post" action="/">
<input type="hidden" name="_csrf" value="${esc(csrf)}">
<input type="hidden" name="action" value="create">
<div class="row"><label>Label<input name="label" maxlength="60" placeholder="laptop" required></label><button type="submit">Create key</button></div>
</form>
</div>
<div class="card">
<h2>Keys</h2>
<table><thead><tr><th>Label</th><th>Prefix</th><th>Created</th><th></th></tr></thead><tbody>${rows}</tbody></table>
</div>
<div class="row">
<form method="post" action="/">
<input type="hidden" name="_csrf" value="${esc(csrf)}">
<input type="hidden" name="action" value="logout">
<button type="submit">Sign out</button>
</form>
</div>`,
  );
}

export default async function handler(req, res) {
  const password = process.env.REGISTRY_ADMIN_PASSWORD || "";
  if (!password) {
    sendHtml(
      res,
      503,
      page(
        "UFME registry admin",
        `<h1>Admin disabled</h1><p class="muted">Set <code>REGISTRY_ADMIN_PASSWORD</code> to enable this dashboard.</p>`,
      ),
    );
    return;
  }

  const authed = verifySession(cookie(req, SESSION_COOKIE));

  if (req.method === "GET" || req.method === "HEAD") {
    if (req.query?.action === "session") {
      sendJson(res, 200, { authenticated: authed });
      return;
    }
    const csrf = csrfToken(req, res);
    const keys = authed ? (await readKeys()).keys || [] : [];
    sendHtml(res, 200, authed ? dashboard(keys, csrf) : loginPage(csrf));
    return;
  }

  if (req.method !== "POST") {
    sendJson(res, 405, { error: "method not allowed" });
    return;
  }

  const body = formBody(req);
  const csrfCookie = cookie(req, CSRF_COOKIE);
  if (!body._csrf || !csrfCookie || !safeEqual(body._csrf, csrfCookie)) {
    sendJson(res, 403, { error: "invalid csrf token" });
    return;
  }

  if (body.action === "login") {
    const limit = rateLimit("admin-login", clientIp(req), intFromEnv("UFME_LOGIN_RATE_MAX", 10));
    if (!limit.ok) {
      res.setHeader("retry-after", String(limit.retryAfter));
      sendHtml(res, 429, loginPage(csrfCookie, "Too many attempts. Try again later."));
      return;
    }
    if (!safeEqual(body.password || "", password)) {
      sendHtml(res, 401, loginPage(csrfCookie, "Wrong password."));
      return;
    }
    res.setHeader(
      "set-cookie",
      `${SESSION_COOKIE}=${createSession()}; Path=${COOKIE_PATH}; HttpOnly; SameSite=Strict; Max-Age=${SESSION_MAX_AGE}${secureFlag(req)}`,
    );
    res.statusCode = 303;
    res.setHeader("location", "/");
    res.end();
    return;
  }

  if (!authed) {
    sendHtml(res, 401, loginPage(csrfCookie, "Session expired. Sign in again."));
    return;
  }

  if (body.action === "logout") {
    res.setHeader(
      "set-cookie",
      `${SESSION_COOKIE}=; Path=${COOKIE_PATH}; HttpOnly; SameSite=Strict; Max-Age=0${secureFlag(req)}`,
    );
    res.statusCode = 303;
    res.setHeader("location", "/");
    res.end();
    return;
  }

  if (body.action === "create") {
    const current = (await readKeys()).keys || [];
    if (process.env.VERCEL && storageMode() === "local") {
      sendHtml(
        res,
        503,
        dashboard(
          current,
          csrfCookie,
          "",
          "Connect a Blob store before creating keys; without it they are lost when the instance recycles.",
        ),
      );
      return;
    }
    const created = createKey(current, body.label);
    await writeKeys(created.keys);
    sendHtml(res, 200, dashboard(created.keys, csrfCookie, created.key));
    return;
  }

  if (body.action === "revoke") {
    const current = (await readKeys()).keys || [];
    const result = revokeKey(current, body.id);
    if (result.removed) await writeKeys(result.keys);
    sendHtml(res, result.removed ? 200 : 404, dashboard(result.keys, csrfCookie));
    return;
  }

  sendJson(res, 400, { error: `unknown action: ${body.action || ""}` });
}
