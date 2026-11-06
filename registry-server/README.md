# UFME library-registry server

Optional MCP server that stores one shared library registry in Vercel Blob, with
a password-protected dashboard for API keys. The skill works without it; the
local Markdown registry stays the default.

## Endpoints

| Route | Method | Purpose |
|-------|--------|---------|
| `/mcp` | `POST` | JSON-RPC 2.0 MCP endpoint |
| `/health` | `GET` | liveness and configuration probe |
| `/` | `GET`/`POST` | API-key dashboard |

`/health` and `/` are rewritten in `vercel.json`. Both send
`x-robots-tag: noindex`.

## Auth

`/mcp` accepts `Authorization: Bearer <key>` where `<key>` is either:

- the bootstrap `REGISTRY_API_KEY` from the environment, or
- a key created in `/` (stored hashed).

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
| On Vercel without Blob storage | `503` | `degraded` |

The response never contains key material. `storage` is `blob` when a Blob store
is configured and `local` otherwise.

## Admin dashboard

Set `REGISTRY_ADMIN_PASSWORD` (and optionally `REGISTRY_ADMIN_SECRET`) in the
Vercel project, then open `/`.

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
cold start and does not aggregate across instances. The free Hobby plan includes
3 WAF custom rules and 10 IP blocks at the edge — use one rule on `/mcp` and one
on `/` for distributed blocking. See `lib/limits.js`.

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

- With a Blob store: `ufme/library-registry.json` and `ufme/admin-keys.json`
  (`access: public`, `allowOverwrite: true`, `addRandomSuffix: false`).
  `BLOB_READ_WRITE_TOKEN` works, and so does a store connected in the Vercel
  dashboard: the SDK then uses OIDC and `BLOB_STORE_ID`, with no long-lived token.
- Without one: `.data/library-registry.json` and `.data/admin-keys.json` next to
  this directory. Fine locally; ephemeral on Vercel.

On Vercel without a Blob store, `/health` reports `degraded` and `/` refuses
to create keys, because they would disappear when the instance recycles.

On first read, a missing registry falls back to `seed.json`; a missing key store
falls back to no keys.

## Free (Hobby) plan

Everything here fits the Hobby plan:

| Resource | Hobby allowance | What this server uses |
|----------|-----------------|-----------------------|
| Blob storage | 1 GB / month | two small JSON files |
| Blob simple ops (reads) | 10,000 / month | ~2 per `/mcp` call |
| Blob advanced ops (writes) | 2,000 / month | 1 per upsert/remove/key change |
| Blob transfer | 10 GB / month | negligible |
| Function invocations | 1,000,000 / month | one per request |
| Function duration | 300s max | capped at 30s in `vercel.json` |
| WAF | 3 custom rules, 10 IP blocks | one rule each for `/mcp` and `/` |
| Deployments | 100 / day | manual or on push |

Hobby is for non-commercial, personal use. If this registry serves a business,
move it to Pro. Exceeding a Hobby allowance pauses that resource until the
30-day window resets; there is no surprise bill.

The in-memory limiter in `lib/limits.js` is the free first line of defence; add
the WAF rules for edge-level blocking.

## Deploy

This folder is a monorepo package: set the Vercel project's **Root Directory** to
`registry-server`, then push to `main` or run `vercel deploy` from here. The
runtime is pinned to Node 22 in `package.json` (`engines`); `nodejs26.x` still
emits the Vercel `DEP0169` `url.parse` warning on every request.

Live deployment (Hobby): <https://ufms-registry-server.vercel.app>

A push to `main` builds a production deployment. If the production aliases keep
serving the previous build, promote it by hand:

```bash
vercel promote <deployment-url>        # or Dashboard → Deployments → Promote to Production
```

In the Vercel project, create a **public** Blob store (Storage → Blob) and connect
it to the project. Then set:

```bash
vercel env add REGISTRY_API_KEY production        # optional bootstrap key
vercel env add REGISTRY_ADMIN_PASSWORD production
vercel env add REGISTRY_ADMIN_SECRET production   # optional, defaults to the password
```

Connecting the store is enough for the SDK (OIDC). Add `BLOB_READ_WRITE_TOKEN`
only if you run the code outside Vercel or prefer a static token.

Vercel Authentication (SSO protection) must be **off** for the project, or every
`/mcp` call is redirected to a Vercel login page.

The first key is created at `/`; until then `/health` returns `503`
`unconfigured` and `/mcp` rejects requests. Blob reads are versioned by ETag, so a
new or revoked key is live within a few seconds (not instantly).

## Client

```bash
export UFME_REGISTRY_URL="https://your-app.vercel.app/mcp"
export UFME_REGISTRY_KEY="a key from /"

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
