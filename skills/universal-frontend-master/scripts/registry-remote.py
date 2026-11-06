#!/usr/bin/env python3
"""registry-remote.py — client for the optional UFME MCP library-registry server.

Environment:
    UFME_REGISTRY_URL   full MCP endpoint, e.g. https://your-app.vercel.app/mcp
    UFME_REGISTRY_KEY   matches the server's REGISTRY_API_KEY

Exit codes: 0 ok, 1 request/tool error, 3 not configured.

Usage:
    registry-remote.py --list [QUERY] [--category C] [--status S] [--limit N] [--json]
    registry-remote.py --get NAME [--json]
    registry-remote.py --upsert FILE|-        # JSON object, '-' reads stdin
    registry-remote.py --remove NAME
    registry-remote.py --approve NAME
    registry-remote.py --seed                 # upsert registry-server/seed.json
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SEED = ROOT / "registry-server" / "seed.json"


class NotConfigured(Exception):
    pass


def endpoint():
    url = os.environ.get("UFME_REGISTRY_URL", "").strip()
    key = os.environ.get("UFME_REGISTRY_KEY", "").strip()
    if not url or not key:
        raise NotConfigured("set UFME_REGISTRY_URL and UFME_REGISTRY_KEY")
    return url, key


def rpc(method, params=None):
    url, key = endpoint()
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})
    request = urllib.request.Request(
        url,
        data=payload.encode("utf-8"),
        headers={
            "content-type": "application/json",
            "authorization": f"Bearer {key}",
            "accept": "application/json, text/event-stream",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}: {exc.reason}") from exc
    except (urllib.error.URLError, OSError) as exc:
        raise RuntimeError(f"request failed: {exc}") from exc
    if "error" in body:
        raise RuntimeError(body["error"].get("message", "JSON-RPC error"))
    return body.get("result", {})


def call_tool(name, arguments):
    result = rpc("tools/call", {"name": name, "arguments": arguments})
    text = (result.get("content") or [{}])[0].get("text", "")
    if result.get("isError"):
        raise RuntimeError(text or f"{name} failed")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def print_json(value):
    print(json.dumps(value, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description="UFME library-registry MCP client")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--list", nargs="?", const="", metavar="QUERY")
    action.add_argument("--get", metavar="NAME")
    action.add_argument("--upsert", metavar="FILE")
    action.add_argument("--remove", metavar="NAME")
    action.add_argument("--approve", metavar="NAME")
    action.add_argument("--seed", action="store_true")
    parser.add_argument("--category")
    parser.add_argument("--status")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    try:
        if args.list is not None:
            arguments = {}
            if args.list:
                arguments["query"] = args.list
            if args.category:
                arguments["category"] = args.category
            if args.status:
                arguments["status"] = args.status
            if args.limit:
                arguments["limit"] = args.limit
            entries = call_tool("registry_list", arguments)
            if args.json:
                print_json(entries)
            else:
                for entry in entries:
                    print(f"{entry['name']}\t{entry.get('category','')}\t{entry.get('license','')}\t{entry.get('status','')}")
            return 0

        if args.get:
            entry = call_tool("registry_get", {"name": args.get})
            print_json(entry) if args.json else print(json.dumps(entry, indent=2))
            return 0

        if args.upsert:
            raw = sys.stdin.read() if args.upsert == "-" else Path(args.upsert).read_text(encoding="utf-8")
            result = call_tool("registry_upsert", json.loads(raw))
            print_json(result) if args.json else print(f"{'created' if result['created'] else 'updated'}: {result['entry']['name']}")
            return 0

        if args.remove:
            result = call_tool("registry_remove", {"name": args.remove})
            print_json(result) if args.json else print(f"removed: {result['removed']}")
            return 0

        if args.approve:
            entry = call_tool("registry_get", {"name": args.approve})
            entry["status"] = "approved"
            approved = call_tool("registry_upsert", entry)
            print_json(approved) if args.json else print(f"approved: {approved['entry']['name']}")
            return 0

        if args.seed:
            entries = json.loads(SEED.read_text(encoding="utf-8"))
            for entry in entries:
                call_tool("registry_upsert", entry)
            print(f"seeded {len(entries)} entries")
            return 0
    except NotConfigured as exc:
        print(f"registry-remote: {exc}", file=sys.stderr)
        return 3
    except (RuntimeError, OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"registry-remote: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
