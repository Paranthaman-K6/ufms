#!/usr/bin/env python3
"""theme-showcase.py — generate a theme showcase PDF for a project.

One page per theme: palette swatches with hex values, the type pairing as a
specimen, and where the theme fits. The project's own choice (from
`.ufme/design-choices.json`) is marked and shown first.

Theme sources, in order:
  1. `.ufme/design-choices.json` — the project's current palette and font
  2. `data/palettes.csv` — the curated local catalog (default)
  3. the UFME MCP registry — entries with category "theme" and a `theme` object,
     used only when UFME_REGISTRY_URL + UFME_REGISTRY_KEY are set

Output: `<target>/.ufme/theme-showcase.pdf` (uncompressed, base-14 fonts).

Usage:
    theme-showcase.py [--target DIR] [--out FILE] [--only NAME] [--json] [--quiet]
    theme-showcase.py --no-registry

Exit: 0 ok, 2 bad data, 3 no themes matched.
"""

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
PALETTES = DATA_DIR / "palettes.csv"
REGISTRY_CLIENT = HERE / "registry-remote.py"

PAGE_W, PAGE_H = 612.0, 792.0
MARGIN = 54.0

COLOR_ROLES = [
    ("bg", "Background"),
    ("surface", "Surface"),
    ("text", "Text"),
    ("muted", "Muted"),
    ("accent", "Accent"),
    ("accent_alt", "Accent alt"),
]
THEME_KEYS = [k for k, _ in COLOR_ROLES]
REQUIRED_COLUMNS = THEME_KEYS + ["font_pairing", "name"]

# Base-14 fonts only: a PDF writer with no dependency and no font files to ship.
FONTS = {
    "F1": "Helvetica",
    "F2": "Helvetica-Bold",
    "F3": "Times-Roman",
    "F4": "Times-Bold",
    "F5": "Courier",
}

SERIF_HINTS = (
    "serif", "playfair", "fraunces", "cormorant", "merriweather", "baskerville",
    "garamond", "georgia", "lora", "dm serif", "source serif", "noto serif",
)
MONO_HINTS = ("mono", "code", "jetbrains", "fira", "courier", "plex mono")

# Average glyph width per em; good enough for wrapping and centring labels.
WIDTH_RATIO = {"F1": 0.52, "F2": 0.55, "F3": 0.46, "F4": 0.50, "F5": 0.60}


# --------------------------------------------------------------------------
# colour helpers
# --------------------------------------------------------------------------

def hex_to_rgb(value):
    value = str(value).strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        raise ValueError(f"bad hex colour: {value!r}")
    return tuple(int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def luminance(rgb):
    def channel(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ink_for(rgb):
    """Black or white, whichever reads on this fill."""
    return (0.06, 0.06, 0.06) if luminance(rgb) > 0.45 else (0.97, 0.97, 0.97)


# --------------------------------------------------------------------------
# themes
# --------------------------------------------------------------------------

def split_pairing(pairing):
    """(display, body, mono) from "Display + Body (+ Mono)"."""
    parts = [p.strip() for p in str(pairing).split("+") if p.strip()]
    if not parts:
        return "Helvetica", "Helvetica", ""
    mono = next((p for p in parts if any(h in p.lower() for h in MONO_HINTS)), "")
    body = next((p for p in parts[1:] if p != mono), parts[0])
    return parts[0], body, mono


def load_local_themes(path=PALETTES):
    if not path.is_file():
        raise SystemExit(f"theme-showcase: missing {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(
                f"theme-showcase: {path.name} is missing columns: {', '.join(missing)}"
            )
        themes = []
        for row in reader:
            display, body, mono = split_pairing(row["font_pairing"])
            theme = {key: row[key].strip() for key in THEME_KEYS}
            theme.update(
                name=row["name"].strip(),
                description=row.get("description", "").strip(),
                best_for=row.get("usage_or_notes", "").strip(),
                display=display,
                body=body,
                mono=mono,
                source="local catalog",
            )
            themes.append(theme)
    return themes


def registry_client():
    if not (os.environ.get("UFME_REGISTRY_URL") and os.environ.get("UFME_REGISTRY_KEY")):
        return None
    return str(REGISTRY_CLIENT) if REGISTRY_CLIENT.is_file() else None


def load_registry_themes(client=None):
    """Curated themes from the MCP registry; any failure means no extras."""
    client = client if client is not None else registry_client()
    if not client:
        return []
    try:
        proc = subprocess.run(
            [sys.executable, client, "--list", "--category", "theme", "--json"],
            capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        return []
    try:
        entries = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    themes = []
    for entry in entries if isinstance(entries, list) else []:
        payload = entry.get("theme") if isinstance(entry, dict) else None
        if not isinstance(payload, dict):
            continue
        if any(not str(payload.get(k, "")).strip() for k in THEME_KEYS):
            continue
        theme = {key: str(payload[key]).strip() for key in THEME_KEYS}
        theme.update(
            name=str(entry.get("name") or payload.get("name") or "").strip(),
            description=str(payload.get("description", entry.get("reason", ""))).strip(),
            best_for=str(payload.get("best_for", "")).strip(),
            display=str(payload.get("display", "Helvetica")).strip(),
            body=str(payload.get("body", "Helvetica")).strip(),
            mono=str(payload.get("mono", "")).strip(),
            source="registry",
        )
        if theme["name"]:
            themes.append(theme)
    return themes


def project_choice(target):
    path = Path(target) / ".ufme" / "design-choices.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def apply_project_theme(themes, choice):
    """Mark the project's palette, and use its font pairing when it has one."""
    palette = str(choice.get("palette", "")).strip().lower()
    if not palette:
        return themes
    fonts = split_pairing(choice.get("font", "")) if choice.get("font") else (None, None, None)
    marked = []
    for theme in themes:
        if theme["name"].lower() == palette:
            theme = dict(theme, project=True)
            if fonts[0]:
                theme["display"], theme["body"], theme["mono"] = fonts
            marked.insert(0, theme)
        else:
            marked.append(theme)
    return marked


def collect_themes(target, use_registry=True, client=None):
    themes = load_local_themes()
    if use_registry:
        seen = {t["name"].lower() for t in themes}
        themes += [t for t in load_registry_themes(client) if t["name"].lower() not in seen]
    return apply_project_theme(themes, project_choice(target))


# --------------------------------------------------------------------------
# PDF writer (no dependencies)
# --------------------------------------------------------------------------

def ascii_text(value):
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"', "\u00b7": "-", "\u00a0": " ",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    return value.encode("ascii", "replace").decode("ascii")


def pdf_string(value):
    return ascii_text(value).replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def font_key(name, bold=False):
    lowered = str(name).lower()
    if any(hint in lowered for hint in MONO_HINTS):
        return "F5"
    if any(hint in lowered for hint in SERIF_HINTS):
        return "F4" if bold else "F3"
    return "F2" if bold else "F1"


def text_width(value, size, key):
    return len(ascii_text(value)) * WIDTH_RATIO[key] * size


def wrap(value, size, key, width):
    words = ascii_text(value).split()
    lines, line = [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if text_width(trial, size, key) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


class Canvas:
    def __init__(self):
        self.ops = []

    def rect(self, x, y, w, h, rgb, stroke=None, line_width=0.5):
        self.ops.append(f"{rgb[0]:.4f} {rgb[1]:.4f} {rgb[2]:.4f} rg")
        if stroke:
            self.ops.append(f"{line_width:.3f} w {stroke[0]:.4f} {stroke[1]:.4f} {stroke[2]:.4f} RG")
            self.ops.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re B")
        else:
            self.ops.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re f")

    def text(self, x, y, value, key, size, rgb, spacing=0.0):
        if not value:
            return
        self.ops.append(f"{rgb[0]:.4f} {rgb[1]:.4f} {rgb[2]:.4f} rg")
        self.ops.append(f"BT /{key} {size:.2f} Tf {spacing:.2f} Tc 1 0 0 1 {x:.2f} {y:.2f} Tm ({pdf_string(value)}) Tj ET")


def build_pdf(contents, producer="theme-showcase.py"):
    objects = []
    offsets = []

    def reserve():
        objects.append(None)
        return len(objects)

    def put(index, body):
        objects[index - 1] = body

    def add(body):
        index = reserve()
        put(index, body)
        return index

    catalog = reserve()
    pages_ref = reserve()
    font_refs = {key: add(f"<< /Type /Font /Subtype /Type1 /BaseFont /{base} /Encoding /WinAnsiEncoding >>")
                 for key, base in FONTS.items()}
    info = add(f"<< /Producer ({pdf_string(producer)}) /Creator ({pdf_string(producer)}) >>")

    kids = []
    for content in contents:
        stream = content.encode("latin-1", "replace")
        content_ref = add(f"<< /Length {len(stream)} >>\nstream\n{content}\nendstream")
        resources = " ".join(f"/{key} {ref} 0 R" for key, ref in font_refs.items())
        kids.append(add(
            f"<< /Type /Page /Parent {pages_ref} 0 R /MediaBox [0 0 {PAGE_W:.0f} {PAGE_H:.0f}] "
            f"/Resources << /Font << {resources} >> >> /Contents {content_ref} 0 R >>"
        ))

    put(catalog, f"<< /Type /Catalog /Pages {pages_ref} 0 R >>")
    put(pages_ref, f"<< /Type /Pages /Count {len(kids)} /Kids [{' '.join(f'{k} 0 R' for k in kids)}] >>")

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    for index, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{index} 0 obj\n{body}\nendobj\n".encode("latin-1")
    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("latin-1")
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("latin-1")
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog} 0 R /Info {info} 0 R >>\n"
        f"startxref\n{xref_at}\n%%EOF\n"
    ).encode("latin-1")
    return bytes(out)


# --------------------------------------------------------------------------
# page layout
# --------------------------------------------------------------------------

def render_page(theme, index, total):
    c = Canvas()
    bg = hex_to_rgb(theme["bg"])
    surface = hex_to_rgb(theme["surface"])
    ink = hex_to_rgb(theme["text"])
    muted = hex_to_rgb(theme["muted"])
    accent = hex_to_rgb(theme["accent"])
    accent_alt = hex_to_rgb(theme["accent_alt"])

    display_key = font_key(theme["display"], bold=True)
    body_key = font_key(theme["body"])
    text_key = font_key(theme["body"])
    content_w = PAGE_W - 2 * MARGIN

    c.rect(0, 0, PAGE_W, PAGE_H, bg)

    # header
    top = PAGE_H - MARGIN
    c.text(MARGIN, top, "UFME  /  THEME SHOWCASE", "F1", 8, muted, spacing=1.6)
    counter = f"{index:02d} / {total:02d}"
    c.text(PAGE_W - MARGIN - text_width(counter, 8, "F1"), top, counter, "F1", 8, muted)

    if theme.get("project"):
        label = "YOUR PROJECT"
        badge_w = text_width(label, 7, "F2") + 16
        c.rect(MARGIN, top - 26, badge_w, 16, accent)
        c.text(MARGIN + 8, top - 21.5, label, "F2", 7, ink_for(accent), spacing=1.2)

    # title
    y = top - 78
    size = 40 if text_width(theme["name"], 40, display_key) <= content_w else 30
    c.text(MARGIN, y, theme["name"], display_key, size, ink)
    y -= 34

    # description
    if theme["description"]:
        for line in wrap(theme["description"], 11.5, text_key, content_w)[:3]:
            c.text(MARGIN, y, line, text_key, 11.5, ink)
            y -= 17
    if theme["best_for"]:
        y -= 4
        for line in wrap(theme["best_for"], 9.5, "F3", content_w)[:3]:
            c.text(MARGIN, y, line, "F3", 9.5, muted)
            y -= 14

    # palette
    y -= 26
    c.text(MARGIN, y, "PALETTE", "F1", 8, muted, spacing=1.8)
    y -= 14
    gap = 10.0
    swatch_w = (content_w - gap * (len(COLOR_ROLES) - 1)) / len(COLOR_ROLES)
    swatch_h = 58.0
    for position, (key, role) in enumerate(COLOR_ROLES):
        rgb = hex_to_rgb(theme[key])
        x = MARGIN + position * (swatch_w + gap)
        border = ink if key in ("bg", "surface") else None
        c.rect(x, y - swatch_h, swatch_w, swatch_h, rgb, stroke=border, line_width=0.4)
        c.text(x, y - swatch_h - 12, role, "F1", 7, muted)
        c.text(x, y - swatch_h - 23, theme[key].upper(), "F5", 7.5, ink)

    # type specimen
    y -= swatch_h + 58
    c.text(MARGIN, y, "TYPE", "F1", 8, muted, spacing=1.8)
    y -= 16
    c.text(MARGIN, y, f"Display - {theme['display']}", "F1", 7.5, muted)
    y -= 34
    sample = "Aa Bb Cc 0123"
    size = 34 if text_width(sample, 34, display_key) <= content_w else 26
    c.text(MARGIN, y, sample, display_key, size, ink)
    y -= 30
    c.text(MARGIN, y, f"Body - {theme['body']}", "F1", 7.5, muted)
    y -= 18
    body_sample = (
        "The quick brown fox jumps over the lazy dog. "
        "Sphinx of black quartz, judge my vow."
    )
    for line in wrap(body_sample, 10.5, body_key, content_w)[:2]:
        c.text(MARGIN, y, line, body_key, 10.5, ink)
        y -= 15
    if theme.get("mono"):
        y -= 4
        c.text(MARGIN, y, f"Mono - {theme['mono']}", "F1", 7.5, muted)
        y -= 16
        c.text(MARGIN, y, "const ship = (theme) => render(theme);", "F5", 9.5, ink)

    # applied specimen: the theme doing its job
    band_bottom = 88.0
    band_h = 150.0
    band_top = band_bottom + band_h
    c.rect(MARGIN, band_bottom, content_w, band_h, surface, stroke=muted, line_width=0.5)
    c.text(MARGIN + 22, band_top - 26, "APPLIED", "F1", 8, muted, spacing=1.8)
    c.text(MARGIN + 22, band_top - 58, "Ship the thing", display_key, 22, ink)
    line_y = band_top - 78
    for line in wrap("One clear sentence of body copy, set in the body face at a readable measure.",
                     9.5, body_key, content_w - 190)[:2]:
        c.text(MARGIN + 22, line_y, line, body_key, 9.5, ink)
        line_y -= 13
    button = "Get started"
    button_w = text_width(button, 8, "F2") + 30
    c.rect(PAGE_W - MARGIN - 22 - button_w, band_bottom + 24, button_w, 26, accent)
    c.text(PAGE_W - MARGIN - 22 - button_w + 15, band_bottom + 32.5, button, "F2", 8, ink_for(accent))

    # accent rule + footer
    c.rect(MARGIN, MARGIN + 20, content_w, 1.5, accent)
    c.rect(MARGIN, MARGIN + 20, 54, 1.5, accent_alt)
    c.text(MARGIN, MARGIN, f"source: {theme['source']}", "F1", 7.5, muted)
    footer = "generated by theme-showcase.py"
    c.text(PAGE_W - MARGIN - text_width(footer, 7.5, "F1"), MARGIN, footer, "F1", 7.5, muted)

    return "\n".join(c.ops)


def generate(target=".", out=None, only=None, use_registry=True, client=None):
    themes = collect_themes(target, use_registry=use_registry, client=client)
    if not themes:
        raise SystemExit("theme-showcase: no themes available (data/palettes.csv is empty)")
    if only:
        needle = only.strip().lower()
        themes = [t for t in themes if needle in t["name"].lower()]
        if not themes:
            raise SystemExit(f"theme-showcase: no theme matches {only!r}")
    contents = [render_page(theme, i + 1, len(themes)) for i, theme in enumerate(themes)]
    destination = Path(out) if out else Path(target) / ".ufme" / "theme-showcase.pdf"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(build_pdf(contents))
    return destination, themes


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a theme showcase PDF.")
    parser.add_argument("--target", default=".", help="project directory (default: .)")
    parser.add_argument("--out", help="output PDF (default: <target>/.ufme/theme-showcase.pdf)")
    parser.add_argument("--only", help="render only themes whose name contains this text")
    parser.add_argument("--no-registry", action="store_true", help="ignore the MCP registry")
    parser.add_argument("--json", action="store_true", help="print the theme list as JSON")
    parser.add_argument("--quiet", action="store_true", help="no success output")
    args = parser.parse_args(argv)

    try:
        destination, themes = generate(
            target=args.target, out=args.out, only=args.only,
            use_registry=not args.no_registry,
        )
    except SystemExit as exc:
        message = str(exc.code)
        print(message, file=sys.stderr)
        return 3 if "no theme" in message else 2

    if args.json:
        print(json.dumps(themes, indent=2))
    elif not args.quiet:
        print(f"theme-showcase: {len(themes)} theme(s) -> {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
