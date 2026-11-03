#!/usr/bin/env python3
"""
detect-slop.py — deterministic design linter over a source directory.

Flags recurring "AI slop" design tells in HTML/CSS files:

  - href="#" placeholder links (not intentionally marked TODO)
  - font-family stacks using ONLY Inter/Arial and no other distinct typefaces
  - purple→pink / violet→pink gradients (#8B5CF6, #EC4899, #A855F7, violet,
    purple, pink combined with linear-gradient)
  - nested card patterns (class 'card' inside an element with class 'card')
  - CSS with no :focus-visible rules at all
  - CSS with no prefers-reduced-motion media query
  - <img> tags missing both width and height, or missing alt

Prints each finding as `file:line: rule-id: detail`. With --json FILE the
findings are also written as JSON.

Usage: python3 detect-slop.py [--path DIR] [--json FILE]
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

FONT_FILE_RE = re.compile(r"\.(?:woff2?|ttf|otf|eot)\b", re.IGNORECASE)
FONT_FAMILY_RE = re.compile(
    r"font-family\s*:\s*([^;{}]+?)(?:\s*!important)?(?=\s*[;{}])", re.IGNORECASE
)
GENERIC_FAMILIES = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui",
    "ui-serif", "ui-sans-serif", "ui-monospace", "ui-rounded",
    "initial", "inherit", "unset",
}
FONT_SLOP_ONLY = {"inter", "arial"}

GRADIENT_RE = re.compile(r"linear-gradient\s*\(", re.IGNORECASE)
PURPLE_RE = re.compile(
    r"#8b5cf6|#a855f7|#7c3aed|#6d28d9|#9333ea"
    r"|(?<![a-z])(?:violet|purple)s?(?![a-z])",
    re.IGNORECASE,
)
PINK_RE = re.compile(
    r"#ec4899|#f472b6|#db2777|#f9a8d4|(?<![a-z])pinks?(?![a-z])",
    re.IGNORECASE,
)

HREF_HASH_RE = re.compile(r"""href\s*=\s*(?:"#"|'#')""", re.IGNORECASE)
TODO_RE = re.compile(r"\bTODO\b", re.IGNORECASE)

IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
ATTR_RE = re.compile(r"""([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')""")
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
        value = match.group(2) if match.group(2) is not None else match.group(3)
        if key not in attrs:
            attrs[key] = decode_attr(value or "")
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
        if path.suffix.lower() not in (HTML_EXTS | CSS_EXTS):
            continue
        parents = path.relative_to(root).parts[:-1]
        if any(part in SKIP_DIRS or part.startswith(".") for part in parents):
            continue
        yield path


def strip_comments(text, path):
    if path.suffix.lower() in CSS_EXTS:
        return CSS_COMMENT_RE.sub("", text)
    return HTML_COMMENT_RE.sub("", text)


def scan(path, findings):
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as err:
        print(f"detect-slop: cannot read {path}: {err}", file=sys.stderr)
        return
    text = strip_comments(raw, path)

    def line_of(index):
        return text.count("\n", 0, index) + 1

    is_css = path.suffix.lower() in CSS_EXTS
    is_html = path.suffix.lower() in HTML_EXTS

    # Per-line rules work in both CSS files and HTML (inline <style> included).
    for match in re.finditer(r"[^\n]*", text):
        line_no = line_of(match.start())
        check_font_family(match.group(0), findings, line_no)
        check_gradient(match.group(0), findings, line_no)
        if is_html:
            check_href(match.group(0), findings, line_no)

    if is_html:
        for match in IMG_TAG_RE.finditer(text):
            check_img(match.group(0), findings, line_of(match.start()))
        check_nested_cards(text, findings, line_of)

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


def main():
    parser = argparse.ArgumentParser(description="deterministic design slop linter")
    parser.add_argument("--path", default=".", help="source directory to scan (default: cwd)")
    parser.add_argument("--json", metavar="FILE", help="also write findings to FILE as JSON")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"detect-slop: path does not exist: {root}", file=sys.stderr)
        return 1

    results = []
    for path in iter_source_files(root):
        per_file = Findings(path)
        scan(path, per_file)
        results.append((path, per_file.items))

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
