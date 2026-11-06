// Storage for the library registry: Vercel Blob when a token exists, a local file otherwise.

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SEED_FILE = path.join(HERE, "..", "seed.json");
const BLOB_PATH = process.env.UFME_REGISTRY_BLOB || "ufme/library-registry.json";
const LOCAL_FILE =
  process.env.UFME_REGISTRY_FILE || path.join(HERE, "..", ".data", "library-registry.json");

function blobToken() {
  return process.env.BLOB_READ_WRITE_TOKEN || "";
}

export async function readSeed() {
  return JSON.parse(await fs.readFile(SEED_FILE, "utf8"));
}

async function readBlob() {
  const { head } = await import("@vercel/blob");
  try {
    const meta = await head(BLOB_PATH, { token: blobToken() });
    const response = await fetch(meta.url, { cache: "no-store" });
    if (!response.ok) throw new Error(`blob read failed: HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    if (error?.name === "BlobNotFoundError") return readSeed();
    throw error;
  }
}

export async function readRegistry() {
  if (blobToken()) return readBlob();
  try {
    return JSON.parse(await fs.readFile(LOCAL_FILE, "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") return readSeed();
    throw error;
  }
}

// shortcut: last write wins; two concurrent upserts can drop one. Upgrade to
// Blob ifMatch/ETag when multiple writers are expected.
export async function writeRegistry(entries) {
  const body = JSON.stringify(entries, null, 2) + "\n";
  if (blobToken()) {
    const { put } = await import("@vercel/blob");
    await put(BLOB_PATH, body, {
      access: "public",
      allowOverwrite: true,
      addRandomSuffix: false,
      contentType: "application/json",
      token: blobToken(),
    });
    return;
  }
  await fs.mkdir(path.dirname(LOCAL_FILE), { recursive: true });
  await fs.writeFile(LOCAL_FILE, body, "utf8");
}

export { LOCAL_FILE, BLOB_PATH };
