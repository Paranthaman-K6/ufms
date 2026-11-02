#!/usr/bin/env python3
"""
search-libraries.py
Library research tool for UFME agents.

Searches the user-level ~/.config/ufme/LIBRARY_REGISTRY.md first, then the
project .ufme/LIBRARY_REGISTRY.md file, then the npm registry for candidate
frontend libraries. Displays results as a selectable table so
agents can choose which libraries to approve for the project.

Usage:
    python3 universal-frontend-master-source/scripts/search-libraries.py <search term> [search term ...]
    python3 universal-frontend-master-source/scripts/search-libraries.py --select <package-name>
    python3 universal-frontend-master-source/scripts/search-libraries.py --approve <package-name>
    python3 universal-frontend-master-source/scripts/search-libraries.py --list
    python3 universal-frontend-master-source/scripts/search-libraries.py --chosen
    python3 universal-frontend-master-source/scripts/search-libraries.py --category <category>

Categories: ui, icons, animation, charts, forms, state, routing, tables, css

Safety: project-local only; reads npm registry and local files;
never sudo/pacman/systemctl.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from typing import List, Tuple, Optional

def find_project_root():
    """Walk up the directory tree to find the project root (marked by .ufme directory or opencode.json)."""
    current = os.path.abspath(os.path.dirname(__file__))
    while True:
        if os.path.exists(os.path.join(current, '.ufme')) or os.path.exists(os.path.join(current, 'opencode.json')):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    # Fallback to a safe default relative to script location
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

ROOT_DIR = find_project_root()
UFME_DIR = os.path.join(ROOT_DIR, ".ufme")
REGISTRY_OUT = os.path.join(UFME_DIR, "LIBRARY_REGISTRY.md")
# User-level registry shared by every project (seeded by install.sh).
GLOBAL_REGISTRY = os.path.join(
    os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"),
    "ufme",
    "LIBRARY_REGISTRY.md",
)
SEARCH_RESULTS = os.path.join(UFME_DIR, "library-search-results.md")
CHOSEN_FILE = os.path.join(UFME_DIR, "library-chosen.md")
DECISIONS = os.path.join(UFME_DIR, "DECISIONS.md")

os.makedirs(UFME_DIR, exist_ok=True)

def log(msg: str) -> None:
    print(f"[search-libraries] {msg}")

def init_registry() -> None:
    """Initialize the library registry file if it doesn't exist."""
    if not os.path.exists(REGISTRY_OUT):
        header = """# Library Research Registry
Registry of frontend libraries, UI component systems, icons, fonts, image sources,
animation tools, charts, templates, hosted developer services, and browser utilities
considered by UFME. Entries are research candidates, not automatic install approvals.
The researcher agent verifies exact version, framework compatibility, package provenance,
license text, maintenance status, and project fit before recommending installation.
Approved decisions belong in .ufme/DECISIONS.md.

**Status meanings:** candidate = potential option; researched = official documentation/source checked;
approved = explicitly selected for a project; rejected = not suitable for the stated context.
A registry entry does not mean the dependency is installed or tested.

| Name | Category | Official repo / site | License / terms | Commercial use | Install / use | Reason for selection | Status |
|------|----------|---------------------|-----------------|----------------|---------------|---------------------|--------|
"""
        with open(REGISTRY_OUT, "w", encoding="utf-8") as f:
            f.write(header)

def categorize(name: str, desc: str) -> str:
    """Categorize a package based on its name and description."""
    lc = f"{name} {desc}".lower()
    if re.search(r"icon|icon-set|phosphor|lucide|hero", lc):
        return "Icons"
    if re.search(r"chart|graph|rechart|plot", lc):
        return "Charts"
    if re.search(r"anim|motion|framer|gsap|transition", lc):
        return "Animation"
    if re.search(r"font|typograph|google-font|inter", lc):
        return "Fonts"
    if re.search(r"ui|component|component-library|mant|shadcn|headless|radix|base-ui|ark", lc):
        return "UI Components"
    if re.search(r"form|hook-form|validat|zod", lc):
        return "Forms"
    if re.search(r"state|zustand|redux|recoil|jotai|context", lc):
        return "State Management"
    if re.search(r"router|routing", lc):
        return "Routing"
    if re.search(r"table|grid|ag-grid|tanstack", lc):
        return "Tables"
    if re.search(r"css|tailwind|style|styled|bootstrap", lc):
        return "CSS Framework"
    return "Utility"

def fetch_pkg_metadata(pkg: str) -> Optional[dict]:
    """Fetch metadata for an npm package (only used for --select/--approve)."""
    url = f"https://registry.npmjs.org/{pkg}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "UFME-Library-Search/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    license_val = data.get("license")
    if isinstance(license_val, dict):
        lic = license_val.get("type", "UNKNOWN")
    else:
        lic = license_val or "UNKNOWN"

    dist_tags = data.get("dist-tags", {}) or {}
    latest = dist_tags.get("latest", "UNKNOWN")
    homepage = data.get("homepage", "")

    commercial = "Yes" if lic in ("MIT", "ISC", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "0BSD") else "Verify"

    return {
        "name": data.get("name", pkg),
        "desc": (data.get("description") or "")[:60],
        "license": lic,
        "version": latest,
        "homepage": homepage,
        "commercial": commercial,
        "install": f"npm install -D {pkg}",
    }

def search_npm(term: str, size: int = 8) -> List[Tuple[str, str]]:
    """Search npm registry for packages matching a term - fast, no metadata fetch."""
    url = f"https://registry.npmjs.org/-/v1/search?text={urllib.parse.quote(term)}&size={size}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "UFME-Library-Search/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []

    results = []
    for obj in data.get("objects", []):
        pkg = obj.get("package", {})
        name = pkg.get("name", "")
        desc = (pkg.get("description") or "")[:50]
        results.append((name, desc))
    return results

def category_terms(category: str) -> str:
    """Map category names to npm search terms."""
    mapping = {
        "ui": "react-components vue-components svelte-components tailwind-components",
        "icons": "lucide-react phosphor-icons react-icons heroicons",
        "animation": "motion framer-motion gsap animejs",
        "charts": "recharts chart.js chartist",
        "forms": "react-hook-form zod",
        "state": "zustand redux recoil jotai",
        "routing": "react-router vue-router svelte-routing",
        "tables": "react-table tanstack-table ag-grid",
        "css": "tailwindcss bootstrap styled-components",
    }
    return mapping.get(category, category)

def registry_files() -> List[str]:
    """User-level registry first, then the project registry."""
    return [
        p for p in (GLOBAL_REGISTRY, REGISTRY_OUT)
        if os.path.exists(p) and os.path.getsize(p) > 0
    ]

def search_local_registry(term: str) -> List[dict]:
    """Search the user-level and local LIBRARY_REGISTRY.md files for matching entries."""
    lc_term = term.lower()
    results = []

    for path in registry_files():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.startswith("|") or line.strip().startswith("|---"):
                    continue
                parts = [p.strip() for p in line.strip().strip("|").split("|")]
                if len(parts) < 8:
                    continue
                name = parts[0]
                if name in ("Name", "------"):
                    continue
                combined = " ".join(parts).lower()
                if lc_term in combined:
                    results.append({
                        "name": name,
                        "category": parts[1] if len(parts) > 1 else "",
                        "site": parts[2] if len(parts) > 2 else "",
                        "license": parts[3] if len(parts) > 3 else "",
                        "commercial": parts[4] if len(parts) > 4 else "",
                        "install": parts[5] if len(parts) > 5 else "",
                        "status": parts[7] if len(parts) > 7 else "",
                    })
    return results

def record_package(pkg: str) -> bool:
    """Record a chosen package into the registry."""
    init_registry()
    meta = fetch_pkg_metadata(pkg)
    if not meta:
        log(f"WARN: could not fetch metadata for {pkg}")
        return False

    if os.path.exists(REGISTRY_OUT):
        with open(REGISTRY_OUT, "r", encoding="utf-8") as f:
            if f"| {meta['name']} |" in f.read():
                log(f"Package {meta['name']} already in registry.")
                return True

    cat = categorize(meta["name"], meta["desc"])
    reason = f"Selected via library search: {meta['desc']}"

    with open(REGISTRY_OUT, "a", encoding="utf-8") as f:
        f.write(
            f"| {meta['name']} | {cat} | {meta['homepage']} | "
            f"{meta['license']} | {meta['commercial']} | {meta['install']} | "
            f"{reason} | candidate |\n"
        )
    log(f"Registered: {meta['name']} ({cat}, {meta['license']}, {meta['commercial']} commercial-use)")
    return True

def approve_package(pkg: str) -> bool:
    """Mark a package as approved in registry and DECISIONS.md."""
    init_registry()

    if os.path.exists(REGISTRY_OUT):
        with open(REGISTRY_OUT, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(
            rf"\| {re.escape(pkg)} \| [^|]* \| [^|]* \| [^|]* \| [^|]* \| [^|]* \| candidate \|",
            r"\1approved |",
            content,
        )
        with open(REGISTRY_OUT, "w", encoding="utf-8") as f:
            f.write(content)

    if not os.path.exists(DECISIONS):
        with open(DECISIONS, "w", encoding="utf-8") as f:
            f.write(
                "# Decisions\n\n"
                "| Decision | Name | Repo/site | License | Commercial use | Install method | Reason |\n"
                "|----------|------|-----------|---------|----------------|----------------|--------|\n"
            )

    if os.path.exists(DECISIONS):
        with open(DECISIONS, "r", encoding="utf-8") as f:
            if f"| {pkg} |" in f.read():
                log(f"{pkg} already in DECISIONS.md.")
                return True

    meta = fetch_pkg_metadata(pkg)
    if meta:
        with open(DECISIONS, "a", encoding="utf-8") as f:
            f.write(
                f"| UI library | {meta['name']} | {meta['homepage']} | "
                f"{meta['license']} | {meta['commercial']} | {meta['install']} | "
                f"{meta['desc']} |\n"
            )
    log(f"Approved: {pkg} recorded in .ufme/DECISIONS.md")
    return True

def list_registry() -> None:
    """List user-level registry plus current project registry contents."""
    files = registry_files()
    if not files:
        print("Library registry is empty or not initialized.")
        print("Run: python3 universal-frontend-master-source/scripts/search-libraries.py <search terms> to discover libraries.")
        return
    for path in files:
        print(f"\n=== {path} ===\n")
        with open(path, "r", encoding="utf-8") as f:
            print(f.read())

def show_chosen() -> None:
    """Show chosen libraries for implementation."""
    if not os.path.exists(CHOSEN_FILE) or os.path.getsize(CHOSEN_FILE) == 0:
        print("No libraries chosen for implementation yet.")
        print("Use: python3 universal-frontend-master-source/scripts/search-libraries.py --select <package-name> to choose libraries.")
        return
    print("\n" + "=" * 80 + "\nLIBRARIES CHOSEN FOR IMPLEMENTATION\n" + "=" * 80 + "\n")
    with open(CHOSEN_FILE, "r", encoding="utf-8") as f:
        print(f.read())
    print("\n")

def display_results(results: List[dict], title: str = "LIBRARY SEARCH RESULTS") -> None:
    """Display search results as a table (no per-package metadata fetch - fast)."""
    print("\n" + "=" * 80 + f"\n{title}\n" + "=" * 80 + "\n")
    print("| # | Package | Description | License | Version | Commercial | Install |")
    print("|---|---------|-------------|---------|---------|------------|---------|")
    for idx, r in enumerate(results, 1):
        print(f"| {idx} | {r['name']} | {r['desc']} | {r['license']} | {r['version']} | {r['commercial']} | {r['install']} |")
    print("\nTo select a package for the project registry:\n  python3 universal-frontend-master-source/scripts/search-libraries.py --select <package-name>\n\nTo approve a selected package for implementation:\n  python3 universal-frontend-master-source/scripts/search-libraries.py --approve <package-name>\n\nTo list current registry:\n  python3 universal-frontend-master-source/scripts/search-libraries.py --list\n")

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 universal-frontend-master-source/scripts/search-libraries.py <search term> [search term ...]")
        print("       python3 universal-frontend-master-source/scripts/search-libraries.py --select <package-name>")
        print("       python3 universal-frontend-master-source/scripts/search-libraries.py --approve <package-name>")
        print("       python3 universal-frontend-master-source/scripts/search-libraries.py --list")
        print("       python3 universal-frontend-master-source/scripts/search-libraries.py --chosen")
        print("       python3 universal-frontend-master-source/scripts/search-libraries.py --category <category>")
        return 1

    if sys.argv[1] == "--select":
        init_registry()
        return 0 if record_package(sys.argv[2]) else 1

    if sys.argv[1] == "--approve":
        return 0 if approve_package(sys.argv[2]) else 1

    if sys.argv[1] == "--list":
        init_registry()
        list_registry()
        return 0

    if sys.argv[1] == "--chosen":
        show_chosen()
        return 0

    if sys.argv[1] == "--category":
        terms = category_terms(sys.argv[2])
    else:
        terms = " ".join(sys.argv[1:])

    print("\n" + "=" * 80 + "\nSTEP 1: Searching local library registry\n" + "=" * 80)
    init_registry()

    local_results = []
    for term in terms.split():
        local_results.extend(search_local_registry(term))

    seen = set()
    unique_local = []
    for r in local_results:
        if r["name"] not in seen:
            seen.add(r["name"])
            unique_local.append(r)

    if unique_local:
        print("\n| # | Package | Category | License | Commercial | Install | Status |")
        print("|---|---------|----------|---------|------------|---------|--------|")
        for idx, r in enumerate(unique_local, 1):
            print(f"| {idx} | {r['name']} | {r['category']} | {r['license']} | {r['commercial']} | {r['install']} | {r['status']} |")
    else:
        print("\nNo matches found in local registry.")

    print("\n" + "=" * 80 + "\nSTEP 2: Searching npm registry\n" + "=" * 80)

    npm_results = []
    seen_npm = set()
    for term in terms.split():
        log(f"Searching npm for: {term}")
        for name, desc in search_npm(term):
            if name not in seen_npm:
                seen_npm.add(name)
                npm_results.append({"name": name, "desc": desc, "license": "Check registry", "version": "latest", "commercial": "Verify", "install": f"npm install -D {name}"})

    if not npm_results:
        print(f"\nNo packages found in npm registry for: {terms}")
    else:
        display_results(npm_results)

    print("=" * 80 + "\nNEXT STEPS\n" + "=" * 80 + "\n")
    print("To select a package for the project registry:\n  python3 universal-frontend-master-source/scripts/search-libraries.py --select <package-name>\n\nTo approve a selected package for implementation:\n  python3 universal-frontend-master-source/scripts/search-libraries.py --approve <package-name>\n\nTo view chosen libraries for implementation:\n  python3 universal-frontend-master-source/scripts/search-libraries.py --chosen\n\nTo list current registry:\n  python3 universal-frontend-master-source/scripts/search-libraries.py --list\n")

    log(f"Search complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
