#!/usr/bin/env python3
"""Session 15 batch update script - 2026-02-08
Tests 20 APIs across 8 categories (close out near-complete no-auth categories).
Directly modifies apis.json (same logic as update-api-status.py).
"""

import json
import os
from datetime import date

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_FILE = "data/apis.json"

updates = [
    # === WORKING APIs (7) ===
    # Dictionaries category
    {
        "name": "Chinese Character Web",
        "status": "working",
        "notes": "Chinese character database API (Unihan). Returns character definitions, Mandarin/Cantonese pronunciations, radical/stroke data. 20,902 CJK characters. CORS enabled. Tested 2026-02-08.",
        "try-it": {
            "url": "http://ccdb.hemiola.com/characters/strokes/1?fields=string,kDefinition,kMandarin",
            "response-type": "json",
        },
    },
    # Finance category
    {
        "name": "Razorpay IFSC",
        "status": "working",
        "notes": "Indian bank branch lookup by IFSC code. Returns branch name, address, city, state, bank name, MICR code, and support flags (RTGS, NEFT, IMPS, UPI). Tested 2026-02-08.",
        "try-it": {
            "url": "https://ifsc.razorpay.com/{ifsc}",
            "response-type": "json",
            "params": {"ifsc": "SBIN0000001"},
        },
    },
    {
        "name": "WallstreetBets",
        "status": "working",
        "notes": "Top 50 Reddit WallstreetBets stocks with sentiment analysis (bullish/bearish). Moved from nbshare.io to tradestie.com. Updates every 15 minutes. Tested 2026-02-08.",
        "try-it": {
            "url": "https://api.tradestie.com/v1/apps/reddit",
            "response-type": "json",
        },
    },
    {
        "name": "Portfolio Optimizer",
        "status": "working",
        "notes": "Portfolio optimization Web API using modern portfolio theory. Free, no registration. POST-only endpoints (no GET try-it). Tested 2026-02-08.",
    },
    # Weather category
    {
        "name": "Hong Kong Obervatory",
        "status": "working",
        "notes": "Hong Kong Observatory open data API. Returns real-time rainfall, temperature, humidity, UV index, and weather warnings across 18+ districts. Tested 2026-02-08.",
        "try-it": {
            "url": "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=en",
            "response-type": "json",
        },
    },
    {
        "name": "ODWeather",
        "status": "working",
        "notes": "Ocean weather data API (Mallorca/Balearic Islands). Returns temperature, wind speed/direction, pressure, humidity, rain data from AEMET and SOCIB stations. Swagger docs available. Tested 2026-02-08.",
        "try-it": {
            "url": "https://api.oceandrivers.com/v1.0/getAemetStation/aeropuertopalma/lastdata/",
            "response-type": "json",
        },
    },
    {
        "name": "weather-api",
        "status": "working",
        "notes": "Simple weather API by city name. Returns current temperature, wind, description, and 3-day forecast. Hosted at goweather.xyz. Tested 2026-02-08.",
        "try-it": {
            "url": "https://goweather.xyz/weather/{city}",
            "response-type": "json",
            "params": {"city": "London"},
        },
    },
    # === BROKEN APIs (12) ===
    # URL Shorteners category
    {
        "name": "Git.io",
        "status": "broken",
        "notes": "GitHub deprecated git.io URL shortener in January 2022. Service displays 'no longer accepting new links'. Tested 2026-02-08.",
    },
    # Jobs category
    {
        "name": "DevITjobs UK",
        "status": "broken",
        "notes": "devitjobs.uk domain no longer resolves (DNS failure). Site appears shut down. Tested 2026-02-08.",
    },
    # Dictionaries category
    {
        "name": "Indonesia Dictionary",
        "status": "broken",
        "notes": "Hosted on Heroku (new-kbbi-api.herokuapp.com). DNS failure — Heroku free tier shut down Nov 2022. Tested 2026-02-08.",
    },
    # Tracking category
    {
        "name": "Postmon",
        "status": "broken",
        "notes": "Brazilian ZIP code API. Docs alive on GitHub Pages (postmon.com.br) but API at api.postmon.com.br appears dead (404 at root, endpoints unresponsive). Tested 2026-02-08.",
    },
    # News category
    {
        "name": "Chronicling America",
        "status": "broken",
        "notes": "Library of Congress newspaper API. Redirects from chroniclingamerica.loc.gov to loc.gov domain, all JSON endpoints return HTTP 403. API appears restricted or restructured. Tested 2026-02-08.",
    },
    {
        "name": "Graphs for Coronavirus",
        "status": "broken",
        "notes": "corona.dnsforfamily.com not responding. COVID-19 data API appears shut down. Tested 2026-02-08.",
    },
    {
        "name": "Inshorts News",
        "status": "broken",
        "notes": "Hosted on Deta Space (inshorts.deta.dev). Deta Space was discontinued — endpoint not responding. GitHub repo unmaintained (3+ years). Tested 2026-02-08.",
    },
    # Weather category
    {
        "name": "MetaWeather",
        "status": "broken",
        "notes": "metaweather.com not responding. Service shut down in 2022. Tested 2026-02-08.",
    },
    # Calendar category
    {
        "name": "Czech Namedays Calendar",
        "status": "broken",
        "notes": "svatky.adresa.info returns HTTP 402 Payment Required. API appears paywalled or shut down. Tested 2026-02-08.",
    },
    {
        "name": "LectServe",
        "status": "broken",
        "notes": "Website at lectserve.com works (shows daily readings) but serves only HTML — no JSON API endpoints found. All /api/ paths return 404. Not a REST API. Tested 2026-02-08.",
    },
    {
        "name": "Non-Working Days",
        "status": "broken",
        "notes": "GitHub repo of static ICS calendar files (gadael/icsdb), not a REST API. No programmatic endpoints — just downloadable .ics files. Tested 2026-02-08.",
    },
    {
        "name": "Russian Calendar",
        "status": "broken",
        "notes": "Self-hosted Docker app (egno/work-calendar) — no public API endpoint. GitHub repo archived Oct 2023. Tested 2026-02-08.",
    },
    # === NEEDS-KEY APIs (1) ===
    # Tracking category
    {
        "name": "WhatPulse",
        "status": "needs-key",
        "notes": "Keyboard/mouse usage statistics API. Requires Bearer token authentication (create API key at whatpulse.org settings). Tested 2026-02-08.",
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
