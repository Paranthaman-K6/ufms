#!/usr/bin/env node
/* Verify selected target elements against the actual reference DOM and styles. */
'use strict';

const fs = require('fs');
const path = require('path');
const { Builder, By, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

const ROOT = path.resolve(__dirname, '..', '..', '..');
const EVIDENCE_DIR = path.resolve(process.env.UFME_EVIDENCE_DIR || path.join(ROOT, '.ufme', 'evidence'));
const TARGET_URL = process.argv[2];
const REF_URL_OVERRIDE = process.argv[3] || '';
const RESULT_FILE = path.join(EVIDENCE_DIR, 'reference-verify.json');
const SHOT_DIR = path.join(EVIDENCE_DIR, 'reference-verify-screenshots');

function readJson(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch (error) { throw new Error('Cannot read ' + file + ': ' + error.message); }
}

function validHttpUrl(value, label) {
  let parsed;
  try { parsed = new URL(value); }
  catch (_) { throw new Error(label + ' is not a valid URL: ' + value); }
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error(label + ' must use http or https');
  }
  return parsed.toString();
}

function safeFilePart(value) {
  return String(value || 'element').replace(/[^a-z0-9_-]+/gi, '-').slice(0, 70);
}

async function inspectSelector(driver, selector, screenshotPath) {
  const elements = await driver.findElements(By.css(selector));
  for (const element of elements) {
    if (!(await element.isDisplayed())) continue;
    const metrics = await driver.executeScript((el) => {
      const cs = window.getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return {
        tagName: el.tagName,
        text: (el.innerText || el.textContent || '').trim().slice(0, 200),
        styles: {
          backgroundColor: cs.backgroundColor,
          color: cs.color,
          fontFamily: cs.fontFamily,
          fontSize: cs.fontSize,
          fontWeight: cs.fontWeight,
          lineHeight: cs.lineHeight,
          letterSpacing: cs.letterSpacing,
          padding: cs.padding,
          margin: cs.margin,
          borderRadius: cs.borderRadius,
          boxShadow: cs.boxShadow,
          display: cs.display,
          gap: cs.gap,
          alignItems: cs.alignItems,
          justifyContent: cs.justifyContent
        },
        rect: {
          width: rect.width,
          height: rect.height,
          top: rect.top,
          left: rect.left
        }
      };
    }, element);
    try {
      fs.writeFileSync(screenshotPath, Buffer.from(await element.takeScreenshot(), 'base64'));
      metrics.screenshotFile = screenshotPath;
    } catch (error) {
      metrics.screenshotWarning = error.message;
    }
    return metrics;
  }
  return null;
}

function compareValue(property, expected, actual) {
  if (expected === undefined || expected === null || expected === '') {
    return { property, status: 'UNAVAILABLE', expected, actual };
  }
  if (property === 'width' || property === 'height') {
    const a = Number(expected);
    const b = Number(actual);
    const tolerance = Math.max(4, Math.abs(a) * 0.2);
    const pass = Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) <= tolerance;
    return { property, status: pass ? 'PASS' : 'FAIL', expected: a, actual: b, tolerance };
  }
  const a = String(expected).trim().toLowerCase().replace(/\s+/g, ' ');
  const b = String(actual === undefined ? '' : actual).trim().toLowerCase().replace(/\s+/g, ' ');
  if (property === 'fontFamily') {
    const first = a.split(',')[0].replace(/['"]/g, '').trim();
    const pass = first && b.replace(/['"]/g, '').includes(first);
    return { property, status: pass ? 'PASS' : 'FAIL', expected, actual };
  }
  return { property, status: a === b ? 'PASS' : 'FAIL', expected, actual };
}

function requestedProperties(aspects) {
  const value = String(aspects || '').toLowerCase();
  const visual = value.includes('visual') || value.includes('combination');
  const layout = value.includes('layout') || value.includes('combination');
  const properties = [];
  if (visual) properties.push('backgroundColor', 'color', 'fontFamily', 'fontSize', 'fontWeight', 'lineHeight', 'borderRadius', 'boxShadow');
  if (layout) properties.push('padding', 'margin', 'display', 'gap', 'alignItems', 'justifyContent', 'width', 'height');
  return { properties: Array.from(new Set(properties)), unsupported: ['behavior', 'animation', 'animations'].filter(x => value.includes(x)) };
}

async function main() {
  if (!TARGET_URL) {
    console.error('Usage: node reference-verify.js <targetUrl> [referenceUrl]');
    process.exit(2);
  }

  fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
  fs.mkdirSync(SHOT_DIR, { recursive: true });

  const matchPath = path.join(EVIDENCE_DIR, 'reference-match.json');
  const plan = readJson(matchPath);
  if (!plan || plan.status !== 'MATCHED' || !Array.isArray(plan.elements) || !plan.elements.length) {
    throw new Error('A MATCHED reference-match.json with selected elements is required; run reference-match.py first.');
  }

  const targetUrl = validHttpUrl(TARGET_URL, 'Target URL');
  const defaultReferenceUrl = REF_URL_OVERRIDE ? validHttpUrl(REF_URL_OVERRIDE, 'Reference URL') : (plan.url ? validHttpUrl(plan.url, 'Reference URL') : '');
  const results = {
    targetUrl,
    referenceUrl: defaultReferenceUrl,
    referenceUrls: plan.urls || (plan.url ? [plan.url] : []),
    referenceId: plan.referenceId || '',
    verifiedAt: new Date().toISOString(),
    status: 'RUNNING',
    comparisons: [],
    errors: [],
    summary: {}
  };

  const options = new chrome.Options();
  const extraFlags = (process.env.UFME_CHROME_FLAGS || '').split(/\s+/).filter(Boolean);
  options.addArguments('--headless=new', '--disable-dev-shm-usage', '--disable-gpu', '--window-size=1440,900', ...extraFlags);

  let driver;
  try {
    driver = await new Builder().forBrowser('chrome').setChromeOptions(options).build();
    const selected = plan.elements.filter(item => item.status === 'matched');
    for (const item of selected) {
      const entry = {
        elementId: item.elementId,
        elementType: item.elementType,
        referenceUrl: item.referenceUrl || defaultReferenceUrl,
        referenceSelector: item.referenceSelector,
        targetSelector: item.targetSelector || '',
        aspects: item.aspects,
        status: 'BLOCKED',
        checks: [],
        errors: []
      };

      if (!item.targetSelector) {
        entry.errors.push('Target selector is missing; implement the element and record its selector in ELEMENT_MAP.md.');
        results.comparisons.push(entry);
        continue;
      }

      const request = requestedProperties(item.aspects);
      if (!request.properties.length) {
        entry.errors.push('No measurable visual/layout aspect requested. Behavior and animation require explicit interaction tests.');
        results.comparisons.push(entry);
        continue;
      }

      let referenceMetrics;
      let targetMetrics;
      let itemReferenceUrl;
      try {
        itemReferenceUrl = validHttpUrl(REF_URL_OVERRIDE || item.referenceUrl || defaultReferenceUrl, 'Reference URL for ' + item.elementId);
        entry.referenceUrl = itemReferenceUrl;
      } catch (error) {
        entry.errors.push(error.message);
        results.comparisons.push(entry);
        continue;
      }
      const fileBase = safeFilePart(item.elementId);
      try {
        await driver.get(itemReferenceUrl);
        await driver.wait(until.elementLocated(By.tagName('body')), 10000);
        await driver.sleep(500);
        referenceMetrics = await inspectSelector(
          driver, item.referenceSelector, path.join(SHOT_DIR, fileBase + '-reference.png')
        );
        if (!referenceMetrics) {
          entry.errors.push('Reference selector did not match a visible element.');
          results.comparisons.push(entry);
          continue;
        }

        await driver.get(targetUrl);
        await driver.wait(until.elementLocated(By.tagName('body')), 10000);
        await driver.sleep(500);
        targetMetrics = await inspectSelector(
          driver, item.targetSelector, path.join(SHOT_DIR, fileBase + '-target.png')
        );
        if (!targetMetrics) {
          entry.errors.push('Target selector did not match a visible element.');
          results.comparisons.push(entry);
          continue;
        }
      } catch (error) {
        entry.errors.push(error.message);
        results.comparisons.push(entry);
        continue;
      }

      const expectedStyles = referenceMetrics.styles || {};
      const actualStyles = targetMetrics.styles || {};
      for (const property of request.properties) {
        const expected = property === 'width' || property === 'height'
          ? referenceMetrics.rect[property] : expectedStyles[property];
        const actual = property === 'width' || property === 'height'
          ? targetMetrics.rect[property] : actualStyles[property];
        entry.checks.push(compareValue(property, expected, actual));
      }

      if (request.unsupported.length) {
        entry.errors.push('Not verified by this style comparison: ' + request.unsupported.join(', ') + '. Add explicit interaction/animation checks before claiming full verification.');
      }
      const failed = entry.checks.some(check => check.status === 'FAIL');
      const unavailable = entry.checks.some(check => check.status === 'UNAVAILABLE');
      entry.status = failed ? 'FAIL' : (unavailable || request.unsupported.length ? 'PARTIAL' : 'PASS');
      entry.reference = referenceMetrics;
      entry.target = targetMetrics;
      results.comparisons.push(entry);
    }

    const statuses = results.comparisons.map(item => item.status);
    const passed = statuses.filter(status => status === 'PASS').length;
    const failed = statuses.filter(status => status === 'FAIL').length;
    const blocked = statuses.filter(status => status === 'BLOCKED').length;
    const partial = statuses.filter(status => status === 'PARTIAL').length;
    results.summary = { total: statuses.length, passed, failed, blocked, partial };
    results.status = statuses.length && passed === statuses.length ? 'PASS'
      : (failed ? 'FAIL' : (blocked ? 'BLOCKED' : 'PARTIAL'));
  } catch (error) {
    results.status = 'BLOCKED';
    results.errors.push(error.message);
  } finally {
    if (driver) {
      try { await driver.quit(); } catch (_) {}
    }
  }

  fs.writeFileSync(RESULT_FILE, JSON.stringify(results, null, 2) + '\n');
  console.log('[reference-verify] Status: ' + results.status);
  console.log('[reference-verify] Summary: ' + JSON.stringify(results.summary));
  console.log('[reference-verify] Evidence: ' + RESULT_FILE);
  process.exit(results.status === 'PASS' ? 0 : 1);
}

main().catch(error => {
  console.error('[reference-verify] Fatal: ' + error.message);
  process.exit(1);
});
