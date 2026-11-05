#!/usr/bin/env python3
"""
seo-gsc.py — Google Search Console integration.

Fetches GSC data when credentials are available. When credentials are
not available, uses clearly labeled mock fixtures.

Usage:
  python3 ufmw_seo_protocol_skill/scripts/seo-gsc.py <url> [evidenceDir]
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UFME = ROOT / ".ufme"
EVIDENCE = Path(os.environ.get("UFME_EVIDENCE_DIR") or (UFME / "evidence"))


def has_gsc_credentials():
    """Check if GSC credentials are configured."""
    creds_file = UFME / "gsc-credentials.json"
    return creds_file.exists()


def fetch_gsc_mock(url):
    """Return clearly labeled mock GSC data."""
    return {
        "url": url,
        "source": "mock",
        "message": "MOCK DATA — Configure GSC credentials for real data",
        "impressions": 0,
        "clicks": 0,
        "ctr": 0.0,
        "averagePosition": 0.0,
        "queries": [],
        "pages": [],
        "countries": [],
        "devices": [],
        "fetchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def fetch_gsc_real(url):
    """Fetch real GSC data using Google Search Console API."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_file = UFME / "gsc-credentials.json"
        creds = service_account.Credentials.from_service_account_file(
            str(creds_file),
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )
        service = build("searchconsole", "v1", credentials=creds)

        # Get property
        properties = service.sites().list().execute()
        site_url = None
        for s in properties.get("siteEntry", []):
            if s.get("siteUrl") == url or s.get("siteUrl") in url:
                site_url = s.get("siteUrl")
                break

        if not site_url:
            return {"error": f"Site {url} not found in GSC properties"}

        # Fetch search analytics
        request = {
            "startDate": "2026-01-01",
            "endDate": "2026-12-31",
            "dimensions": ["query", "page", "country", "device"],
            "rowLimit": 1000,
        }
        response = service.searchanalytics().query(siteUrl=site_url, body=request).execute()

        return {
            "url": url,
            "source": "google_search_console",
            "property": site_url,
            "fetchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "data": response.get("rows", []),
        }
    except ImportError:
        return {"error": "google-api-python-client not installed. Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"}
    except Exception as e:
        return {"error": str(e)}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 seo-gsc.py <url> [evidenceDir]")
        sys.exit(2)

    url = sys.argv[1]
    evidence_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else EVIDENCE

    if has_gsc_credentials():
        print(f"[seo-gsc] Fetching real GSC data for {url}...")
        data = fetch_gsc_real(url)
    else:
        print(f"[seo-gsc] No GSC credentials found. Using mock data.")
        print("[seo-gsc] Configure .ufme/gsc-credentials.json for real GSC integration.")
        data = fetch_gsc_mock(url)

    evidence_dir.mkdir(parents=True, exist_ok=True)
    gsc_file = evidence_dir / "seo-gsc.json"
    gsc_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Generate markdown report
    md_lines = [
        "# Google Search Console Report",
        "",
        f"- **Target URL**: {url}",
        f"- **Source**: {data.get('source', 'unknown')}",
        f"- **Fetched**: {data.get('fetchedAt', '')}",
        "",
    ]

    if data.get("error"):
        md_lines.append(f"## Error\n\n{data['error']}\n")
    elif data.get("source") == "mock":
        md_lines.append("## ⚠️ Mock Data\n\nConfigure GSC credentials for real data.\n")
    else:
        rows = data.get("data", [])
        total_impressions = sum(r.get("impressions", 0) for r in rows)
        total_clicks = sum(r.get("clicks", 0) for r in rows)
        md_lines.append(f"- **Total impressions**: {total_impressions}")
        md_lines.append(f"- **Total clicks**: {total_clicks}")
        if total_impressions > 0:
            md_lines.append(f"- **Average CTR**: {total_clicks / total_impressions * 100:.2f}%")
        md_lines.append("")
        md_lines.append("## Top Queries")
        md_lines.append("")
        md_lines.append("| Query | Impressions | Clicks | CTR | Position |")
        md_lines.append("|-------|-------------|--------|-----|----------|")
        for row in rows[:10]:
            keys = row.get("keys", [])
            query = keys[0] if len(keys) > 0 else ""
            impressions = row.get("impressions", 0)
            clicks = row.get("clicks", 0)
            ctr = row.get("ctr", 0) * 100
            position = row.get("position", 0)
            md_lines.append(f"| {query} | {impressions} | {clicks} | {ctr:.2f}% | {position:.1f} |")

    md_file = UFME / "SEO_GSC_REPORT.md"
    UFME.mkdir(parents=True, exist_ok=True)
    md_file.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"[seo-gsc] Report: {md_file}")
    print(f"[seo-gsc] Data: {gsc_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
