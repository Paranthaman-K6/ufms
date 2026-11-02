#!/usr/bin/env python3
"""
generate-prototype.py
Priority 2 — Design Intelligence: Prototype generation.
Reads .ufme/ project memory files and produces working HTML/CSS prototype pages.
"""

import html
import os
import re
import sys
import time
from typing import List, Tuple, Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UFME_DIR = os.path.join(ROOT_DIR, ".ufme")
OUT_DIR = os.path.join(ROOT_DIR, "prototypes")

# Memory Files
PROJECT_SPEC = os.path.join(UFME_DIR, "PROJECT_SPEC.md")
PRD = os.path.join(UFME_DIR, "PRD.md")
SITEMAP = os.path.join(UFME_DIR, "SITEMAP.md")
DESIGN_SYSTEM = os.path.join(UFME_DIR, "DESIGN_SYSTEM.md")
USER_FLOWS = os.path.join(UFME_DIR, "USER_FLOWS.md")
FEATURES = os.path.join(UFME_DIR, "FEATURES.md")
API_MAP = os.path.join(UFME_DIR, "API_MAP.md")
CHOSEN_LIBS = os.path.join(UFME_DIR, "library-chosen.md")

os.makedirs(OUT_DIR, exist_ok=True)

def log(msg: str) -> None:
    print(f"[generate-prototype] {msg}")

def extract_value(file_path: str, key: str) -> str:
    if not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(rf"#* *{re.escape(key)}.*?\n([^\n]+)", content, re.IGNORECASE)
            if match:
                return match.group(1).strip().lstrip("-* ").strip()
    except Exception:
        pass
    return ""

def extract_token(file_path: str, key: str, default: str) -> str:
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if re.search(key, line, re.IGNORECASE):
                    val = re.sub(r".*[:#]\s*", "", line).strip()
                    if val:
                        return val[:40]
    except Exception:
        pass
    return default

def parse_routes(file_path: str) -> List[str]:
    routes = []
    if not os.path.exists(file_path):
        return routes
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("|") and not any(x in line for x in ["Page | Route", "---|---"]):
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) > 2:
                        route = parts[2]
                        if route and route != "Route":
                            routes.append(route)
    except Exception:
        pass
    return routes

# Precompile regex for slugify to optimize repeated calls
SLUGIFY_REGEX = re.compile(r'[^a-z0-9-]')

def slugify(text: str) -> str:
    result = SLUGIFY_REGEX.sub('', text.lower().replace(' ', '-'))
    return result if result else "index"

def write_css() -> None:
    primary = extract_token(DESIGN_SYSTEM, r"color.*primary", "#2563eb")
    bg = extract_token(DESIGN_SYSTEM, r"color.*bg", "#ffffff")
    text = extract_token(DESIGN_SYSTEM, r"color.*text", "#111827")
    
    # Integrate chosen libraries into CSS if any (e.g., Tailwind CDN)
    lib_imports = ""
    if os.path.exists(CHOSEN_LIBS):
        with open(CHOSEN_LIBS, "r", encoding="utf-8") as f:
            content = f.read()
            if "tailwindcss" in content.lower():
                lib_imports = '<script src="https://cdn.tailwindcss.com"></script>'

    css_content = f"""/* UFME generated prototype stylesheet */
:root {{
  --color-primary: {primary};
  --color-bg: {bg};
  --color-text: {text};
  --font-sans: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  --radius: 8px;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: var(--font-sans);
  color: var(--color-text);
  background: var(--color-bg);
  line-height: 1.5;
  padding: var(--spacing-md);
}}
a {{ color: var(--color-primary); text-decoration: underline; }}
button, .btn {{
  background: var(--color-primary);
  color: #fff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 1rem;
}}
.nav {{ display: flex; gap: var(--spacing-md); padding: var(--spacing-md) 0; border-bottom: 1px solid #ccc; flex-wrap: wrap; }}
.nav a {{ text-decoration: none; color: var(--color-text); font-weight: 500; }}
.nav a:hover {{ color: var(--color-primary); }}
.container {{ max-width: 1200px; margin: 0 auto; }}
.grid {{ display: grid; gap: var(--spacing-md); grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
.card {{ border: 1px solid #ddd; border-radius: var(--radius); padding: var(--spacing-md); background: var(--color-bg); }}
.state-loading {{ padding: var(--spacing-lg); text-align: center; border-radius: var(--radius); margin: var(--spacing-md) 0; background: #e5edff; color: #1e3a8a; }}
.state-empty {{ padding: var(--spacing-lg); text-align: center; border-radius: var(--radius); margin: var(--spacing-md) 0; background: #f3f4f6; color: #4b5563; }}
.state-error {{ padding: var(--spacing-lg); text-align: center; border-radius: var(--radius); margin: var(--spacing-md) 0; background: #fee2e2; color: #991b1b; }}
@media (max-width: 640px) {{ body {{ padding: 0.5rem; }} .grid {{ grid-template-columns: 1fr; }} }}
@media (prefers-color-scheme: dark) {{
  body {{ --color-bg: #111827; --color-text: #f3f4f6; }}
  .card {{ border-color: #374151; background: #111827; }}
}}
"""
    with open(os.path.join(OUT_DIR, "style.css"), "w", encoding="utf-8") as f:
        f.write(css_content)

def write_page(name: str, title: str, body: str, nav: str, run_id: int) -> None:
    # One run id for every page and nav link, so links never point at another run.
    filename = f"{name}_{run_id}.html"
    safe_title = html.escape(title)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe_title}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<nav class="nav">{nav}</nav>
<div class="container">
<h1>{safe_title}</h1>
{body}
</div>
</body>
</html>"""
    with open(os.path.join(OUT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Also create a symlink or a copy of the latest index.html for convenience
    if name == "index":
        with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_content)

def main():
    log("Reading project memory from " + UFME_DIR)

    write_css()

    run_id = int(time.time())
    routes = parse_routes(SITEMAP)
    nav = "".join(
        f'<a href="{slugify(r)}_{run_id}.html">{html.escape(r)}</a>' for r in routes
    )

    if routes:
        for route in routes:
            page = slugify(route)
            title = route
            safe_route = html.escape(route)

            if any(x in route for x in ["Home", "Index", "Dashboard"]):
                body = f"<p>Welcome to {safe_route}.</p><div class='grid'><div class='card'><h3>Overview</h3><p>Key metrics for {safe_route}.</p></div><div class='card'><h3>Recent Activity</h3><p>Latest updates.</p></div></div>"
            elif any(x in route for x in ["Login", "Sign", "Auth"]):
                body = f"<div class='card' style='max-width: 400px; margin: 0 auto;'><h3>Sign In</h3><form><label>Email</label><br><input type='email' style='width:100%;padding:0.5rem;margin:0.5rem 0;'><br><label>Password</label><br><input type='password' style='width:100%;padding:0.5rem;margin:0.5rem 0;'><br><button class='btn' type='button'>Sign In</button></form></div>"
            elif any(x in route for x in ["Profile", "Account"]):
                body = f"<div class='card'><h3>Profile Settings</h3><p>Manage account preferences.</p><div class='state-loading'><p>Loading profile...</p></div></div>"
            else:
                body = f"<p>Content for {safe_route}.</p><div class='state-empty'><p>No items found.</p><button class='btn'>Refresh</button></div>"

            write_page(page, title, body, nav, run_id)
            log(f"Generated prototype: {page}.html")
    else:
        write_page("index", "Home", "<p>Welcome to the generated prototype.</p><button class='btn'>Get Started</button>", nav, run_id)
        log("Generated prototype: index.html (no sitemap routes found)")

    log("Prototype output: " + OUT_DIR)

if __name__ == "__main__":
    main()
