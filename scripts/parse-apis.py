#!/usr/bin/env python3
"""Parse public-apis.md into structured JSON."""

import json
import re
import sys
from pathlib import Path


def slugify(text):
    """Convert category name to kebab-case slug."""
    slug = text.lower()
    slug = re.sub(r"[&]", "", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def parse_auth(raw):
    """Normalize auth field to kebab-case."""
    stripped = raw.strip("` ")
    mapping = {
        "no": "none",
        "apikey": "api-key",
        "oauth": "oauth",
        "x-mashape-key": "x-mashape-key",
        "user-agent": "user-agent",
    }
    return mapping.get(stripped.lower(), stripped.lower())


def parse_cors(raw):
    """Normalize CORS field."""
    val = raw.strip().lower()
    if val in ("unkown", "unknown", ""):
        return "unknown"
    return val


ROW_PATTERN = re.compile(
    r"^\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|"  # name and url
    r"\s*(.+?)\s*\|"  # description
    r"\s*(`[^`]+`|No)\s*\|"  # auth
    r"\s*(Yes|No|YES)\s*\|"  # HTTPS (some entries use uppercase)
    r"\s*(Yes|No|Unknown|Unkown|)\s*"  # CORS (some empty or missing)
    r"\|?\s*"  # optional trailing pipe and whitespace
)


def parse_apis(md_path):
    apis = []
    current_category = None

    for line in md_path.read_text(encoding="utf-8").splitlines():
        # Detect category headers (### only, skip ## sections)
        if line.startswith("### "):
            current_category = slugify(line[4:].strip())
            continue

        # Only parse rows that start with | [
        if not line.startswith("| ["):
            continue

        match = ROW_PATTERN.match(line)
        if not match:
            continue

        # Skip entries without a category (e.g., promotional tables)
        if current_category is None:
            continue

        apis.append(
            {
                "name": match.group(1),
                "url": match.group(2),
                "description": match.group(3).replace("\t", " ").strip(),
                "auth": parse_auth(match.group(4)),
                "https": match.group(5).lower() == "yes",
                "cors": parse_cors(match.group(6)),
                "category": current_category,
                "status": "pending",
                "notes": "",
                "date-checked": None,
            }
        )

    return apis


def main():
    root = Path(__file__).resolve().parent.parent
    md_path = root / "public-apis.md"
    out_path = root / "data" / "apis.json"
    out_path.parent.mkdir(exist_ok=True)

    # Safety check: don't overwrite tested data
    if out_path.exists() and "--force" not in sys.argv:
        existing = json.loads(out_path.read_text(encoding="utf-8"))
        tested = [a for a in existing if a.get("status") != "pending"]
        if tested:
            print(f"ERROR: {out_path} has {len(tested)} tested APIs.")
            print("Running this script will reset all statuses to pending.")
            print("Use --force to overwrite.")
            sys.exit(1)

    apis = parse_apis(md_path)
    out_path.write_text(
        json.dumps(apis, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Summary
    categories = sorted(set(a["category"] for a in apis))
    print(f"Parsed {len(apis)} APIs across {len(categories)} categories")
    by_auth = {}
    for a in apis:
        by_auth[a["auth"]] = by_auth.get(a["auth"], 0) + 1
    for auth, count in sorted(by_auth.items()):
        print(f"  {auth}: {count}")


if __name__ == "__main__":
    main()
