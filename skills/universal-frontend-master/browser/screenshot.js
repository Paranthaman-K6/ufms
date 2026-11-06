// skills/universal-frontend-master/browser/screenshot.js
// Screenshot helpers with an evidence budget (todo 4.2).
//
// Budget modes (CLI flag read from process.argv, so callers inherit it for free):
//   --budget=viewport (default) : above-the-fold only, at mobile 390 and
//                                 desktop 1440 ONLY.
//   --budget=full               : adds full-page captures at the four UFME
//                                 viewports plus tablet 768 / laptop 1280.
//
// Other behaviors:
//   - Captures are written as the driver's native PNG bytes so pngjs and
//     pixelmatch can decode them; no lossy re-encode.
//   - Every capture records its actual pixel width/height, and
//     writeManifest() records file + dimensions + viewport/theme next to the
//     screenshots for visual-diff.js to verify.
//   - Section crops via element.takeScreenshot() for each --sections selector
//     (comma-separated or repeated flags).
//   - Dark-theme pass ONLY when the page actually defines
//     prefers-color-scheme rules or exposes a theme toggle (detectDarkSupport);
//     callers that honor the budget skip dark captures when detection says no.
'use strict';

const fs = require('fs');
const path = require('path');
const { VIEWPORTS } = require('./viewport');

// Dark mode application modes:
//   'os-preference'   - Emulate OS color-scheme preference via media feature
//   'website-theme'   - Apply the website's own dark theme class
//   'color-scheme-hint' - Force CSS color-scheme hint only (weakest signal)
const DARK_MODE_MODES = {
  OS_PREFERENCE: 'os-preference',
  WEBSITE_THEME: 'website-theme',
  COLOR_SCHEME_HINT: 'color-scheme-hint',
};

// ---- Budget configuration (todo 4.2) ----
const BUDGET_MODES = {
  VIEWPORT: 'viewport',
  FULL: 'full',
};

// Default budget = above-the-fold at these two widths ONLY.
const BUDGET_VIEWPORTS = {
  mobile: { width: 390, height: 844 },
  desktop: { width: 1440, height: 900 },
};

// Downscale cap and canvas limit no longer apply: comparison needs the native
// PNG, so captures keep the exact pixel dimensions the driver produced.

// ---- CLI flag helpers (shared runtime state: same process as run.js) ----

function getFlag(name) {
  const argv = process.argv;
  const prefix = `--${name}=`;
  const idx = argv.indexOf(`--${name}`);
  if (idx !== -1) {
    const next = argv[idx + 1];
    if (next && !next.startsWith('--')) return next;
    return '';
  }
  const prefixed = argv.find((a) => a.startsWith(prefix));
  return prefixed ? prefixed.slice(prefix.length) : null;
}

function getBudget() {
  const value = getFlag('budget');
  return value === BUDGET_MODES.FULL ? BUDGET_MODES.FULL : BUDGET_MODES.VIEWPORT;
}

function getSectionSelectors() {
  const argv = process.argv;
  const selectors = [];
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg.startsWith('--sections=')) {
      selectors.push(...arg.slice('--sections='.length).split(','));
    } else if (arg === '--sections') {
      const next = argv[i + 1];
      if (next && !next.startsWith('--')) selectors.push(...next.split(','));
    }
  }
  return selectors.map((s) => s.trim()).filter(Boolean);
}

// ---- Light built-in processing (no extra dependencies) ----

// Read width/height straight from the PNG IHDR chunk. Keeps screenshot capture
// dependency-free while giving the manifest real pixel dimensions.
function pngDimensions(buffer) {
  const signature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  if (buffer.length < 24 || !buffer.subarray(0, 8).equals(signature)) {
    throw new Error('capture is not a PNG');
  }
  if (buffer.toString('ascii', 12, 16) !== 'IHDR') {
    throw new Error('PNG has no IHDR chunk');
  }
  return { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) };
}

async function saveScreenshot(browser, outDir, baseName, base64Png) {
  const file = path.join(outDir, `${baseName}.png`);
  const buffer = Buffer.from(base64Png, 'base64');
  fs.writeFileSync(file, buffer);
  assertFile(file);
  const { width, height } = pngDimensions(buffer);
  return { file, size: buffer.length, encoding: 'png', width, height };
}

// Record the captures that actually exist on disk. Dimensions are re-read from
// each file, so the manifest cannot drift from the pixels it describes.
function writeManifest(outDir, captures, meta = {}) {
  const images = new Map();
  for (const capture of captures) {
    if (!capture || !capture.file || !fs.existsSync(capture.file)) continue;
    const { width, height } = pngDimensions(fs.readFileSync(capture.file));
    images.set(path.basename(capture.file), {
      file: path.basename(capture.file),
      width,
      height,
      viewport: capture.viewport || null,
      theme: capture.theme || null,
      ...(capture.selector ? { selector: capture.selector } : {}),
    });
  }
  const manifest = {
    generatedAt: new Date().toISOString(),
    ...meta,
    images: [...images.values()],
  };
  const file = path.join(outDir, 'manifest.json');
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(manifest, null, 2)}\n`);
  return file;
}

function assertFile(file) {
  if (!fs.existsSync(file) || fs.statSync(file).size === 0) {
    throw new Error(`Screenshot file is missing or empty: ${file}`);
  }
}

// ---- Dark theme support detection (todo 4.2) ----
// Returns true ONLY when the page itself defines prefers-color-scheme rules
// (inline <style> text or same-origin stylesheet cssRules), a dark-aware
// <meta name="color-scheme"> hint, or a theme toggle / data-theme attribute.
// Inconclusive detection returns false (callers skip the dark pass).
const DARK_SUPPORT_SCRIPT = `
return (function () {
  var dark = false;
  function mentionsDark(t) { return typeof t === 'string' && t.indexOf('prefers-color-scheme') !== -1; }

  var styleEls = document.querySelectorAll('style');
  for (var i = 0; i < styleEls.length; i++) {
    if (mentionsDark(styleEls[i].textContent)) { dark = true; break; }
  }

  if (!dark) {
    for (var j = 0; j < document.styleSheets.length; j++) {
      try {
        var rules = document.styleSheets[j].cssRules;
        for (var k = 0; k < rules.length; k++) {
          if (mentionsDark(rules[k].cssText)) { dark = true; break; }
        }
      } catch (e) { /* cross-origin stylesheet: cssRules not readable */ }
      if (dark) break;
    }
  }

  if (!dark) {
    var meta = document.querySelector('meta[name="color-scheme"]');
    if (meta && /dark/i.test(meta.getAttribute('content') || '')) dark = true;
  }

  if (!dark) {
    if (document.querySelector(
      '[data-theme],[data-theme-toggle],[data-bs-theme],' +
      '[class*="theme-toggle" i],[id*="theme-toggle" i],' +
      '[aria-label*="theme" i],[data-test*="theme" i]')) dark = true;
  }

  if (!dark) {
    if (document.documentElement.hasAttribute('data-theme') ||
        document.documentElement.hasAttribute('data-color-scheme')) dark = true;
  }

  return dark;
})()`;

async function detectDarkSupport(browser) {
  try {
    return Boolean(await browser.executeScript(DARK_SUPPORT_SCRIPT));
  } catch (e) {
    // Inconclusive detection -> skip the dark theme pass.
    return false;
  }
}

// ---- Capture helpers ----

// Light captures are always applied; dark requires explicit page support and
// is invoked by the caller only when detectDarkSupport() returned true.
async function applyTheme(browser, theme, darkModeMode = DARK_MODE_MODES.COLOR_SCHEME_HINT) {
  if (theme !== 'dark') return;
  try {
    if (darkModeMode === DARK_MODE_MODES.OS_PREFERENCE) {
      await browser.executeScript(
        `document.documentElement.classList.add('ufme-dark-os-preference');`
      );
    } else if (darkModeMode === DARK_MODE_MODES.WEBSITE_THEME) {
      await browser.executeScript(
        `document.documentElement.classList.add('ufme-dark-theme', 'dark');`
      );
    } else {
      await browser.executeScript(
        `document.documentElement.style.colorScheme='dark';`
      );
    }
  } catch (e) {
    // Dark theme override not applicable to this page.
  }
}

async function documentDimensions(browser, size) {
  try {
    return await browser.executeScript(() => {
      const body = document.body;
      const html = document.documentElement;
      return {
        width: Math.max(body.scrollWidth, body.offsetWidth, html.clientWidth, html.scrollWidth, html.offsetWidth),
        height: Math.max(body.scrollHeight, body.offsetHeight, html.clientHeight, html.scrollHeight, html.offsetHeight),
      };
    });
  } catch (e) {
    return { width: size.width, height: size.height };
  }
}

// Above-the-fold captures at a fixed set of viewports (budget mode).
async function captureViewportSet(browser, outDir, name, theme, viewports, darkModeMode = DARK_MODE_MODES.COLOR_SCHEME_HINT) {
  const results = [];
  for (const [vp, size] of Object.entries(viewports)) {
    await browser.setViewport(vp);
    await applyTheme(browser, theme, darkModeMode);

    const base64 = await browser.screenshot(name, vp);

    const saved = await saveScreenshot(
      browser, outDir, `${name}-${vp}-${theme}`, base64
    );
    results.push({
      viewport: vp, theme, budget: BUDGET_MODES.VIEWPORT,
      darkModeMode: theme === 'dark' ? darkModeMode : null,
      ...saved,
    });
  }
  return results;
}

// Full-page captures (resize window to document size) - used by --budget=full
// and kept as the backwards-compatible entry point.
async function captureFullPage(browser, outDir, name, theme = 'light', darkModeMode = DARK_MODE_MODES.COLOR_SCHEME_HINT) {
  const results = [];
  for (const [vp, size] of Object.entries(VIEWPORTS)) {
    await browser.setViewport(vp);
    await applyTheme(browser, theme, darkModeMode);

    const dimensions = await documentDimensions(browser, size);

    // Grow the window to the full document size via WebDriver (window.resizeTo
    // inside the page is ignored by headless browsers).
    try {
      await browser.setWindowSize(dimensions.width, dimensions.height);
      await new Promise((r) => setTimeout(r, 100));
    } catch (e) {
      // Resize may not be supported in all headless contexts; continue with viewport.
    }

    const base64 = await browser.screenshot(name);
    const saved = await saveScreenshot(browser, outDir, `${name}-${vp}-${theme}`, base64);

    results.push({
      viewport: vp, theme, budget: BUDGET_MODES.FULL,
      darkModeMode: theme === 'dark' ? darkModeMode : null,
      ...saved,
    });
  }
  return results;
}

// Main entry honoring the --budget flag (and --sections crops).
async function captureBudget(browser, outDir, name, theme = 'light', darkModeMode = DARK_MODE_MODES.COLOR_SCHEME_HINT) {
  const budget = getBudget();
  const results = [];

  // Above-the-fold pass: {390, 1440} by default; +768/1280 in full budget.
  if (budget === BUDGET_MODES.FULL) {
    results.push(...await captureViewportSet(browser, outDir, name, theme, VIEWPORTS, darkModeMode));
  } else {
    results.push(...await captureViewportSet(browser, outDir, name, theme, BUDGET_VIEWPORTS, darkModeMode));
  }

  // Full budget additionally captures complete page scrolls.
  if (budget === BUDGET_MODES.FULL) {
    const fullPageName = `${name}-fullpage`;
    results.push(...await captureFullPage(browser, outDir, fullPageName, theme, darkModeMode));
  }

  // Section crops (both budgets; cropped from the rendered elements).
  const selectors = getSectionSelectors();
  for (const selector of selectors) {
    const sectionViewports = budget === BUDGET_MODES.FULL
      ? Object.keys(VIEWPORTS)
      : Object.keys(BUDGET_VIEWPORTS);
    for (const vp of sectionViewports) {
      try {
        results.push(await captureSection(browser, outDir, name, selector, vp));
      } catch (e) {
        // Selector not present on this page/viewport; best effort only.
      }
    }
  }

  return results;
}

async function captureSection(browser, outDir, name, selector, viewport = 'desktop', theme = 'light') {
  await browser.setViewport(viewport);
  if (theme === 'dark') {
    try {
      await applyTheme(browser, theme);
    } catch (e) {
      // Dark theme override not applicable; continue with light capture.
    }
  }
  await browser.waitForSelector(selector);

  const base64 = await browser.screenshotElement(selector);
  const saved = await saveScreenshot(
    browser, outDir, `${name}-section-${selector.replace(/[^a-z0-9_-]+/gi, '-')}-${viewport}-${theme}`, base64
  );

  return { viewport, selector, theme, budget: getBudget(), ...saved };
}

module.exports = {
  captureFullPage,
  captureSection,
  captureBudget,
  detectDarkSupport,
  writeManifest,
  pngDimensions,
  applyTheme,
  budget: getBudget,
  sectionSelectors: getSectionSelectors,
  VIEWPORTS,
  BUDGET_MODES,
  BUDGET_VIEWPORTS,
  DARK_MODE_MODES,
};
