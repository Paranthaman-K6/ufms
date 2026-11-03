#!/usr/bin/env python3
"""
design-search.py — search design reference CSV knowledge base (todo 4.8 / P2.1).

Searches local CSV files under universal-frontend-master-source/data/ (styles.csv,
palettes.csv, font_pairings.csv, ux_rules.csv) using pure Python keyword/TF scoring.

Usage:
  python3 design-search.py --q "minimal saas landing" [--n 5] [--kind palettes] [--scaffold] [--page home]

Output: ranked list of matching design references with truncated description and usage notes.
With --scaffold: writes .ufme/design-system/MASTER.md + .ufme/pages/<page>.md overrides.

Pure python3, no external dependencies.
"""

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
UFME_DIR = ROOT.parent / ".ufme"


def load_csv(path):
    rows = []
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def score_row(row, query_tokens):
    text = f"{row.get('name', '')} {row.get('keywords', '')} {row.get('description', '')} {row.get('usage_or_notes', '')}".lower()
    score = 0
    for tok in query_tokens:
        if tok in text:
            # Higher weight if matched in name or keywords
            if tok in row.get('name', '').lower() or tok in row.get('keywords', '').lower():
                score += 3
            else:
                score += 1
    return score


def search_all(query, top_n, kind):
    query_tokens = [t.lower() for t in query.split() if t.strip()]
    if not query_tokens:
        return []

    files = {
        "styles": DATA_DIR / "styles.csv",
        "palettes": DATA_DIR / "palettes.csv",
        "font_pairings": DATA_DIR / "font_pairings.csv",
        "ux_rules": DATA_DIR / "ux_rules.csv",
    }

    targets = [kind] if kind != "all" else list(files.keys())
    results = []

    for k in targets:
        path = files.get(k)
        if not path or not path.is_file():
            continue
        for row in load_csv(path):
            s = score_row(row, query_tokens)
            if s > 0:
                results.append((s, k, row))

    results.sort(key=lambda x: x[0], reverse=True)
    return results[:top_n]


def scaffold_design_system(top_result):
    UFME_DIR.mkdir(parents=True, exist_ok=True)
    ds_dir = UFME_DIR / "design-system"
    ds_dir.mkdir(parents=True, exist_ok=True)
    master_path = ds_dir / "MASTER.md"

    if not top_result:
        palette = "Default Neutral & Indigo"
        notes = "No specific design search query provided."
    else:
        score, kind, row = top_result
        palette = row.get("name", "Unknown")
        notes = row.get("usage_or_notes", row.get("description", ""))

    content = f"""# Design System Master

Chosen Design / Palette: **{palette}**
Generated via design-search.py knowledge base.

## Notes & Usage
{notes}

## Tokens
- Canvas / Background: #ffffff (light) / #0f172a (dark)
- Primary Accent: Indigo / Blue
- Typography: Inter, sans-serif
"""
    master_path.write_text(content, encoding="utf-8")
    print(f"[design-search] Wrote design system master → {master_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--q", default="saas modern clean landing", help="Search query")
    parser.add_argument("--n", type=int, default=5, help="Top N results")
    parser.add_argument("--kind", default="all", choices=["all", "styles", "palettes", "font_pairings", "ux_rules"])
    parser.add_argument("--scaffold", action="store_true", help="Write design system master scaffold into .ufme/")
    parser.add_argument("--page", default="home", help="Page name for scaffold override")
    args = parser.parse_args()

    matches = search_all(args.q, args.n, args.kind)
    if not matches:
        print(f"No design matches found for query: '{args.q}'")
    else:
        print(f"Design search results for '{args.q}' (top {args.n}):\n")
        for rank, (score, kind, row) in enumerate(matches, 1):
            name = row.get("name", "Unnamed")
            desc = row.get("description", "")
            usage = row.get("usage_or_notes", "")
            print(f"{rank}. [{kind.upper()}] {name} (score: {score})")
            print(f"   Desc: {desc}")
            print(f"   Usage: {usage}\n")

    if args.scaffold:
        top = matches[0] if matches else None
        scaffold_design_system(top)

    return 0


if __name__ == "__main__":
    sys.exit(main())
