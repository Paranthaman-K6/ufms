#!/usr/bin/env node
/*
 * tests/visual/run.js — visual-diff.js regression tests.
 *
 * Creates real PNG fixtures with pngjs and verifies:
 *   * first run creates the baseline and exits 0
 *   * identical screenshots PASS with ratio 0
 *   * changed screenshots FAIL and report the pixel ratio
 *   * --max-diff-ratio allows a small intended change
 *   * no current screenshots SKIPs with exit 3
 *   * a current image without a baseline FAILs
 *   * size mismatches and bad arguments are handled
 *
 * Usage: node tests/visual/run.js
 * Exit: 0 all pass, 1 failure.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execFileSync } = require('child_process');
const { PNG } = require('pngjs');

const ROOT = path.resolve(__dirname, '..', '..');
const SCRIPT = path.join(ROOT, 'universal-frontend-master-source', 'scripts', 'visual-diff.js');
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

test('first run creates the baseline', () => {
  const tmp = tempDir();
  const current = path.join(tmp, 'current');
  const baseline = path.join(tmp, 'baseline');
  const out = path.join(tmp, 'out.json');
  makePng(path.join(current, 'home.png'), 8, 8, [10, 20, 30]);
  const result = run(['--baseline', baseline, '--current', current, '--out', out]);
  assert(result.code === 0, `exit ${result.code}`);
  const data = readJson(out);
  assert(data.status === 'BASELINE_CREATED', data.status);
  assert(fs.existsSync(path.join(baseline, 'home.png')), 'baseline image missing');
});

test('identical screenshots PASS with ratio 0', () => {
  const tmp = tempDir();
  const current = path.join(tmp, 'current');
  const baseline = path.join(tmp, 'baseline');
  const out = path.join(tmp, 'out.json');
  makePng(path.join(current, 'home.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(baseline, 'home.png'), 8, 8, [10, 20, 30]);
  const result = run(['--baseline', baseline, '--current', current, '--out', out]);
  assert(result.code === 0, `exit ${result.code}`);
  const data = readJson(out);
  assert(data.status === 'PASS', data.status);
  assert(data.maxDiffRatio === 0, data.maxDiffRatio);
});

test('changed screenshots FAIL and record the ratio', () => {
  const tmp = tempDir();
  const current = path.join(tmp, 'current');
  const baseline = path.join(tmp, 'baseline');
  const out = path.join(tmp, 'out.json');
  makePng(path.join(current, 'home.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(baseline, 'home.png'), 8, 8, [200, 210, 220]);
  const result = run(['--baseline', baseline, '--current', current, '--out', out]);
  assert(result.code === 1, `exit ${result.code}`);
  const data = readJson(out);
  assert(data.status === 'FAIL', data.status);
  assert(data.maxDiffRatio > 0, data.maxDiffRatio);
  assert(data.images[0].diffPixels === 64, data.images[0].diffPixels);
});

test('--max-diff-ratio allows a small intended change', () => {
  const tmp = tempDir();
  const current = path.join(tmp, 'current');
  const baseline = path.join(tmp, 'baseline');
  const out = path.join(tmp, 'out.json');
  makePng(path.join(current, 'home.png'), 10, 10, [10, 20, 30], { x: 0, y: 0, color: [255, 0, 0] });
  makePng(path.join(baseline, 'home.png'), 10, 10, [10, 20, 30]);
  const strict = run(['--baseline', baseline, '--current', current, '--out', out]);
  assert(strict.code === 1, `strict exit ${strict.code}`);
  const loose = run([
    '--baseline', baseline, '--current', current, '--out', out, '--max-diff-ratio', '0.02',
  ]);
  assert(loose.code === 0, `loose exit ${loose.code}`);
  assert(readJson(out).status === 'PASS', readJson(out).status);
});

test('no current screenshots SKIP with exit 3', () => {
  const tmp = tempDir();
  const out = path.join(tmp, 'out.json');
  const result = run([
    '--baseline', path.join(tmp, 'baseline'), '--current', path.join(tmp, 'empty'), '--out', out,
  ]);
  assert(result.code === 3, `exit ${result.code}`);
  const data = readJson(out);
  assert(data.status === 'SKIPPED', data.status);
  assert(/no PNG screenshots/.test(data.reason), data.reason);
});

test('a current image with no baseline FAILs', () => {
  const tmp = tempDir();
  const current = path.join(tmp, 'current');
  const baseline = path.join(tmp, 'baseline');
  const out = path.join(tmp, 'out.json');
  makePng(path.join(current, 'home.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(baseline, 'other.png'), 8, 8, [10, 20, 30]);
  const result = run(['--baseline', baseline, '--current', current, '--out', out]);
  assert(result.code === 1, `exit ${result.code}`);
  const data = readJson(out);
  assert(data.images[0].status === 'missing-baseline', data.images[0].status);
});

test('a baseline image with no current capture FAILs', () => {
  const tmp = tempDir();
  const current = path.join(tmp, 'current');
  const baseline = path.join(tmp, 'baseline');
  const out = path.join(tmp, 'out.json');
  makePng(path.join(current, 'home.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(baseline, 'home.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(baseline, 'removed.png'), 8, 8, [10, 20, 30]);
  const result = run(['--baseline', baseline, '--current', current, '--out', out]);
  assert(result.code === 1, `exit ${result.code}`);
  const data = readJson(out);
  const removed = data.images.find((image) => image.file === 'removed.png');
  assert(removed && removed.status === 'missing-current', JSON.stringify(data.images));
});

test('size mismatch FAILs', () => {
  const tmp = tempDir();
  const current = path.join(tmp, 'current');
  const baseline = path.join(tmp, 'baseline');
  const out = path.join(tmp, 'out.json');
  makePng(path.join(current, 'home.png'), 8, 8, [10, 20, 30]);
  makePng(path.join(baseline, 'home.png'), 4, 4, [10, 20, 30]);
  const result = run(['--baseline', baseline, '--current', current, '--out', out]);
  assert(result.code === 1, `exit ${result.code}`);
  assert(readJson(out).images[0].status === 'size-mismatch');
});

test('invalid --max-diff-ratio exits 2', () => {
  const tmp = tempDir();
  makePng(path.join(tmp, 'current', 'home.png'), 4, 4, [0, 0, 0]);
  const result = run([
    '--baseline', path.join(tmp, 'baseline'), '--current', path.join(tmp, 'current'),
    '--out', path.join(tmp, 'out.json'), '--max-diff-ratio', '2',
  ]);
  assert(result.code === 2, `exit ${result.code}`);
});

test('unknown option exits 2', () => {
  const result = run(['--nonsense']);
  assert(result.code === 2, `exit ${result.code}`);
});

const failed = results.filter((r) => r.status === 'FAIL');
fs.mkdirSync(EVIDENCE, { recursive: true });
fs.writeFileSync(
  path.join(EVIDENCE, 'visual-test.json'),
  `${JSON.stringify({ checks: results.length, pass: passed, failed: failed.length, results }, null, 2)}\n`,
);
console.log(`\n${passed} passed, ${failed.length} failed`);
process.exit(failed.length ? 1 : 0);
