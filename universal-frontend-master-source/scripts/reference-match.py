#!/usr/bin/env python3
"""
reference-match.py — Match reference elements to target project locations.

Reads .ufme/ELEMENT_MAP.md and .ufme/evidence/reference-analysis.json,
then produces an implementation plan matching each reference element to
a destination in the target project.

Usage:
  python3 universal-frontend-master-source/scripts/reference-match.py [evidenceDir]

Output:
  .ufme/evidence/reference-match.json  — machine-readable match plan
  .ufme/DESIGN_ADAPTATIONS.md          — how each element is adapted to target design
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UFME = ROOT / ".ufme"
EVIDENCE = Path(os.environ.get("UFME_EVIDENCE_DIR") or (UFME / "evidence"))


def load_analysis(evidence_dir):
    analysis_file = evidence_dir / "reference-analysis.json"
    if not analysis_file.exists():
        return None
    return json.loads(analysis_file.read_text(encoding="utf-8"))


def load_element_map(ufme_dir):
    map_file = ufme_dir / "ELEMENT_MAP.md"
    if map_file.exists():
        return map_file.read_text(encoding="utf-8")
    return ""


def parse_element_map(content):
    """Parse ELEMENT_MAP.md to extract element entries with destinations/aspects."""
    elements = []
    lines = content.splitlines()
    current_element = None
    current_type = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#### Element "):
            if current_element:
                elements.append(current_element)
            current_element = {
                "title": stripped,
                "elementId": "",
                "selector": "",
                "text": "",
                "destination": "",
                "aspects": "",
                "status": "pending",
            }
            current_type = None
        elif stripped.startswith("- **Element ID**:"):
            if current_element:
                current_element["elementId"] = stripped.split("`")[1] if "`" in stripped else ""
        elif stripped.startswith("- **Selector**:"):
            if current_element:
                current_element["selector"] = stripped.split("`")[1] if "`" in stripped else ""
        elif stripped.startswith("- **Text**:"):
            if current_element:
                current_element["text"] = stripped.split("`")[1] if "`" in stripped else ""
        elif stripped.startswith("- **Destination**:"):
            if current_element:
                val = stripped.replace("- **Destination**:", "").strip()
                current_element["destination"] = val.replace("_", " ") if val else ""
        elif stripped.startswith("- **Aspects**:"):
            if current_element:
                val = stripped.replace("- **Aspects**:", "").strip()
                current_element["aspects"] = val.replace("_", " ") if val else ""
        elif stripped.startswith("- **Status**:"):
            if current_element:
                current_element["status"] = stripped.split("`")[-2] if "`" in stripped else "pending"

    if current_element:
        elements.append(current_element)

    return elements


def render_match_entry(el):
    """Render a single match entry as markdown."""
    lines = []
    lines.append(f"### {el['elementId']}")
    lines.append(f"- **Source element**: {el.get('elementType', 'unknown').title()}")
    lines.append(f"- **Selector**: `{el.get('selector', '')}`")
    lines.append(f"- **Destination**: {el.get('destination', 'pending')}")
    lines.append(f"- **Aspects**: {el.get('aspects', 'pending')}")
    lines.append(f"- **Adaptation**: {el.get('adaptation', 'pending')}")
    lines.append(f"- **CSS variables**: {', '.join(el.get('cssVariables', [])) or 'pending'}")
    lines.append("")
    return "\n".join(lines)


def match(evidence_dir=EVIDENCE, ufme_dir=UFME):
    analysis = load_analysis(evidence_dir)
    if not analysis:
        print(f"[reference-match] No reference-analysis.json found in {evidence_dir}")
        print("[reference-match] Run: python3 universal-frontend-master-source/scripts/reference-analyze.py")
        return 1

    map_content = load_element_map(ufme_dir)
    elements = parse_element_map(map_content)

    # Build match plan
    match_plan = {
        "url": analysis.get("url", ""),
        "matchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "elements": [],
    }

    # Design adaptation rules based on destination
    destination_adaptations = {
        "homepage": "Adapt to homepage layout with full-width container",
        "existing header": "Match existing header height, font sizes, and colors",
        "product page": "Fit within product page grid system",
        "dashboard": "Adapt to dashboard sidebar + content layout",
        "replace current component": "Replace existing component markup one-to-one",
        "add new section": "Insert as new section with consistent spacing",
        "another location": "Adapt to specified target location",
    }

    for el in elements:
        destination = el.get("destination", "pending")
        aspects = el.get("aspects", "pending")

        match_entry = {
            "elementId": el.get("elementId", ""),
            "elementType": el.get("title", "").split(": ")[-1] if ": " in el.get("title", "") else "unknown",
            "selector": el.get("selector", ""),
            "text": el.get("text", ""),
            "destination": destination,
            "aspects": aspects,
            "adaptation": destination_adaptations.get(destination, "pending"),
            "cssVariables": [],
            "status": "matched" if destination and aspects else "pending",
        }

        # Extract CSS variables from the source element's styles
        source_styles = el.get("styles", {})
        if source_styles:
            # Map source styles to CSS variable names
            var_map = {
                "backgroundColor": "--ufmw-ref-bg-color",
                "color": "--ufmw-ref-text-color",
                "fontFamily": "--ufmw-ref-font-family",
                "fontSize": "--ufmw-ref-font-size",
            }
            for style_key, var_name in var_map.items():
                if source_styles.get(style_key):
                    match_entry["cssVariables"].append(var_name)

        match_plan["elements"].append(match_entry)

    # Write machine-readable match plan
    match_file = evidence_dir / "reference-match.json"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    match_file.write_text(json.dumps(match_plan, indent=2), encoding="utf-8")

    # Build DESIGN_ADAPTATIONS.md
    adapt_file = ufme_dir / "DESIGN_ADAPTATIONS.md"
    if adapt_file.exists():
        adapt_content = adapt_file.read_text(encoding="utf-8")
    else:
        adapt_content = "# Design Adaptations\n\n"

    adapt_content += f"\n## Reference: {analysis.get('url', '')}\n"
    adapt_content += f"- **Matched**: {match_plan['matchedAt']}\n"
    adapt_content += f"- **Total elements**: {len(match_plan['elements'])}\n"
    adapt_content += f"- **Matched**: {sum(1 for e in match_plan['elements'] if e['status'] == 'matched')}\n"
    adapt_content += f"- **Pending**: {sum(1 for e in match_plan['elements'] if e['status'] == 'pending')}\n\n"

    for el in match_plan["elements"]:
        adapt_content += render_match_entry(el)

    adapt_file.write_text(adapt_content, encoding="utf-8")

    matched_count = sum(1 for e in match_plan["elements"] if e["status"] == "matched")
    print(f"[reference-match] Matched {matched_count}/{len(match_plan['elements'])} elements")
    print(f"[reference-match] Match plan: {match_file}")
    print(f"[reference-match] Adaptations: {adapt_file}")
    print()
    print("[reference-match] NEXT STEPS:")
    print("  1. Review .ufme/DESIGN_ADAPTATIONS.md")
    print("  2. Run: python3 universal-frontend-master-source/scripts/reference-adapt.py")
    return 0


def main():
    evidence_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else EVIDENCE
    sys.exit(match(evidence_dir))


if __name__ == "__main__":
    main()
