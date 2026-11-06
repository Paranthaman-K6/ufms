#!/usr/bin/env python3
"""
detect-slop.py — deterministic design linter over a source directory.

Flags recurring "AI slop" design tells in HTML/CSS and component files
(.jsx/.tsx/.vue/.svelte, so React/Vue/Svelte + Tailwind projects are scanned):

  - href="#" placeholder links (not intentionally marked TODO)
  - font-family stacks using ONLY default typefaces (Inter, Arial, system-ui,
    Roboto, Helvetica, …) and no distinct typeface
  - purple→pink / violet→pink gradients, including Tailwind `from-violet-* to-pink-*`
  - the same entrance motion variant reused on 4+ components (uniform per-section reveal)
  - nested card patterns (class 'card' inside an element with class 'card')
  - CSS with no :focus-visible rules at all
  - CSS with no prefers-reduced-motion media query
  - <img> tags missing both width and height, or missing alt
  - an empty or template-only .ufme/DESIGN_SYSTEM.md (no design direction decided);
    pass --design FILE to check another path, --no-design to skip

Prints each finding as `file:line: rule-id: detail`. With --json FILE the
findings are also written as JSON.

Usage: python3 detect-slop.py [--path DIR] [--json FILE] [--design FILE|--no-design]
Exit codes: 0 = clean, 2 = findings, 1 = usage/IO error.

Pure python3, no dependencies.
"""

import argparse
import json
import re
import sys
from pathlib import Path

HTML_EXTS = {".html", ".htm", ".xhtml"}
CSS_EXTS = {".css", ".scss", ".sass", ".less"}
# shortcut: plain .js/.ts with JSX is not scanned; add when a project needs it
COMPONENT_EXTS = {".jsx", ".tsx", ".vue", ".svelte"}
SKIP_DIRS = {
    "node_modules", ".git", ".ufme", "dist", "build", "out", "coverage",
    ".venv", "venv", "__pycache__", ".next", ".nuxt", "vendor", ".svelte-kit",
}

RULE_HREF = "href-placeholder-hash"
RULE_FONT = "font-stack-inter-or-arial-only"
RULE_GRADIENT = "gradient-purple-to-pink"
RULE_NESTED_CARD = "nested-card"
RULE_FOCUS = "css-missing-focus-visible"
RULE_REDUCED = "css-missing-prefers-reduced-motion"
RULE_IMG_DIMS = "img-missing-width-and-height"
RULE_IMG_ALT = "img-missing-alt"
RULE_UNIFORM_MOTION = "uniform-entrance-motion"
RULE_DESIGN = "design-system-incomplete"

FONT_FILE_RE = re.compile(r"\.(?:woff2?|ttf|otf|eot)\b", re.IGNORECASE)
FONT_FAMILY_RE = re.compile(
    r"font-family\s*:\s*([^;{}]+?)(?:\s*!important)?(?=\s*[;{}])", re.IGNORECASE
)
GENERIC_FAMILIES = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui",
    "ui-serif", "ui-sans-serif", "ui-monospace", "ui-rounded",
    "initial", "inherit", "unset",
}
# Default-OS typefaces: a stack made only of these has no type identity.
FONT_SLOP_ONLY = {
    "inter", "arial", "helvetica", "helvetica neue", "-apple-system",
    "blinkmacsystemfont", "segoe ui", "roboto", "sf pro", "sf pro text",
    "sf pro display", "noto sans", "open sans", "lato",
}

GRADIENT_RE = re.compile(
    r"linear-gradient\s*\(|bg-gradient-to-[a-z]+"
    r"|\bfrom-(?:violet|purple|fuchsia|indigo|pink|rose)-\d{2,3}\b",
    re.IGNORECASE,
)
PURPLE_RE = re.compile(
    r"#8b5cf6|#a855f7|#7c3aed|#6d28d9|#9333ea"
    r"|\b(?:violet|purple|fuchsia|indigo)-\d{2,3}\b"
    r"|(?<![a-z])(?:violet|purple)s?(?![a-z])",
    re.IGNORECASE,
)
PINK_RE = re.compile(
    r"#ec4899|#f472b6|#db2777|#f9a8d4"
    r"|\b(?:pink|rose)-\d{2,3}\b"
    r"|(?<![a-z])pinks?(?![a-z])",
    re.IGNORECASE,
)
VARIANT_USE_RE = re.compile(r"variants=\{([A-Za-z_$][\w$]*)\}")

# Heading keyword -> what a filled design system must answer under it.
DESIGN_SECTIONS = [
    ("design direction", "tone, type pairing, palette rationale, layout concept"),
    ("typography", "type roles and the actual typeface(s)"),
    ("color", "palette tokens and why they fit this content"),
    ("component", "component inventory and states"),
    ("animation", "motion hierarchy (which element moves, and why)"),
]
DESIGN_ALTERNATE_HEADINGS = {"animation": "motion"}

HREF_HASH_RE = re.compile(r"""href\s*=\s*(?:"#"|'#')""", re.IGNORECASE)
TODO_RE = re.compile(r"\bTODO\b", re.IGNORECASE)

IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
ATTR_RE = re.compile(r"""([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|\{([^}]*)\})""")
CLASS_ATTR_RE = re.compile(r"""class\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.IGNORECASE)
TAG_RE = re.compile(r"<(/?)\s*([A-Za-z][\w:-]*)([^>]*?)(/?)>")
SELF_CLOSING_SLASH_RE = re.compile(r"/\s*$")
CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>(.*?)</style\s*>", re.IGNORECASE | re.DOTALL)

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


def decode_attr(raw):
    return raw.replace("&quot;", '"').replace("&#39;", "'").replace("&amp;", "&")


def class_tokens(tag):
    match = CLASS_ATTR_RE.search(tag)
    if not match:
        return []
    raw = match.group(1) if match.group(1) is not None else match.group(2)
    return decode_attr(raw or "").split()


def parse_attrs(tag):
    attrs = {}
    for match in ATTR_RE.finditer(tag):
        key = match.group(1).lower()
        quoted = match.group(2) if match.group(2) is not None else match.group(3)
        value = quoted if quoted is not None else match.group(4)
        if key not in attrs:
            attrs[key] = decode_attr((value or "").strip())
    return attrs


class Findings:
    """Collects (line, rule, detail), deduped per line."""

    def __init__(self, path):
        self.path = path
        self.items = []      # list of (line, rule, detail)
        self._seen = set()

    def add(self, line_no, rule, detail):
        key = (line_no, rule)
        if key in self._seen:
            return
        self._seen.add(key)
        self.items.append((line_no, rule, detail))


def check_font_family(line, findings, line_no):
    match = FONT_FAMILY_RE.search(line)
    if not match:
        return
    stack = match.group(1)
    # src-like content means this is an @font-face block, not a design stack.
    if FONT_FILE_RE.search(stack):
        return
    tokens = [tok.strip().strip("'\"").lower() for tok in stack.split(",")]
    tokens = [tok for tok in tokens if tok]
    distinct = [tok for tok in tokens if tok not in GENERIC_FAMILIES]
    if distinct and all(tok in FONT_SLOP_ONLY for tok in distinct):
        names = " / ".join(sorted(set(distinct)))
        findings.add(
            line_no, RULE_FONT,
            f"font stack uses only {names} — no distinct typefaces",
        )


def check_gradient(line, findings, line_no):
    if not GRADIENT_RE.search(line):
        return
    if PURPLE_RE.search(line) and PINK_RE.search(line):
        findings.add(
            line_no, RULE_GRADIENT,
            "purple/violet → pink linear-gradient (generic AI palette)",
        )


def check_href(line, findings, line_no):
    if HREF_HASH_RE.search(line) and not TODO_RE.search(line):
        findings.add(
            line_no, RULE_HREF,
            'placeholder link href="#" (mark the line TODO if intentional)',
        )


def check_img(tag_text, findings, line_no):
    attrs = parse_attrs(tag_text)
    has_width = bool(attrs.get("width", "").strip())
    has_height = bool(attrs.get("height", "").strip())
    if not has_width and not has_height:
        findings.add(line_no, RULE_IMG_DIMS, "<img> missing both width and height")
    if "alt" not in attrs:
        findings.add(line_no, RULE_IMG_ALT, "<img> missing alt attribute")


def check_nested_cards(text, findings, line_of):
    """Stack-based: an element whose class list contains 'card' inside
    another element whose class list contains 'card'."""
    open_stack = []   # (tag_name, has_card)
    card_depth = 0
    for match in TAG_RE.finditer(text):
        closing, name, rest, self_close = match.groups()
        name = name.lower()
        if closing:
            # Pop up to the matching open tag (HTML is not XML-strict; be
            # tolerant of mismatched tags but keep the stack sane).
            while open_stack:
                open_name, open_has_card = open_stack.pop()
                if open_has_card and card_depth > 0:
                    card_depth -= 1
                if open_name == name:
                    break
            continue
        toks = [tok.lower() for tok in class_tokens(rest)]
        has_card = "card" in toks
        if has_card and card_depth > 0:
            findings.add(line_of(match.start()), RULE_NESTED_CARD,
                         "element with class 'card' nested inside another 'card'")
        if name in VOID_TAGS or self_close or SELF_CLOSING_SLASH_RE.search(rest):
            continue
        open_stack.append((name, has_card))
        if has_card:
            card_depth += 1


def iter_source_files(root):
    if root.is_file():
        yield root
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in (HTML_EXTS | CSS_EXTS | COMPONENT_EXTS):
            continue
        parents = path.relative_to(root).parts[:-1]
        if any(part in SKIP_DIRS or part.startswith(".") for part in parents):
            continue
        yield path


def strip_comments(text, path):
    if path.suffix.lower() in CSS_EXTS:
        return CSS_COMMENT_RE.sub("", text)
    if path.suffix.lower() in COMPONENT_EXTS:
        return CSS_COMMENT_RE.sub("", text)
    return HTML_COMMENT_RE.sub("", text)


def scan(path, findings, motion_uses=None):
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as err:
        print(f"detect-slop: cannot read {path}: {err}", file=sys.stderr)
        return
    text = strip_comments(raw, path)

    def line_of(index):
        return text.count("\n", 0, index) + 1

    suffix = path.suffix.lower()
    is_css = suffix in CSS_EXTS
    is_html = suffix in HTML_EXTS
    is_component = suffix in COMPONENT_EXTS

    # Per-line rules work in CSS, HTML (inline <style> included) and components.
    for match in re.finditer(r"[^\n]*", text):
        line_no = line_of(match.start())
        check_font_family(match.group(0), findings, line_no)
        check_gradient(match.group(0), findings, line_no)
        if is_html or is_component:
            check_href(match.group(0), findings, line_no)

    if is_html:
        for match in IMG_TAG_RE.finditer(text):
            check_img(match.group(0), findings, line_of(match.start()))
        check_nested_cards(text, findings, line_of)

    if is_component:
        for match in IMG_TAG_RE.finditer(text):
            check_img(match.group(0), findings, line_of(match.start()))
        if motion_uses is not None:
            for match in VARIANT_USE_RE.finditer(text):
                motion_uses.append((path, line_of(match.start()), match.group(1)))

    if is_css:
        # Whole-file coverage checks reported once, at the first line.
        if ":focus-visible" not in text.lower():
            findings.add(1, RULE_FOCUS, "stylesheet contains no :focus-visible")
        if "prefers-reduced-motion" not in text.lower():
            findings.add(1, RULE_REDUCED,
                         "stylesheet contains no prefers-reduced-motion media query")
    elif is_html and STYLE_BLOCK_RE.search(text):
        # Only complain about inline <style> when styles actually exist there;
        # otherwise a CSS-free HTML file is not a slop finding.
        style_text = "".join(m.group(1) for m in STYLE_BLOCK_RE.finditer(text))
        if ":focus-visible" not in style_text.lower():
            first = line_of(STYLE_BLOCK_RE.search(text).start())
            findings.add(first, RULE_FOCUS, "<style> block contains no :focus-visible")
        if "prefers-reduced-motion" not in style_text.lower():
            first = line_of(STYLE_BLOCK_RE.search(text).start())
            findings.add(first, RULE_REDUCED, "<style> block contains no prefers-reduced-motion media query")


def check_design_system(path, findings):
    """A seeded-but-unfilled DESIGN_SYSTEM.md means no design direction was decided."""
    def report(line_no, detail):
        # Design sections share one rule id, so do not dedupe by line.
        findings.items.append((line_no, RULE_DESIGN, detail))

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        report(1, f"cannot read design system: {path}")
        return
    lines = text.splitlines()

    def heading(line):
        match = re.match(r"^(#{1,6})\s+(.*\S)\s*$", line)
        return (len(match.group(1)), match.group(2).strip().lower()) if match else None

    heads = [(i, *heading(line)) for i, line in enumerate(lines) if heading(line)]
    for keyword, expected in DESIGN_SECTIONS:
        found = None
        for pos, (index, level, title) in enumerate(heads):
            alternate = DESIGN_ALTERNATE_HEADINGS.get(keyword, "")
            if keyword in title or (alternate and alternate in title):
                found = (pos, index, level)
                break
        if not found:
            report(1, f"missing '{keyword}' section — state {expected}")
            continue
        pos, index, level = found
        end = len(lines)
        for next_index, next_level, _ in heads[pos + 1:]:
            if next_level <= level:
                end = next_index
                break
        body = []
        for line in lines[index + 1:end]:
            stripped = line.strip()
            if not stripped or heading(line):
                continue
            if re.fullmatch(r"\|[\s:|-]+\|", stripped):
                continue
            body.append(stripped)
        # A lone table header row or a labelled bullet with no value is still
        # the template, not a decision.
        body = [line for line in body
                if not re.fullmatch(r"\|(\s*[A-Za-z /]+\s*\|)+", line)
                and not re.fullmatch(r"[-*]\s*[^:]+:\s*", line)]
        if not body:
            report(index + 1, f"'{keyword}' section is empty — state {expected}")


def main():
    parser = argparse.ArgumentParser(description="deterministic design slop linter")
    parser.add_argument("--path", default=".", help="source directory to scan (default: cwd)")
    parser.add_argument("--json", metavar="FILE", help="also write findings to FILE as JSON")
    parser.add_argument("--design", metavar="FILE",
                        help="design system file to validate (default: <path>/.ufme/DESIGN_SYSTEM.md)")
    parser.add_argument("--no-design", action="store_true",
                        help="skip the design-system completeness check")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"detect-slop: path does not exist: {root}", file=sys.stderr)
        return 1

    results = []
    by_path = {}
    motion_uses = []
    for path in iter_source_files(root):
        per_file = Findings(path)
        scan(path, per_file, motion_uses)
        by_path[path] = per_file
        results.append((path, per_file.items))

    # Uniform per-section entrance motion: the same variant on 4+ components.
    variant_counts = {}
    for path, line_no, name in motion_uses:
        variant_counts.setdefault(name, []).append((path, line_no))
    for name, uses in variant_counts.items():
        if len(uses) >= 4:
            path, line_no = uses[0]
            by_path[path].add(
                line_no, RULE_UNIFORM_MOTION,
                f"variant '{name}' reused on {len(uses)} components — "
                "vary motion by hierarchy (hero, section, list, supporting)",
            )

    design = None
    if not args.no_design:
        design = Path(args.design).resolve() if args.design else root / ".ufme" / "DESIGN_SYSTEM.md"
        if args.design or design.is_file():
            design_findings = Findings(design)
            check_design_system(design, design_findings)
            results.append((design, design_findings.items))

    findings = []
    for path, items in results:
        rel = str(path)
        for line_no, rule, detail in sorted(items):
            findings.append(f"{rel}:{line_no}: {rule}: {detail}")

    for finding in findings:
        print(finding)

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps({"count": len(findings), "findings": findings}, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"— {len(findings)} design finding(s)")
    return 2 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
