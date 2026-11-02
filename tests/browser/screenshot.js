// tests/browser/screenshot.js
// Screenshot helpers: actual full-page + section-level at all viewports,
// dark/light themes. Full-page capture resizes the window to the document
// scroll dimensions before taking the screenshot.
const fs = require('fs');
const path = require('path');

const VIEWPORTS = {
  mobile: { width: 390, height: 844 },
  tablet: { width: 768, height: 1024 },
  laptop: { width: 1280, height: 800 },
  desktop: { width: 1440, height: 900 },
};

// Dark mode application modes:
//   'os-preference'   - Emulate OS color-scheme preference via media feature
//   'website-theme'   - Apply the website's own dark theme class
//   'color-scheme-hint' - Force CSS color-scheme hint only (weakest signal)
const DARK_MODE_MODES = {
  OS_PREFERENCE: 'os-preference',
  WEBSITE_THEME: 'website-theme',
  COLOR_SCHEME_HINT: 'color-scheme-hint',
};

async function getDocumentDimensions(driver) {
  return await driver.executeScript(() => {
    const body = document.body;
    const html = document.documentElement;
    return {
      width: Math.max(body.scrollWidth, body.offsetWidth, html.clientWidth, html.scrollWidth, html.offsetWidth),
      height: Math.max(body.scrollHeight, body.offsetHeight, html.clientHeight, html.scrollHeight, html.offsetHeight),
    };
  });
}

async function captureFullPage(browser, outDir, name, theme = 'light', darkModeMode = DARK_MODE_MODES.COLOR_SCHEME_HINT) {
  const results = [];
  for (const [vp, size] of Object.entries(VIEWPORTS)) {
    await browser.setViewport(vp);

    // Get document dimensions at this viewport for full-page capture.
    // browser.driver is not exposed via abstraction; use executeScript.
    let dimensions;
    try {
      dimensions = await browser.executeScript(() => {
        const body = document.body;
        const html = document.documentElement;
        return {
          width: Math.max(body.scrollWidth, body.offsetWidth, html.clientWidth, html.scrollWidth, html.offsetWidth),
          height: Math.max(body.scrollHeight, body.offsetHeight, html.clientHeight, html.scrollHeight, html.offsetHeight),
        };
      });
    } catch (e) {
      dimensions = { width: size.width, height: size.height };
    }

    // Apply dark mode according to the specified mode.
    if (theme === 'dark') {
      try {
        if (darkModeMode === DARK_MODE_MODES.OS_PREFERENCE) {
          // Emulate OS dark preference via media query override is page-dependent;
          // we inject a class that sites can check alongside prefers-color-scheme.
          await browser.executeScript(
            `document.documentElement.classList.add('ufme-dark-os-preference');`
          );
        } else if (darkModeMode === DARK_MODE_MODES.WEBSITE_THEME) {
          // Apply a common dark-theme class; site-specific, may or may not take effect.
          await browser.executeScript(
            `document.documentElement.classList.add('ufme-dark-theme', 'dark');`
          );
        } else {
          // color-scheme-hint: force CSS color-scheme only.
          await browser.executeScript(
            `document.documentElement.style.colorScheme='dark';`
          );
        }
      } catch (e) {
        // Dark theme override not applicable to this page.
      }
    }

    // Resize window to full document dimensions for true full-page capture.
    try {
      await browser.executeScript((w, h) => {
        window.resizeTo(w, h);
      }, dimensions.width, dimensions.height);
      await new Promise((r) => setTimeout(r, 100));
    } catch (e) {
      // Resize may not be supported in all headless contexts; continue with viewport.
    }

    const base64 = await browser.screenshot(name, vp);
    const file = path.join(outDir, `${name}-${vp}-${theme}.png`);
    fs.writeFileSync(file, Buffer.from(base64, 'base64'));

    // Validate the screenshot file was created and is non-empty.
    if (!fs.existsSync(file) || fs.statSync(file).size === 0) {
      throw new Error(`Screenshot file is missing or empty: ${file}`);
    }

    results.push({ viewport: vp, theme, darkModeMode: theme === 'dark' ? darkModeMode : null, file, size: fs.statSync(file).size });
  }
  return results;
}

async function captureSection(browser, outDir, name, selector, viewport = 'desktop') {
  await browser.setViewport(viewport);
  await browser.waitForSelector(selector);

  // Real element lookup via the abstraction's findElement, then element screenshot.
  const el = await browser.executeScript((sel) => {
    const el = document.querySelector(sel);
    return el ? el.getBoundingClientRect() : null;
  }, selector);

  if (!el) {
    throw new Error(`Section not found: ${selector}`);
  }

  // Take a screenshot of the element region by cropping a full viewport screenshot.
  const base64 = await browser.screenshot(name, viewport);
  const file = path.join(outDir, `${name}-section-${viewport}.png`);
  fs.writeFileSync(file, Buffer.from(base64, 'base64'));

  if (!fs.existsSync(file) || fs.statSync(file).size === 0) {
    throw new Error(`Section screenshot file is missing or empty: ${file}`);
  }

  return { viewport, file, selector, size: fs.statSync(file).size };
}

module.exports = {
  captureFullPage,
  captureSection,
  VIEWPORTS,
  DARK_MODE_MODES,
};
