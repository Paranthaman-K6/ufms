#!/usr/bin/env node
/*
 * visual-diff.js — pixel-level screenshot regression comparison.
 *
 * Usage:
 *   node visual-diff.js --baseline <dir> --current <dir> [--out <json>]
 *        [--max-diff-ratio 0.001] [--pixel-threshold 0.1] [--update-baseline]
 *
 * Behaviour:
 *   * First run (baseline missing/empty): copies current PNGs into the baseline
 *     directory, records status BASELINE_CREATED, and exits 0.
 *   * Identical images: diffRatio 0, exit 0.
 *   * Modified images: diffRatio = changed pixels / total pixels per image.
 *     Exit 1 when the largest ratio exceeds --max-diff-ratio.
 *   * A current image with no baseline is reported as missed-baseline and fails.
 *   * A baseline image with no current capture is reported as missing-current
 *     and fails (a deleted or renamed screenshot is a regression, not a pass).
 *   * No PNGs in current: status SKIPPED, exit 3.
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

const ROOT = path.resolve(__dirname, '..', '..');
const DEFAULT_OUT = path.join(ROOT, '.ufme', 'evidence', 'visual-diff.json');

function parseArgs(argv) {
  const args = {
    baseline: path.join(ROOT, '.ufme', 'evidence', 'baseline'),
    current: path.join(ROOT, '.ufme', 'evidence', 'screenshots'),
    out: DEFAULT_OUT,
    maxDiffRatio: 0.001,
    pixelThreshold: 0.1,
    updateBaseline: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--baseline') args.baseline = next();
    else if (a === '--current') args.current = next();
    else if (a === '--out') args.out = next();
    else if (a === '--max-diff-ratio') args.maxDiffRatio = Number(next());
    else if (a === '--pixel-threshold') args.pixelThreshold = Number(next());
    else if (a === '--update-baseline') args.updateBaseline = true;
    else if (a === '--help' || a === '-h') {
      console.log('Usage: node visual-diff.js --baseline <dir> --current <dir> [--out <json>] [--max-diff-ratio N] [--pixel-threshold N] [--update-baseline]');
      process.exit(0);
    } else {
      console.error(`[visual-diff] unknown option: ${a}`);
      process.exit(2);
    }
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

function createBaseline(args, currentFiles, reason) {
  fs.mkdirSync(args.baseline, { recursive: true });
  for (const name of currentFiles) {
    fs.copyFileSync(path.join(args.current, name), path.join(args.baseline, name));
  }
  return {
    status: 'BASELINE_CREATED',
    reason,
    baseline: args.baseline,
    current: args.current,
    threshold: args.maxDiffRatio,
    images: currentFiles.map((file) => ({ file, status: 'baseline-created', diffRatio: 0 })),
    timestamp: new Date().toISOString(),
  };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const currentFiles = pngFiles(args.current);
  if (currentFiles.length === 0) {
    const result = {
      status: 'SKIPPED',
      reason: `no PNG screenshots in ${args.current}`,
      baseline: args.baseline,
      current: args.current,
      timestamp: new Date().toISOString(),
    };
    writeJson(args.out, result);
    console.log(`[visual-diff] SKIPPED: ${result.reason}`);
    process.exit(3);
  }

  if (args.updateBaseline) {
    const result = createBaseline(args, currentFiles, 'baseline updated from current screenshots');
    writeJson(args.out, result);
    console.log(`[visual-diff] Baseline updated: ${args.baseline} (${currentFiles.length} images)`);
    process.exit(0);
  }

  const baselineFiles = pngFiles(args.baseline);
  if (baselineFiles.length === 0) {
    const result = createBaseline(args, currentFiles, 'first run: baseline created from current screenshots');
    writeJson(args.out, result);
    console.log(`[visual-diff] Baseline created: ${args.baseline} (${currentFiles.length} images)`);
    process.exit(0);
  }

  const results = [];
  let maxRatio = 0;
  let failed = false;
  for (const file of currentFiles) {
    const basePath = path.join(args.baseline, file);
    const curPath = path.join(args.current, file);
    if (!fs.existsSync(basePath)) {
      results.push({ file, status: 'missing-baseline', diffRatio: 1 });
      maxRatio = 1;
      failed = true;
      continue;
    }
    let base;
    let cur;
    try {
      base = PNG.sync.read(fs.readFileSync(basePath));
      cur = PNG.sync.read(fs.readFileSync(curPath));
    } catch (err) {
      results.push({ file, status: 'unreadable', reason: err.message, diffRatio: 1 });
      maxRatio = 1;
      failed = true;
      continue;
    }
    if (base.width !== cur.width || base.height !== cur.height) {
      results.push({
        file,
        status: 'size-mismatch',
        baseline: `${base.width}x${base.height}`,
        current: `${cur.width}x${cur.height}`,
        diffRatio: 1,
      });
      maxRatio = 1;
      failed = true;
      continue;
    }
    const total = base.width * base.height;
    const diffPixels = pixelmatch(
      base.data, cur.data, null, base.width, base.height, { threshold: args.pixelThreshold },
    );
    const diffRatio = total ? diffPixels / total : 0;
    maxRatio = Math.max(maxRatio, diffRatio);
    if (diffRatio > args.maxDiffRatio) failed = true;
    results.push({
      file,
      status: diffRatio > args.maxDiffRatio ? 'changed' : 'unchanged',
      width: base.width,
      height: base.height,
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
    status: failed ? 'FAIL' : 'PASS',
    baseline: args.baseline,
    current: args.current,
    threshold: args.maxDiffRatio,
    maxDiffRatio: Number(maxRatio.toFixed(6)),
    images: results,
    timestamp: new Date().toISOString(),
  };
  writeJson(args.out, result);
  console.log(
    `[visual-diff] ${result.status}: maxDiffRatio=${result.maxDiffRatio} threshold=${args.maxDiffRatio} ` +
    `images=${results.length}`,
  );
  process.exit(failed ? 1 : 0);
}

main();
