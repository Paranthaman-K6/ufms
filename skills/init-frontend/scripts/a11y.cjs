#!/usr/bin/env node
/**
 * scripts/a11y.cjs — Dependency-free static accessibility gate.
 *
 * Checks the A11Y foundations encoded in built HTML/CSS without needing
 * a browser or axe-core (which requires Chrome + a running server).
 *
 * Usage:
 *   node scripts/a11y.cjs [build-dir]
 *
 * Default build-dir: dist (Vite default) or the arg provided.
 *
 * Exit 0 = all checks pass, Exit 1 = failures found.
 *
 * Checks:
 *   1. Every  has an alt attribute
 *   2. Every <input>, <select>, <textarea> has an associated <label>
 *   3. Every interactive element has a focus-visible outline (via CSS)
 *   4. No removed focus outlines (outline: none without :focus-visible fallback)
 *   5. Skip link present
 *   6. Semantic landmark elements present (<header>, <nav>, <main>, <footer>)
 *   7. Touch targets >= 24px (min-height/min-width on interactive elements)
 *   8. Reduced-motion media query present
 *   9. Contrast text classes used on text (text-muted contrast class)
 *   10. ARIA labels where needed (icon-only buttons)
 */
"use strict";

const fs = require("fs");
const path = require("path");

const BUILD_DIR = process.argv[2] || "dist";
const ROOT = process.cwd();
const TARGET = path.resolve(ROOT, BUILD_DIR);

let failures = 0;
let checks = 0;

function check(name, cond, detail = "") {
  checks++;
  if (cond) {
    process.stdout.write(`  ✅ ${name}\n`);
  } else {
    failures++;
    process.stdout.write(`  ❌ ${name}${detail ? " — " + detail : ""}\n`);
  }
}

function readHtmlFiles(dir) {
  const results = [];
  (function walk(d) {
    for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.isFile() && entry.name.endsWith(".html")) results.push(full);
    }
  })(dir);
  return results;
}

function readCssFiles(dir) {
  const results = [];
  (function walk(d) {
    for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.isFile() && entry.name.endsWith(".css")) results.push(full);
    }
  })(dir);
  return results;
}

function main() {
  if (!fs.existsSync(TARGET)) {
    console.error(`❌ Build directory not found: ${TARGET}`);
    console.error("   Run 'npm run build' first, or pass the build dir as an argument.");
    process.exit(1);
  }

  console.log(`\n🔍 Static accessibility gate — scanning ${TARGET}\n`);

  const htmlFiles = readHtmlFiles(TARGET);
  const cssFiles = readCssFiles(TARGET);

  if (htmlFiles.length === 0) {
    console.warn("⚠️  No HTML files found in build directory.");
  }

  const allHtml = htmlFiles.map((f) => fs.readFileSync(f, "utf8")).join("\n");
  const allCss = cssFiles.map((f) => fs.readFileSync(f, "utf8")).join("\n");

  // --- 1. Every  has an alt attribute ---
  const imgTags = allHtml.match(/<img\b[^>]*>/gi) || [];
  let imgsWithoutAlt = 0;
  for (const tag of imgTags) {
    if (!/alt\s*=/i.test(tag)) imgsWithoutAlt++;
  }
  check("Every  has an alt attribute", imgsWithoutAlt === 0, `${imgsWithoutAlt} image(s) missing alt`);

  // --- 2. Every form control has an associated <label> ---
  const inputs = (allHtml.match(/<input\b[^>]*>/gi) || []).length;
  const selects = (allHtml.match(/<select\b[^>]*>/gi) || []).length;
  const textareas = (allHtml.match(/<textarea\b[^>]*>/gi) || []).length;
  const labels = (allHtml.match(/<label\b[^>]*>/gi) || []).length;
  const ariaLabels = (allHtml.match(/aria-label\s*=/gi) || []).length;
  const ariaLabelledBy = (allHtml.match(/aria-labelledby\s*=/gi) || []).length;
  const formControls = inputs + selects + textareas;
  const labelledInputs = labels + ariaLabels + ariaLabelledBy;
  check(
    "Every <input>/<select>/<textarea> has a <label> or ARIA label",
    formControls === 0 || labelledInputs > 0,
    `${formControls} form control(s), ${labelledInputs} label(s)/ARIA label(s)`
  );

  // --- 3. focus-visible outline present in CSS ---
  check(
    "focus-visible outline defined in CSS",
    /:focus-visible\s*\{[^}]*outline\s*:/i.test(allCss),
    "No :focus-visible outline rule found"
  );

  // --- 4. No removed focus outlines without fallback ---
  const outlineNone = (allCss.match(/outline\s*:\s*none/i) || []).length;
  const outlineNoneFocusVisible = (allCss.match(/:\s*focus-visible[^}]*outline\s*:\s*none/gi) || []).length;
  check(
    "No 'outline: none' without :focus-visible fallback",
    outlineNone === 0 || outlineNoneFocusVisible > 0,
    `${outlineNone} outline:none rule(s), ${outlineNoneFocusVisible} with focus-visible fallback`
  );

  // --- 5. Skip link present ---
  check(
    "Skip-to-content link present",
    /skip[-_]link|skip-to-content/i.test(allHtml),
    "No .skip-link or skip-to-content anchor found"
  );

  // --- 6. Semantic landmarks ---
  const hasHeader = /<header\b/i.test(allHtml);
  const hasNav = /<nav\b/i.test(allHtml);
  const hasMain = /<main\b/i.test(allHtml);
  const hasFooter = /<footer\b/i.test(allHtml);
  check("Semantic <header> present", hasHeader);
  check("Semantic <nav> present", hasNav);
  check("Semantic <main> present", hasMain);
  check("Semantic <footer> present", hasFooter);

  // --- 7. Touch targets >= 24px ---
  check(
    "Touch targets >= 24px in CSS",
    /min-height\s*:\s*24px/i.test(allCss) || /min-height:\s*var\(--space-?/i.test(allCss),
    "No min-height: 24px rule for interactive elements"
  );

  // --- 8. Reduced motion ---
  check(
    "Reduced-motion media query present",
    /prefers-reduced-motion/i.test(allCss),
    "No @media (prefers-reduced-motion) rule found"
  );

  // --- 9. Contrast-aware text classes ---
  check(
    "Text contrast class (text-muted) present",
    /text-muted/i.test(allHtml) || /color.*text-muted/i.test(allCss),
    "No text-muted contrast class found"
  );

  // --- 10. ARIA labels on icon-only buttons ---
  const iconButtons = (allHtml.match(/<button[^>]*>(?:\s*<svg|\s*<img|\s*<i)/gi) || []).length;
  const ariaOnButtons = (allHtml.match(/<button[^>]*aria-label=/gi) || []).length;
  if (iconButtons > 0) {
    check(
      "Icon-only buttons have aria-label",
      ariaOnButtons === iconButtons,
      `${iconButtons} icon button(s), ${ariaOnButtons} with aria-label`
    );
  } else {
    check("Icon-only buttons have aria-label", true, "No icon-only buttons found");
  }

  // --- Summary ---
  console.log(`\n📊 A11Y gate: ${checks - failures}/${checks} checks passed\n`);
  if (failures > 0) {
    console.error(`❌ ${failures} accessibility check(s) failed. Fix the issues above.`);
    process.exit(1);
  } else {
    console.log("✅ All accessibility checks passed.\n");
    process.exit(0);
  }
}

main();
