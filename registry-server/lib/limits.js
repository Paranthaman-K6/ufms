// In-memory fixed-window rate limiting and request-size helpers.

// shortcut: counts live in one lambda instance and reset on cold start. On
// Vercel each instance counts separately; Hobby allows 3 WAF custom rules and
// 10 IP blocks at the edge, which is the free way to block distributed abuse.
const windows = new Map();
const MAX_TRACKED = 5000;

export function clientIp(req) {
  const forwarded = String(req.headers?.["x-forwarded-for"] || "").split(",")[0].trim();
  return forwarded || String(req.headers?.["x-real-ip"] || "") || "unknown";
}

export function intFromEnv(name, fallback) {
  const value = Number.parseInt(process.env[name] || "", 10);
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

export function rateLimit(bucket, ip, max, windowMs = 60_000) {
  const key = `${bucket}:${ip}`;
  const now = Date.now();
  const current = windows.get(key);
  if (!current || current.resetAt <= now) {
    if (windows.size >= MAX_TRACKED) windows.clear();
    windows.set(key, { count: 1, resetAt: now + windowMs });
    return { ok: true, retryAfter: 0 };
  }
  current.count += 1;
  if (current.count > max) {
    return { ok: false, retryAfter: Math.max(1, Math.ceil((current.resetAt - now) / 1000)) };
  }
  return { ok: true, retryAfter: 0 };
}

export function bodyTooLarge(body, maxBytes) {
  if (body === undefined || body === null) return false;
  const text = typeof body === "string" ? body : JSON.stringify(body);
  return Buffer.byteLength(text) > maxBytes;
}

export function resetLimits() {
  windows.clear();
}
