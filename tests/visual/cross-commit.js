#!/usr/bin/env node
/*
 * tests/visual/cross-commit.js — proves visual-diff detects a screenshot
 * change made in a later commit (not a build compared against itself).
 *
 * Creates a throwaway git repository, commits a PNG as the "base" commit,
 * commits a changed PNG as the "head" commit, materializes both images from
 * their commits with `git show`, and compares:
 *   * base vs head  -> FAIL (exit 1), changed image reported
 *   * base vs base  -> PASS (exit 0)
 *   * head vs head  -> PASS (exit 0)
 *
 * Usage: node tests/visual/cross-commit.js
 * Exit: 0 all pass, 1 failure.
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const { PNG } = require('pngjs');

const ROOT = path.resolve(__dirname, '..', '..');
const SCRIPT = path.join(ROOT, 'skills/universal-frontend-master', 'scripts', 'visual-diff.js');
const EVIDENCE = path.join(ROOT, '.ufme', 'evidence');

function git(cwd, args) {
  const result = spawnSync(
    'git', ['-c', 'user.email=ufme@example.invalid', '-c', 'user.name=UFME', ...args],
    { cwd, encoding: 'utf8' },
  );
  if (result.status !== 0) throw new Error(`git ${args.join(' ')}: ${result.stderr}`);
  return result.stdout;
}

function png(buffer, color) {
  const image = new PNG({ width: 12, height: 12 });
  for (let i = 0; i < image.data.length; i += 4) {
    image.data[i] = color[0];
    image.data[i + 1] = color[1];
    image.data[i + 2] = color[2];
    image.data[i + 3] = 255;
  }
  fs.writeFileSync(buffer, PNG.sync.write(image));
}

// Materialize <rev>:screenshot.png into <dir>/screenshot.png (a real capture
// of that commit, not a copy of the working tree).
function exportAt(cwd, rev, dir) {
  const result = spawnSync('git', ['show', `${rev}:screenshot.png`], { cwd });
  if (result.status !== 0) throw new Error(`git show ${rev}: ${result.stderr}`);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'screenshot.png'), result.stdout);
}

function compare(baseline, current, out) {
  const result = spawnSync('node', [
    SCRIPT, '--baseline', baseline, '--current', current, '--out', out,
  ], { cwd: ROOT, encoding: 'utf8' });
  return {
    code: result.status,
    data: fs.existsSync(out) ? JSON.parse(fs.readFileSync(out, 'utf8')) : null,
  };
}

function main() {
  const checks = [];
  const record = (name, ok, detail) => {
    checks.push({ name, status: ok ? 'PASS' : 'FAIL', detail });
    console.log(`${ok ? 'PASS' : 'FAIL'}: ${name}${detail ? ` — ${detail}` : ''}`);
  };

  const repo = fs.mkdtempSync(path.join(os.tmpdir(), 'ufme-cross-commit-'));
  try {
    git(repo, ['init', '-q']);
    png(path.join(repo, 'screenshot.png'), [10, 20, 30]);
    git(repo, ['add', 'screenshot.png']);
    git(repo, ['commit', '-q', '-m', 'base screenshot']);
    const baseRev = git(repo, ['rev-parse', 'HEAD']).trim();

    png(path.join(repo, 'screenshot.png'), [220, 30, 40]);
    git(repo, ['add', 'screenshot.png']);
    git(repo, ['commit', '-q', '-m', 'head screenshot change']);
    const headRev = git(repo, ['rev-parse', 'HEAD']).trim();

    if (baseRev === headRev) throw new Error('commits did not advance');

    const base = path.join(repo, 'captures', 'base');
    const head = path.join(repo, 'captures', 'head');
    exportAt(repo, baseRev, base);
    exportAt(repo, headRev, head);

    const changed = compare(base, head, path.join(repo, 'changed.json'));
    record(
      'base-vs-head detects the visual change',
      changed.code === 1 && changed.data && changed.data.status === 'FAIL',
      `exit ${changed.code}, status ${changed.data && changed.data.status}`,
    );
    record(
      'the changed image is reported as changed',
      Boolean(changed.data) && changed.data.images.some((i) => i.file === 'screenshot.png' && i.status === 'changed'),
      changed.data ? JSON.stringify(changed.data.images) : 'no report',
    );

    const sameBase = compare(base, base, path.join(repo, 'same-base.json'));
    record(
      'base-vs-base passes (no false positive)',
      sameBase.code === 0 && sameBase.data && sameBase.data.status === 'PASS',
      `exit ${sameBase.code}, status ${sameBase.data && sameBase.data.status}`,
    );

    const sameHead = compare(head, head, path.join(repo, 'same-head.json'));
    record(
      'head-vs-head passes (no false positive)',
      sameHead.code === 0 && sameHead.data && sameHead.data.status === 'PASS',
      `exit ${sameHead.code}, status ${sameHead.data && sameHead.data.status}`,
    );
  } catch (err) {
    record('cross-commit comparison runs', false, err.message);
  }

  const failed = checks.filter((c) => c.status === 'FAIL');
  fs.mkdirSync(EVIDENCE, { recursive: true });
  fs.writeFileSync(
    path.join(EVIDENCE, 'visual-cross-commit.json'),
    `${JSON.stringify({ checks: checks.length, failed: failed.length, results: checks }, null, 2)}\n`,
  );
  console.log(`\n${checks.length - failed.length} passed, ${failed.length} failed`);
  return failed.length ? 1 : 0;
}

process.exit(main());
