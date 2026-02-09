#!/usr/bin/env python3
"""Apply batch updates to apis.json from a JSON session file.

Usage:
    python3 scripts/batch-update.py data/sessions/session-17.json
    python3 scripts/batch-update.py data/sessions/session-17.json --dry-run

Session file format (JSON array):
[
  {
    "name": "API Name",
    "status": "working",
    "notes": "Testing notes...",
    "try-it": {
      "url": "https://api.example.com/endpoint",
      "response-type": "json",
      "params": {"key": "value"}
    }
  },
  {
    "name": "Dead API",
    "status": "broken",
    "notes": "Returns 404. Tested 2026-02-08."
  }
]

- "name" and "status" are required
- "notes" is required
- "try-it" is optional (only for working APIs with GET endpoints)
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "apis.json"

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

STATUS_COLORS = {
    "working": GREEN,
    "broken": RED,
    "needs-key": YELLOW,
    "paid-only": YELLOW,
    "skipped": DIM,
}

VALID_STATUSES = {"pending", "working", "broken", "paid-only", "needs-key", "skipped"}


def main():
    parser = argparse.ArgumentParser(description="Apply batch updates from a JSON session file")
    parser.add_argument("session_file", help="Path to session JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    # Load session file
    session_path = Path(args.session_file)
    if not session_path.exists():
        print(f"{RED}Session file not found: {session_path}{RESET}")
        sys.exit(1)

    with open(session_path) as f:
        updates = json.load(f)

    if not isinstance(updates, list):
        print(f"{RED}Session file must contain a JSON array{RESET}")
        sys.exit(1)

    # Validate updates
    for i, u in enumerate(updates):
        if "name" not in u:
            print(f"{RED}Entry {i} missing 'name'{RESET}")
            sys.exit(1)
        if "status" not in u:
            print(f"{RED}Entry {i} ({u['name']}) missing 'status'{RESET}")
            sys.exit(1)
        if u["status"] not in VALID_STATUSES:
            print(f"{RED}Entry {i} ({u['name']}) invalid status: {u['status']}{RESET}")
            sys.exit(1)
        if "notes" not in u:
            print(f"{RED}Entry {i} ({u['name']}) missing 'notes'{RESET}")
            sys.exit(1)

    # Load apis.json
    with open(DATA_FILE) as f:
        apis = json.load(f)

    today = str(date.today())
    success = 0
    failed = 0

    print(f"\n{BOLD}Applying {len(updates)} updates from {session_path.name}{RESET}")
    if args.dry_run:
        print(f"{YELLOW}(dry run — no changes will be written){RESET}")
    print()

    for u in updates:
        matches = [a for a in apis if a["name"].lower() == u["name"].lower()]
        if not matches:
            print(f"  {RED}NOT FOUND:{RESET} {u['name']}")
            failed += 1
            continue

        api = matches[0]
        old_status = api.get("status", "pending")
        new_status = u["status"]
        color = STATUS_COLORS.get(new_status, "")

        if not args.dry_run:
            api["status"] = new_status
            api["notes"] = u["notes"]
            if new_status != "pending":
                api["date-checked"] = today
            if "try-it" in u:
                api["try-it"] = u["try-it"]

        print(f"  {u['name']:<40s} {DIM}{old_status:<10s}{RESET} -> {color}{new_status}{RESET}")
        success += 1

    if not args.dry_run and success > 0:
        with open(DATA_FILE, "w") as f:
            json.dump(apis, f, indent=2, ensure_ascii=False)
            f.write("\n")

    print(f"\n{BOLD}Done:{RESET} {success} updated, {failed} failed out of {len(updates)} total")
    if args.dry_run:
        print(f"{YELLOW}No changes written (dry run){RESET}")


if __name__ == "__main__":
    main()
