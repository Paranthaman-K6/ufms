// GET /health — liveness and configuration probe. No secrets in the response.

import { readKeys, readRegistry, storageMode } from "../lib/store.js";

function send(res, status, body) {
  res.statusCode = status;
  res.setHeader("content-type", "application/json");
  res.setHeader("cache-control", "no-store");
  res.setHeader("x-robots-tag", "noindex");
  res.end(JSON.stringify(body));
}

export default async function handler(req, res) {
  if (req.method !== "GET" && req.method !== "HEAD") {
    send(res, 405, { error: "method not allowed" });
    return;
  }

  const rootKey = Boolean(process.env.REGISTRY_API_KEY);
  let keys = [];
  try {
    keys = (await readKeys()).keys || [];
  } catch {
    keys = [];
  }

  const body = {
    status: rootKey || keys.length ? "ok" : "unconfigured",
    service: "ufme-library-registry",
    version: "1.0.0",
    storage: storageMode(),
    auth: { rootKey, storedKeys: keys.length },
  };

  if (body.status !== "ok") {
    body.error = "REGISTRY_API_KEY is not configured";
    send(res, 503, body);
    return;
  }

  if (process.env.VERCEL && body.storage === "local") {
    body.status = "degraded";
    body.error = "Blob is not configured; writes are lost when the instance recycles";
    send(res, 503, body);
    return;
  }

  if (req.query?.deep === "1" || req.query?.deep === "true") {
    try {
      body.entries = (await readRegistry()).length;
    } catch (error) {
      body.status = "degraded";
      body.error = String(error.message || error);
      send(res, 503, body);
      return;
    }
  }

  send(res, 200, body);
}
