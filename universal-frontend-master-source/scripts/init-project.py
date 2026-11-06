#!/usr/bin/env python3
"""
init-project.py — Interactive project initialization for UFMW.

Asks the user design-preference questions (palette, typography, visual style,
reference URLs) and records the answers in .ufme/ so the design system and
prototype generator can use them.

All design questions are mandatory: the user must pick one option for each.
Reference URLs are optional (blank line to finish).

Usage:
  python3 init-project.py [target-dir]
"""
import csv
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


def pick_one(rows, label):
    """Show a numbered list and require a valid selection (no skip)."""
    if not rows:
        print(f"(no {label} options available)")
        return None
    while True:
        print(f"\n--- {label} (required) ---")
        for i, r in enumerate(rows, 1):
            name = r.get("name", "")
            desc = r.get("description", "") or r.get("usage_or_notes", "")
            print(f"  {i}. {name} — {desc[:90]}")
        choice = input(f"Choose a {label} [1-{len(rows)}]: ").strip()
        try:
            idx = int(choice)
            if 1 <= idx <= len(rows):
                return rows[idx - 1]
        except ValueError:
            pass
        print("  Invalid choice — please select a number from the list.")


def ask_text(prompt, required=False):
    while True:
        if required:
            prompt = f"{prompt} (required): "
        else:
            prompt = f"{prompt}: "
        val = input(prompt).strip()
        if val or not required:
            return val
        print("  This field is required — please enter a value.")


def read_design_system(target):
    path = target / "DESIGN_SYSTEM.md"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return ("# Design System\n\n## Tokens\n### Typography\n"
            "### Spacing\n### Color\n\n## Components\n## Responsive rules\n"
            "## Animation guidance\n## Accessible UI patterns\n## Assets\n"
            "| Asset | Repo/site | License | Commercial use | Install method | Reason |\n"
            "|-------|-----------|---------|----------------|----------------|----------------|\n")


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
    print("Design questions are required. Answer each one to set up your design system.\n")

    # --- Palette (required) ---
    palettes = load_csv("palettes.csv")
    chosen_palette = pick_one(palettes, "color palette")

    # --- Typography (required) ---
    fonts = load_csv("font_pairings.csv")
    chosen_font = pick_one(fonts, "font pairing")

    # --- Visual style (required) ---
    styles = load_csv("styles.csv")
    chosen_style = pick_one(styles, "visual style")

    # --- Reference URLs (optional) ---
    refs = []
    print("\n--- Reference websites (optional) ---")
    print("Paste reference URLs for design inspiration (blank line to finish).")
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
