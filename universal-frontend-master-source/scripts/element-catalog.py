#!/usr/bin/env python3
"""
element-catalog.py — Maintain a persistent catalog of reference elements
across sessions so previously analyzed references don't need re-discovery.

Reads/writes .ufme/ELEMENT_CATALOG.json

Usage:
  python3 universal-frontend-master-source/scripts/element-catalog.py [add|list|show|clear] [refId]
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UFME = ROOT / ".ufme"
EVIDENCE = Path(os.environ.get("UFME_EVIDENCE_DIR") or (UFME / "evidence"))
CATALOG_FILE = UFME / "ELEMENT_CATALOG.json"


def load_catalog():
    if CATALOG_FILE.exists():
        return json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
    return {"elements": [], "createdAt": datetime.now(timezone.utc).isoformat()}


def save_catalog(catalog):
    UFME.mkdir(parents=True, exist_ok=True)
    CATALOG_FILE.write_text(json.dumps(catalog, indent=2), encoding="utf-8")


def add_element(catalog, ref_url, element_type, selector, destination, aspects, text=""):
    element = {
        "id": str(uuid.uuid4())[:8],
        "refUrl": ref_url,
        "elementType": element_type,
        "selector": selector,
        "text": text[:200],
        "destination": destination,
        "aspects": aspects,
        "addedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "cataloged",
    }
    catalog["elements"].append(element)
    save_catalog(catalog)
    return element


def list_elements(catalog):
    if not catalog["elements"]:
        print("[element-catalog] No elements in catalog.")
        return
    print(f"[element-catalog] {len(catalog['elements'])} element(s):")
    print()
    for el in catalog["elements"]:
        print(f"  {el['id']} | {el['elementType']} | {el['destination']} | {el['refUrl']}")
        print(f"    Selector: {el['selector']}")
        print(f"    Text: {el['text'][:80]}")
        print(f"    Aspects: {el['aspects']}")
        print(f"    Added: {el['addedAt']}")
        print()


def show_element(catalog, ref_id):
    for el in catalog["elements"]:
        if el["id"] == ref_id:
            print(json.dumps(el, indent=2))
            return
    print(f"[element-catalog] Element {ref_id} not found.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 element-catalog.py [add|list|show|clear] [refId]")
        return 1

    command = sys.argv[1]
    catalog = load_catalog()

    if command == "list":
        list_elements(catalog)
    elif command == "show":
        if len(sys.argv) < 3:
            print("Usage: python3 element-catalog.py show <refId>")
            return 1
        show_element(catalog, sys.argv[2])
    elif command == "add":
        if len(sys.argv) < 7:
            print("Usage: python3 element-catalog.py add <refUrl> <elementType> <selector> <destination> <aspects> [text]")
            return 1
        element = add_element(
            catalog,
            sys.argv[2],  # refUrl
            sys.argv[3],  # elementType
            sys.argv[4],  # selector
            sys.argv[5],  # destination
            sys.argv[6],  # aspects
            sys.argv[7] if len(sys.argv) > 7 else "",  # text
        )
        print(f"[element-catalog] Added element {element['id']}: {element['elementType']} -> {element['destination']}")
    elif command == "clear":
        catalog["elements"] = []
        save_catalog(catalog)
        print("[element-catalog] Catalog cleared.")
    else:
        print(f"[element-catalog] Unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
