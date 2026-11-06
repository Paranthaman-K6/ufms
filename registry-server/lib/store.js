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

export async function readSeed() {
  return JSON.parse(await fs.readFile(SEED_FILE, "utf8"));
}

function fallbackValue(fallback) {
  return typeof fallback === "function" ? fallback() : fallback;
}

async function readBlobJson(blobPath, fallback) {
  const { head } = await import("@vercel/blob");
  try {
    const meta = await head(blobPath, { token: blobToken() });
    const response = await fetch(meta.url, { cache: "no-store" });
    if (!response.ok) throw new Error(`blob read failed: HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    if (error?.name === "BlobNotFoundError") return fallbackValue(fallback);
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
  if (blobToken()) {
    const { put } = await import("@vercel/blob");
    await put(blobPath, body, {
      access: "public",
      allowOverwrite: true,
      addRandomSuffix: false,
      contentType: "application/json",
      token: blobToken(),
    });
    return;
  }
  await fs.mkdir(path.dirname(file), { recursive: true });
  await fs.writeFile(file, body, "utf8");
}

export async function readRegistry() {
  if (blobToken()) return readBlobJson(BLOB_PATH, readSeed);
  return readLocalJson(LOCAL_FILE, readSeed);
}

export async function writeRegistry(entries) {
  await writeJson(BLOB_PATH, LOCAL_FILE, entries);
}

export async function readKeys() {
  const empty = () => ({ keys: [] });
  if (blobToken()) return readBlobJson(KEYS_BLOB_PATH, empty);
  return readLocalJson(KEYS_LOCAL_FILE, empty);
}

export async function writeKeys(keys) {
  await writeJson(KEYS_BLOB_PATH, KEYS_LOCAL_FILE, { keys });
}

export { LOCAL_FILE, BLOB_PATH, KEYS_LOCAL_FILE, KEYS_BLOB_PATH };
