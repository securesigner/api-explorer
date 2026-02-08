#!/usr/bin/env python3
"""Session 13 batch update script - 2026-02-08
Tests 24 APIs across 8 new zero-tested categories.
Directly modifies apis.json (same logic as update-api-status.py).
"""

import json
import os
from datetime import date

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_FILE = "data/apis.json"

updates = [
    # === WORKING APIs (7) ===
    {
        "name": "Arbeitnow",
        "status": "working",
        "notes": "Free public JSON API for job listings. Returns paginated results with company, title, description, tags, location. Tested 2026-02-08.",
        "try-it": {"url": "https://www.arbeitnow.com/api/job-board-api", "response-type": "json"},
    },
    {
        "name": "File.io",
        "status": "working",
        "notes": "Ephemeral file sharing API. POST to upload, files deleted after download. Free up to 4GB. Tested 2026-02-08.",
    },
    {
        "name": "Pantry",
        "status": "working",
        "notes": "Free cloud JSON storage with CRUD API. Active service with 1230+ projects and 2.57M monthly requests. Tested 2026-02-08.",
    },
    {
        "name": "The Null Pointer",
        "status": "working",
        "notes": "Temporary file hosting at 0x0.st. POST to upload, retention based on file size (30 days to 1 year, max 512 MiB). Tested 2026-02-08.",
    },
    {
        "name": "Vector Express v2.0",
        "status": "working",
        "notes": "Free vector file conversion API. Returns JSON conversion paths between formats (DXF, SVG, PDF, etc). Tested 2026-02-08.",
        "try-it": {
            "url": "https://vector.express/api/v2/public/convert/dxf/auto/pdf",
            "response-type": "json",
        },
    },
    {
        "name": "WakaTime",
        "status": "working",
        "notes": "Developer coding activity tracker. Public endpoints /api/v1/editors, /api/v1/program_languages, /api/v1/meta return JSON without auth. Tested 2026-02-08.",
        "try-it": {"url": "https://wakatime.com/api/v1/editors", "response-type": "json"},
    },
    {
        "name": "CleanURI",
        "status": "working",
        "notes": "URL shortener API. POST /api/v1/shorten with url param returns shortened link. Rate limit 2 req/sec. Tested 2026-02-08.",
    },
    # === NEEDS-KEY APIs (1) ===
    {
        "name": "PatentsView",
        "status": "needs-key",
        "notes": "Legacy API discontinued May 2025 (returns 410 Gone). New PatentSearch API requires API key (returns 403 without). Tested 2026-02-08.",
    },
    # === BROKEN APIs (16) ===
    {
        "name": "AnonFiles",
        "status": "broken",
        "notes": "Service shut down in 2023. Domain no longer serves API responses. Tested 2026-02-08.",
    },
    {
        "name": "BayFiles",
        "status": "broken",
        "notes": "Service shut down alongside AnonFiles in 2023. Domain dead. Tested 2026-02-08.",
    },
    {
        "name": "Deepcode",
        "status": "broken",
        "notes": "Acquired by Snyk. Domain redirects to snyk.io/platform/deepcode-ai/. No standalone API available. Tested 2026-02-08.",
    },
    {
        "name": "EXUDE-API",
        "status": "broken",
        "notes": "Homepage at uttesh.com/exude-api/ not loading. API appears defunct. Tested 2026-02-08.",
    },
    {
        "name": "Drivet URL Shortener",
        "status": "broken",
        "notes": "Domain wiki.drivet.xyz redirects to parked/ad domain ww1.drivet.xyz. Service dead. Tested 2026-02-08.",
    },
    {
        "name": "Free Url Shortener",
        "status": "broken",
        "notes": "ulvis.net returns HTTP 403 Forbidden. Service appears to block all requests. Tested 2026-02-08.",
    },
    {
        "name": "GoTiny",
        "status": "broken",
        "notes": "Officially shut down. GitHub README states GoTiny is no longer available. See github.com/robvanbakel/gotiny-api/issues/11. Tested 2026-02-08.",
    },
    {
        "name": "owo",
        "status": "broken",
        "notes": "owo.vc/api returns HTTP 404. API endpoint no longer exists. Tested 2026-02-08.",
    },
    {
        "name": "Short Link",
        "status": "broken",
        "notes": "GitHub repo FayasNoushad/Short-Link-API returns 404. Repository deleted. Tested 2026-02-08.",
    },
    {
        "name": "Mgnet.me",
        "status": "broken",
        "notes": "mgnet.me/api.html redirects to Facebook plugins page. Service dead. Tested 2026-02-08.",
    },
    {
        "name": "1pt",
        "status": "broken",
        "notes": "POST endpoint at csclub.uwaterloo.ca returns 404. University-hosted service appears down. Tested 2026-02-08.",
    },
    {
        "name": "Shrtcode",
        "status": "broken",
        "notes": "shrtco.de not loading. Both docs page and main site return no content. Tested 2026-02-08.",
    },
    {
        "name": "Open Skills",
        "status": "broken",
        "notes": "api.dataatwork.org not responding. Last wiki update Jan 2019. Government workforce data API appears abandoned. Tested 2026-02-08.",
    },
    {
        "name": "GraphQL Jobs",
        "status": "broken",
        "notes": "graphql.jobs not loading. Both docs and main site return no content. Tested 2026-02-08.",
    },
    {
        "name": "KONTESTS",
        "status": "broken",
        "notes": "kontests.net not loading. Both main site and API endpoint return no content. Tested 2026-02-08.",
    },
    {
        "name": "OpenVisionAPI",
        "status": "broken",
        "notes": "openvisionapi.com not loading. Site returns no content. Tested 2026-02-08.",
    },
]


def main():
    with open(DATA_FILE) as f:
        apis = json.load(f)

    today = str(date.today())
    success = 0
    failed = 0

    for u in updates:
        # Find the API by exact name (case-insensitive)
        matches = [a for a in apis if a["name"].lower() == u["name"].lower()]
        if not matches:
            print(f"  NOT FOUND: {u['name']}")
            failed += 1
            continue

        api = matches[0]
        old_status = api.get("status", "pending")
        api["status"] = u["status"]
        api["notes"] = u["notes"]
        if u["status"] != "pending":
            api["date-checked"] = today
        if "try-it" in u:
            api["try-it"] = u["try-it"]
        print(f"  {u['name']:30s} {old_status:10s} -> {u['status']}")
        success += 1

    with open(DATA_FILE, "w") as f:
        json.dump(apis, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\nDONE: {success} updated, {failed} failed out of {len(updates)} total")


if __name__ == "__main__":
    main()
