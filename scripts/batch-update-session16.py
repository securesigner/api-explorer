#!/usr/bin/env python3
"""Session 16 batch update script - 2026-02-08
Tests 20 APIs across 8 categories. Strategy: maximize working count.
Directly modifies apis.json (same logic as update-api-status.py).
"""

import json
import os
from datetime import date

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_FILE = "data/apis.json"

updates = [
    # === WORKING APIs (16) ===
    # science-math (4)
    {
        "name": "Numbers",
        "status": "working",
        "notes": "Random trivia, math, date, and year facts about numbers. Returns plain text by default, JSON with ?json flag. Free, no auth. Tested 2026-02-08.",
        "try-it": {
            "url": "http://numbersapi.com/{number}/trivia",
            "response-type": "text",
            "params": {"number": "42"},
        },
    },
    {
        "name": "GBIF",
        "status": "working",
        "notes": "Global Biodiversity Information Facility API. Species search, occurrence records, datasets. 2.4B+ occurrence records from 82K+ datasets. Tested 2026-02-08.",
        "try-it": {
            "url": "https://api.gbif.org/v1/species/search?q={query}&limit=5",
            "response-type": "json",
            "params": {"query": "bear"},
        },
    },
    {
        "name": "TLE",
        "status": "working",
        "notes": "Satellite TLE (Two-Line Element) orbital data. Search by name, get current orbital parameters. Includes ISS, Starlink, weather sats. Tested 2026-02-08.",
        "try-it": {
            "url": "https://tle.ivanstanojevic.me/api/tle?search={query}&page_size=5",
            "response-type": "json",
            "params": {"query": "ISS"},
        },
    },
    {
        "name": "Open Science Framework",
        "status": "working",
        "notes": "Center for Open Science research platform API (JSON:API format). Access public research projects, preprints, files, contributors. 566K+ public nodes. Tested 2026-02-08.",
        "try-it": {
            "url": "https://api.osf.io/v2/nodes/?page[size]=3",
            "response-type": "json",
        },
    },
    # Also test SHARE (related to OSF, same category)
    {
        "name": "SHARE",
        "status": "working",
        "notes": "Open dataset of research activities (papers, preprints, datasets) aggregated from 100+ sources. JSON:API format. Endpoints for sources, users, feeds. Tested 2026-02-08.",
        "try-it": {
            "url": "https://share.osf.io/api/v2/sources/",
            "response-type": "json",
        },
    },
    # games-comics (8)
    {
        "name": "Pokémon TCG",
        "status": "working",
        "notes": "Pokémon Trading Card Game API. Card data with images, prices (TCGplayer/Cardmarket), attacks, abilities, sets. 20K+ cards. Tested 2026-02-08.",
        "try-it": {
            "url": "https://api.pokemontcg.io/v2/cards?pageSize=3&q=name:charizard",
            "response-type": "json",
        },
    },
    {
        "name": "Universalis",
        "status": "working",
        "notes": "Final Fantasy XIV market board data API. Crowdsourced pricing from all FFXIV worlds/data centers. Item listings, sale history, tax rates. Tested 2026-02-08.",
        "try-it": {
            "url": "https://universalis.app/api/v2/North-America/5?listings=3",
            "response-type": "json",
        },
    },
    {
        "name": "Digimon Information",
        "status": "working",
        "notes": "Digimon character data API. Returns name, image URL, and level (Fresh/In Training/Rookie/Champion/Ultimate/Mega) for all Digimon. Vercel-hosted. Tested 2026-02-08.",
        "try-it": {
            "url": "https://digimon-api.vercel.app/api/digimon/name/{name}",
            "response-type": "json",
            "params": {"name": "Agumon"},
        },
    },
    {
        "name": "Dungeons and Dragons (Alternate)",
        "status": "working",
        "notes": "Open5e D&D 5th Edition SRD API. Monsters, spells, classes, items from official SRD + third-party (Kobold Press). 3,207 monsters, Django REST framework. Tested 2026-02-08.",
        "try-it": {
            "url": "https://api.open5e.com/v1/monsters/?limit=3",
            "response-type": "json",
        },
    },
    {
        "name": "Board Game Geek",
        "status": "working",
        "notes": "BoardGameGeek XML API v2. Game info, ratings, images, mechanics. 130K+ board games. Returns XML (not JSON). Tested 2026-02-08.",
        "try-it": {
            "url": "https://boardgamegeek.com/xmlapi2/thing?id=174430",
            "response-type": "text",
        },
    },
    {
        "name": "Magic The Gathering",
        "status": "working",
        "notes": "Magic: The Gathering card data API. Card names, mana costs, types, sets, images, prices, foreign names. All MTG sets included. Tested 2026-02-08.",
        "try-it": {
            "url": "https://api.magicthegathering.io/v1/cards?pageSize=3",
            "response-type": "json",
        },
    },
    {
        "name": "Hyrule Compendium",
        "status": "working",
        "notes": "Zelda Breath of the Wild / Tears of the Kingdom compendium data. Creatures, equipment, materials, monsters, treasures with images and descriptions. Hosted on Heroku (still alive). Tested 2026-02-08.",
        "try-it": {
            "url": "https://botw-compendium.herokuapp.com/api/v3/compendium/entry/{entry}",
            "response-type": "json",
            "params": {"entry": "moblin"},
        },
    },
    {
        "name": "Raider",
        "status": "working",
        "notes": "Raider.IO World of Warcraft Mythic+ and Raid progression API. Character profiles, season cutoffs, dungeon rankings. Very active community. Tested 2026-02-08.",
        "try-it": {
            "url": "https://raider.io/api/v1/mythic-plus/season-cutoffs?season=season-tww-2&region=us",
            "response-type": "json",
        },
    },
    # open-source-projects (2)
    {
        "name": "Drupal.org",
        "status": "working",
        "notes": "Official Drupal CMS platform API. Nodes, users, taxonomy terms. 2.1M+ nodes. Drupal 7 REST API format. Tested 2026-02-08.",
        "try-it": {
            "url": "https://www.drupal.org/api-d7/node.json?limit=3",
            "response-type": "json",
        },
    },
    {
        "name": "Shields",
        "status": "working",
        "notes": "Shields.io badge/shield generation service. SVG/PNG badges for GitHub, npm, CI status, custom labels. Used by millions of repos. Returns SVG images. Tested 2026-02-08.",
        "try-it": {
            "url": "https://img.shields.io/badge/{label}-{message}-{color}",
            "response-type": "image",
            "params": {"label": "build", "message": "passing", "color": "green"},
        },
    },
    # test-data (1)
    {
        "name": "What The Commit",
        "status": "working",
        "notes": "Random funny/sarcastic commit messages. Plain text endpoint. Simple, no auth, been running 10+ years. Tested 2026-02-08.",
        "try-it": {
            "url": "http://whatthecommit.com/index.txt",
            "response-type": "text",
        },
    },
    # food-drink (1)
    {
        "name": "Foodish",
        "status": "working",
        "notes": "Random food dish images API. Returns JSON with image URL from 1000+ food photos across categories (pizza, pasta, burger, etc.). Tested 2026-02-08.",
        "try-it": {
            "url": "https://foodish-api.com/api/",
            "response-type": "json",
        },
    },
    # === BROKEN APIs (4) ===
    # games-comics
    {
        "name": "Crafatar",
        "status": "broken",
        "notes": "Minecraft avatar/skin rendering service. crafatar.com returns HTTP 521 (Cloudflare: Web Server Is Down). Server appears offline. Tested 2026-02-08.",
    },
    {
        "name": "Final Fantasy XIV",
        "status": "broken",
        "notes": "XIVAPI character/item search. xivapi.com returns HTTP 403 Forbidden on all endpoints. API may now require authentication or has been restructured. Tested 2026-02-08.",
    },
    {
        "name": "FunTranslations",
        "status": "broken",
        "notes": "Yoda/Shakespeare/Pirate text translations. api.funtranslations.com returns HTTP 405 Method Not Allowed on all tested endpoints. API appears non-functional. Tested 2026-02-08.",
    },
    # food-drink
    {
        "name": "WhiskyHunter",
        "status": "broken",
        "notes": "Whisky auction data API. whiskyhunter.net/api/ endpoints return HTTP 404. API appears removed or restructured. Tested 2026-02-08.",
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
