#!/usr/bin/env python3
"""
init-project.py — Interactive project initialization for UFMW.

Asks the user design-preference questions (palette, typography, visual style,
reference URLs) and records the answers in .ufme/ so the design system and
prototype generator can use them.

ALL design questions are mandatory and are asked BEFORE any code is written.

Two modes:
  * Interactive (TTY available): prompts via input() for each question.
  * Non-interactive (no TTY / OpenCode agent): pass answers via CLI flags.
    If no flags are given, prints the questions and exits so the user can
    provide answers before any code is scaffolded.

Usage:
  python3 init-project.py [target-dir] [--palette <name>] [--font <name>]
      [--style <name>] [--refs <url1,url2>] [--profile basic|advanced]
      [--list-palettes|--list-fonts|--list-styles]

Examples:
  # Interactive (asks each question)
  python3 init-project.py .

  # Non-interactive (OpenCode agent passes answers)
  python3 init-project.py . --palette "Stripe Gradient Blue" \
      --font "IBM Plex Sans + Plex Mono" --style "Minimal Monochrome" \
      --refs "https://stripe.com" --profile advanced
"""
import argparse
import csv
import os
import re
import subprocess
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


def list_options(rows, label):
    """Print numbered options for a category."""
    if not rows:
        print(f"(no {label} options available)")
        return
    print(f"\n--- {label} ---")
    for i, r in enumerate(rows, 1):
        name = r.get("name", "")
        desc = r.get("description", "") or r.get("usage_or_notes", "")
        print(f"  {i}. {name} — {desc[:90]}")


def pick_one_interactive(rows, label):
    """Show a numbered list and require a valid selection (interactive TTY)."""
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


def pick_one_by_name(rows, name):
    """Find a row by exact name (case-insensitive)."""
    if not name:
        return None
    for r in rows:
        if r.get("name", "").strip().lower() == name.strip().lower():
            return r
    return None


def pick_one_by_index(rows, index):
    """Find a row by 1-based index."""
    try:
        idx = int(index)
        if 1 <= idx <= len(rows):
            return rows[idx - 1]
    except (ValueError, TypeError):
        pass
    return None


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


def build_design_system(ds, palette, font, style, refs):
    """Fill in design-system sections from chosen options."""
    if palette:
        name = palette.get("name", "")
        notes = palette.get("usage_or_notes", "")
        body = f"- Primary: {name}\n- Notes: {notes}\n"
        ds = replace_section(ds, "Color", body)
    if font:
        name = font.get("name", "")
        notes = font.get("usage_or_notes", "")
        body = f"- Pairing: {name}\n- Notes: {notes}\n"
        ds = replace_section(ds, "Typography", body)
    if style:
        name = style.get("name", "")
        notes = style.get("usage_or_notes", "")
        body = f"- Style: {name}\n- Notes: {notes}\n"
        ds = replace_section(ds, "Spacing", f"- Visual style applied: {name}\n- Notes: {notes}\n")
    return ds


def write_references(ufme, refs):
    if refs:
        ref_path = ufme / "REFERENCES.md"
        lines = ["# References", ""]
        for url in refs:
            lines.append(f"- {url}")
        ref_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_questions(palettes, fonts, styles):
    """Print all design questions in a structured format for non-interactive use."""
    print("=== UFMW Project Initialization — Design Questions ===")
    print("Answer ALL questions below before any code is scaffolded.")
    print("Provide answers via CLI flags or re-run interactively.\n")

    print("1. Color palette (required) — choose one:")
    for i, r in enumerate(palettes, 1):
        name = r.get("name", "")
        desc = r.get("usage_or_notes", "") or r.get("description", "")
        print(f"   {i}. {name} — {desc[:90]}")
    print("   Flag: --palette <name-or-number>")

    print("\n2. Font pairing (required) — choose one:")
    for i, r in enumerate(fonts, 1):
        name = r.get("name", "")
        desc = r.get("usage_or_notes", "") or r.get("description", "")
        print(f"   {i}. {name} — {desc[:90]}")
    print("   Flag: --font <name-or-number>")

    print("\n3. Visual style (required) — choose one:")
    for i, r in enumerate(styles, 1):
        name = r.get("name", "")
        desc = r.get("usage_or_notes", "") or r.get("description", "")
        print(f"   {i}. {name} — {desc[:90]}")
    print("   Flag: --style <name-or-number>")

    print("\n4. Reference URLs (optional) — comma-separated list")
    print("   Flag: --refs <url1>,<url2>")

    print("\n5. Profile (required) — basic or advanced")
    print("   Flag: --profile basic|advanced")

    print("\n6. Project name (required)")
    print("   Flag: --project-name <name>")

    print("\n7. Template type (default: landing)")
    print("   Flag: --type landing|portfolio|blog|ecommerce|dashboard|admin|saas|docs|restaurant|realestate|event|nonprofit|resume")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize UFMW project design system (asks questions before code).",
        add_help=True,
    )
    parser.add_argument("target", nargs="?", default=".", help="project directory (default: .)")
    parser.add_argument("--palette", "-p", help="color palette name or number (1-13)")
    parser.add_argument("--font", "-f", help="font pairing name or number (1-14)")
    parser.add_argument("--style", "-s", help="visual style name or number (1-14)")
    parser.add_argument("--refs", "-r", help="comma-separated reference URLs")
    parser.add_argument("--profile", help="basic or advanced (default: basic)")
    parser.add_argument("--project-name", "-n", help="project name (required)")
    parser.add_argument("--type", "-t", default="landing", help="template category (default: landing)")
    parser.add_argument("--list-palettes", action="store_true", help="list color palettes and exit")
    parser.add_argument("--list-fonts", action="store_true", help="list font pairings and exit")
    parser.add_argument("--list-styles", action="store_true", help="list visual styles and exit")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    ufme = target / ".ufme"
    ufme.mkdir(parents=True, exist_ok=True)

    palettes = load_csv("palettes.csv")
    fonts = load_csv("font_pairings.csv")
    styles = load_csv("styles.csv")

    # List-only modes
    if args.list_palettes:
        list_options(palettes, "color palette")
        return 0
    if args.list_fonts:
        list_options(fonts, "font pairing")
        return 0
    if args.list_styles:
        list_options(styles, "visual style")
        return 0

    has_tty = os.isatty(sys.stdin.fileno())
    cli_args_provided = any([
        args.palette, args.font, args.style, args.refs,
        args.profile, args.project_name,
    ])

    # Non-interactive mode: require all CLI answers; if missing, print questions and exit.
    if not has_tty and not cli_args_provided:
        print_questions(palettes, fonts, styles)
        print("\nNo TTY detected and no CLI answers provided.")
        print("Re-run with --palette, --font, --style, --profile, --project-name (and --refs) to answer non-interactively.")
        print("Or run in an interactive terminal to answer via prompts.")
        return 2

    # Resolve each required choice: CLI arg > interactive prompt
    def resolve_palette():
        if args.palette:
            r = pick_one_by_name(palettes, args.palette) or pick_one_by_index(palettes, args.palette)
            if r:
                return r
            print(f"Palette '{args.palette}' not found. Use --list-palettes to see options.")
            sys.exit(2)
        return pick_one_interactive(palettes, "color palette")

    def resolve_font():
        if args.font:
            r = pick_one_by_name(fonts, args.font) or pick_one_by_index(fonts, args.font)
            if r:
                return r
            print(f"Font '{args.font}' not found. Use --list-fonts to see options.")
            sys.exit(2)
        return pick_one_interactive(fonts, "font pairing")

    def resolve_style():
        if args.style:
            r = pick_one_by_name(styles, args.style) or pick_one_by_index(styles, args.style)
            if r:
                return r
            print(f"Style '{args.style}' not found. Use --list-styles to see options.")
            sys.exit(2)
        return pick_one_interactive(styles, "visual style")

    chosen_palette = resolve_palette()
    chosen_font = resolve_font()
    chosen_style = resolve_style()

    # Reference URLs (optional)
    if args.refs:
        refs = [u.strip() for u in args.refs.split(",") if u.strip()]
    elif has_tty:
        print("\n--- Reference websites (optional) ---")
        print("Paste reference URLs for design inspiration (blank line to finish).")
        refs = []
        while True:
            url = input("  URL: ").strip()
            if not url:
                break
            refs.append(url)
    else:
        refs = []

    # Profile (required)
    profile = args.profile or ("basic" if not has_tty else ask_text("Profile (basic/advanced) [default: basic]", required=False) or "basic")
    if profile not in ("basic", "advanced"):
        print(f"Invalid profile '{profile}' — must be 'basic' or 'advanced'.")
        sys.exit(2)

    # Project name (required)
    project_name = args.project_name or ("" if not has_tty else ask_text("Project name (required)", required=True))
    if not project_name:
        print("Project name is required. Use --project-name <name>.")
        sys.exit(2)

    # --- Build design system markdown (questions answered, now write) ---
    ds = read_design_system(target)
    ds = build_design_system(ds, chosen_palette, chosen_font, chosen_style, refs)
    write_design_system(ufme, ds)
    write_references(ufme, refs)

    # Record design choices for the scaffold script to consume
    choices = {
        "project_name": project_name,
        "type": args.type,
        "profile": profile,
        "palette": chosen_palette.get("name", ""),
        "font": chosen_font.get("name", ""),
        "style": chosen_style.get("name", ""),
        "refs": refs,
    }
    choices_path = ufme / "design-choices.json"
    import json
    choices_path.write_text(json.dumps(choices, indent=2), encoding="utf-8")

    # Theme showcase: the answers rendered as a reviewable PDF. Never blocks init.
    showcase = ROOT / "scripts" / "theme-showcase.py"
    if showcase.is_file():
        try:
            result = subprocess.run(
                [sys.executable, str(showcase), "--target", str(target), "--quiet"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                print(f"warning: theme showcase not generated: {result.stderr.strip()}")
        except (OSError, subprocess.SubprocessError):
            print("warning: theme showcase not generated")

    print("\nDesign questions answered — .ufme/DESIGN_SYSTEM.md saved.")
    print("You can now scaffold your project using @universal-frontend-master.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
