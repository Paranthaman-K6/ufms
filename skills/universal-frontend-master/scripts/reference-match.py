#!/usr/bin/env python3
"""Validate selected reference mappings across one or more reference URLs."""

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
        print(f"[reference-match] Cannot read {path}: {exc}", file=sys.stderr)
        return None


def is_placeholder(value):
    text = str(value or "").strip().lower()
    cleaned = text.replace("*", "").replace("_", "").replace(chr(96), "").strip()
    return not cleaned or any(token in cleaned for token in (
        "user to specify", "to be specified", "todo", "tbd", "pending",
        "not set", "choose", "select an element"
    ))


def parse_value(value):
    value = value.strip()
    tick = chr(96)
    if len(value) >= 2 and value[0] == tick and value[-1] == tick:
        return value[1:-1].strip()
    return value.strip()


def parse_element_map(content):
    entries = []
    current = None
    fields = {
        "element type": "elementType",
        "reference selector": "referenceSelector",
        "target selector": "targetSelector",
        "destination": "destination",
        "aspects": "aspects",
        "status": "status",
    }
    for line in content.splitlines():
        text = line.strip()
        if text.startswith("#### Element ID:"):
            if current:
                entries.append(current)
            current = {
                "elementId": parse_value(text.partition(":")[2]),
                "elementType": "",
                "referenceSelector": "",
                "targetSelector": "",
                "destination": "",
                "aspects": "",
                "status": "pending",
            }
        elif current and text.startswith("- **"):
            label, separator, value = text[4:].partition("**:")
            key = fields.get(label.strip().lower()) if separator else None
            if key:
                current[key] = parse_value(value)
        elif current and text.startswith("- Element ID:"):
            current["elementId"] = parse_value(text.partition(":")[2])
        elif text.startswith("<!-- /ufmw-reference:"):
            if current:
                entries.append(current)
                current = None
    if current:
        entries.append(current)

    unique = {}
    for entry in entries:
        if entry.get("elementId"):
            unique[entry["elementId"]] = entry
    return list(unique.values())


def load_analyses(evidence_dir, source_name=None):
    if source_name:
        paths = [evidence_dir / source_name]
    else:
        paths = sorted(evidence_dir.glob("reference-analysis-*.json"))
        if not paths:
            paths = [evidence_dir / "reference-analysis.json"]

    analyses = {}
    for path in paths:
        data = read_json(path)
        if not isinstance(data, dict):
            continue
        reference_id = data.get("referenceId")
        if reference_id and isinstance(data.get("elements"), list):
            analyses[reference_id] = data
    return analyses


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


def match(evidence_dir=EVIDENCE, ufme_dir=UFME, source_name=None):
    analyses = load_analyses(evidence_dir, source_name)
    if not analyses:
        print(f"[reference-match] No valid reference-analysis evidence in {evidence_dir}", file=sys.stderr)
        return 1

    map_path = ufme_dir / "ELEMENT_MAP.md"
    if not map_path.is_file():
        print(f"[reference-match] Missing {map_path}", file=sys.stderr)
        return 1

    source_by_id = {}
    for reference_id, analysis in analyses.items():
        for index, source in enumerate(analysis["elements"]):
            element_type = str(source.get("elementType") or "unknown")
            element_id = f"{reference_id}:{element_type}:{int(source.get('index', index))}"
            source_by_id[element_id] = (reference_id, source)

    mapped = parse_element_map(map_path.read_text(encoding="utf-8"))
    plan_elements = []
    for item in mapped:
        destination = item.get("destination", "")
        aspects = item.get("aspects", "")
        if is_placeholder(destination) and is_placeholder(aspects):
            continue

        element_id = item.get("elementId", "")
        source_entry = source_by_id.get(element_id)
        reference_id, source = source_entry if source_entry else ("", {})
        reference_url = analyses.get(reference_id, {}).get("url", "")
        reference_selector = item.get("referenceSelector", "")
        valid = (
            source_entry is not None
            and not is_placeholder(destination)
            and not is_placeholder(aspects)
            and not is_placeholder(reference_selector)
        )
        target_selector = item.get("targetSelector", "")
        plan_elements.append({
            "elementId": element_id,
            "referenceId": reference_id,
            "referenceUrl": reference_url,
            "elementType": item.get("elementType") or source.get("elementType", "unknown"),
            "referenceSelector": reference_selector,
            "targetSelector": "" if is_placeholder(target_selector) else target_selector,
            "destination": destination,
            "aspects": aspects,
            "text": source.get("textContent", ""),
            "tagName": source.get("tagName", ""),
            "className": source.get("className", ""),
            "sourceStyles": source.get("styles", {}),
            "screenshotFile": source.get("screenshotFile", ""),
            "status": "matched" if valid else "pending",
            "verificationReady": valid and not is_placeholder(target_selector),
            "reason": "" if valid else (
                "source element not found in inspection evidence" if source_entry is None
                else "destination, aspects, and reference selector must be supplied"
            ),
        })

    matched_count = sum(item["status"] == "matched" for item in plan_elements)
    ready_count = sum(item["verificationReady"] for item in plan_elements)
    reference_ids = sorted({item["referenceId"] for item in plan_elements if item["referenceId"]})
    urls = sorted({analyses[item]["url"] for item in reference_ids if analyses[item].get("url")})
    single_reference = len(reference_ids) == 1
    plan = {
        "referenceId": reference_ids[0] if single_reference else "multiple",
        "referenceIds": reference_ids,
        "url": urls[0] if len(urls) == 1 else "",
        "urls": urls,
        "matchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "MATCHED" if plan_elements and matched_count == len(plan_elements) else "PENDING",
        "totalElements": len(plan_elements),
        "matchedElements": matched_count,
        "pendingElements": len(plan_elements) - matched_count,
        "verificationReady": ready_count == len(plan_elements) and bool(plan_elements),
        "verificationReadyElements": ready_count,
        "elements": plan_elements,
    }

    evidence_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(plan, indent=2) + "\n"
    (evidence_dir / "reference-match.json").write_text(payload, encoding="utf-8")

    for reference_id in reference_ids:
        subset = dict(plan)
        subset["referenceId"] = reference_id
        subset["referenceIds"] = [reference_id]
        subset["url"] = analyses[reference_id].get("url", "")
        subset["urls"] = [subset["url"]] if subset["url"] else []
        subset["elements"] = [item for item in plan_elements if item["referenceId"] == reference_id]
        subset["totalElements"] = len(subset["elements"])
        subset["matchedElements"] = sum(item["status"] == "matched" for item in subset["elements"])
        subset["pendingElements"] = subset["totalElements"] - subset["matchedElements"]
        subset["status"] = "MATCHED" if subset["totalElements"] and subset["matchedElements"] == subset["totalElements"] else "PENDING"
        subset["verificationReady"] = all(item["verificationReady"] for item in subset["elements"])
        (evidence_dir / f"reference-match-{reference_id}.json").write_text(
            json.dumps(subset, indent=2) + "\n", encoding="utf-8"
        )

        ref_lines = [
            f"## Reference: {subset['url']}",
            f"- Reference ID: {reference_id}",
            f"- Match status: {subset['status']}",
            f"- Matched selected elements: {subset['matchedElements']}/{subset['totalElements']}",
            "",
        ]
        for element in subset["elements"]:
            ref_lines.extend([
                f"### {element['elementId'] or 'Unidentified element'}",
                f"- Reference selector: {element['referenceSelector'] or 'pending'}",
                f"- Target selector: {element['targetSelector'] or 'pending'}",
                f"- Destination: {element['destination'] or 'pending'}",
                f"- Aspects: {element['aspects'] or 'pending'}",
                f"- Status: {element['status']}",
                f"- Reason: {element['reason']}",
                "",
            ])
        upsert_section(
            ufme_dir / "DESIGN_ADAPTATIONS.md",
            f"<!-- ufmw-reference:{reference_id} -->",
            "\n".join(ref_lines),
        )

    print(f"[reference-match] Matched {matched_count}/{len(plan_elements)} selected elements across {len(reference_ids)} reference(s)")
    print(f"[reference-match] Match plan: {evidence_dir / 'reference-match.json'}")
    if not plan_elements:
        print("[reference-match] No elements selected. Set Destination and Aspects for at least one element.", file=sys.stderr)
        return 1
    if matched_count != len(plan_elements):
        print("[reference-match] One or more selected mappings are invalid.", file=sys.stderr)
        return 1
    return 0


def main():
    evidence_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else EVIDENCE
    source_name = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(match(evidence_dir, UFME, source_name))


if __name__ == "__main__":
    main()
