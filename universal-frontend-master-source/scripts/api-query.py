#!/usr/bin/env python3
"""api-query.py — slice .ufme/BACKEND_CONTRACTS.md by tag, path, or method.

todo 4.9: return only the matching endpoints instead of the whole backend map.
Handles markdown tables (Method|Path|..., plus generic columns such as
Capability|Type|Classification) and ## sections.

Semantics (all matching is case-insensitive substring):
- --tag    matches a ## section heading, or the first column of a table
           (Tag/Capability/Name/Endpoint/Feature), when that column exists.
- --path   matches the Path/Endpoint/Route column (falls back to any cell
           that looks like a path).
- --method matches the Method column (GET/POST/PUT/PATCH/DELETE/WS/SSE/...).

A section is emitted only when at least one of its table rows matches; the
output keeps the section heading, the table header + separator, and just the
matching rows. --json emits {file, count, matches:[{section, columns, cells}]}.

Usage:
  python3 api-query.py [--file .ufme/BACKEND_CONTRACTS.md]
      [--tag auth] [--path /users] [--method GET] [--json]

Exit codes: 0 = handled (matches / no matches with count+hint / file missing
with an empty-marked note). 1 = usage or read error.

Pure python3, no dependencies.
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_FILE = ".ufme/BACKEND_CONTRACTS.md"

METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD",
           "OPTIONS", "CONNECT", "WS", "SSE")

TAG_COLUMNS = ("tag", "capability", "endpoint", "name", "feature")
PATH_COLUMNS = ("path", "endpoint", "route")
METHOD_COLUMNS = ("method", "verb")


def parse_args():
    p = argparse.ArgumentParser(
        description="Slice BACKEND_CONTRACTS.md by tag, path, or method.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--file", default=DEFAULT_FILE,
                   help="Markdown map to slice (default: .ufme/BACKEND_CONTRACTS.md)")
    p.add_argument("--tag", default=None,
                   help="Section heading or first-column substring match")
    p.add_argument("--path", default=None,
                   help="Path-column substring match")
    p.add_argument("--method", default=None,
                   help="Method-column substring match")
    p.add_argument("--json", dest="as_json", action="store_true",
                   help="Emit structured JSON instead of markdown")
    return p.parse_args()


def split_row(line):
    """Split a markdown table row into cells, trimming outer pipes."""
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [cell.strip() for cell in inner.split("|")]


def is_separator_row(cells):
    """True when a table row is the |---|---| separator."""
    filled = [c for c in cells if c]
    if not filled:
        return False
    return all(set(c) <= set("-:") and c.count("-") >= 2 for c in filled)


def lower(text):
    return (text or "").lower()


def column_index(header_cells, name):
    """0-based index of a column by lowercase name, or None."""
    indices = {lower(c): i for i, c in enumerate(header_cells)}
    return indices.get(name)


def first_column_index(header_cells, names):
    for name in names:
        idx = column_index(header_cells, name)
        if idx is not None:
            return idx
    return None


def row_filters_ok(header_cells, data, args, heading_match_tag):
    """True when the row passes every filter the user provided."""
    if args.tag is not None and not heading_match_tag:
        tag_i = first_column_index(header_cells, TAG_COLUMNS)
        if tag_i is None:
            return False
        if len(data) <= tag_i:
            return False
        if args.tag.lower() not in lower(data[tag_i]):
            return False

    path_i = first_column_index(header_cells, PATH_COLUMNS)
    if path_i is None:
        path_i = next((i for i, c in enumerate(data)
                       if c.startswith("/") or ("/" in c and " " not in c)),
                      None)
    if args.path is not None:
        if path_i is None or len(data) <= path_i:
            return False
        if args.path.lower() not in lower(data[path_i]):
            return False

    method_i = first_column_index(header_cells, METHOD_COLUMNS)
    if method_i is None:
        method_i = next((i for i, c in enumerate(data)
                         if c.upper() in METHODS), None)
    if args.method is not None:
        if method_i is None or len(data) <= method_i:
            return False
        if args.method.lower() not in lower(data[method_i]):
            return False
    return True


def parse_blocks(text):
    """Split markdown into sections: [(name, heading_line|None, blocks)].

    blocks are ('para', line) or ('table', header_cells, header_display,
    separator_display, [(display, cells), ...]).
    Prologue (before any heading) is section '(top)' with heading_line None.
    """
    sections = [{"name": "(top)", "heading": None, "blocks": []}]

    def close_table(blocks, pending):
        if not pending["header"]:
            return
        blocks.append(("table", pending["header"], pending["header_display"],
                       pending["separator"], pending["rows"]))
        pending["header"] = None
        pending["rows"] = []
        pending["header_display"] = None
        pending["separator"] = None

    pending = {"header": None, "rows": [], "header_display": None,
               "separator": None}
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped.startswith("#"):
            close_table(sections[-1]["blocks"], pending)
            name = stripped.lstrip("#").strip() or "(top)"
            sections.append({"name": name, "heading": line, "blocks": []})
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = split_row(stripped)
            if pending["header"] is None:
                if is_separator_row(cells):
                    continue
                pending["header"] = cells
                pending["header_display"] = stripped
                continue
            if is_separator_row(cells):
                pending["separator"] = stripped
                continue
            pending["rows"].append((stripped, cells))
            continue
        # non-table line ends any open table
        close_table(sections[-1]["blocks"], pending)
        if stripped:
            sections[-1]["blocks"].append(("para", line))
            continue
    close_table(sections[-1]["blocks"], pending)
    return sections


def query_document(text, args):
    """Filter parsed sections; return (markdown_blob, match_rows)."""
    sections = parse_blocks(text)
    out_lines = []
    rows = []
    for section in sections:
        heading_match_tag = tags_match_heading(args, section["name"])
        matched_table_rows = []
        for block in section["blocks"]:
            if block[0] != "table":
                continue
            _, header_cells, header_display, separator_display, data = block
            for display, cells in data:
                if row_filters_ok(header_cells, cells, args,
                                  args.tag is None or heading_match_tag):
                    matched_table_rows.append(
                        (header_cells, header_display, separator_display,
                         display, cells))
        if not matched_table_rows:
            continue
        rendered = []
        last_header = None
        for header_cells, header_display, separator_display, display, cells \
                in matched_table_rows:
            if last_header != header_display:
                if section["heading"]:
                    rendered.append(section["heading"])
                rendered.append(header_display)
                rendered.append(separator_display)
                last_header = header_display
            rendered.append(display)
            rows.append({"section": section["name"],
                         "columns": list(header_cells), "cells": list(cells)})
        if out_lines:
            out_lines.append("")
        out_lines.extend(rendered)
    blob = "\n".join(out_lines)
    if blob:
        blob += "\n"
    return blob, rows


def tags_match_heading(args, heading):
    if args.tag is None:
        return True
    return args.tag.lower() in lower(heading)


def main():
    args = parse_args()
    if args.tag is None and args.path is None and args.method is None:
        sys.stderr.write(
            "[api-query] ERROR: give at least one of --tag, --path, --method\n")
        return 1
    fpath = Path(args.file)
    if not fpath.is_file():
        print(f"[api-query] NOTE: empty-marked — no backend map at {fpath}. "
              "Run scripts/enhance-backend-discovery.py to generate "
              "BACKEND_CONTRACTS.md, or pass --file <path>.")
        return 0
    try:
        text = fpath.read_text(encoding="utf-8")
    except OSError as exc:
        sys.stderr.write(f"[api-query] ERROR: cannot read {fpath}: {exc}\n")
        return 1
    blob, rows = query_document(text, args)
    if args.as_json:
        print(json.dumps({"file": str(fpath), "count": len(rows),
                          "matches": rows}, indent=2, ensure_ascii=False))
        return 0
    if not rows:
        filters = []
        for key in ("tag", "path", "method"):
            value = getattr(args, key)
            if value:
                filters.append(f"{key}='{value}'")
        print(f"[api-query] {len(rows)} matches for "
              + ", ".join(filters) + f" in {fpath}")
        print("Hint: list sections with `grep '^##' " + str(fpath)
              + "`, or match the first column, e.g. --tag WebSocket "
              "(filters match the Capability/Tag column or a ## heading).")
        return 0
    print(blob)
    return 0


if __name__ == "__main__":
    sys.exit(main())
