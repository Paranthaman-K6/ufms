// API-key and admin-session primitives. Keys are stored hashed; the plaintext
// is shown once, when it is created.

import crypto from "node:crypto";

const PREFIX = "ufme_";
const SESSION_TTL_MS = 12 * 60 * 60 * 1000;

export function sha256(value) {
  return crypto.createHash("sha256").update(String(value)).digest("hex");
}

export function safeEqual(a, b) {
  const left = Buffer.from(String(a));
  const right = Buffer.from(String(b));
  return left.length === right.length && crypto.timingSafeEqual(left, right);
}

export function bearer(header) {
  return String(header || "").replace(/^Bearer\s+/i, "").trim();
}

export function generateKey() {
  return PREFIX + crypto.randomBytes(24).toString("base64url");
}

export function authenticateApiKey(header, keys) {
  const provided = bearer(header);
  if (!provided.startsWith(PREFIX)) return null;
  const hash = sha256(provided);
  return (keys || []).find((key) => !key.revokedAt && safeEqual(key.hash, hash)) || null;
}

export function createKey(keys, label) {
  const key = generateKey();
  const record = {
    id: crypto.randomUUID(),
    label: String(label || "").trim().slice(0, 60) || "untitled",
    prefix: key.slice(0, 12),
    hash: sha256(key),
    createdAt: new Date().toISOString(),
  };
  return { key, record, keys: [...(keys || []), record] };
}

export function revokeKey(keys, id) {
  let removed = false;
  const next = (keys || []).filter((key) => {
    if (key.id === id) {
      removed = true;
      return false;
    }
    return true;
  });
  return { keys: next, removed };
}

function sessionSecret() {
  return process.env.REGISTRY_ADMIN_SECRET || process.env.REGISTRY_ADMIN_PASSWORD || "";
}

export function createSession(now = Date.now()) {
  const payload = String(now + SESSION_TTL_MS);
  const signature = crypto.createHmac("sha256", sessionSecret()).update(payload).digest("base64url");
  return `${payload}.${signature}`;
}

export function verifySession(token, now = Date.now()) {
  const [payload, signature] = String(token || "").split(".");
  if (!payload || !signature) return false;
  const expected = crypto.createHmac("sha256", sessionSecret()).update(payload).digest("base64url");
  return safeEqual(signature, expected) && Number(payload) > now;
}
