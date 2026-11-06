#!/usr/bin/env python3
"""
init-project.py — Interactive project initialization for UFMW.

Asks the user design-preference questions (palette, typography, visual style,
reference URLs) and records the answers in .ufme/ so the design system and
prototype generator can use them.

Usage:
  python3 init-project.py [target-dir]

Questions are optional: pressing Enter keeps the existing/default value.
"""
import csv
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def load_csv(name):
    path = DATA_DIR / name
    rows = []
    if path.is_file():
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                rows.append(r)
    return rows


def pick_one(rows, label, hint_key=None):
    """Show a numbered list of rows and return the chosen row dict (or None)."""
    if not rows:
        print(f"(no {label} options available)")
        return None
    print(f"\n--- {label} ---")
    for i, r in enumerate(rows, 1):
        name = r.get("name", "")
        desc = r.get("description", "") or r.get("usage_or_notes", "")
        print(f"  {i}. {name} — {desc[:90]}")
    print(f"  0. skip / keep default")
    choice = input(f"Choose a {label} [0-{len(rows)}]: ").strip()
    if not choice or choice == "0":
        return None
    try:
        idx = int(choice)
        if 1 <= idx <= len(rows):
            return rows[idx - 1]
    except ValueError:
        pass
    print("  (invalid choice, keeping default)")
    return None


def ask_text(prompt, default=""):
    if default:
        prompt = f"{prompt} [{default}]"
    prompt += ": "
    val = input(prompt).strip()
    return val if val else default


def ask_bool(prompt, default=False):
    d = "Y/n" if default else "y/N"
    val = input(f"{prompt} [{d}]: ").strip().lower()
    if not val:
        return default
    return val in ("y", "yes")


def read_design_system(target):
    path = target / "DESIGN_SYSTEM.md"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return "# Design System\n\n## Tokens\n### Typography\n### Spacing\n### Color\n\n## Components\n## Responsive rules\n## Animation guidance\n## Accessible UI patterns\n## Assets\n| Asset | Repo/site | License | Commercial use | Install method | Reason |\n|-------|-----------|---------|----------------|----------------|----------------|\n"


def write_design_system(target, content):
    path = target / "DESIGN_SYSTEM.md"
    path.write_text(content, encoding="utf-8")


def replace_section(content, heading, body):
    """Replace the content under a ### heading (until next ### or ##)."""
    pattern = rf"(### {re.escape(heading)}\n)(.*?)(?=\n### |\n## |\Z)"
    replacement = rf"\1{body}\n"
    return re.sub(pattern, replacement, content, flags=re.S)


def main():
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".").expanduser().resolve()
    ufme = target / ".ufme"
    ufme.mkdir(parents=True, exist_ok=True)

    print("=== UFMW Project Initialization ===")
    print("Answer the design questions below (Enter = keep default/skip).\n")

    # --- Palette ---
    palettes = load_csv("palettes.csv")
    chosen_palette = pick_one(palettes, "color palette")

    # --- Typography ---
    fonts = load_csv("font_pairings.csv")
    chosen_font = pick_one(fonts, "font pairing")

    # --- Visual style ---
    styles = load_csv("styles.csv")
    chosen_style = pick_one(styles, "visual style")

    # --- Reference URLs ---
    refs = []
    print("\n--- Reference websites ---")
    print("Paste reference URLs you'd like to use as design inspiration (blank line to finish).")
    while True:
        url = input("  URL: ").strip()
        if not url:
            break
        refs.append(url)

    # --- Build design system markdown ---
    ds = read_design_system(target)

    if chosen_palette:
        name = chosen_palette.get("name", "")
        notes = chosen_palette.get("usage_or_notes", "")
        body = f"- Primary: {name}\n- Notes: {notes}\n"
        ds = replace_section(ds, "Color", body)

    if chosen_font:
        name = chosen_font.get("name", "")
        notes = chosen_font.get("usage_or_notes", "")
        body = f"- Pairing: {name}\n- Notes: {notes}\n"
        ds = replace_section(ds, "Typography", body)

    if chosen_style:
        name = chosen_style.get("name", "")
        notes = chosen_style.get("usage_or_notes", "")
        body = f"- Style: {name}\n- Notes: {notes}\n"
        ds = replace_section(ds, "Spacing", f"- Visual style applied: {name}\n- Notes: {notes}\n")

    write_design_system(ufme, ds)

    # --- References ---
    if refs:
        ref_path = ufme / "REFERENCES.md"
        lines = ["# References", ""]
        for url in refs:
            lines.append(f"- {url}")
        ref_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nRecorded {len(refs)} reference URL(s) in .ufme/REFERENCES.md")

    print("\nDesign system saved to .ufme/DESIGN_SYSTEM.md")
    print("You can edit it directly or re-run this script to update choices.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
