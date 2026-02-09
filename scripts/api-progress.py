#!/usr/bin/env python3
"""Display progress statistics for API testing.

Usage:
    python3 scripts/api-progress.py                    # Overall summary
    python3 scripts/api-progress.py --auth none         # Filter by auth type
    python3 scripts/api-progress.py --category animals  # Detail for one category
    python3 scripts/api-progress.py --category animals --auth none  # Combined
    python3 scripts/api-progress.py --category animals --pending    # List pending APIs only
    python3 scripts/api-progress.py --auth none --next              # Suggest categories to close out
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "apis.json"

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"
WHITE = "\033[97m"

STATUS_COLORS = {
    "pending": DIM,
    "working": GREEN,
    "broken": RED,
    "paid-only": YELLOW,
    "needs-key": YELLOW,
    "skipped": DIM,
}

ALL_STATUSES = ["working", "broken", "needs-key", "paid-only", "skipped", "pending"]


def colorize(text, color):
    return f"{color}{text}{RESET}"


def pct(n, total):
    return f"{n / total * 100:.0f}%" if total > 0 else "0%"


def print_summary_table(categories, totals_row=None):
    """Print a formatted table of category stats."""
    # Column headers
    headers = ["Category", "Total", "Wkg", "Brk", "Key", "Paid", "Skip", "Pnd", "Done"]
    widths = [22, 6, 5, 5, 5, 5, 5, 5, 6]

    # Header line
    header = ""
    for h, w in zip(headers, widths):
        header += f"{BOLD}{h:<{w}}{RESET} "
    print(header)
    print("─" * (sum(widths) + len(widths)))

    # Data rows
    for cat in categories:
        total = cat["total"]
        tested = total - cat.get("pending", 0)
        done_pct = pct(tested, total)

        row_parts = [
            f"{cat['name']:<{widths[0]}}",
            f"{total:<{widths[1]}}",
            colorize(f"{cat.get('working', 0):<{widths[2]}}", GREEN),
            colorize(f"{cat.get('broken', 0):<{widths[3]}}", RED),
            colorize(f"{cat.get('needs-key', 0):<{widths[4]}}", YELLOW),
            colorize(f"{cat.get('paid-only', 0):<{widths[5]}}", YELLOW),
            colorize(f"{cat.get('skipped', 0):<{widths[6]}}", DIM),
            colorize(f"{cat.get('pending', 0):<{widths[7]}}", DIM),
            f"{done_pct:<{widths[8]}}",
        ]
        print(" ".join(row_parts))

    # Totals row
    if totals_row:
        print("─" * (sum(widths) + len(widths)))
        total = totals_row["total"]
        tested = total - totals_row.get("pending", 0)
        done_pct = pct(tested, total)

        row_parts = [
            f"{BOLD}{'TOTAL':<{widths[0]}}{RESET}",
            f"{BOLD}{total:<{widths[1]}}{RESET}",
            colorize(f"{totals_row.get('working', 0):<{widths[2]}}", GREEN),
            colorize(f"{totals_row.get('broken', 0):<{widths[3]}}", RED),
            colorize(f"{totals_row.get('needs-key', 0):<{widths[4]}}", YELLOW),
            colorize(f"{totals_row.get('paid-only', 0):<{widths[5]}}", YELLOW),
            colorize(f"{totals_row.get('skipped', 0):<{widths[6]}}", DIM),
            colorize(f"{totals_row.get('pending', 0):<{widths[7]}}", DIM),
            f"{BOLD}{done_pct:<{widths[8]}}{RESET}",
        ]
        print(" ".join(row_parts))


def print_category_detail(apis, category):
    """Print detailed listing for a single category."""
    cat_apis = [a for a in apis if a["category"] == category]
    if not cat_apis:
        print(f"{RED}No APIs found in category '{category}'{RESET}")
        available = sorted(set(a["category"] for a in apis))
        print(f"\n{YELLOW}Available categories:{RESET}")
        for c in available:
            print(f"  - {c}")
        sys.exit(1)

    # Sort: pending last, then alphabetically
    status_order = {"working": 0, "broken": 1, "needs-key": 2, "paid-only": 3, "skipped": 4, "pending": 5}
    cat_apis.sort(key=lambda a: (status_order.get(a["status"], 9), a["name"].lower()))

    print(f"\n{BOLD}{category}{RESET} — {len(cat_apis)} APIs\n")

    for api in cat_apis:
        status_str = colorize(f"{api['status']:<10}", STATUS_COLORS.get(api["status"], ""))
        auth_str = f"{DIM}{api['auth']:<12}{RESET}"
        notes = f" — {api['notes']}" if api["notes"] else ""
        print(f"  {status_str} {auth_str} {api['name']}{DIM}{notes}{RESET}")

    # Summary
    counts = defaultdict(int)
    for a in cat_apis:
        counts[a["status"]] += 1

    tested = len(cat_apis) - counts["pending"]
    print(f"\n  {BOLD}Summary:{RESET} {tested}/{len(cat_apis)} tested ({pct(tested, len(cat_apis))})")
    for status in ALL_STATUSES:
        if counts[status] > 0:
            print(f"    {colorize(f'{status}:', STATUS_COLORS[status])} {counts[status]}")


def main():
    parser = argparse.ArgumentParser(description="API testing progress dashboard")
    parser.add_argument("--category", "-c", help="Show detail for a specific category")
    parser.add_argument("--auth", "-a", help="Filter by auth type (none, api-key, oauth, etc.)")
    parser.add_argument("--sort", choices=["name", "total", "done", "pending"],
                        default="name", help="Sort categories by (default: name)")
    parser.add_argument("--pending", "-p", action="store_true",
                        help="List only pending API names (use with --category)")
    parser.add_argument("--next", "-n", action="store_true",
                        help="Suggest categories closest to completion")
    args = parser.parse_args()

    # Load data
    with open(DATA_FILE) as f:
        apis = json.load(f)

    # Filter by auth if specified
    if args.auth:
        apis = [a for a in apis if a["auth"] == args.auth]
        if not apis:
            print(f"{RED}No APIs found with auth type '{args.auth}'{RESET}")
            sys.exit(1)
        print(f"{CYAN}Filtered to auth: {args.auth} ({len(apis)} APIs){RESET}\n")

    # Pending list mode (requires --category)
    if args.pending:
        if not args.category:
            print(f"{RED}--pending requires --category{RESET}")
            sys.exit(1)
        cat_apis = [a for a in apis if a["category"] == args.category and a["status"] == "pending"]
        if not cat_apis:
            print(f"{GREEN}No pending APIs in '{args.category}'{RESET}")
            return
        print(f"\n{BOLD}{args.category}{RESET} — {len(cat_apis)} pending\n")
        for api in sorted(cat_apis, key=lambda a: a["name"].lower()):
            auth_str = f"{DIM}{api['auth']:<12}{RESET}"
            print(f"  {auth_str} {api['name']}")
            print(f"             {DIM}{api['url']}{RESET}")
        print()
        return

    # Next categories mode
    if args.next:
        cat_stats = defaultdict(lambda: defaultdict(int))
        for api in apis:
            cat = api["category"]
            cat_stats[cat]["total"] += 1
            cat_stats[cat][api["status"]] += 1

        # Only categories with pending APIs, sorted by fewest pending
        candidates = []
        for name, stats in cat_stats.items():
            pending = stats.get("pending", 0)
            if pending > 0:
                candidates.append({
                    "name": name,
                    "pending": pending,
                    "total": stats["total"],
                    "tested": stats["total"] - pending,
                })
        candidates.sort(key=lambda c: c["pending"])

        print(f"\n{BOLD}Categories closest to completion:{RESET}\n")
        for cat in candidates[:10]:
            pct_done = cat["tested"] / cat["total"] * 100
            bar_width = 20
            filled = int(pct_done / 100 * bar_width)
            bar = f"{GREEN}{'█' * filled}{RESET}{DIM}{'░' * (bar_width - filled)}{RESET}"
            print(f"  {cat['name']:<25} {bar} {cat['tested']}/{cat['total']} ({cat['pending']} pending)")
        print()
        return

    # Category detail mode
    if args.category:
        print_category_detail(apis, args.category)
        return

    # Build per-category stats
    cat_stats = defaultdict(lambda: defaultdict(int))
    for api in apis:
        cat = api["category"]
        cat_stats[cat]["total"] += 1
        cat_stats[cat][api["status"]] += 1

    # Convert to list for sorting
    categories = []
    for name, stats in cat_stats.items():
        row = {"name": name, **stats}
        categories.append(row)

    # Sort
    if args.sort == "name":
        categories.sort(key=lambda c: c["name"])
    elif args.sort == "total":
        categories.sort(key=lambda c: -c["total"])
    elif args.sort == "done":
        categories.sort(key=lambda c: -(c["total"] - c.get("pending", 0)))
    elif args.sort == "pending":
        categories.sort(key=lambda c: -c.get("pending", 0))

    # Compute totals
    totals = {"total": 0}
    for cat in categories:
        totals["total"] += cat["total"]
        for status in ALL_STATUSES:
            totals[status] = totals.get(status, 0) + cat.get(status, 0)

    # Print header
    auth_label = f" (auth: {args.auth})" if args.auth else ""
    print(f"{BOLD}Public APIs Progress{auth_label}{RESET}")
    tested = totals["total"] - totals.get("pending", 0)
    print(f"{tested}/{totals['total']} tested ({pct(tested, totals['total'])})\n")

    # Print table
    print_summary_table(categories, totals_row=totals)
    print()


if __name__ == "__main__":
    main()
