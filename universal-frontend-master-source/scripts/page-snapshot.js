// universal-frontend-master-source/scripts/page-snapshot.js
// Text-first page outline via Selenium WebDriver (todo 4.1).
//
// Headless chromium-preferred-then-firefox (same approach as
// universal-frontend-master-source/browser/engines/). No Playwright. The
// Chromium sandbox is preserved: --no-sandbox is never added.
//
// Captures (text only, no visual rendering):
//   - page title
//   - heading hierarchy h1-h3
//   - link texts + hrefs (deduplicated, first 50)
//   - interactive elements with accessible names (buttons via text /
//     aria-label, form labels + input names)
//   - image alt texts (first 30)
//   - landmark roles (main, nav, header, footer, aside)
//
// Usage:
//   node page-snapshot.js <url> [--out <path>] [--json]
//
// Default output: .ufme/evidence/page-snapshot-<slug>.md (or .json with --json).
'use strict';

const fs = require('fs');
const path = require('path');

const { Builder } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const firefox = require('selenium-webdriver/firefox');

const ROOT_DIR = path.resolve(__dirname, '..', '..');
const EVIDENCE_DIR = path.join(ROOT_DIR, '.ufme', 'evidence');

// Snapshot script definitions (W3C execute-script body semantics: statements
// run in a function body with `arguments` bound; returned Promise awaited /
// completion value used).
const SNAPSHOT_SCRIPT = `
return (function () {
  function clean(t) { return (t || '').replace(/\\s+/g, ' ').trim(); }

  // --- page title ---
  var title = document.title || '';

  // --- heading hierarchy h1-h3 ---
  var headings = [];
  var headingEls = document.querySelectorAll('h1, h2, h3');
  var headingLimit = 200;
  for (var h = 0; h < headingEls.length && headings.length < headingLimit; h++) {
    var el0 = headingEls[h];
    var text0 = clean(el0.textContent);
    if (!text0) {
      text0 = clean(el0.getAttribute('aria-label'));
    }
    headings.push({ level: el0.tagName.toLowerCase(), text: text0 });
  }

  // --- links: text + href, dedup on text+href, first 50 ---
  var links = [];
  var seenLinks = {};
  var linkEls = document.querySelectorAll('a[href]');
  for (var a = 0; a < linkEls.length && links.length < 50; a++) {
    var el1 = linkEls[a];
    var text1 = clean(el1.textContent) || clean(el1.getAttribute('aria-label')) ||
      clean(el1.querySelector('img') && el1.querySelector('img').alt) || '(no text)';
    var href1 = el1.getAttribute('href') || '';
    var key1 = text1 + '\\u0000' + href1;
    if (seenLinks[key1]) continue;
    seenLinks[key1] = true;
    links.push({ text: text1, href: href1 });
  }

  // --- interactive elements with accessible names ---
  function accessibleName(el) {
    var label = clean(el.getAttribute('aria-label'));
    if (label) return label;
    var labelledBy = clean(el.getAttribute('aria-labelledby'));
    if (labelledBy) {
      var t = document.getElementById(labelledBy);
      if (t) label = clean(t.textContent);
      if (label) return label;
    }
    var innerText = clean(el.textContent);
    if (innerText) return innerText;
    label = clean(el.getAttribute('title')) || clean(el.value);
    return label || '';
  }

  var buttons = [];
  var buttonEls = document.querySelectorAll(
    'button, [role="button"], input[type="button"], input[type="submit"], input[type="reset"], summary');
  var buttonLimit = 50;
  for (var b = 0; b < buttonEls.length && buttons.length < buttonLimit; b++) {
    var el2 = buttonEls[b];
    var name2 = accessibleName(el2) || clean(el2.getAttribute('value'));
    buttons.push({
      name: name2,
      type: el2.getAttribute('type') || el2.tagName.toLowerCase(),
    });
  }

  var labelsByFor = {};
  var labelEls = document.querySelectorAll('label');
  for (var l = 0; l < labelEls.length; l++) {
    var el3 = labelEls[l];
    var forId = el3.getAttribute('for');
    if (forId) labelsByFor[forId] = clean(el3.textContent);
  }

  var inputs = [];
  var inputEls = document.querySelectorAll(
    'input:not([type="hidden"]):not([type="button"]):not([type="submit"]):not([type="reset"])' +
    ', select, textarea');
  var inputLimit = 80;
  for (var i = 0; i < inputEls.length && inputs.length < inputLimit; i++) {
    var el4 = inputEls[i];
    var id4 = el4.getAttribute('id') || '';
    var label4 = labelsByFor[id4] ||
      (el4.closest('label') ? clean(el4.closest('label').textContent) : '') ||
      clean(el4.getAttribute('aria-label')) ||
      clean(el4.getAttribute('placeholder')) || '';
    inputs.push({
      name: el4.getAttribute('name') || '',
      type: el4.tagName.toLowerCase() === 'input' ? (el4.getAttribute('type') || 'text') : el4.tagName.toLowerCase(),
      label: label4,
    });
  }

  // --- image alts (first 30) ---
  var images = [];
  var imgEls = document.querySelectorAll('img');
  for (var m = 0; m < imgEls.length && images.length < 30; m++) {
    var alt4 = imgEls[m].getAttribute('alt');
    images.push({
      alt: alt4 === null ? '(alt attribute missing)' : (clean(alt4) === '' ? '(empty alt)' : clean(alt4)),
      src: clean(imgEls[m].getAttribute('src')).slice(0, 120),
    });
  }

  // --- landmark roles ---
  var landmarks = [];
  var landmarkSelectors = [
    { tag: 'main', role: 'main' },
    { tag: 'nav', role: 'nav' },
    { tag: 'header', role: 'header' },
    { tag: 'footer', role: 'footer' },
    { tag: 'aside', role: 'aside' },
    { tag: '[role="main"]', role: 'main' },
    { tag: '[role="navigation"]', role: 'nav' },
    { tag: '[role="banner"]', role: 'header' },
    { tag: '[role="contentinfo"]', role: 'footer' },
    { tag: '[role="complementary"]', role: 'aside' },
  ];
  var seenLandmarks = {};
  for (var w = 0; w < landmarkSelectors.length; w++) {
    var sel = landmarkSelectors[w];
    var els = document.querySelectorAll(sel.tag);
    for (var z = 0; z < els.length; z++) {
      var label5 = clean(els[z].getAttribute('aria-label'));
      var key5 = sel.role + '|' + label5;
      if (seenLandmarks[key5]) continue;
      seenLandmarks[key5] = true;
      landmarks.push({ role: sel.role, label: label5 });
    }
  }

  return {
    title: title,
    headings: headings,
    links: links,
    buttons: buttons,
    inputs: inputs,
    images: images,
    landmarks: landmarks,
  };
})()`;

function slugify(url) {
  let slug = '';
  try {
    const parsed = new URL(url);
    slug = `${parsed.hostname}${parsed.pathname}`;
  } catch (e) {
    slug = String(url);
  }
  return slug.toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80) || 'page';
}

function parseArgs(argv) {
  const rest = [];
  let out = null;
  let json = false;
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '--json') {
      json = true;
    } else if (a === '--out') {
      out = argv[i + 1];
      i += 1;
    } else if (a.startsWith('--out=')) {
      out = a.slice('--out='.length);
    } else if (!a.startsWith('--')) {
      rest.push(a);
    }
  }
  return { url: rest[0], out, json };
}

function toMarkdown(data, url, engine) {
  const lines = [];
  lines.push(`# Page snapshot: ${data.title || '(no title)'}`);
  lines.push('');
  lines.push(`- URL: ${url}`);
  lines.push(`- Captured: ${new Date().toISOString()}`);
  lines.push(`- Engine: ${engine}`);
  lines.push('');

  lines.push('## Title');
  lines.push(data.title || '(no title)');
  lines.push('');

  lines.push('## Headings (h1-h3)');
  if (data.headings.length === 0) lines.push('(none)');
  for (const h of data.headings) {
    lines.push(`- [${h.level}] ${h.text}`);
  }
  lines.push('');

  lines.push('## Links (deduplicated, first 50)');
  if (data.links.length === 0) lines.push('(none)');
  for (const l of data.links) {
    lines.push(`- [${l.text}](${l.href})`);
  }
  lines.push('');

  lines.push('## Interactive elements');
  lines.push('### Buttons');
  if (data.buttons.length === 0) lines.push('(none)');
  for (const b of data.buttons) {
    lines.push(`- button "${b.name || '(unnamed)'}" (${b.type})`);
  }
  lines.push('### Inputs');
  if (data.inputs.length === 0) lines.push('(none)');
  for (const f of data.inputs) {
    lines.push(`- ${f.type} name="${f.name || '(unnamed)'}"${f.label ? ` label="${f.label}"` : ''}`);
  }
  lines.push('');

  lines.push('## Images (alt text, first 30)');
  if (data.images.length === 0) lines.push('(none)');
  for (const img of data.images) {
    lines.push(`- alt: ${img.alt} (src: ${img.src || 'n/a'})`);
  }
  lines.push('');

  lines.push('## Landmarks');
  if (data.landmarks.length === 0) lines.push('(none)');
  for (const lm of data.landmarks) {
    lines.push(`- ${lm.role}${lm.label ? `: "${lm.label}"` : ''}`);
  }
  lines.push('');

  return lines.join('\n');
}

async function launchDriver(engine) {
  if (engine === 'firefox') {
    const o = new firefox.Options();
    if (process.env.FIREFOX_BIN) o.setBinary(process.env.FIREFOX_BIN);
    o.addArguments('-headless');
    return new Builder().forBrowser('firefox').setFirefoxOptions(o).build();
  }
  // Chromium: sandbox preserved (no --no-sandbox), same flags as the runtime engines.
  const o = new chrome.Options();
  o.addArguments('--headless=new', '--disable-dev-shm-usage', '--disable-gpu', '--window-size=1440,900');
  return new Builder().forBrowser('chrome').setChromeOptions(o).build();
}

async function main() {
  let args = parseArgs(process.argv.slice(2));
  let { url } = args;
  const { out, json } = args;
  args = null;

  if (!url) {
    process.stderr.write('Usage: node page-snapshot.js <url> [--out <path>] [--json]\n');
    process.exit(2);
  }

  let driver = null;
  let engine = 'chromium';
  try {
    try {
      driver = await launchDriver('chromium');
      engine = 'chromium';
    } catch (eChromium) {
      driver = await launchDriver('firefox');
      engine = 'firefox';
    }

    await driver.get(url);
    await new Promise((r) => setTimeout(r, 1000)); // settle render
    const data = await driver.executeScript(SNAPSHOT_SCRIPT);

    const slug = slugify(url);
    let outPath = out || path.join(EVIDENCE_DIR, `page-snapshot-${slug}.${json ? 'json' : 'md'}`);
    fs.mkdirSync(path.dirname(outPath), { recursive: true });

    const payload = {
      url,
      engine,
      capturedAt: new Date().toISOString(),
      title: data.title,
      headings: data.headings,
      links: data.links,
      buttons: data.buttons,
      inputs: data.inputs,
      images: data.images,
      landmarks: data.landmarks,
    };

    if (json) {
      fs.writeFileSync(outPath, JSON.stringify(payload, null, 2));
      process.stdout.write(JSON.stringify(payload, null, 2));
    } else {
      const md = toMarkdown(data, url, engine);
      fs.writeFileSync(outPath, md);
      process.stdout.write(`page-snapshot: ${outPath}\n`);
    }
    process.exit(0);
  } catch (err) {
    process.stderr.write(`page-snapshot failed: ${err.message}\n`);
    process.exit(1);
  } finally {
    if (driver) {
      try { await driver.quit(); } catch (e) { /* ignore */ }
    }
  }
}

main();
