#!/usr/bin/env python3
"""
seo-crawl.py — Deterministic HTTP-based website crawler for SEO data extraction.

Crawls a website and extracts SEO-relevant data:
- Titles, meta descriptions, headings (H1-H6)
- Internal/external links with status codes
- Images with alt text
- Canonical tags, robots meta, structured data (JSON-LD)
- robots.txt and sitemap.xml
- Page load indicators

Output:
  .ufme/evidence/seo-crawl.json — machine-readable crawl data
  .ufme/SEO_CRAWL.md — human-readable summary

Usage:
  python3 skills/ufmw-seo-protocol/scripts/seo-crawl.py <url> [maxPages]
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UFME = ROOT / ".ufme"
EVIDENCE = Path(os.environ.get("UFME_EVIDENCE_DIR") or (UFME / "evidence"))

USER_AGENT = "UFME-SEO-Bot/1.0 (+https://ufme.example.com/bot)"


class SEODOMParser(HTMLParser):
    """Extract SEO-relevant data from HTML."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.in_title = False
        self.meta_description = ""
        self.meta_robots = ""
        self.canonical = ""
        self.headings = {"h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []}
        self.in_heading = None
        self.heading_text = ""
        self.images = []
        self.links = []
        self.structured_data = []
        self.in_script_ld = False
        self.ld_json = ""
        self.current_tag = ""

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        self.current_tag = tag

        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            name = attr_dict.get("name", attr_dict.get("property", ""))
            content = attr_dict.get("content", "")
            if name == "description":
                self.meta_description = content
            elif name == "robots":
                self.meta_robots = content
        elif tag == "link":
            rel = attr_dict.get("rel", "")
            if rel == "canonical":
                self.canonical = attr_dict.get("href", "")
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.in_heading = tag
            self.heading_text = ""
        elif tag == "img":
            self.images.append({
                "src": attr_dict.get("src", ""),
                "alt": attr_dict.get("alt", ""),
                "width": attr_dict.get("width", ""),
                "height": attr_dict.get("height", ""),
            })
        elif tag == "a":
            href = attr_dict.get("href", "")
            if href:
                self.links.append({
                    "href": href,
                    "text": "",
                    "rel": attr_dict.get("rel", ""),
                })
        elif tag == "script":
            if attr_dict.get("type") == "application/ld+json":
                self.in_script_ld = True
                self.ld_json = ""

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if self.in_heading == tag and self.heading_text.strip():
                self.headings[tag].append(self.heading_text.strip())
            self.in_heading = None
            self.heading_text = ""
        elif tag == "script" and self.in_script_ld:
            self.in_script_ld = False
            try:
                data = json.loads(self.ld_json)
                self.structured_data.append(data)
            except (json.JSONDecodeError, ValueError):
                pass

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif self.in_heading:
            self.heading_text += data
        elif self.in_script_ld:
            self.ld_json += data
        elif self.current_tag == "a" and self.links:
            self.links[-1]["text"] += data.strip()


def fetch(url, timeout=15):
    """Fetch a URL and return (html, status_code, final_url) or None on error."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            return html, resp.status, resp.geturl()
    except Exception as e:
        return None, 0, str(e)


def normalize_url(base_url, href):
    """Normalize a relative URL to absolute."""
    if not href:
        return None
    if href.startswith("#"):
        return None
    if href.startswith("mailto:") or href.startswith("tel:"):
        return None
    parsed = urllib.parse.urljoin(base_url, href)
    parsed = urllib.parse.urlparse(parsed)
    # Remove fragment
    return parsed._replace(fragment="").geturl()


def is_same_domain(url1, url2):
    """Check if two URLs are on the same domain."""
    p1 = urllib.parse.urlparse(url1)
    p2 = urllib.parse.urlparse(url2)
    return p1.netloc == p2.netloc


def fetch_robots_txt(base_url):
    """Fetch and parse robots.txt."""
    parsed = urllib.parse.urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    html, status, _ = fetch(robots_url)
    if status == 200 and html:
        return html
    return None


def fetch_sitemap(base_url):
    """Fetch and parse sitemap.xml."""
    parsed = urllib.parse.urlparse(base_url)
    sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"
    html, status, _ = fetch(sitemap_url)
    if status == 200 and html:
        return html
    return None


def crawl(start_url, max_pages=50):
    """Crawl a website starting from start_url."""
    visited = set()
    to_visit = [start_url]
    pages = []
    base_domain = urllib.parse.urlparse(start_url).netloc

    robots_txt = fetch_robots_txt(start_url)
    sitemap_xml = fetch_sitemap(start_url)

    while to_visit and len(pages) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        html, status, final_url = fetch(url)
        if html is None:
            pages.append({
                "url": url,
                "status": 0,
                "error": final_url,
            })
            continue

        parser = SEODOMParser()
        parser.feed(html)

        # Extract internal links for further crawling
        for link in parser.links:
            abs_url = normalize_url(final_url, link["href"])
            if abs_url and is_same_domain(start_url, abs_url) and abs_url not in visited:
                to_visit.append(abs_url)

        pages.append({
            "url": final_url,
            "status": status,
            "title": parser.title.strip(),
            "metaDescription": parser.meta_description.strip(),
            "metaRobots": parser.meta_robots.strip(),
            "canonical": parser.canonical.strip(),
            "headings": {k: v for k, v in parser.headings.items() if v},
            "images": parser.images,
            "links": parser.links,
            "structuredData": parser.structured_data,
            "internalLinkCount": len([l for l in parser.links if is_same_domain(final_url, l["href"])]),
            "externalLinkCount": len([l for l in parser.links if not is_same_domain(final_url, l["href"])]),
            "imageCount": len(parser.images),
            "wordCount": len(re.findall(r"\w+", html)),
        })

        # Be polite
        time.sleep(0.5)

    return {
        "startUrl": start_url,
        "baseDomain": base_domain,
        "pagesCrawled": len(pages),
        "robotsTxt": robots_txt,
        "sitemapXml": sitemap_xml,
        "pages": pages,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 seo-crawl.py <url> [maxPages]")
        sys.exit(2)

    url = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    print(f"[seo-crawl] Crawling {url} (max {max_pages} pages)...")
    result = crawl(url, max_pages)

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    crawl_file = EVIDENCE / "seo-crawl.json"
    crawl_file.write_text(json.dumps(result, indent=2), encoding="utf-8")

    # Generate human-readable summary
    md_lines = [
        "# SEO Crawl Results",
        "",
        f"- **Target URL**: {result['startUrl']}",
        f"- **Base domain**: {result['baseDomain']}",
        f"- **Pages crawled**: {result['pagesCrawled']}",
        f"- **robots.txt**: {'found' if result['robotsTxt'] else 'not found'}",
        f"- **sitemap.xml**: {'found' if result['sitemapXml'] else 'not found'}",
        "",
        "## Pages",
        "",
        "| URL | Status | Title | H1 | Meta Desc | Canonical | Links | Images |",
        "|-----|--------|-------|----|-----------|-----------|-------|--------|",
    ]

    for p in result["pages"]:
        h1_count = len(p.get("headings", {}).get("h1", []))
        md_lines.append(
            f"| {p['url']} | {p['status']} | {p.get('title', '')[:50]} | "
            f"{h1_count} | {'yes' if p.get('metaDescription') else 'no'} | "
            f"{'yes' if p.get('canonical') else 'no'} | "
            f"{p.get('internalLinkCount', 0)}/{p.get('externalLinkCount', 0)} | "
            f"{p.get('imageCount', 0)} |"
        )

    md_lines.append("")
    md_lines.append("## Issues Found")
    md_lines.append("")

    issues = 0
    for p in result["pages"]:
        if not p.get("title"):
            md_lines.append(f"- **Missing title**: {p['url']}")
            issues += 1
        if not p.get("metaDescription"):
            md_lines.append(f"- **Missing meta description**: {p['url']}")
            issues += 1
        h1s = p.get("headings", {}).get("h1", [])
        if len(h1s) == 0:
            md_lines.append(f"- **Missing H1**: {p['url']}")
            issues += 1
        elif len(h1s) > 1:
            md_lines.append(f"- **Multiple H1s**: {p['url']} ({len(h1s)})")
            issues += 1
        if not p.get("canonical"):
            md_lines.append(f"- **Missing canonical**: {p['url']}")
            issues += 1
        for img in p.get("images", []):
            if not img.get("alt"):
                md_lines.append(f"- **Missing alt text**: {p['url']} - {img.get('src', '')}")
                issues += 1

    md_lines.append(f"\nTotal issues: {issues}")
    md_file = UFME / "SEO_CRAWL.md"
    UFME.mkdir(parents=True, exist_ok=True)
    md_file.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"[seo-crawl] Crawled {result['pagesCrawled']} pages, {issues} issues found")
    print(f"[seo-crawl] Data: {crawl_file}")
    print(f"[seo-crawl] Summary: {md_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
