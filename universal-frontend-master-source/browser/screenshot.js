// universal-frontend-master-source/browser/screenshot.js
// Screenshot helpers with an evidence budget (todo 4.2).
//
// Budget modes (CLI flag read from process.argv, so callers inherit it for free):
//   --budget=viewport (default) : above-the-fold only, at mobile 390 and
//                                 desktop 1440 ONLY.
//   --budget=full               : adds full-page captures at the four UFME
//                                 viewports plus tablet 768 / laptop 1280.
//
// Other behaviors:
//   - Output width capped at 1280px via in-page canvas downscale (no extra
//     deps; native PNG bytes are kept only if canvas encoding is impossible).
//   - Encoded as JPEG quality ~70 via in-page canvas (todo 4.2: JPEG/WebP
//     instead of PNG) instead of raw PNG.
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

// Downscale cap and JPEG quality for the light built-in encoder.
const MAX_OUTPUT_WIDTH = 1280;
const MAX_CANVAS_HEIGHT = 16000; // stay under Chrome's 16384 canvas limit
const JPEG_QUALITY = 0.7;

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

// Re-encode a raw Selenium PNG (base64) via an in-page canvas:
//   - downscales to MAX_OUTPUT_WIDTH wide (and MAX_CANVAS_HEIGHT tall),
//   - encodes JPEG at JPEG_QUALITY.
// Falls back to the untouched PNG bytes when canvas processing is not
// possible (e.g. exotic drivers or canvas memory limits).
async function encodeImage(browser, base64Png) {
  const script = `
return (function () {
  return new Promise(function (resolve, reject) {
    try {
      var img = new Image();
      img.onload = function () {
        try {
          var scale = Math.min(1, ${MAX_OUTPUT_WIDTH} / img.naturalWidth, ${MAX_CANVAS_HEIGHT} / img.naturalHeight);
          var canvas = document.createElement('canvas');
          canvas.width = Math.max(1, Math.round(img.naturalWidth * scale));
          canvas.height = Math.max(1, Math.round(img.naturalHeight * scale));
          var ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          resolve(canvas.toDataURL('image/jpeg', ${JPEG_QUALITY}));
        } catch (encodeErr) {
          reject(encodeErr);
        }
      };
      img.onerror = function () { reject(new Error('screenshot image decode failed')); };
      img.src = 'data:image/png;base64,' + arguments[0];
    } catch (outerErr) {
      reject(outerErr);
    }
  });
})()`;
  try {
    const dataUrl = await browser.executeScript(script, base64Png);
    const marker = 'data:image/jpeg;base64,';
    if (typeof dataUrl === 'string' && dataUrl.startsWith(marker)) {
      return { buffer: Buffer.from(dataUrl.slice(marker.length), 'base64'), ext: '.jpg', encoding: 'jpeg' };
    }
  } catch (e) {
    // Canvas processing unavailable; keep the untouched PNG below.
  }
  return {
    buffer: Buffer.from(base64Png, 'base64'),
    ext: '.png',
    encoding: 'png-fallback',
  };
}

async function saveScreenshot(browser, outDir, baseName, base64Png) {
  const encoded = await encodeImage(browser, base64Png);
  const file = path.join(outDir, `${baseName}${encoded.ext}`);
  fs.writeFileSync(file, encoded.buffer);
  assertFile(file);
  return { file, size: fs.statSync(file).size, encoding: encoded.encoding };
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

async function captureSection(browser, outDir, name, selector, viewport = 'desktop') {
  await browser.setViewport(viewport);
  await browser.waitForSelector(selector);

  const base64 = await browser.screenshotElement(selector);
  const saved = await saveScreenshot(
    browser, outDir, `${name}-section-${selector.replace(/[^a-z0-9_-]+/gi, '-')}-${viewport}`
  );

  return { viewport, selector, budget: getBudget(), ...saved };
}

module.exports = {
  captureFullPage,
  captureSection,
  captureBudget,
  detectDarkSupport,
  encodeImage,
  applyTheme,
  budget: getBudget,
  sectionSelectors: getSectionSelectors,
  VIEWPORTS,
  BUDGET_MODES,
  BUDGET_VIEWPORTS,
  MAX_OUTPUT_WIDTH,
  JPEG_QUALITY,
  DARK_MODE_MODES,
};
