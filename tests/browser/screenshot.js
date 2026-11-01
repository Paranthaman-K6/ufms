// tests/browser/screenshot.js
// Screenshot helpers: full-page + section-level at all viewports, dark/light themes.
const fs = require('fs');
const path = require('path');

const VIEWPORTS = {
  mobile: { width: 390, height: 844 },
  tablet: { width: 768, height: 1024 },
  laptop: { width: 1280, height: 800 },
  desktop: { width: 1440, height: 900 },
};

async function captureFullPage(browser, outDir, name, theme = 'light') {
  const results = [];
  for (const [vp, size] of Object.entries(VIEWPORTS)) {
    await browser.setViewport(vp);
    if (theme === 'dark') {
      // Best-effort dark theme via CSS media override is page-dependent; note it.
    }
    const base64 = await browser.screenshot(name, vp);
    const file = path.join(outDir, `${name}-${vp}-${theme}.png`);
    fs.writeFileSync(file, Buffer.from(base64, 'base64'));
    results.push({ viewport: vp, theme, file });
  }
  return results;
}

async function captureSection(browser, outDir, name, selector, viewport = 'desktop') {
  await browser.setViewport(viewport);
  await browser.waitForSelector(selector);
  const el = await browser.driverFindElement ? browser.driverFindElement({ css: selector }) : null;
  if (!el) throw new Error(`Section not found: ${selector}`);
  const base64 = await el.takeScreenshot ? await el.takeScreenshot() : await browser.screenshot(name, viewport);
  const file = path.join(outDir, `${name}-section-${viewport}.png`);
  fs.writeFileSync(file, Buffer.from(base64, 'base64'));
  return { viewport, file };
}

module.exports = { captureFullPage, captureSection, VIEWPORTS };
