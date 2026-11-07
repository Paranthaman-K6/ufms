#!/usr/bin/env node
/*
 * Inspect a reference URL with Selenium and persist evidence by stable URL ID.
 * Usage: node reference-inspect.js <url> [evidenceDir]
 */
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { Builder, By, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

const ROOT = path.resolve(__dirname, '..', '..', '..');
const RAW_URL = process.argv[2];
const OUT_DIR = path.resolve(process.argv[3] || path.join(ROOT, '.ufme', 'evidence'));

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
  { name: 'product-layout', selector: '.product, .product-grid, .product-list', weight: 7 }
];

function normalizeUrl(value) {
  let url;
  try { url = new URL(value); }
  catch (_) { throw new Error('Invalid reference URL: ' + value); }
  if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Reference URL must use http or https.');
  return url.toString();
}

async function readElement(driver, element) {
  return driver.executeScript((el) => {
    const cs = window.getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return {
      tagName: el.tagName,
      className: typeof el.className === 'string' ? el.className : '',
      id: el.id || '',
      uniqueSelector: (() => {
        const escape = (value) => (window.CSS && CSS.escape)
          ? CSS.escape(value)
          : String(value).replace(/([^a-zA-Z0-9_-])/g, '\\$1');
        const parts = [];
        let node = el;
        while (node && node.nodeType === 1 && node !== document.documentElement) {
          let part = node.tagName.toLowerCase();
          if (node.id) {
            part += '#' + escape(node.id);
            parts.unshift(part);
            break;
          }
          const classes = Array.from(node.classList || []).filter(Boolean).slice(0, 2);
          if (classes.length) {
            part += '.' + classes.map(escape).join('.');
          }
          if (node.parentElement) {
            const sameTag = Array.from(node.parentElement.children)
              .filter(sibling => sibling.tagName === node.tagName);
            if (sameTag.length > 1) part += ':nth-of-type(' + (sameTag.indexOf(node) + 1) + ')';
          }
          parts.unshift(part);
          node = node.parentElement;
          if (node === document.body) {
            parts.unshift('body');
            break;
          }
        }
        return parts.join(' > ');
      })(),
      role: el.getAttribute('role') || '',
      textContent: (el.textContent || '').trim().slice(0, 300),
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
        position: cs.position,
        gap: cs.gap,
        alignItems: cs.alignItems,
        justifyContent: cs.justifyContent,
        gridTemplateColumns: cs.gridTemplateColumns,
        flexDirection: cs.flexDirection
      },
      rect: {
        width: rect.width,
        height: rect.height,
        top: rect.top,
        left: rect.left
      }
    };
  }, element);
}

async function main() {
  if (!RAW_URL) {
    console.error('Usage: node reference-inspect.js <url> [evidenceDir]');
    process.exit(2);
  }

  let url;
  try { url = normalizeUrl(RAW_URL); }
  catch (error) { console.error('[reference-inspect] ' + error.message); process.exit(2); }

  const referenceId = crypto.createHash('sha256').update(url).digest('hex').slice(0, 12);
  const screenshotDir = path.join(OUT_DIR, 'reference-screenshots', referenceId);
  fs.mkdirSync(screenshotDir, { recursive: true });

  const result = {
    referenceId,
    url,
    inspectedAt: new Date().toISOString(),
    elements: [],
    errors: [],
    warnings: []
  };

  const options = new chrome.Options();
  const extraFlags = (process.env.UFME_CHROME_FLAGS || '').split(/\s+/).filter(Boolean);
  options.addArguments('--headless=new', '--disable-dev-shm-usage', '--disable-gpu', '--window-size=1440,900', ...extraFlags);

  let driver;
  try {
    driver = await new Builder().forBrowser('chrome').setChromeOptions(options).build();
    await driver.get(url);
    await driver.wait(until.elementLocated(By.tagName('body')), 10000);
    await driver.sleep(1200);
    result.pageTitle = await driver.getTitle();

    await driver.executeScript('window.scrollTo(0, document.body.scrollHeight);');
    await driver.sleep(600);
    await driver.executeScript('window.scrollTo(0, 0);');
    await driver.sleep(300);

    for (const type of ELEMENT_TYPES) {
      try {
        const found = await driver.findElements(By.css(type.selector));
        for (let index = 0; index < found.length; index++) {
          const element = found[index];
          if (!(await element.isDisplayed())) continue;
          const info = await readElement(driver, element);
          info.elementType = type.name;
          // Use a unique selector for this exact inspected element. Broad
          // selectors (for example "button") make later verification ambiguous.
          info.selector = info.uniqueSelector;
          delete info.uniqueSelector;
          info.index = index;
          info.confidence = type.weight;

          const shotName = type.name + '-' + index + '.png';
          const shotFile = path.join(screenshotDir, shotName);
          try {
            fs.writeFileSync(shotFile, Buffer.from(await element.takeScreenshot(), 'base64'));
            info.screenshotFile = shotFile;
          } catch (error) {
            info.screenshotFile = '';
            result.warnings.push(type.name + '[' + index + '] screenshot failed: ' + error.message);
          }
          result.elements.push(info);
        }
      } catch (error) {
        result.errors.push(type.selector + ': ' + error.message);
      }
    }

    result.status = result.elements.length ? 'PASS' : 'EMPTY';
    if (!result.elements.length) result.errors.push('No visible supported UI elements were found.');
  } catch (error) {
    result.status = 'FAIL';
    result.errors.push(error.message);
  } finally {
    if (driver) {
      try { await driver.quit(); } catch (error) { result.warnings.push('Browser close failed: ' + error.message); }
    }
  }

  const payload = JSON.stringify(result, null, 2) + '\n';
  const uniqueFile = path.join(OUT_DIR, 'reference-inspect-' + referenceId + '.json');
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(uniqueFile, payload);
  fs.writeFileSync(path.join(OUT_DIR, 'reference-inspect.json'), payload);

  console.log('[reference-inspect] ' + result.status + ': ' + result.elements.length + ' visible elements from ' + url);
  console.log('[reference-inspect] Evidence: ' + uniqueFile);
  console.log('[reference-inspect] Screenshots: ' + screenshotDir);
  if (result.warnings.length) console.warn('[reference-inspect] ' + result.warnings.length + ' warning(s); see evidence JSON.');
  process.exit(result.status === 'PASS' ? 0 : 1);
}

main().catch(error => {
  console.error('[reference-inspect] Fatal: ' + error.message);
  process.exit(1);
});
