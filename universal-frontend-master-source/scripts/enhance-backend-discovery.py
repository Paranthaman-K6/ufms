#!/usr/bin/env python3
"""
enhance-backend-discovery.py — parse backend contracts into BACKEND_CONTRACTS.md.

Detects OpenAPI/Swagger (JSON or YAML), Postman, GraphQL, AsyncAPI, plus
WebSocket/SSE/auth hints in source. Classifies each capability as CONFIRMED,
INFERRED, UNKNOWN, NOT_FOUND, or NOT_APPLICABLE, with an evidence source.

Writes .ufme/BACKEND_CONTRACTS.md only. No jq or PyYAML install is required:
YAML is parsed when PyYAML is present, otherwise reported as unparsed.

Safety: read-only analysis.
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UFME = ROOT / ".ufme"
OUT = UFME / "BACKEND_CONTRACTS.md"

SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "vendor"}
CODE_EXT = {".js", ".ts", ".jsx", ".tsx", ".py", ".go", ".java", ".rb", ".php"}
WS_RE = re.compile(r"new WebSocket|ws://|wss://|io\.connect|socket\.io")
SSE_RE = re.compile(r"EventSource|text/event-stream")
AUTH_RE = re.compile(r"authorization|bearer|jwt|oauth|api.?key", re.I)


def log(msg):
    print(f"[enhance-backend-discovery] {msg}")


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def load_yaml(path):
    try:
        import yaml  # optional
    except ImportError:
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def spec_methods(spec):
    paths = spec.get("paths") or {}
    methods = []
    for path, ops in paths.items():
        if isinstance(ops, dict):
            for verb in ops:
                if str(verb).lower() in {"get", "post", "put", "patch", "delete", "head", "options"}:
                    methods.append(f"{verb.upper()} {path}")
    return list(paths), methods


def source_hits(pattern):
    hits = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            path = Path(dirpath) / name
            if path.suffix.lower() not in CODE_EXT:
                continue
            try:
                if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                    hits.append(str(path.relative_to(ROOT)))
                    if len(hits) >= 5:
                        return hits
            except OSError:
                continue
    return hits


def main():
    UFME.mkdir(parents=True, exist_ok=True)
    rows = []
    found = False

    for name in ("openapi.json", "swagger.json"):
        path = ROOT / name
        if not path.exists():
            continue
        found = True
        spec = load_json(path)
        if spec is None:
            rows.append((name, "REST", "CONFIRMED", name, "JSON could not be parsed"))
            continue
        paths, methods = spec_methods(spec)
        auth = spec.get("security") or (spec.get("components") or {}).get("securitySchemes") or "none"
        if isinstance(auth, dict):
            auth = ", ".join(auth) or "none"
        rows.append(
            ("OpenAPI/Swagger", "REST", "CONFIRMED", name,
             f"methods: {', '.join(methods)} | paths: {', '.join(paths)} | auth: {auth}")
        )

    for name in ("openapi.yaml", "openapi.yml", "swagger.yaml", "swagger.yml"):
        path = ROOT / name
        if not path.exists():
            continue
        found = True
        spec = load_yaml(path)
        if spec is None:
            rows.append(("OpenAPI/Swagger YAML", "REST", "CONFIRMED", name,
                         "YAML could not be parsed (install PyYAML)"))
            continue
        paths, methods = spec_methods(spec)
        rows.append(("OpenAPI/Swagger YAML", "REST", "CONFIRMED", name,
                     f"methods: {', '.join(methods)} | paths: {', '.join(paths)}"))

    for name in ("postman.json", "postman_collection.json"):
        path = ROOT / name
        if not path.exists():
            continue
        found = True
        spec = load_json(path)
        items = []
        if isinstance(spec, dict):
            for item in (spec.get("item") or [])[:20]:
                req = item.get("request") or {}
                url = req.get("url") or {}
                raw = url.get("raw") if isinstance(url, dict) else url
                items.append(f"{req.get('method', '')} {raw or ''}".strip())
        rows.append(("Postman", "REST", "CONFIRMED", name,
                     f"requests: {', '.join(items) if items else 'none parsed'}"))

    for name in ("schema.graphql", "schema.gql"):
        path = ROOT / name
        if not path.exists():
            continue
        found = True
        text = path.read_text(encoding="utf-8", errors="ignore")
        rows.append((
            "GraphQL", "GraphQL", "CONFIRMED", name,
            f"types: {len(re.findall(r'^(?:type|input|enum|interface|union) ', text, re.M))} | "
            f"queries: {len(re.findall(r'^\s*query ', text, re.M))} | "
            f"mutations: {len(re.findall(r'^\s*mutation ', text, re.M))}",
        ))

    for name in ("asyncapi.json", "asyncapi.yaml", "asyncapi.yml"):
        path = ROOT / name
        if not path.exists():
            continue
        found = True
        spec = load_json(path) if path.suffix == ".json" else load_yaml(path)
        channels = list((spec or {}).get("channels") or {}) if isinstance(spec, dict) else []
        label = "AsyncAPI" if path.suffix != ".json" else "AsyncJSON"
        rows.append((label, "AsyncAPI", "CONFIRMED", name,
                     f"channels: {', '.join(channels) if channels else 'none parsed'}"))

    for label, kind, pattern, detail in (
        ("WebSocket", "WebSocket", WS_RE, "Source references detected; verify manually"),
        ("SSE", "SSE", SSE_RE, "Source references detected; verify manually"),
        ("Authentication", "Auth", AUTH_RE, "Auth references detected; verify manually"),
    ):
        hits = source_hits(pattern)
        if hits:
            found = True
            rows.append((label, kind, "INFERRED", ", ".join(hits), detail))
        else:
            rows.append((label, kind, "NOT_FOUND", "—", f"No {label.lower()} references in source"))

    if not found:
        rows.append(("None", "—", "NOT_FOUND", "—", "No backend contract files detected"))

    lines = [
        "# Backend Contracts",
        f"Generated: {__import__('datetime').datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "| Capability | Type | Classification | Evidence | Details |",
        "|------------|------|----------------|----------|---------|",
    ]
    lines += [f"| {a} | {b} | {c} | {d} | {e} |" for a, b, c, d, e in rows]
    lines += [
        "",
        "## Classification scale",
        "| Classification | Meaning |",
        "|----------------|---------|",
        "| CONFIRMED | Verified in contract file with evidence |",
        "| INFERRED | Strongly suggested but not directly evidenced |",
        "| UNKNOWN | Mentioned but details not available |",
        "| NOT_FOUND | Not present |",
        "| NOT_APPLICABLE | Not relevant to this frontend |",
        "",
        "## Contract verification rule",
        "Frontend API clients are generated ONLY from capabilities classified CONFIRMED.",
        "Never invent endpoints, fields, permissions, or response structures.",
    ]

    fd, tmp = tempfile.mkstemp(dir=str(UFME), prefix=".backend-contracts.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        os.replace(tmp, OUT)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

    log(f"Backend contracts written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
