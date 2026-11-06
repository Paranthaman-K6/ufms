// Storage for the library registry and admin keys: Vercel Blob when a token
// exists, a local file otherwise.

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SEED_FILE = path.join(HERE, "..", "seed.json");
const BLOB_PATH = process.env.UFME_REGISTRY_BLOB || "ufme/library-registry.json";
const LOCAL_FILE =
  process.env.UFME_REGISTRY_FILE || path.join(HERE, "..", ".data", "library-registry.json");
const KEYS_BLOB_PATH = process.env.UFME_KEYS_BLOB || "ufme/admin-keys.json";
const KEYS_LOCAL_FILE =
  process.env.UFME_KEYS_FILE || path.join(HERE, "..", ".data", "admin-keys.json");

function blobToken() {
  return process.env.BLOB_READ_WRITE_TOKEN || "";
}

// A connected Blob store exposes BLOB_STORE_ID and the SDK authenticates with
// OIDC, so a long-lived token is optional on Vercel.
function blobEnabled() {
  return Boolean(blobToken() || process.env.BLOB_STORE_ID);
}

export function storageMode() {
  return blobEnabled() ? "blob" : "local";
}

export async function readSeed() {
  return JSON.parse(await fs.readFile(SEED_FILE, "utf8"));
}

function fallbackValue(fallback) {
  return typeof fallback === "function" ? fallback() : fallback;
}

// The SDK wraps the API 404 in a generic error whose message starts with
// "BlobNotFoundError", so the class name alone misses it.
export function isBlobNotFound(error) {
  return (
    error?.name === "BlobNotFoundError" ||
    error?.status === 404 ||
    error?.statusCode === 404 ||
    /BlobNotFoundError|does not exist/i.test(String(error?.message || ""))
  );
}

async function readBlobJson(blobPath, fallback) {
  const { head } = await import("@vercel/blob");
  try {
    const meta = await head(blobPath, blobToken() ? { token: blobToken() } : {});
    const response = await fetch(meta.url, { cache: "no-store" });
    if (!response.ok) throw new Error(`blob read failed: HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    if (isBlobNotFound(error)) return fallbackValue(fallback);
    throw error;
  }
}

async function readLocalJson(file, fallback) {
  try {
    return JSON.parse(await fs.readFile(file, "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") return fallbackValue(fallback);
    throw error;
  }
}

// shortcut: last write wins; two concurrent writes can drop one. Upgrade to
// Blob ifMatch/ETag when multiple writers are expected.
async function writeJson(blobPath, file, value) {
  const body = JSON.stringify(value, null, 2) + "\n";
  if (blobEnabled()) {
    const { put } = await import("@vercel/blob");
    const options = {
      access: "public",
      allowOverwrite: true,
      addRandomSuffix: false,
      contentType: "application/json",
    };
    if (blobToken()) options.token = blobToken();
    await put(blobPath, body, options);
    return;
  }
  await fs.mkdir(path.dirname(file), { recursive: true });
  await fs.writeFile(file, body, "utf8");
}

export async function readRegistry() {
  if (blobEnabled()) return readBlobJson(BLOB_PATH, readSeed);
  return readLocalJson(LOCAL_FILE, readSeed);
}

export async function writeRegistry(entries) {
  await writeJson(BLOB_PATH, LOCAL_FILE, entries);
}

export async function readKeys() {
  const empty = () => ({ keys: [] });
  if (blobEnabled()) return readBlobJson(KEYS_BLOB_PATH, empty);
  return readLocalJson(KEYS_LOCAL_FILE, empty);
}

export async function writeKeys(keys) {
  await writeJson(KEYS_BLOB_PATH, KEYS_LOCAL_FILE, { keys });
}

export { LOCAL_FILE, BLOB_PATH, KEYS_LOCAL_FILE, KEYS_BLOB_PATH };
