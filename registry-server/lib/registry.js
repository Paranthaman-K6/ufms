// Registry entry validation, querying and merging. Pure functions; storage lives in store.js.

export const STATUSES = ["candidate", "researched", "approved", "rejected"];
export const REQUIRED_FIELDS = [
  "name",
  "category",
  "site",
  "license",
  "commercial",
  "install",
  "reason",
];

export function validateEntry(entry) {
  const errors = [];
  for (const field of REQUIRED_FIELDS) {
    if (typeof entry[field] !== "string" || !entry[field].trim()) {
      errors.push(`missing '${field}'`);
    }
  }
  if (entry.site && !/^https:\/\//.test(entry.site)) {
    errors.push("site must be an https URL");
  }
  if (entry.status && !STATUSES.includes(entry.status)) {
    errors.push(`status must be one of ${STATUSES.join(", ")}`);
  }
  if (entry.stars !== undefined && (!Number.isInteger(entry.stars) || entry.stars < 0)) {
    errors.push("stars must be a non-negative integer");
  }
  return errors;
}

export function normalizeEntry(input, existing = {}) {
  const entry = { ...existing, ...input };
  entry.name = String(entry.name || "").trim();
  entry.category = String(entry.category || "").trim().toLowerCase();
  entry.status = entry.status || existing.status || "candidate";
  entry.stars = Number.isInteger(entry.stars) ? entry.stars : existing.stars ?? 0;
  return entry;
}

export function query(entries, { query: text, category, status, limit } = {}) {
  const needle = String(text || "").trim().toLowerCase();
  const max = Number.isInteger(limit) && limit > 0 ? limit : entries.length;
  return entries
    .filter((entry) => {
      if (category && entry.category !== String(category).toLowerCase()) return false;
      if (status && entry.status !== status) return false;
      if (!needle) return true;
      return [entry.name, entry.npm, entry.reason, entry.category]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle));
    })
    .slice(0, max);
}

export function upsert(entries, input) {
  const name = String(input.name || "").trim();
  const index = entries.findIndex((entry) => entry.name === name);
  const existing = index === -1 ? {} : entries[index];
  const entry = normalizeEntry(input, existing);
  const errors = validateEntry(entry);
  if (errors.length) {
    throw new Error(`invalid registry entry: ${errors.join("; ")}`);
  }
  const next = entries.slice();
  if (index === -1) next.push(entry);
  else next[index] = entry;
  return { entries: next, entry, created: index === -1 };
}

export function remove(entries, name) {
  const index = entries.findIndex((entry) => entry.name === name);
  if (index === -1) return { entries, removed: false };
  const next = entries.slice();
  next.splice(index, 1);
  return { entries: next, removed: true };
}
