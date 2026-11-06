#!/usr/bin/env node
/*
 * reference-inspect.js — Selenium-based reference website element inspector.
 *
 * Loads a reference URL in a real browser, inspects the live DOM, extracts
 * computed CSS styles, and identifies individual UI elements (navigation,
 * headers, hero sections, cards, buttons, forms, etc.) with their selectors,
 * styles, and screenshots.
 *
 * Usage:
 *   node skills/universal-frontend-master/scripts/reference-inspect.js <url> [outputDir]
 *
 * Output:
 *   <outputDir>/.ufme/evidence/reference-inspect.json  — element catalog
 *   <outputDir>/.ufme/evidence/reference-screenshots/   — per-element PNGs
 *
 * Safety: project-local only; never sudo/pacman/systemctl.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { Builder, By, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

const ROOT = path.resolve(__dirname, '..', '..');
const URL = process.argv[2];
const OUT_DIR = process.argv[3] || path.join(ROOT, '.ufme', 'evidence');

if (!URL) {
  console.error('Usage: node reference-inspect.js <url> [outputDir]');
  process.exit(2);
}

fs.mkdirSync(OUT_DIR, { recursive: true });
const SCREENSHOT_DIR = path.join(OUT_DIR, 'reference-screenshots');
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

// Element types we look for, with their CSS selectors and confidence weights.
const ELEMENT_TYPES = [
  { name: 'navigation', selector: 'nav, [role="navigation"], .navbar, .nav-menu, header nav', weight: 10 },
  { name: 'header', selector: 'header, .header, .site-header, .masthead', weight: 9 },
  { name: 'hero', selector: '.hero, .hero-section, .banner, [role="banner"]', weight: 9 },
  { name: 'pricing', selector: '.pricing, .pricing-table, .pricing-card, .price-card', weight: 8 },
  { name: 'card', selector: '.card, .card-component, .feature-card', weight: 7 },
  { name: 'button', selector: 'button, .btn, .button, [role="button"]', weight: 6 },
  { name: 'form', selector: 'form, .form, .contact-form, [role="form"]', weight: 8 },
  { name: 'footer', selector: 'footer, .footer, .site-footer', weight: 8 },
  { name: 'sidebar', selector: 'aside, .sidebar, [role="complementary"]', weight: 7 },
  { name: 'gallery', selector: '.gallery, .image-grid, .carousel, .slider', weight: 7 },
  { name: 'dropdown', selector: '.dropdown, .select, [role="menu"]', weight: 6 },
  { name: 'mega-menu', selector: '.mega-menu, .mega-nav', weight: 7 },
  { name: 'dashboard', selector: '.dashboard, .admin-dashboard', weight: 8 },
  { name: 'product-layout', selector: '.product, .product-grid, .product-list', weight: 7 },
];

async function getComputedStyle(driver, element) {
  return await driver.executeScript((el) => {
    const cs = window.getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return {
      tagName: el.tagName,
      className: el.className || '',
      id: el.id || '',
      role: el.getAttribute('role') || '',
      textContent: (el.textContent || '').trim().slice(0, 200),
      styles: {
        backgroundColor: cs.backgroundColor,
        color: cs.color,
        fontFamily: cs.fontFamily,
        fontSize: cs.fontSize,
        padding: cs.padding,
        margin: cs.margin,
        display: cs.display,
        position: cs.position,
        width: rect.width + 'px',
        height: rect.height + 'px',
        top: rect.top + 'px',
        left: rect.left + 'px',
      },
    };
  }, element);
}

async function inspectReference() {
  const options = new chrome.Options();
  const extraFlags = (process.env.UFME_CHROME_FLAGS || '').split(/\s+/).filter(Boolean);
  // CI/container safety
  if (!extraFlags.includes('--no-sandbox') && (!process.env.XDG_RUNTIME_DIR || process.env.CI)) {
    extraFlags.push('--no-sandbox');
  }
  options.addArguments('--headless=new', '--disable-dev-shm-usage', '--disable-gpu', '--window-size=1440,900', ...extraFlags);

  const driver = await new Builder().forBrowser('chrome').setChromeOptions(options).build();

  const results = {
    url: URL,
    inspectedAt: new Date().toISOString(),
    elements: [],
    errors: [],
  };

  try {
    await driver.get(URL);
    await driver.wait(until.elementLocated(By.tagName('body')), 10000);
    await new Promise((r) => setTimeout(r, 2000)); // let JS render

    const pageTitle = await driver.getTitle();
    results.pageTitle = pageTitle;

    // Scroll to load lazy content
    await driver.executeScript('window.scrollTo(0, document.body.scrollHeight);');
    await new Promise((r) => setTimeout(r, 1000));
    await driver.executeScript('window.scrollTo(0, 0);');
    await new Promise((r) => setTimeout(r, 500));

    for (const { name, selector, weight } of ELEMENT_TYPES) {
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
          info.confidence = weight;

          // Capture screenshot of this element
          try {
            const screenshotBase64 = await el.takeScreenshot();
            const shotFile = path.join(SCREENSHOT_DIR, `${name}_${i}_${Date.now()}.png`);
            fs.writeFileSync(shotFile, Buffer.from(screenshotBase64, 'base64'));
            info.screenshotFile = shotFile;
          } catch (e) {
            // Screenshot may fail for some elements; not critical
          }

          results.elements.push(info);
        }
      } catch (e) {
        results.errors.push(`${selector}: ${e.message}`);
      }
    }

    results.status = 'PASS';
  } catch (e) {
    results.status = 'FAIL';
    results.errors.push(e.message);
  } finally {
    await driver.quit();
  }

  fs.writeFileSync(path.join(OUT_DIR, 'reference-inspect.json'), JSON.stringify(results, null, 2));
  console.log(`[reference-inspect] Found ${results.elements.length} elements from ${URL}`);
  console.log(`[reference-inspect] Results: ${path.join(OUT_DIR, 'reference-inspect.json')}`);
  process.exit(results.status === 'PASS' ? 0 : 1);
}

inspectReference().catch((e) => {
  console.error(`[reference-inspect] Fatal: ${e.message}`);
  process.exit(1);
});
