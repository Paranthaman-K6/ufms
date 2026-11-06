#!/usr/bin/env python3
"""
reference-analyze.py — Analyze inspected reference elements and match them
to target project locations.

Reads .ufme/evidence/reference-inspect.json and produces:
  .ufme/REFERENCES.md    — catalog of references with elements and destinations
  .ufme/ELEMENT_MAP.md   — mapping of reference elements to implementation locations
  .ufme/evidence/reference-analysis.json — machine-readable analysis

Usage:
  python3 skills/universal-frontend-master/scripts/reference-analyze.py [evidenceDir]
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UFME = ROOT / ".ufme"
EVIDENCE = Path(os.environ.get("UFME_EVIDENCE_DIR") or (UFME / "evidence"))

# Destination options the user can choose from.
DESTINATIONS = [
    "homepage",
    "existing header",
    "product page",
    "dashboard",
    "replace current component",
    "add new section",
    "another location",
]

# Aspects the user can specify.
ASPECTS = [
    "visual appearance",
    "behavior",
    "animations",
    "layout",
    "combination",
]


def load_inspect(evidence_dir):
    inspect_file = evidence_dir / "reference-inspect.json"
    if not inspect_file.exists():
        return None
    return json.loads(inspect_file.read_text(encoding="utf-8"))


def load_references(ufme_dir):
    ref_file = ufme_dir / "REFERENCES.md"
    if ref_file.exists():
        return ref_file.read_text(encoding="utf-8")
    return "# References\n\n## Reference Catalog\n\n"


def save_references(ufme_dir, content):
    ref_file = ufme_dir / "REFERENCES.md"
    ref_file.write_text(content, encoding="utf-8")


def load_element_map(ufme_dir):
    map_file = ufme_dir / "ELEMENT_MAP.md"
    if map_file.exists():
        return map_file.read_text(encoding="utf-8")
    return "# Element Map\n\n## Element-to-Location Mapping\n\n"


def save_element_map(ufme_dir, content):
    map_file = ufme_dir / "ELEMENT_MAP.md"
    map_file.write_text(content, encoding="utf-8")


def group_elements_by_type(elements):
    """Group inspected elements by their elementType."""
    groups = {}
    for el in elements:
        etype = el.get("elementType", "unknown")
        groups.setdefault(etype, []).append(el)
    return groups


def render_element_entry(el, idx):
    """Render a single element as a markdown entry."""
    lines = []
    lines.append(f"### {idx + 1}. {el['elementType'].title()}")
    lines.append(f"- **Selector**: `{el.get('selector', '')}`")
    lines.append(f"- **Tag**: `{el.get('tagName', '')}`")
    lines.append(f"- **Class**: `{el.get('className', '')}`")
    lines.append(f"- **ID**: `{el.get('id', '')}`")
    lines.append(f"- **Role**: `{el.get('role', '')}`")
    lines.append(f"- **Text**: `{el.get('textContent', '')[:100]}`")
    styles = el.get("styles", {})
    if styles:
        lines.append(f"- **Background**: `{styles.get('backgroundColor', '')}`")
        lines.append(f"- **Color**: `{styles.get('color', '')}`")
        lines.append(f"- **Font**: `{styles.get('fontFamily', '')}`")
        lines.append(f"- **Size**: `{styles.get('width', '')} x {styles.get('height', '')}`")
    if el.get("screenshotFile"):
        lines.append(f"- **Screenshot**: `{el['screenshotFile']}`")
    lines.append(f"- **Confidence**: {el.get('confidence', 0)}/10")
    lines.append("")
    return "\n".join(lines)


def analyze(evidence_dir=EVIDENCE, ufme_dir=UFME):
    inspect_data = load_inspect(evidence_dir)
    if not inspect_data:
        print(f"[reference-analyze] No reference-inspect.json found in {evidence_dir}")
        print("[reference-analyze] Run: node skills/universal-frontend-master/scripts/reference-inspect.js <url>")
        return 1

    elements = inspect_data.get("elements", [])
    url = inspect_data.get("url", "unknown")
    groups = group_elements_by_type(elements)

    # Build REFERENCES.md content
    ref_content = load_references(ufme_dir)
    ref_content += f"\n## Reference: {url}\n"
    ref_content += f"- **Inspected**: {inspect_data.get('inspectedAt', '')}\n"
    ref_content += f"- **Page title**: {inspect_data.get('pageTitle', '')}\n"
    ref_content += f"- **Elements found**: {len(elements)}\n\n"

    for etype, els in sorted(groups.items()):
        ref_content += f"### {etype.title()} ({len(els)} element(s))\n"
        for i, el in enumerate(els):
            ref_content += render_element_entry(el, i)
        ref_content += "\n"

    save_references(ufme_dir, ref_content)

    # Build ELEMENT_MAP.md content
    map_content = load_element_map(ufme_dir)
    map_content += f"\n## Reference: {url}\n"
    map_content += "The following elements were identified. For each, specify:\n"
    map_content += "- **Destination**: where to implement (homepage, existing header, product page, dashboard, replace current component, add new section, another location)\n"
    map_content += "- **Aspects**: what to adapt (visual appearance, behavior, animations, layout, combination)\n\n"

    for etype, els in sorted(groups.items()):
        map_content += f"### {etype.title()}\n"
        for i, el in enumerate(els):
            el_id = f"{url}#{etype}#{i}"
            map_content += f"#### Element {i + 1}: {el['elementType'].title()}\n"
            map_content += f"- **Element ID**: `{el_id}`\n"
            map_content += f"- **Selector**: `{el.get('selector', '')}`\n"
            map_content += f"- **Text**: `{el.get('textContent', '')[:80]}`\n"
            map_content += f"- **Destination**: _[user to specify]_\n"
            map_content += f"- **Aspects**: _[user to specify]_\n"
            map_content += f"- **Status**: pending\n\n"

    save_element_map(ufme_dir, map_content)

    # Machine-readable analysis
    analysis = {
        "url": url,
        "inspectedAt": inspect_data.get("inspectedAt", ""),
        "pageTitle": inspect_data.get("pageTitle", ""),
        "totalElements": len(elements),
        "elementTypes": {etype: len(els) for etype, els in groups.items()},
        "elements": elements,
        "analyzedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    analysis_file = evidence_dir / "reference-analysis.json"
    fs_mkdir = evidence_dir.mkdir(parents=True, exist_ok=True)
    analysis_file.write_text(json.dumps(analysis, indent=2), encoding="utf-8")

    print(f"[reference-analyze] Analyzed {len(elements)} elements from {url}")
    print(f"[reference-analyze] References: {ufme_dir / 'REFERENCES.md'}")
    print(f"[reference-analyze] Element map: {ufme_dir / 'ELEMENT_MAP.md'}")
    print(f"[reference-analyze] Evidence: {analysis_file}")
    print(f"[reference-analyze] Element types: {', '.join(f'{k} ({v})' for k, v in sorted(groups.items()))}")
    print()
    print("[reference-analyze] NEXT STEPS:")
    print("  1. Review .ufme/REFERENCES.md and .ufme/ELEMENT_MAP.md")
    print("  2. For each element, specify destination and aspects in ELEMENT_MAP.md")
    print("  3. Run: python3 skills/universal-frontend-master/scripts/reference-match.py")
    return 0


def main():
    evidence_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else EVIDENCE
    sys.exit(analyze(evidence_dir))


if __name__ == "__main__":
    main()
