#!/usr/bin/env node
/*
 * tests/visual/run.js — visual-diff.js lifecycle, regression and manifest tests.
 *
 * Creates real PNG fixtures with pngjs. Covers:
 *   * missing baseline -> BASELINE_MISSING (exit 4), nothing written
 *   * --create-baseline only when absent; refuses to replace a baseline
 *   * --update-baseline replaces explicitly, records removals, removes stale files
 *   * ordinary runs never modify baseline bytes
 *   * unchanged / changed / missing-baseline / missing-current / size-mismatch /
 *     unreadable comparison classes
 *   * manifest dimension-mismatch, missing-screenshot, unexpected-screenshot,
 *     manifest-invalid, and a valid manifest passing
 *   * screenshot.js writeManifest records the actual PNG dimensions
 *   * SKIPPED (no current), argument validation, exit/status agreement
 *
 * Usage: node tests/visual/run.js
 * Exit: 0 all pass, 1 failure.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const { PNG } = require('pngjs');

const ROOT = path.resolve(__dirname, '..', '..');
const SCRIPT = path.join(ROOT, 'universal-frontend-master-source', 'scripts', 'visual-diff.js');
const SCREENSHOT = path.join(ROOT, 'universal-frontend-master-source', 'browser', 'screenshot.js');
const EVIDENCE = path.join(ROOT, '.ufme', 'evidence');

let passed = 0;
const results = [];

function test(name, fn) {
  try {
    fn();
    passed += 1;
    results.push({ name, status: 'PASS' });
    console.log(`PASS: ${name}`);
  } catch (err) {
    results.push({ name, status: 'FAIL', error: err.message });
    console.log(`FAIL: ${name}: ${err.message}`);
    if (process.env.UFME_DEBUG) console.error(err);
  }
}

function assert(condition, message) {
  if (!condition) throw new Error(message || 'assertion failed');
}

function assertEqual(actual, expected, label) {
  assert(actual === expected, `${label || 'value'}: expected ${expected}, got ${actual}`);
}

function makePng(file, width, height, rgb, patch) {
  const png = new PNG({ width, height });
  for (let i = 0; i < png.data.length; i += 4) {
    png.data[i] = rgb[0];
    png.data[i + 1] = rgb[1];
    png.data[i + 2] = rgb[2];
    png.data[i + 3] = 255;
  }
  if (patch) {
    const { x, y, color } = patch;
    const offset = (y * width + x) * 4;
    png.data[offset] = color[0];
    png.data[offset + 1] = color[1];
    png.data[offset + 2] = color[2];
  }
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, PNG.sync.write(png));
}

function writeManifest(dir, images, extra = {}) {
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(
    path.join(dir, 'manifest.json'),
    `${JSON.stringify({ generatedAt: '2026-01-01T00:00:00.000Z', ...extra, images }, null, 2)}\n`,
  );
}

function run(args) {
  try {
    const stdout = execFileSync('node', [SCRIPT, ...args], {
      cwd: ROOT, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
    });
    return { code: 0, stdout };
  } catch (err) {
    return { code: err.status, stdout: String(err.stdout || ''), stderr: String(err.stderr || '') };
  }
}

function tempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'ufme-visual-'));
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function hash(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

function layout(opts = {}) {
  const tmp = tempDir();
  const current = path.join(tmp, 'current');
  const baseline = path.join(tmp, 'baseline');
  const out = path.join(tmp, 'visual-diff.json');
  return { tmp, current, baseline, out };
}

function baseArgs({ baseline, current, out }, extra = []) {
  return ['--baseline', baseline, '--current', current, '--out', out, ...extra];
}

// ---------------------------------------------------------------- lifecycle

test('an ordinary run with no baseline reports BASELINE_MISSING and writes nothing', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  const result = run(baseArgs(ctx));
  assertEqual(result.code, 4, 'exit');
  const data = readJson(ctx.out);
  assertEqual(data.status, 'BASELINE_MISSING', 'status');
  assert(!fs.existsSync(path.join(ctx.baseline, 'home-mobile-light.png')), 'baseline was created');
  assertEqual(fs.readdirSync(ctx.current).length, 1, 'current PNG count');
});

test('--create-baseline creates a missing baseline', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  const result = run(baseArgs(ctx, ['--create-baseline']));
  assertEqual(result.code, 0, 'exit');
  const data = readJson(ctx.out);
  assertEqual(data.status, 'BASELINE_CREATED', 'status');
  assert(fs.existsSync(path.join(ctx.baseline, 'home-mobile-light.png')), 'baseline image missing');
});

test('--create-baseline refuses to overwrite an existing baseline', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [200, 10, 10]);
  makePng(path.join(ctx.baseline, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  const before = hash(path.join(ctx.baseline, 'home-mobile-light.png'));
  const result = run(baseArgs(ctx, ['--create-baseline']));
  assertEqual(result.code, 2, 'exit');
  assertEqual(hash(path.join(ctx.baseline, 'home-mobile-light.png')), before, 'baseline bytes');
});

test('--update-baseline replaces explicitly and removes stale baseline files', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [200, 10, 10]);
  makePng(path.join(ctx.baseline, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(ctx.baseline, 'gone-desktop-dark.png'), 8, 8, [10, 20, 30]);
  const result = run(baseArgs(ctx, ['--update-baseline']));
  assertEqual(result.code, 0, 'exit');
  const data = readJson(ctx.out);
  assertEqual(data.status, 'BASELINE_UPDATED', 'status');
  assert(data.removed.includes('gone-desktop-dark.png'), JSON.stringify(data.removed));
  assert(!fs.existsSync(path.join(ctx.baseline, 'gone-desktop-dark.png')), 'stale baseline kept');
  assertEqual(
    hash(path.join(ctx.baseline, 'home-mobile-light.png')),
    hash(path.join(ctx.current, 'home-mobile-light.png')),
    'baseline replaced',
  );
});

test('an ordinary comparison never modifies the baseline', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [200, 10, 10]);
  makePng(path.join(ctx.baseline, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  const before = hash(path.join(ctx.baseline, 'home-mobile-light.png'));
  const beforeMtime = fs.statSync(path.join(ctx.baseline, 'home-mobile-light.png')).mtimeMs;
  run(baseArgs(ctx));
  assertEqual(hash(path.join(ctx.baseline, 'home-mobile-light.png')), before, 'baseline bytes');
  assertEqual(
    fs.statSync(path.join(ctx.baseline, 'home-mobile-light.png')).mtimeMs,
    beforeMtime,
    'baseline mtime',
  );
});

test('--create-baseline and --update-baseline are mutually exclusive', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  const result = run(baseArgs(ctx, ['--create-baseline', '--update-baseline']));
  assertEqual(result.code, 2, 'exit');
});

// --------------------------------------------------------------- comparison

test('identical screenshots PASS with ratio 0', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(ctx.baseline, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  const result = run(baseArgs(ctx));
  assertEqual(result.code, 0, 'exit');
  const data = readJson(ctx.out);
  assertEqual(data.status, 'PASS', 'status');
  assertEqual(data.maxDiffRatio, 0, 'maxDiffRatio');
  assertEqual(data.images[0].status, 'unchanged', 'image status');
});

test('changed screenshots FAIL and record the pixel ratio', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(ctx.baseline, 'home-mobile-light.png'), 8, 8, [200, 210, 220]);
  const result = run(baseArgs(ctx));
  assertEqual(result.code, 1, 'exit');
  const data = readJson(ctx.out);
  assertEqual(data.status, 'FAIL', 'status');
  assertEqual(data.images[0].status, 'changed', 'image status');
  assertEqual(data.images[0].diffPixels, 64, 'diffPixels');
  assert(data.maxDiffRatio > 0, 'maxDiffRatio');
});

test('--max-diff-ratio tolerates a small intended change', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 10, 10, [10, 20, 30], {
    x: 0, y: 0, color: [255, 0, 0],
  });
  makePng(path.join(ctx.baseline, 'home-mobile-light.png'), 10, 10, [10, 20, 30]);
  assertEqual(run(baseArgs(ctx)).code, 1, 'strict exit');
  const loose = run(baseArgs(ctx, ['--max-diff-ratio', '0.02']));
  assertEqual(loose.code, 0, 'loose exit');
  assertEqual(readJson(ctx.out).status, 'PASS', 'loose status');
  assertEqual(readJson(ctx.out).images[0].status, 'unchanged', 'loose image status');
});

test('a current image with no baseline FAILs as missing-baseline', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(ctx.baseline, 'other-mobile-light.png'), 8, 8, [10, 20, 30]);
  const result = run(baseArgs(ctx));
  assertEqual(result.code, 1, 'exit');
  const images = readJson(ctx.out).images;
  assert(images.some((i) => i.status === 'missing-baseline'), JSON.stringify(images));
});

test('a baseline image with no current capture FAILs as missing-current', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(ctx.baseline, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(ctx.baseline, 'removed-desktop-dark.png'), 8, 8, [10, 20, 30]);
  const result = run(baseArgs(ctx));
  assertEqual(result.code, 1, 'exit');
  const removed = readJson(ctx.out).images.find((i) => i.file === 'removed-desktop-dark.png');
  assert(removed && removed.status === 'missing-current', JSON.stringify(readJson(ctx.out).images));
});

test('a size mismatch FAILs as size-mismatch', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(ctx.baseline, 'home-mobile-light.png'), 4, 4, [10, 20, 30]);
  const result = run(baseArgs(ctx));
  assertEqual(result.code, 1, 'exit');
  const image = readJson(ctx.out).images[0];
  assertEqual(image.status, 'size-mismatch', 'image status');
  assertEqual(image.baseline, '4x4', 'baseline size');
  assertEqual(image.current, '8x8', 'current size');
});

test('a corrupt current PNG FAILs as unreadable', () => {
  const ctx = layout();
  fs.mkdirSync(ctx.current, { recursive: true });
  fs.writeFileSync(path.join(ctx.current, 'home-mobile-light.png'), 'not a png');
  makePng(path.join(ctx.baseline, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  const result = run(baseArgs(ctx));
  assertEqual(result.code, 1, 'exit');
  assertEqual(readJson(ctx.out).images[0].status, 'unreadable', 'image status');
});

test('no current screenshots SKIP with exit 3', () => {
  const ctx = layout();
  const result = run(baseArgs(ctx));
  assertEqual(result.code, 3, 'exit');
  const data = readJson(ctx.out);
  assertEqual(data.status, 'SKIPPED', 'status');
  assert(/no PNG screenshots/.test(data.reason), data.reason);
});

// ----------------------------------------------------------------- manifest

test('a valid manifest passes when dimensions match the files', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(ctx.baseline, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  writeManifest(ctx.current, [
    { file: 'home-mobile-light.png', width: 8, height: 8, viewport: 'mobile', theme: 'light' },
  ]);
  const result = run(baseArgs(ctx));
  assertEqual(result.code, 0, 'exit');
  assertEqual(readJson(ctx.out).manifest.issues.length, 0, 'manifest issues');
});

test('a manifest dimension mismatch FAILs with viewport/theme context', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(ctx.baseline, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  writeManifest(ctx.current, [
    { file: 'home-mobile-light.png', width: 390, height: 844, viewport: 'mobile', theme: 'light' },
  ]);
  const result = run(baseArgs(ctx));
  assertEqual(result.code, 1, 'exit');
  const data = readJson(ctx.out);
  const issue = data.manifest.issues.find((i) => i.status === 'dimension-mismatch');
  assert(issue, JSON.stringify(data.manifest.issues));
  assertEqual(issue.expected, '390x844', 'expected');
  assertEqual(issue.actual, '8x8', 'actual');
  assertEqual(issue.viewport, 'mobile', 'viewport');
  assertEqual(issue.theme, 'light', 'theme');
  assertEqual(data.status, 'FAIL', 'status');
});

test('a manifest entry with no captured file FAILs as missing-screenshot', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(ctx.baseline, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  writeManifest(ctx.current, [
    { file: 'home-mobile-light.png', width: 8, height: 8 },
    { file: 'about-mobile-light.png', width: 8, height: 8 },
  ]);
  const result = run(baseArgs(ctx));
  assertEqual(result.code, 1, 'exit');
  assert(
    readJson(ctx.out).manifest.issues.some((i) => i.status === 'missing-screenshot'),
    JSON.stringify(readJson(ctx.out).manifest.issues),
  );
});

test('a captured file absent from the manifest FAILs as unexpected-screenshot', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(ctx.current, 'extra-desktop-dark.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(ctx.baseline, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(ctx.baseline, 'extra-desktop-dark.png'), 8, 8, [10, 20, 30]);
  writeManifest(ctx.current, [
    { file: 'home-mobile-light.png', width: 8, height: 8 },
  ]);
  const result = run(baseArgs(ctx));
  assertEqual(result.code, 1, 'exit');
  assert(
    readJson(ctx.out).manifest.issues.some((i) => i.status === 'unexpected-screenshot'),
    JSON.stringify(readJson(ctx.out).manifest.issues),
  );
});

test('a malformed manifest FAILs as manifest-invalid', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(ctx.baseline, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  fs.writeFileSync(path.join(ctx.current, 'manifest.json'), '{"images": "nope"}\n');
  const result = run(baseArgs(ctx));
  assertEqual(result.code, 1, 'exit');
  assert(
    readJson(ctx.out).manifest.issues.some((i) => i.status === 'manifest-invalid'),
    JSON.stringify(readJson(ctx.out).manifest.issues),
  );
});

test('an unreadable manifest FAILs as manifest-invalid', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(ctx.baseline, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  fs.writeFileSync(path.join(ctx.current, 'manifest.json'), '{broken');
  const result = run(baseArgs(ctx));
  assertEqual(result.code, 1, 'exit');
  assert(
    readJson(ctx.out).manifest.issues.some((i) => i.status === 'manifest-invalid'),
    JSON.stringify(readJson(ctx.out).manifest.issues),
  );
});

test('--update-baseline copies the current manifest into the baseline', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 8, 8, [10, 20, 30]);
  writeManifest(ctx.current, [
    { file: 'home-mobile-light.png', width: 8, height: 8, viewport: 'mobile', theme: 'light' },
  ]);
  const result = run(baseArgs(ctx, ['--update-baseline']));
  assertEqual(result.code, 0, 'exit');
  assert(fs.existsSync(path.join(ctx.baseline, 'manifest.json')), 'baseline manifest missing');
  assertEqual(
    readJson(path.join(ctx.baseline, 'manifest.json')).images[0].viewport,
    'mobile',
    'baseline manifest viewport',
  );
});

// -------------------------------------------------------------- screening

test('screenshot.writeManifest records the real PNG dimensions', () => {
  const screenshot = require(SCREENSHOT);
  const tmp = tempDir();
  makePng(path.join(tmp, 'home-mobile-light.png'), 12, 7, [1, 2, 3]);
  const file = screenshot.writeManifest(
    tmp,
    [{ file: path.join(tmp, 'home-mobile-light.png'), viewport: 'mobile', theme: 'light' }],
    { url: 'http://example.test' },
  );
  const manifest = readJson(file);
  assertEqual(manifest.url, 'http://example.test', 'url');
  assertEqual(manifest.images[0].width, 12, 'width');
  assertEqual(manifest.images[0].height, 7, 'height');
  assertEqual(manifest.images[0].viewport, 'mobile', 'viewport');
  assertEqual(manifest.images[0].theme, 'light', 'theme');
  const decoded = PNG.sync.read(fs.readFileSync(path.join(tmp, 'home-mobile-light.png')));
  assertEqual(manifest.images[0].width, decoded.width, 'width matches pixels');
  assertEqual(manifest.images[0].height, decoded.height, 'height matches pixels');
});

test('screenshot.pngDimensions rejects non-PNG input', () => {
  const screenshot = require(SCREENSHOT);
  let threw = false;
  try {
    screenshot.pngDimensions(Buffer.from('not a png'));
  } catch (err) {
    threw = true;
  }
  assert(threw, 'pngDimensions accepted non-PNG data');
});

// --------------------------------------------------------------- arguments

test('invalid --max-diff-ratio exits 2', () => {
  const ctx = layout();
  makePng(path.join(ctx.current, 'home-mobile-light.png'), 4, 4, [0, 0, 0]);
  assertEqual(run(baseArgs(ctx, ['--max-diff-ratio', '2'])).code, 2, 'exit');
});

test('unknown option exits 2', () => {
  assertEqual(run(['--nonsense']).code, 2, 'exit');
});

const failed = results.filter((r) => r.status === 'FAIL');
fs.mkdirSync(EVIDENCE, { recursive: true });
fs.writeFileSync(
  path.join(EVIDENCE, 'visual-test.json'),
  `${JSON.stringify({ checks: results.length, pass: passed, failed: failed.length, results }, null, 2)}\n`,
);
console.log(`\n${passed} passed, ${failed.length} failed`);
process.exit(failed.length ? 1 : 0);
