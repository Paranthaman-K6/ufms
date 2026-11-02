// tests/browser/screenshot.js
// Screenshot helpers: full-page and section-level at all viewports, light/dark.
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

function assertFile(file) {
  if (!fs.existsSync(file) || fs.statSync(file).size === 0) {
    throw new Error(`Screenshot file is missing or empty: ${file}`);
  }
}

async function captureFullPage(browser, outDir, name, theme = 'light', darkModeMode = DARK_MODE_MODES.COLOR_SCHEME_HINT) {
  const results = [];
  for (const [vp, size] of Object.entries(VIEWPORTS)) {
    await browser.setViewport(vp);

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

    if (theme === 'dark') {
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

    // Grow the window to the full document size via WebDriver (window.resizeTo
    // inside the page is ignored by headless browsers).
    try {
      await browser.setWindowSize(dimensions.width, dimensions.height);
      await new Promise((r) => setTimeout(r, 100));
    } catch (e) {
      // Resize may not be supported in all headless contexts; continue with viewport.
    }

    const base64 = await browser.screenshot(name);
    const file = path.join(outDir, `${name}-${vp}-${theme}.png`);
    fs.writeFileSync(file, Buffer.from(base64, 'base64'));
    assertFile(file);

    results.push({ viewport: vp, theme, darkModeMode: theme === 'dark' ? darkModeMode : null, file, size: fs.statSync(file).size });
  }
  return results;
}

async function captureSection(browser, outDir, name, selector, viewport = 'desktop') {
  await browser.setViewport(viewport);
  await browser.waitForSelector(selector);

  const base64 = await browser.screenshotElement(selector);
  const file = path.join(outDir, `${name}-section-${viewport}.png`);
  fs.writeFileSync(file, Buffer.from(base64, 'base64'));
  assertFile(file);

  return { viewport, file, selector, size: fs.statSync(file).size };
}

module.exports = {
  captureFullPage,
  captureSection,
  VIEWPORTS,
  DARK_MODE_MODES,
};
