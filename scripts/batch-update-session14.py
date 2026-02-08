#!/usr/bin/env python3
"""Session 14 batch update script - 2026-02-08
Tests 20 APIs across 10 categories (all pending, no-auth).
Directly modifies apis.json (same logic as update-api-status.py).
"""

import json
import os
from datetime import date

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_FILE = "data/apis.json"

updates = [
    # === WORKING APIs (16) ===
    # Government category
    {
        "name": "USAspending.gov",
        "status": "working",
        "notes": "Federal spending data API. Returns JSON with agency names, budgets, toptier codes, abbreviations. Tested 2026-02-08.",
        "try-it": {
            "url": "https://api.usaspending.gov/api/v2/references/toptier_agencies/",
            "response-type": "json",
            "params": "sort=agency_name&order=asc&limit=3",
        },
    },
    {
        "name": "Open Government, Australia",
        "status": "working",
        "notes": "Australian government open data catalog (CKAN API). Returns dataset lists and metadata. Note: use /data/ path (v0 endpoint is deprecated). Tested 2026-02-08.",
        "try-it": {
            "url": "https://data.gov.au/data/api/3/action/package_list",
            "response-type": "json",
            "params": "limit=3",
        },
    },
    # Geocoding category
    {
        "name": "ip-api",
        "status": "working",
        "notes": "IP geolocation API. Returns country, city, ISP, org, AS number, lat/lon coordinates for any IP. HTTP only (HTTPS requires paid plan). Tested 2026-02-08.",
        "try-it": {
            "url": "http://ip-api.com/json/8.8.8.8",
            "response-type": "json",
        },
    },
    {
        "name": "Nominatim",
        "status": "working",
        "notes": "OpenStreetMap geocoding/search API. Returns places with lat/lon, display name, bounding box. Requires User-Agent header (browsers send automatically). Tested 2026-02-08.",
        "try-it": {
            "url": "https://nominatim.openstreetmap.org/search",
            "response-type": "json",
            "params": "q=london&format=json&limit=2",
        },
    },
    {
        "name": "ViaCep",
        "status": "working",
        "notes": "Brazilian ZIP code lookup API. Returns address details (street, neighborhood, city, state) for CEP codes. Tested 2026-02-08.",
        "try-it": {
            "url": "https://viacep.com.br/ws/01001000/json/",
            "response-type": "json",
        },
    },
    # Health category
    {
        "name": "NPPES",
        "status": "working",
        "notes": "National Provider Identifier (NPI) registry lookup. Returns healthcare provider details (name, taxonomy, address, practice info). Tested 2026-02-08.",
        "try-it": {
            "url": "https://npiregistry.cms.hhs.gov/api/",
            "response-type": "json",
            "params": "number=1234567893&version=2.1",
        },
    },
    {
        "name": "Open Data NHS Scotland",
        "status": "working",
        "notes": "Scottish NHS open data portal (CKAN-based). Returns dataset lists and health statistics metadata. Tested 2026-02-08.",
        "try-it": {
            "url": "https://www.opendata.nhs.scot/api/3/action/package_list",
            "response-type": "json",
            "params": "limit=5",
        },
    },
    # Development category
    {
        "name": "Kroki",
        "status": "working",
        "notes": "Diagram-as-a-service API. Converts text descriptions (PlantUML, Mermaid, GraphViz, etc.) to diagrams via POST. Supports 20+ diagram types. Tested 2026-02-08.",
    },
    {
        "name": "DigitalOcean Status",
        "status": "working",
        "notes": "DigitalOcean infrastructure status API (via Statuspage.io). Returns current operational status, active incidents, and component health. Tested 2026-02-08.",
        "try-it": {
            "url": "https://s2k7tnzlhrpw.statuspage.io/api/v2/status.json",
            "response-type": "json",
        },
    },
    # Science & Math category
    {
        "name": "Launch Library 2",
        "status": "working",
        "notes": "Space launch data API. Returns upcoming launches with rocket details, mission info, launch pads, agencies, status, and countdown timers. Tested 2026-02-08.",
        "try-it": {
            "url": "https://ll.thespacedevs.com/2.2.0/launch/upcoming/",
            "response-type": "json",
            "params": "limit=3&format=json",
        },
    },
    # Finance category
    {
        "name": "World Bank",
        "status": "working",
        "notes": "World Bank country and indicator data API. Returns country profiles with regions, income levels, capital cities, lending types. Tested 2026-02-08.",
        "try-it": {
            "url": "https://api.worldbank.org/v2/country",
            "response-type": "json",
            "params": "format=json&per_page=5",
        },
    },
    # Transportation category
    {
        "name": "transport.rest",
        "status": "working",
        "notes": "Public transport API for European systems (Deutsche Bahn, VBB, etc). Returns stations, departures, journeys with real-time data. Tested 2026-02-08.",
        "try-it": {
            "url": "https://v6.db.transport.rest/locations",
            "response-type": "json",
            "params": "query=berlin&results=3",
        },
    },
    # Security category
    {
        "name": "National Vulnerability Database",
        "status": "working",
        "notes": "NIST NVD CVE vulnerability database API. Returns CVE records with descriptions, CVSS scores, affected products, references. Tested 2026-02-08.",
        "try-it": {
            "url": "https://services.nvd.nist.gov/rest/json/cves/2.0",
            "response-type": "json",
            "params": "resultsPerPage=3",
        },
    },
    # Sports & Fitness category
    {
        "name": "OpenLigaDB",
        "status": "working",
        "notes": "Free sports data API (primarily European football/soccer). Returns leagues, match data, scores, team info for Bundesliga, Champions League, etc. Tested 2026-02-08.",
        "try-it": {
            "url": "https://api.openligadb.de/getmatchdata/bl1/2024/1",
            "response-type": "json",
        },
    },
    # Music category
    {
        "name": "Lyrics.ovh",
        "status": "working",
        "notes": "Song lyrics API. Returns full lyrics as JSON for artist/song queries. Tested 2026-02-08.",
        "try-it": {
            "url": "https://api.lyrics.ovh/v1/coldplay/yellow",
            "response-type": "json",
        },
    },
    # Test Data category
    {
        "name": "UUID Generator",
        "status": "working",
        "notes": "UUID v4 generation API. Returns array of random UUIDs. Simple GET endpoint. Tested 2026-02-08.",
        "try-it": {
            "url": "https://www.uuidtools.com/api/generate/v4",
            "response-type": "json",
        },
    },
    # === BROKEN APIs (4) ===
    {
        "name": "EPA",
        "status": "broken",
        "notes": "EnviroFacts API endpoints return 404. data.epa.gov/efservice/ appears restructured or deprecated. Tested 2026-02-08.",
    },
    {
        "name": "Transport for Los Angeles, US",
        "status": "broken",
        "notes": "api.metro.net/agencies/lametro/routes/ returns 404. API endpoints appear deprecated or restructured. Tested 2026-02-08.",
    },
    {
        "name": "Teleport",
        "status": "broken",
        "notes": "teleport.org and developers.teleport.org not loading. Service appears shut down (acquired by Topia). Tested 2026-02-08.",
    },
    {
        "name": "Quotable Quotes",
        "status": "broken",
        "notes": "api.quotable.io not responding. Hosted on Heroku (free tier discontinued Nov 2022). Project unmaintained since 2023. Tested 2026-02-08.",
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
        print(f"  {u['name']:40s} {old_status:10s} -> {u['status']}")
        success += 1

    with open(DATA_FILE, "w") as f:
        json.dump(apis, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\nDONE: {success} updated, {failed} failed out of {len(updates)} total")


if __name__ == "__main__":
    main()
