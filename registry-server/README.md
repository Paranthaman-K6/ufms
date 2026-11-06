# UFME library-registry server

Optional MCP server that stores one shared library registry in Vercel Blob, with
a password-protected dashboard for API keys. The skill works without it; the
local Markdown registry stays the default.

## Endpoints

| Route | Method | Purpose |
|-------|--------|---------|
| `/mcp` | `POST` | JSON-RPC 2.0 MCP endpoint |
| `/health` | `GET` | liveness and configuration probe |
| `/admin` | `GET`/`POST` | API-key dashboard |

`/health` and `/admin` are rewritten in `vercel.json`. Both send
`x-robots-tag: noindex`.

## Auth

`/mcp` accepts `Authorization: Bearer <key>` where `<key>` is either:

- the bootstrap `REGISTRY_API_KEY` from the environment, or
- a key created in `/admin` (stored hashed).

| Case | Status |
|------|--------|
| No bootstrap key and no stored keys | `503` |
| Missing or wrong key | `401` |
| Valid request | `200` |

Keys created in the dashboard are shown once, stored as SHA-256 hashes, and
revoked by deleting the record.

## Health

```bash
curl -s https://your-app.vercel.app/health
# {"status":"ok","service":"ufme-library-registry","version":"1.0.0",
#  "auth":{"rootKey":true,"storedKeys":0}}

curl -s "https://your-app.vercel.app/health?deep=1"
# adds "entries": 52 (reads the registry)
```

| Case | Status | `status` |
|------|--------|----------|
| Bootstrap key or at least one stored key | `200` | `ok` |
| Neither configured | `503` | `unconfigured` |
| `?deep=1` and the registry cannot be read | `503` | `degraded` |

The response never contains key material.

## Admin dashboard

Set `REGISTRY_ADMIN_PASSWORD` (and optionally `REGISTRY_ADMIN_SECRET`) in the
Vercel project, then open `/admin`.

- Sign in with the password. The session is an HMAC-signed, `HttpOnly`,
  `SameSite=Strict` cookie valid for 12 hours.
- Create a key with a label; copy it from the one-time callout.
- Revoke any key; it stops working on the next `/mcp` request.
- POSTs require the double-submit CSRF token rendered into the form.
- Without `REGISTRY_ADMIN_PASSWORD` the dashboard returns `503` and no session
  can be created.

The dashboard is a single server-rendered page with an inline stylesheet and a
strict CSP; it loads no external assets.

## Bot protection

| Guard | Default | Env |
|-------|---------|-----|
| `/mcp` requests per minute per IP | 60 | `UFME_MCP_RATE_MAX` |
| Admin login attempts per minute per IP | 10 | `UFME_LOGIN_RATE_MAX` |
| JSON body size | 256 KiB | `UFME_MAX_BODY_BYTES` |

Exceeding a limit returns `429` with `retry-after`; an oversized body returns
`413`; a non-JSON content type on `/mcp` returns `415`.

The limiter is an in-memory fixed window per lambda instance, so it resets on
cold start and does not aggregate across instances. For distributed protection
add Vercel Firewall or Upstash. See `lib/limits.js`.

## Tools

| Tool | Arguments | Behaviour |
|------|-----------|-----------|
| `registry_list` | `query?`, `category?`, `status?`, `limit?` | filtered entries |
| `registry_get` | `name` | one entry |
| `registry_upsert` | entry fields | create or merge by `name` |
| `registry_remove` | `name` | delete |

Entry fields: `name`, `category`, `site` (https), `license`, `commercial`,
`install`, `reason`, `status` (`candidate|researched|approved|rejected`),
optional `npm`, `stars`.

Entries with `category: "theme"` may carry a `theme` object (`bg`, `surface`,
`text`, `muted`, `accent`, `accent_alt`, `display`, `body`, optional `mono`).
`theme-showcase.py` appends them to the local palette catalog.

## Storage

- With `BLOB_READ_WRITE_TOKEN`: `ufme/library-registry.json` and
  `ufme/admin-keys.json` in Vercel Blob (`access: public`,
  `allowOverwrite: true`, `addRandomSuffix: false`).
- Without it: `.data/library-registry.json` and `.data/admin-keys.json` next to
  this directory. Fine locally; ephemeral on Vercel, so set the token in
  production.

On first read, a missing registry falls back to `seed.json`; a missing key store
falls back to no keys.

## Deploy

```bash
npm install
npm test
vercel deploy
```

Set in the Vercel project:

```bash
vercel env add REGISTRY_API_KEY production        # optional bootstrap key
vercel env add REGISTRY_ADMIN_PASSWORD production
vercel env add REGISTRY_ADMIN_SECRET production   # optional, defaults to the password
vercel env add BLOB_READ_WRITE_TOKEN production
```

## Client

```bash
export UFME_REGISTRY_URL="https://your-app.vercel.app/mcp"
export UFME_REGISTRY_KEY="a key from /admin"

python3 ../skills/universal-frontend-master/scripts/registry-remote.py --list motion
python3 ../skills/universal-frontend-master/scripts/registry-remote.py --seed
```

Unset env → exit `3`, and `search-libraries.py` falls back to local files silently.

## Seed

`seed.json` is generated from live GitHub metadata: 52 frontend repositories with
stars, SPDX license, npm package, category and reason. `NOASSERTION` licenses are
marked `commercial: "verify"` and must be checked before use.

## Test

```bash
node test/run.mjs
```

Covers 503/401 auth, `initialize`, `tools/list`, list/get/upsert/remove,
validation, unknown methods/tools, seed validity, health (`200`/`503`/deep),
`415`/`413`/`429`, and the admin login, CSRF, create, use and revoke flow. No
network or Blob token required.
