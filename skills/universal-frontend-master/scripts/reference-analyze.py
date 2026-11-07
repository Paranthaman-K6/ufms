#!/usr/bin/env python3
"""Analyze one reference inspection and upsert its element map without losing edits."""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("UFME_PROJECT_ROOT") or Path(__file__).resolve().parents[3]).resolve()
UFME = Path(os.environ.get("UFME_DIR") or (ROOT / ".ufme")).resolve()
EVIDENCE = Path(os.environ.get("UFME_EVIDENCE_DIR") or (UFME / "evidence")).resolve()


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[reference-analyze] Cannot read {path}: {exc}", file=sys.stderr)
        return None


def section_marker(reference_id):
    return f"<!-- ufmw-reference:{reference_id} -->"


def upsert_section(path, marker, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    closing = marker.replace("<!--", "<!-- /").replace("-->", " -->")
    section = marker + "\n" + body.rstrip() + "\n" + closing
    start = existing.find(marker)
    if start < 0:
        updated = existing.rstrip() + ("\n\n" if existing.strip() else "") + section + "\n"
    else:
        end = existing.find(closing, start + len(marker))
        updated = existing[:start] + section + existing[end + len(closing):] if end >= 0 else existing[:start] + section
    path.write_text(updated, encoding="utf-8")


def parse_existing_map(content):
    saved = {}
    current = None
    for line in content.splitlines():
        value = line.strip()
        if value.startswith("#### Element ID:"):
            current = value.partition(":")[2].strip().strip(chr(96))
            if current:
                saved[current] = {}
        elif current and value.startswith("- **"):
            label, separator, field_value = value[4:].partition("**:")
            if separator:
                saved[current][label.strip()] = field_value.strip()
        elif value.startswith("<!-- /ufmw-reference:"):
            current = None
    return saved


def clean(value):
    return str(value or "").replace(chr(96), "'").replace("\n", " ").strip()


def analyze(evidence_dir=EVIDENCE, ufme_dir=UFME, source_name=None):
    input_path = evidence_dir / (source_name or "reference-inspect.json")
    inspection = read_json(input_path)
    if not isinstance(inspection, dict) or inspection.get("status") != "PASS":
        print(f"[reference-analyze] No successful inspection evidence in {input_path}", file=sys.stderr)
        return 1

    url = str(inspection.get("url") or "").strip()
    elements = inspection.get("elements")
    if not url or not isinstance(elements, list) or not elements:
        print("[reference-analyze] Inspection must include a URL and at least one visible element.", file=sys.stderr)
        return 1

    reference_id = inspection.get("referenceId") or hashlib.sha256(url.encode()).hexdigest()[:12]
    map_path = ufme_dir / "ELEMENT_MAP.md"
    previous = map_path.read_text(encoding="utf-8") if map_path.exists() else ""
    saved = parse_existing_map(previous)

    reference_lines = [
        f"## Reference: {url}",
        f"- Reference ID: {reference_id}",
        f"- Inspected: {inspection.get('inspectedAt', '')}",
        f"- Page title: {inspection.get('pageTitle', '')}",
        f"- Elements found: {len(elements)}",
        "",
    ]
    mapping_lines = [
        f"## Reference: {url}",
        f"- Reference ID: {reference_id}",
        "",
        "Set Destination and Aspects only for the elements you want to adapt.",
        "After implementation, set Target selector to the selector in the target project for verification.",
        "",
    ]

    for position, element in enumerate(elements):
        if not isinstance(element, dict):
            continue
        element_type = str(element.get("elementType") or "unknown")
        index = int(element.get("index", position))
        element_id = f"{reference_id}:{element_type}:{index}"
        selector = clean(element.get("selector", ""))
        styles = element.get("styles") or {}
        reference_lines.extend([
            f"### {element_type.title()} - {position + 1}",
            f"- Element ID: {element_id}",
            f"- Selector: {selector}",
            f"- Tag: {clean(element.get('tagName'))}",
            f"- Class: {clean(element.get('className'))}",
            f"- Text: {clean(str(element.get('textContent', ''))[:120])}",
            f"- Background: {clean(styles.get('backgroundColor'))}",
            f"- Color: {clean(styles.get('color'))}",
            f"- Font: {clean(styles.get('fontFamily'))}",
            f"- Size: {clean(styles.get('width'))} x {clean(styles.get('height'))}",
            f"- Screenshot: {clean(element.get('screenshotFile'))}",
            "",
        ])
        existing = saved.get(element_id, {})
        mapping_lines.extend([
            f"#### Element ID: {element_id}",
            f"- **Element type**: {element_type}",
            f"- **Reference selector**: {selector}",
            f"- **Target selector**: {existing.get('Target selector', '_[user to specify]_')}",
            f"- **Destination**: {existing.get('Destination', '_[user to specify]_')}",
            f"- **Aspects**: {existing.get('Aspects', '_[user to specify]_')}",
            f"- **Status**: {existing.get('Status', 'pending')}",
            "",
        ])

    upsert_section(ufme_dir / "REFERENCES.md", section_marker(reference_id), "\n".join(reference_lines))
    upsert_section(map_path, section_marker(reference_id), "\n".join(mapping_lines))

    analysis = {
        "referenceId": reference_id,
        "url": url,
        "inspectedAt": inspection.get("inspectedAt", ""),
        "pageTitle": inspection.get("pageTitle", ""),
        "totalElements": len(elements),
        "elements": elements,
        "analyzedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    evidence_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(analysis, indent=2) + "\n"
    per_reference = evidence_dir / f"reference-analysis-{reference_id}.json"
    per_reference.write_text(payload, encoding="utf-8")
    (evidence_dir / "reference-analysis.json").write_text(payload, encoding="utf-8")

    print(f"[reference-analyze] Analyzed {len(elements)} elements from {url}")
    print(f"[reference-analyze] Reference ID: {reference_id}")
    print(f"[reference-analyze] Element map: {map_path}")
    print(f"[reference-analyze] Evidence: {per_reference}")
    return 0


def main():
    evidence_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else EVIDENCE
    source_name = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(analyze(evidence_dir, UFME, source_name))


if __name__ == "__main__":
    main()
