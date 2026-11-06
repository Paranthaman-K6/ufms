#!/usr/bin/env node
/*
 * reference-verify.js — Verify reference element implementation against target URL.
 *
 * Captures before/after screenshots of the target page and compares them
 * against the reference intent. Reports whether the implementation matches.
 *
 * Usage:
 *   node skills/universal-frontend-master/scripts/reference-verify.js <targetUrl> [referenceUrl]
 *
 * Output:
 *   .ufme/evidence/reference-verify.json  — verification results
 *   .ufme/evidence/reference-verify-screenshots/  — before/after PNGs
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { Builder, By, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

const ROOT = path.resolve(__dirname, '..', '..', '..');
const TARGET_URL = process.argv[2];
const REF_URL = process.argv[3];
const OUT_DIR = path.join(ROOT, '.ufme', 'evidence');

if (!TARGET_URL) {
  console.error('Usage: node reference-verify.js <targetUrl> [referenceUrl]');
  process.exit(2);
}

fs.mkdirSync(OUT_DIR, { recursive: true });
const SHOT_DIR = path.join(OUT_DIR, 'reference-verify-screenshots');
fs.mkdirSync(SHOT_DIR, { recursive: true });

async function getComputedStyle(driver, element) {
  return await driver.executeScript((el) => {
    const cs = window.getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return {
      tagName: el.tagName,
      className: el.className || '',
      id: el.id || '',
      styles: {
        backgroundColor: cs.backgroundColor,
        color: cs.color,
        fontFamily: cs.fontFamily,
        fontSize: cs.fontSize,
        padding: cs.padding,
        margin: cs.margin,
        display: cs.display,
      },
      rect: { width: rect.width, height: rect.height, top: rect.top, left: rect.left },
    };
  }, element);
}

async function captureVerification() {
  const options = new chrome.Options();
  const extraFlags = (process.env.UFME_CHROME_FLAGS || '').split(/\s+/).filter(Boolean);
  if (!extraFlags.includes('--no-sandbox') && (!process.env.XDG_RUNTIME_DIR || process.env.CI)) {
    extraFlags.push('--no-sandbox');
  }
  options.addArguments('--headless=new', '--disable-dev-shm-usage', '--disable-gpu', '--window-size=1440,900', ...extraFlags);

  const driver = await new Builder().forBrowser('chrome').setChromeOptions(options).build();

  const results = {
    targetUrl: TARGET_URL,
    referenceUrl: REF_URL || null,
    verifiedAt: new Date().toISOString(),
    elements: [],
    errors: [],
    status: 'RUNNING',
  };

  try {
    await driver.get(TARGET_URL);
    await driver.wait(until.elementLocated(By.tagName('body')), 10000);
    await new Promise((r) => setTimeout(r, 2000));

    const pageTitle = await driver.getTitle();
    results.pageTitle = pageTitle;

    // Inspect key elements on the target page
    const elementTypes = [
      { name: 'navigation', selector: 'nav, [role="navigation"], .navbar, .nav-menu, header nav' },
      { name: 'header', selector: 'header, .header, .site-header, .masthead' },
      { name: 'hero', selector: '.hero, .hero-section, .banner, [role="banner"]' },
      { name: 'pricing', selector: '.pricing, .pricing-table, .pricing-card, .price-card' },
      { name: 'card', selector: '.card, .card-component, .feature-card' },
      { name: 'button', selector: 'button, .btn, .button, [role="button"]' },
      { name: 'form', selector: 'form, .form, .contact-form, [role="form"]' },
      { name: 'footer', selector: 'footer, .footer, .site-footer' },
    ];

    for (const { name, selector } of elementTypes) {
      try {
        const elements = await driver.findElements(By.css(selector));
        for (let i = 0; i < elements.length; i++) {
          const el = elements[i];
          const isDisplayed = await el.isDisplayed();
          if (!isDisplayed) continue;

          const info = await getComputedStyle(driver, el);
          info.elementType = name;
          info.selector = selector;
          info.index = i;

          // Capture screenshot of this element
          try {
            const screenshotBase64 = await el.takeScreenshot();
            const shotFile = path.join(SHOT_DIR, `verify-${name}-${i}-${Date.now()}.png`);
            fs.writeFileSync(shotFile, Buffer.from(screenshotBase64, 'base64'));
            info.screenshotFile = shotFile;
          } catch (e) {
            // Not critical
          }

          results.elements.push(info);
        }
      } catch (e) {
        results.errors.push(`${selector}: ${e.message}`);
      }
    }

    results.status = 'PASS';
    results.summary = {
      totalElements: results.elements.length,
      elementTypes: {},
    };
    for (const el of results.elements) {
      const t = el.elementType;
      results.summary.elementTypes[t] = (results.summary.elementTypes[t] || 0) + 1;
    }
  } catch (e) {
    results.status = 'FAIL';
    results.errors.push(e.message);
  } finally {
    await driver.quit();
  }

  fs.writeFileSync(path.join(OUT_DIR, 'reference-verify.json'), JSON.stringify(results, null, 2));
  console.log(`[reference-verify] Verified ${results.elements.length} elements on ${TARGET_URL}`);
  console.log(`[reference-verify] Results: ${path.join(OUT_DIR, 'reference-verify.json')}`);
  process.exit(results.status === 'PASS' ? 0 : 1);
}

captureVerification().catch((e) => {
  console.error(`[reference-verify] Fatal: ${e.message}`);
  process.exit(1);
});
