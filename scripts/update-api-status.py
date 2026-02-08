#!/usr/bin/env python3
"""Update an API entry's status, notes, and try-it config in apis.json.

Usage:
    python3 scripts/update-api-status.py "Dogs" --status working --notes "GET /api/breeds/image/random"
    python3 scripts/update-api-status.py "Dogs" --status working --try-url "https://dog.ceo/api/breeds/image/random" --try-type json
    python3 scripts/update-api-status.py "Cat Facts" --status broken --notes "herokuapp dead"
    python3 scripts/update-api-status.py "Dogs" --status working --dry-run
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "apis.json"

VALID_STATUSES = {"pending", "working", "broken", "paid-only", "needs-key", "skipped"}
VALID_RESPONSE_TYPES = {"json", "image", "text"}

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def find_matches(apis, query):
    """Find APIs matching the query (case-insensitive substring match)."""
    query_lower = query.lower()
    # Exact match first
    exact = [a for a in apis if a["name"].lower() == query_lower]
    if exact:
        return exact

    # Substring match
    return [a for a in apis if query_lower in a["name"].lower()]


def format_entry(api, label=""):
    """Pretty-print an API entry."""
    prefix = f"{label} " if label else ""
    lines = [
        f"{prefix}{BOLD}{api['name']}{RESET} ({api['category']})",
        f"  status:       {colorize_status(api['status'])}",
        f"  notes:        {api['notes'] or DIM + '(none)' + RESET}",
        f"  date-checked: {api['date-checked'] or DIM + '(none)' + RESET}",
        f"  try-it:       {format_tryit(api.get('try-it'))}",
    ]
    return "\n".join(lines)


def colorize_status(status):
    """Color a status string."""
    colors = {
        "pending": DIM,
        "working": GREEN,
        "broken": RED,
        "paid-only": YELLOW,
        "needs-key": YELLOW,
        "skipped": DIM,
    }
    return f"{colors.get(status, '')}{status}{RESET}"


def format_tryit(tryit):
    """Format try-it object for display."""
    if tryit is None:
        return f"{DIM}null{RESET}"
    parts = [tryit["url"], f"({tryit['response-type']})"]
    if "params" in tryit:
        parts.append(f"params={tryit['params']}")
    return " ".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Update an API entry in apis.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Dogs" --status working --notes "GET /api/breeds/image/random"
  %(prog)s "Dogs" --status working --try-url "https://dog.ceo/api/breeds/image/random" --try-type json
  %(prog)s "Cat Facts" --status broken --notes "herokuapp dead"
  %(prog)s "Dogs" --dry-run
        """,
    )
    parser.add_argument(
        "name", help="API name to search for (case-insensitive substring match)"
    )
    parser.add_argument(
        "--status", choices=sorted(VALID_STATUSES), help="New status value"
    )
    parser.add_argument("--notes", help="Testing notes (overwrites existing)")
    parser.add_argument("--try-url", help="Try-it endpoint URL")
    parser.add_argument(
        "--try-type", choices=sorted(VALID_RESPONSE_TYPES), help="Try-it response type"
    )
    parser.add_argument(
        "--try-params", help='Try-it params as JSON string, e.g. \'{"code": "200"}\''
    )
    parser.add_argument("--clear-tryit", action="store_true", help="Set try-it to null")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without writing"
    )
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip confirmation prompt"
    )
    parser.add_argument("--category", help="Filter matches to a specific category")
    args = parser.parse_args()

    if not args.status and not args.notes and not args.try_url and not args.clear_tryit:
        parser.error(
            "At least one of --status, --notes, --try-url, or --clear-tryit is required"
        )

    if args.try_url and not args.try_type:
        parser.error("--try-type is required when --try-url is specified")

    # Load data
    with open(DATA_FILE) as f:
        apis = json.load(f)

    # Find matches
    matches = find_matches(apis, args.name)

    if args.category:
        matches = [m for m in matches if m["category"] == args.category]

    if not matches:
        print(f"{RED}No API found matching '{args.name}'{RESET}")
        # Suggest close matches
        query_lower = args.name.lower()
        suggestions = [
            a for a in apis if any(w in a["name"].lower() for w in query_lower.split())
        ][:5]
        if suggestions:
            print(f"\n{YELLOW}Did you mean:{RESET}")
            for s in suggestions:
                print(f"  - {s['name']} ({s['category']})")
        sys.exit(1)

    if len(matches) > 1:
        print(f"{YELLOW}Multiple matches found for '{args.name}':{RESET}\n")
        for i, m in enumerate(matches):
            print(
                f"  [{i + 1}] {m['name']} ({m['category']}) — {colorize_status(m['status'])}"
            )
        print()

        if args.yes:
            print(
                f"{RED}Cannot use --yes with ambiguous matches. Be more specific or add --category.{RESET}"
            )
            sys.exit(1)

        try:
            choice = input(f"Select entry [1-{len(matches)}]: ").strip()
            idx = int(choice) - 1
            if idx < 0 or idx >= len(matches):
                raise ValueError
        except (ValueError, EOFError, KeyboardInterrupt):
            print(f"\n{RED}Cancelled.{RESET}")
            sys.exit(1)

        matches = [matches[idx]]

    api = matches[0]

    # Find the index in the original array
    api_index = next(i for i, a in enumerate(apis) if a is api)

    # Show current state
    print(f"\n{format_entry(api, f'{CYAN}BEFORE:{RESET}')}\n")

    # Apply changes
    if args.status:
        api["status"] = args.status

    if args.notes is not None:
        api["notes"] = args.notes

    # Auto-set date-checked when status changes from pending
    if args.status and args.status != "pending":
        api["date-checked"] = str(date.today())

    # Build try-it
    if args.try_url:
        tryit = {
            "url": args.try_url,
            "response-type": args.try_type,
        }
        if args.try_params:
            try:
                tryit["params"] = json.loads(args.try_params)
            except json.JSONDecodeError:
                print(f"{RED}Invalid JSON for --try-params: {args.try_params}{RESET}")
                sys.exit(1)
        api["try-it"] = tryit

    if args.clear_tryit:
        api["try-it"] = None

    # Show new state
    print(f"{format_entry(api, f'{GREEN}AFTER:{RESET}')}\n")

    # Confirm and write
    if args.dry_run:
        print(f"{YELLOW}Dry run — no changes written.{RESET}")
        return

    if not args.yes:
        try:
            confirm = input("Write changes? [Y/n] ").strip().lower()
            if confirm and confirm != "y":
                print(f"{RED}Cancelled.{RESET}")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print(f"\n{RED}Cancelled.{RESET}")
            sys.exit(0)

    # Write back
    apis[api_index] = api
    with open(DATA_FILE, "w") as f:
        json.dump(apis, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"{GREEN}Updated '{api['name']}' in {DATA_FILE.name}{RESET}")


if __name__ == "__main__":
    main()
