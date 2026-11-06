#!/usr/bin/env node
/*
 * visual-diff.js — pixel-level screenshot regression comparison.
 *
 * Usage:
 *   node visual-diff.js --baseline <dir> --current <dir> [--out <json>]
 *        [--manifest <json>] [--max-diff-ratio 0.001] [--pixel-threshold 0.1]
 *        [--create-baseline | --update-baseline]
 *
 * Baseline lifecycle (explicit, never silent):
 *   * Ordinary run with no baseline: status BASELINE_MISSING, exit 4. Nothing is written.
 *   * --create-baseline: creates the baseline ONLY when it is absent/empty
 *     (BASELINE_CREATED, exit 0); refuses to overwrite an existing baseline (exit 2).
 *   * --update-baseline: explicit overwrite from current captures (BASELINE_UPDATED,
 *     exit 0) and removes baseline images that no longer have a current capture.
 *   * No current PNGs: status SKIPPED, exit 3.
 *
 * Comparison classes: unchanged, changed, missing-baseline (current image has no
 * baseline), missing-current (baseline image has no current capture), size-mismatch,
 * unreadable (broken PNG on either side). Any non-unchanged class fails (exit 1).
 *
 * Manifest: when <current>/manifest.json exists (or --manifest is given), every
 * entry declares the expected image width/height (and usually viewport/theme).
 * A manifest entry with no file (missing-screenshot), a file not listed in the
 * manifest (unexpected-screenshot), a malformed entry, or actual pixels that
 * disagree with the expected dimensions (dimension-mismatch) all fail.
 *
 * Writes .ufme/evidence/visual-diff.json by default.
 * Safety: project-local only; read-only except the baseline/evidence writes.
 */
'use strict';

const fs = require('fs');
const path = require('path');

let PNG;
let pixelmatch;
try {
  PNG = require('pngjs').PNG;
  pixelmatch = require('pixelmatch');
} catch (err) {
  console.error('[visual-diff] Missing dependency — run: npm i -D pngjs pixelmatch');
  process.exit(3);
}

const ROOT = path.resolve(__dirname, '..', '..', '..');
const DEFAULT_OUT = path.join(ROOT, '.ufme', 'evidence', 'visual-diff.json');

function parseArgs(argv) {
  const args = {
    baseline: path.join(ROOT, '.ufme', 'evidence', 'baseline'),
    current: path.join(ROOT, '.ufme', 'evidence', 'screenshots'),
    out: DEFAULT_OUT,
    manifest: null,
    maxDiffRatio: 0.001,
    pixelThreshold: 0.1,
    createBaseline: false,
    updateBaseline: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--baseline') args.baseline = next();
    else if (a === '--current') args.current = next();
    else if (a === '--out') args.out = next();
    else if (a === '--manifest') args.manifest = next();
    else if (a === '--max-diff-ratio') args.maxDiffRatio = Number(next());
    else if (a === '--pixel-threshold') args.pixelThreshold = Number(next());
    else if (a === '--create-baseline') args.createBaseline = true;
    else if (a === '--update-baseline') args.updateBaseline = true;
    else if (a === '--help' || a === '-h') {
      console.log('Usage: node visual-diff.js --baseline <dir> --current <dir> [--out <json>] [--manifest <json>] [--max-diff-ratio N] [--pixel-threshold N] [--create-baseline | --update-baseline]');
      process.exit(0);
    } else {
      console.error(`[visual-diff] unknown option: ${a}`);
      process.exit(2);
    }
  }
  if (args.createBaseline && args.updateBaseline) {
    console.error('[visual-diff] --create-baseline and --update-baseline are mutually exclusive');
    process.exit(2);
  }
  if (!Number.isFinite(args.maxDiffRatio) || args.maxDiffRatio < 0 || args.maxDiffRatio > 1) {
    console.error('[visual-diff] --max-diff-ratio must be between 0 and 1');
    process.exit(2);
  }
  if (!Number.isFinite(args.pixelThreshold) || args.pixelThreshold < 0 || args.pixelThreshold > 1) {
    console.error('[visual-diff] --pixel-threshold must be between 0 and 1');
    process.exit(2);
  }
  return args;
}

function pngFiles(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((name) => name.toLowerCase().endsWith('.png'))
    .sort();
}

function writeJson(file, data) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = `${file}.tmp-${process.pid}`;
  fs.writeFileSync(tmp, `${JSON.stringify(data, null, 2)}\n`);
  fs.renameSync(tmp, file);
}

function copyManifest(args) {
  const source = args.manifest || path.join(args.current, 'manifest.json');
  const target = path.join(args.baseline, 'manifest.json');
  if (fs.existsSync(source)) fs.copyFileSync(source, target);
  else if (fs.existsSync(target)) fs.unlinkSync(target);
}

function writeBaseline(args, currentFiles, status, reason) {
  fs.mkdirSync(args.baseline, { recursive: true });
  for (const name of currentFiles) {
    fs.copyFileSync(path.join(args.current, name), path.join(args.baseline, name));
  }
  const currentSet = new Set(currentFiles);
  const removed = [];
  for (const name of pngFiles(args.baseline)) {
    if (!currentSet.has(name)) {
      fs.unlinkSync(path.join(args.baseline, name));
      removed.push(name);
    }
  }
  copyManifest(args);
  return {
    status,
    reason,
    baseline: args.baseline,
    current: args.current,
    threshold: args.maxDiffRatio,
    images: currentFiles.map((file) => ({ file, status: status === 'BASELINE_CREATED' ? 'baseline-created' : 'baseline-updated', diffRatio: 0 })),
    removed,
    timestamp: new Date().toISOString(),
  };
}

function readManifest(args) {
  const file = args.manifest || path.join(args.current, 'manifest.json');
  if (!fs.existsSync(file)) return { file, images: null, error: null };
  let data;
  try {
    data = JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (err) {
    return { file, images: null, error: `unreadable manifest: ${err.message}` };
  }
  const images = Array.isArray(data.images) ? data.images : data.captures;
  if (!Array.isArray(images)) {
    return { file, images: null, error: 'manifest has no images array' };
  }
  return { file, images, error: null };
}

function checkManifest(args, currentFiles) {
  const manifest = readManifest(args);
  if (!manifest.images) {
    return { file: manifest.file, checked: 0, issues: manifest.error ? [{ status: 'manifest-invalid', reason: manifest.error }] : [] };
  }
  const issues = [];
  const listed = new Set();
  let checked = 0;
  for (const entry of manifest.images) {
    if (!entry || typeof entry.file !== 'string' || !entry.file) {
      issues.push({ status: 'manifest-invalid', reason: `entry without a file: ${JSON.stringify(entry)}` });
      continue;
    }
    listed.add(entry.file);
    if (!Number.isInteger(entry.width) || !Number.isInteger(entry.height) || entry.width < 1 || entry.height < 1) {
      issues.push({ file: entry.file, status: 'manifest-invalid', reason: 'entry needs positive integer width and height' });
      continue;
    }
    const imagePath = path.join(args.current, entry.file);
    if (!fs.existsSync(imagePath)) {
      issues.push({ file: entry.file, status: 'missing-screenshot', reason: 'manifest entry has no captured file' });
      continue;
    }
    let actual;
    try {
      actual = PNG.sync.read(fs.readFileSync(imagePath));
    } catch (err) {
      issues.push({ file: entry.file, status: 'unreadable', reason: err.message });
      continue;
    }
    checked += 1;
    if (actual.width !== entry.width || actual.height !== entry.height) {
      issues.push({
        file: entry.file,
        status: 'dimension-mismatch',
        expected: `${entry.width}x${entry.height}`,
        actual: `${actual.width}x${actual.height}`,
        viewport: entry.viewport,
        theme: entry.theme,
      });
    }
  }
  for (const file of currentFiles) {
    if (!listed.has(file)) {
      issues.push({ file, status: 'unexpected-screenshot', reason: 'captured file is not listed in the manifest' });
    }
  }
  return { file: manifest.file, checked, issues };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const currentFiles = pngFiles(args.current);
  const base = {
    baseline: args.baseline,
    current: args.current,
    threshold: args.maxDiffRatio,
    timestamp: new Date().toISOString(),
  };

  if (currentFiles.length === 0) {
    const result = { ...base, status: 'SKIPPED', reason: `no PNG screenshots in ${args.current}` };
    writeJson(args.out, result);
    console.log(`[visual-diff] SKIPPED: ${result.reason}`);
    process.exit(3);
  }

  if (args.updateBaseline) {
    const result = writeBaseline(args, currentFiles, 'BASELINE_UPDATED', 'baseline explicitly updated from current screenshots');
    writeJson(args.out, result);
    console.log(`[visual-diff] Baseline updated: ${args.baseline} (${currentFiles.length} images, ${result.removed.length} removed)`);
    process.exit(0);
  }

  const baselineFiles = pngFiles(args.baseline);
  if (args.createBaseline) {
    if (baselineFiles.length > 0) {
      console.error('[visual-diff] Baseline already exists; use --update-baseline to replace it explicitly');
      process.exit(2);
    }
    const result = writeBaseline(args, currentFiles, 'BASELINE_CREATED', 'baseline explicitly created from current screenshots');
    writeJson(args.out, result);
    console.log(`[visual-diff] Baseline created: ${args.baseline} (${currentFiles.length} images)`);
    process.exit(0);
  }

  if (baselineFiles.length === 0) {
    const result = {
      ...base,
      status: 'BASELINE_MISSING',
      reason: `no baseline PNGs in ${args.baseline}; create one explicitly with --create-baseline`,
    };
    writeJson(args.out, result);
    console.log(`[visual-diff] BASELINE_MISSING: ${result.reason}`);
    process.exit(4);
  }

  const manifest = checkManifest(args, currentFiles);
  let failed = manifest.issues.length > 0;
  const results = [];
  let maxRatio = 0;

  for (const file of currentFiles) {
    const basePath = path.join(args.baseline, file);
    const curPath = path.join(args.current, file);
    if (!fs.existsSync(basePath)) {
      results.push({ file, status: 'missing-baseline', diffRatio: 1 });
      maxRatio = 1;
      failed = true;
      continue;
    }
    let basePng;
    let curPng;
    try {
      basePng = PNG.sync.read(fs.readFileSync(basePath));
      curPng = PNG.sync.read(fs.readFileSync(curPath));
    } catch (err) {
      results.push({ file, status: 'unreadable', reason: err.message, diffRatio: 1 });
      maxRatio = 1;
      failed = true;
      continue;
    }
    if (basePng.width !== curPng.width || basePng.height !== curPng.height) {
      results.push({
        file,
        status: 'size-mismatch',
        baseline: `${basePng.width}x${basePng.height}`,
        current: `${curPng.width}x${curPng.height}`,
        diffRatio: 1,
      });
      maxRatio = 1;
      failed = true;
      continue;
    }
    const total = basePng.width * basePng.height;
    const diffPixels = pixelmatch(
      basePng.data, curPng.data, null, basePng.width, basePng.height, { threshold: args.pixelThreshold },
    );
    const diffRatio = total ? diffPixels / total : 0;
    maxRatio = Math.max(maxRatio, diffRatio);
    if (diffRatio > args.maxDiffRatio) failed = true;
    results.push({
      file,
      status: diffRatio > args.maxDiffRatio ? 'changed' : 'unchanged',
      width: basePng.width,
      height: basePng.height,
      diffPixels,
      totalPixels: total,
      diffRatio: Number(diffRatio.toFixed(6)),
    });
  }

  const currentSet = new Set(currentFiles);
  for (const file of baselineFiles) {
    if (!currentSet.has(file)) {
      results.push({ file, status: 'missing-current', diffRatio: 1 });
      maxRatio = 1;
      failed = true;
    }
  }

  const result = {
    ...base,
    status: failed ? 'FAIL' : 'PASS',
    maxDiffRatio: Number(maxRatio.toFixed(6)),
    manifest,
    images: results,
  };
  writeJson(args.out, result);
  console.log(
    `[visual-diff] ${result.status}: maxDiffRatio=${result.maxDiffRatio} threshold=${args.maxDiffRatio} ` +
    `images=${results.length} manifestIssues=${manifest.issues.length}`,
  );
  process.exit(failed ? 1 : 0);
}

main();
