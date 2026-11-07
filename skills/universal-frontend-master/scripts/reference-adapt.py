#!/usr/bin/env python3
"""Create measured-style implementation briefs from matched reference elements."""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("UFME_PROJECT_ROOT") or Path(__file__).resolve().parents[3]).resolve()
UFME = Path(os.environ.get("UFME_DIR") or (ROOT / ".ufme")).resolve()
EVIDENCE = Path(os.environ.get("UFME_EVIDENCE_DIR") or (UFME / "evidence")).resolve()

STYLE_PROPERTIES = {
    "backgroundColor": "background-color",
    "color": "color",
    "fontFamily": "font-family",
    "fontSize": "font-size",
    "fontWeight": "font-weight",
    "lineHeight": "line-height",
    "letterSpacing": "letter-spacing",
    "padding": "padding",
    "margin": "margin",
    "borderRadius": "border-radius",
    "boxShadow": "box-shadow",
    "display": "display",
    "gap": "gap",
    "gridTemplateColumns": "grid-template-columns",
    "alignItems": "align-items",
    "justifyContent": "justify-content",
}


def safe_css(value):
    value = str(value or "").strip()
    if not value or len(value) > 300:
        return ""
    if re.search(r"[{};<>]|url\s*\(|expression\s*\(|@import", value, re.I):
        return ""
    return value


def load_plan(evidence_dir):
    path = evidence_dir / "reference-match.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[reference-adapt] Cannot read {path}: {exc}", file=sys.stderr)
        return None


def make_variable_name(element_id, property_name):
    stem = re.sub(r"[^a-z0-9]+", "-", str(element_id).lower()).strip("-")
    return f"--ufmw-ref-{stem[:35]}-{property_name}"


def build_elements(plan):
    output = []
    for element in plan.get("elements") or []:
        if element.get("status") != "matched":
            continue
        styles = element.get("sourceStyles") or {}
        declarations = []
        variables = {}
        for source_key, css_property in STYLE_PROPERTIES.items():
            value = safe_css(styles.get(source_key))
            if not value:
                continue
            var_name = make_variable_name(element.get("elementId", "element"), css_property)
            variables[var_name] = value
            declarations.append({
                "property": css_property,
                "value": value,
                "variable": var_name,
            })
        output.append({
            "elementId": element.get("elementId", ""),
            "referenceId": element.get("referenceId", ""),
            "referenceUrl": element.get("referenceUrl", ""),
            "elementType": element.get("elementType", "unknown"),
            "referenceSelector": element.get("referenceSelector", ""),
            "targetSelector": element.get("targetSelector", ""),
            "destination": element.get("destination", ""),
            "aspects": element.get("aspects", ""),
            "text": element.get("text", ""),
            "tagName": element.get("tagName", ""),
            "className": element.get("className", ""),
            "screenshotFile": element.get("screenshotFile", ""),
            "sourceStyles": styles,
            "cssVariables": variables,
            "cssDeclarations": declarations,
        })
    return output


def upsert_section(path, marker, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    end_marker = marker.replace("<!--", "<!-- /").replace("-->", " -->")
    section = marker + "\n" + body.rstrip() + "\n" + end_marker
    start = current.find(marker)
    if start >= 0:
        end = current.find(end_marker, start + len(marker))
        current = current[:start] + section + current[end + len(end_marker):] if end >= 0 else current[:start] + section
    else:
        current = current.rstrip() + ("\n\n" if current.strip() else "") + section + "\n"
    path.write_text(current, encoding="utf-8")


def adapt(evidence_dir=EVIDENCE, ufme_dir=UFME):
    plan = load_plan(evidence_dir)
    if not isinstance(plan, dict):
        return 1
    if plan.get("status") != "MATCHED" or not plan.get("elements"):
        print("[reference-adapt] No complete match plan. Finish mapping selected elements first.", file=sys.stderr)
        return 1

    elements = build_elements(plan)
    if len(elements) != len(plan["elements"]):
        print("[reference-adapt] Refusing partial or pending mappings.", file=sys.stderr)
        return 1

    adapted_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    urls = plan.get("urls") or ([plan.get("url")] if plan.get("url") else [])
    data = {
        "referenceId": plan.get("referenceId", ""),
        "referenceIds": plan.get("referenceIds", []),
        "url": plan.get("url", ""),
        "urls": urls,
        "adaptedAt": adapted_at,
        "totalElements": len(elements),
        "elements": elements,
        "note": "Implementation specification only; no target source files are modified by this script.",
    }

    evidence_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2) + "\n"
    (evidence_dir / "reference-adapt.json").write_text(payload, encoding="utf-8")
    reference_id = plan.get("referenceId") or "latest"
    (evidence_dir / f"reference-adapt-{reference_id}.json").write_text(payload, encoding="utf-8")

    lines = [
        f"## References: {', '.join(urls)}",
        f"- Reference ID(s): {', '.join(plan.get('referenceIds') or [reference_id])}",
        f"- Adapted: {adapted_at}",
        f"- Selected elements: {len(elements)}",
        "",
        "This is an implementation brief, not generated application code. Implement each element in the existing project's framework, component conventions, design tokens, and responsive layout.",
        "",
    ]
    for element in elements:
        lines.extend([
            f"### {element['elementType'].title()} — {element['elementId']}",
            f"- Reference URL: {element['referenceUrl']}",
            f"- Destination: {element['destination']}",
            f"- Target selector: {element['targetSelector'] or 'to be recorded after implementation'}",
            f"- Reference selector: {element['referenceSelector']}",
            f"- Aspects: {element['aspects']}",
            f"- Reference text sample: {str(element['text'])[:160]}",
            f"- Reference screenshot: {element['screenshotFile'] or 'not captured'}",
            "- Measured source styles:",
        ])
        if element["cssDeclarations"]:
            for declaration in element["cssDeclarations"]:
                lines.append(f"  - {declaration['property']}: {declaration['value']}")
        else:
            lines.append("  - No supported computed style values were captured.")
        lines.append("- Implementation notes: preserve target semantics, responsiveness, accessibility, and existing component contracts; adapt only the requested aspects.")
        lines.append("")

    upsert_section(
        ufme_dir / "REFERENCE_IMPLEMENTATION.md",
        f"<!-- ufmw-reference:{reference_id} -->",
        "\n".join(lines),
    )
    print(f"[reference-adapt] Prepared {len(elements)} implementation brief(s) from {len(urls)} reference(s)")
    print(f"[reference-adapt] Evidence: {evidence_dir / 'reference-adapt.json'}")
    print(f"[reference-adapt] Brief: {ufme_dir / 'REFERENCE_IMPLEMENTATION.md'}")
    return 0


def main():
    evidence_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else EVIDENCE
    sys.exit(adapt(evidence_dir))


if __name__ == "__main__":
    main()
