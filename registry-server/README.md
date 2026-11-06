# UFME library-registry server

Optional, stateless MCP server that stores one shared library registry in Vercel Blob.
The skill works without it; the local Markdown registry stays the default.

## Endpoint

`POST /mcp` — JSON-RPC 2.0, JSON responses (no SSE stream required).

Auth: `Authorization: Bearer $REGISTRY_API_KEY`

| Case | Status |
|------|--------|
| `REGISTRY_API_KEY` unset on the server | `503` |
| Missing or wrong bearer token | `401` |
| Valid request | `200` |

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

- With `BLOB_READ_WRITE_TOKEN`: `ufme/library-registry.json` in Vercel Blob
  (`access: public`, `allowOverwrite: true`, `addRandomSuffix: false`).
- Without it: `.data/library-registry.json` next to this directory. Fine locally;
  ephemeral on Vercel, so set the token in production.

On first read, a missing store falls back to `seed.json`.

## Deploy

```bash
npm install
npm test
vercel deploy
```

Set in the Vercel project:

```bash
vercel env add REGISTRY_API_KEY production
vercel env add BLOB_READ_WRITE_TOKEN production
```

`vercel.json` rewrites `/mcp` to `/api/mcp`.

## Client

```bash
export UFME_REGISTRY_URL="https://your-app.vercel.app/mcp"
export UFME_REGISTRY_KEY="$REGISTRY_API_KEY"

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

Covers 503/401 auth, `initialize`, `tools/list`, list/get/upsert/remove, validation,
unknown methods/tools, and seed validity. No network or Blob token required.
