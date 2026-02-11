#!/usr/bin/env python3
"""Merge new APIs from public-apis-2 into this project's apis.json.

Reads both data files, classifies each source entry as duplicate/url-update/new,
and optionally writes merged output directly into apis.json.

Usage:
    python3 scripts/merge-apis-2.py              # dry-run (preview only)
    python3 scripts/merge-apis-2.py --apply       # merge into apis.json + write reports
    python3 scripts/merge-apis-2.py --verbose     # show per-entry classification
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
TARGET_FILE = ROOT / "data" / "apis.json"
SOURCE_FILE = ROOT.parent / "public-apis-2" / "db" / "resources.json"
REPORT_DIR = ROOT / "data" / "merge-report"

# ANSI colors (matches batch-update.py)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Auth normalization: source -> target
AUTH_MAP: dict[str, str] = {
    "": "none",
    "apikey": "api-key",
    "oauth": "oauth",
    "x-mashape-key": "x-mashape-key",
    "user-agent": "user-agent",
    "yes": "api-key",  # data quality issue in source
}

# Domains too generic for meaningful domain-level matching
GENERIC_DOMAINS: frozenset[str] = frozenset({
    "github.com", "github.io", "gitlab.com", "bitbucket.org",
    "herokuapp.com", "netlify.app", "vercel.app", "render.com",
    "replit.com", "glitch.me", "firebase.google.com",
    "documenter.getpostman.com", "rapidapi.com", "readme.io",
    "swagger.io", "postman.com", "apiary.io",
})


# --- Transformation functions ---

def slugify(text: str) -> str:
    """Convert category name to kebab-case slug. Exact match of parse-apis.py."""
    slug = text.lower()
    slug = re.sub(r"[&]", "", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def normalize_auth(raw: str) -> str:
    """Map source auth value to target format."""
    key = raw.strip().lower()
    result = AUTH_MAP.get(key)
    if result is None:
        return "api-key"
    return result


def normalize_url(url: str) -> str:
    """Normalize URL for comparison: strip whitespace, trailing slash, www prefix."""
    url = url.strip().rstrip("/")
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/")
    return host + path


def get_domain(url: str) -> str:
    """Extract domain from URL, stripping www prefix."""
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def transform_entry(src: dict) -> dict:
    """Convert a public-apis-2 entry to public-apis schema."""
    return {
        "name": src["API"],
        "url": src["Link"],
        "description": src["Description"],
        "auth": normalize_auth(src["Auth"]),
        "https": src["HTTPS"],
        "cors": src["Cors"].lower(),
        "category": slugify(src["Category"]),
        "status": "pending",
        "notes": "",
        "date-checked": None,
        "try-it": None,
    }


# --- Lookup structures ---

@dataclass(frozen=True)
class TargetLookup:
    """Indexed views into the target data for fast matching."""
    by_name: dict[str, list[dict]]
    by_url: dict[str, list[dict]]
    by_domain: dict[str, list[dict]]
    by_name_cat: dict[tuple[str, str], list[dict]]


def build_lookup(target: list[dict]) -> TargetLookup:
    """Build lookup indexes from target data."""
    by_name: dict[str, list[dict]] = {}
    by_url: dict[str, list[dict]] = {}
    by_domain: dict[str, list[dict]] = {}
    by_name_cat: dict[tuple[str, str], list[dict]] = {}

    for api in target:
        name_key = api["name"].lower()
        by_name.setdefault(name_key, []).append(api)

        url_key = normalize_url(api["url"])
        by_url.setdefault(url_key, []).append(api)

        domain = get_domain(api["url"])
        if domain and domain not in GENERIC_DOMAINS:
            by_domain.setdefault(domain, []).append(api)

        cat_key = (name_key, api["category"])
        by_name_cat.setdefault(cat_key, []).append(api)

    return TargetLookup(
        by_name=by_name,
        by_url=by_url,
        by_domain=by_domain,
        by_name_cat=by_name_cat,
    )


# --- Classification ---

@dataclass
class MergeResults:
    """Collects classified entries during merge."""
    duplicates: list[dict] = field(default_factory=list)
    renamed: list[dict] = field(default_factory=list)
    url_updates: list[dict] = field(default_factory=list)
    url_updates_applied: list[dict] = field(default_factory=list)
    cross_category: list[dict] = field(default_factory=list)
    domain_matches: list[dict] = field(default_factory=list)
    new_apis: list[dict] = field(default_factory=list)


def classify_and_merge(
    source: list[dict],
    target: list[dict],
    lookup: TargetLookup,
    verbose: bool = False,
) -> MergeResults:
    """Classify each source entry and collect results."""
    results = MergeResults()

    for src in source:
        transformed = transform_entry(src)
        name_key = transformed["name"].lower()
        url_key = normalize_url(transformed["url"])
        domain = get_domain(transformed["url"])
        category = transformed["category"]

        # Tier 1: Exact name + URL match → definite duplicate
        name_matches = lookup.by_name.get(name_key, [])
        url_matches = lookup.by_url.get(url_key, [])

        if name_matches and url_matches:
            # Both name and URL exist in target
            results.duplicates.append(transformed)
            if verbose:
                print(f"  {DIM}DUPLICATE:{RESET} {transformed['name']}")
            continue

        # Tier 2: URL match but name differs → renamed API
        if url_matches:
            existing = url_matches[0]
            results.renamed.append({
                "source-name": transformed["name"],
                "existing-name": existing["name"],
                "url": transformed["url"],
                "category": category,
            })
            if verbose:
                print(f"  {DIM}RENAMED:{RESET} {transformed['name']} = {existing['name']}")
            continue

        # Tier 3: Name + category match, URL differs → possible URL update
        cat_matches = lookup.by_name_cat.get((name_key, category), [])
        if cat_matches:
            existing = cat_matches[0]
            entry = {
                "name": transformed["name"],
                "category": category,
                "current-url": existing["url"],
                "current-status": existing["status"],
                "source-url": transformed["url"],
            }
            # Auto-update if existing is broken
            if existing["status"] == "broken":
                existing["url"] = transformed["url"]
                existing["status"] = "pending"
                existing["notes"] = f"URL updated from public-apis-2 (was broken). Previous: {existing['notes']}"
                existing["date-checked"] = None
                existing["try-it"] = None
                entry["action"] = "auto-updated"
                results.url_updates_applied.append(entry)
                if verbose:
                    print(f"  {GREEN}URL UPDATE (broken → pending):{RESET} {transformed['name']}")
            else:
                entry["action"] = "flagged"
                results.url_updates.append(entry)
                if verbose:
                    print(f"  {YELLOW}URL DIFF:{RESET} {transformed['name']} ({existing['status']})")
            continue

        # Tier 4: Name match but different category → flag for review
        if name_matches:
            existing = name_matches[0]
            results.cross_category.append({
                "source-name": transformed["name"],
                "source-category": category,
                "existing-name": existing["name"],
                "existing-category": existing["category"],
                "source-url": transformed["url"],
                "existing-url": existing["url"],
            })
            if verbose:
                print(f"  {YELLOW}CROSS-CAT:{RESET} {transformed['name']} ({category} vs {existing['category']})")
            continue

        # Tier 5: Domain match (non-generic) → add as new, note in report
        if domain and domain not in GENERIC_DOMAINS:
            domain_hits = lookup.by_domain.get(domain, [])
            if domain_hits:
                existing = domain_hits[0]
                results.domain_matches.append({
                    "source-name": transformed["name"],
                    "source-url": transformed["url"],
                    "source-category": category,
                    "existing-name": existing["name"],
                    "existing-url": existing["url"],
                    "existing-category": existing["category"],
                    "action": "added-as-new",
                })
                if verbose:
                    print(f"  {CYAN}DOMAIN MATCH (added):{RESET} {transformed['name']} ~ {existing['name']}")
                results.new_apis.append(transformed)
                continue

        # Tier 6: Genuinely new
        results.new_apis.append(transformed)
        if verbose:
            print(f"  {GREEN}NEW:{RESET} {transformed['name']} ({category})")

    return results


# --- Insertion ---

def insert_sorted(existing: list[dict], new_entries: list[dict]) -> list[dict]:
    """Insert new entries alphabetically within their categories.

    Returns a new list — never mutates existing.
    """
    by_cat: dict[str, list[dict]] = {}
    for api in existing:
        by_cat.setdefault(api["category"], []).append(api)
    for api in new_entries:
        by_cat.setdefault(api["category"], []).append(api)

    result: list[dict] = []
    for cat in sorted(by_cat.keys()):
        entries = sorted(by_cat[cat], key=lambda a: a["name"].lower())
        result.extend(entries)

    return result


# --- Reporting ---

def print_report(results: MergeResults, target_count: int, source_count: int) -> None:
    """Print color-coded summary to console."""
    print(f"\n{BOLD}MERGE REPORT: public-apis-2 → public-apis{RESET}")
    print("=" * 50)
    print(f"Source: {source_count} entries")
    print(f"Target: {target_count} entries")

    print(f"\n{BOLD}CLASSIFICATION{RESET}")
    print(f"  Exact duplicates (skipped):      {len(results.duplicates):>4}")
    print(f"  URL match, renamed (skipped):    {len(results.renamed):>4}")
    print(f"  Name+cat match, URL differs:     {len(results.url_updates):>4}")
    print(f"  Name+cat match, URL auto-updated:{len(results.url_updates_applied):>4}")
    print(f"  Name match, diff category:       {len(results.cross_category):>4}")
    print(f"  Domain match (added as new):     {len(results.domain_matches):>4}")
    print(f"  {GREEN}Genuinely new:                   {len(results.new_apis):>4}{RESET}")

    # New categories
    existing_cats = set()
    new_cats: dict[str, int] = {}
    for api in results.new_apis:
        cat = api["category"]
        new_cats[cat] = new_cats.get(cat, 0) + 1

    # We need target categories to figure out which are truly new
    # (handled in main where we have access to target data)

    # New entries by category (top 15)
    if results.new_apis:
        cat_counts: dict[str, int] = {}
        for api in results.new_apis:
            cat_counts[api["category"]] = cat_counts.get(api["category"], 0) + 1
        sorted_cats = sorted(cat_counts.items(), key=lambda x: -x[1])

        print(f"\n{BOLD}NEW ENTRIES BY CATEGORY{RESET}")
        for cat, count in sorted_cats[:15]:
            print(f"  {cat:<35} {count:>3}")
        if len(sorted_cats) > 15:
            remaining = sum(c for _, c in sorted_cats[15:])
            print(f"  {DIM}... {len(sorted_cats) - 15} more categories ({remaining} entries){RESET}")

    # URL updates for broken APIs
    if results.url_updates_applied:
        print(f"\n{BOLD}URL UPDATES APPLIED (broken → pending){RESET}")
        for u in results.url_updates_applied:
            print(f"  {u['name']}: {DIM}{u['current-url']}{RESET}")
            print(f"    → {GREEN}{u['source-url']}{RESET}")

    # Flagged URL diffs (not broken)
    if results.url_updates:
        print(f"\n{BOLD}URL DIFFS (not broken, flagged only){RESET}")
        for u in results.url_updates[:10]:
            print(f"  {u['name']} ({u['current-status']}): {DIM}{u['current-url']}{RESET}")
            print(f"    → {YELLOW}{u['source-url']}{RESET}")
        if len(results.url_updates) > 10:
            print(f"  {DIM}... {len(results.url_updates) - 10} more{RESET}")


def write_reports(results: MergeResults, output_dir: Path) -> None:
    """Write JSON report files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # New APIs
    new_path = output_dir / "new-apis.json"
    new_path.write_text(
        json.dumps(results.new_apis, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # URL updates
    all_url_updates = results.url_updates + results.url_updates_applied
    if all_url_updates:
        url_path = output_dir / "url-updates.json"
        url_path.write_text(
            json.dumps(all_url_updates, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # Flagged for review
    flagged = results.cross_category + results.domain_matches
    if flagged:
        flag_path = output_dir / "flagged-review.json"
        flag_path.write_text(
            json.dumps(flagged, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # Text report
    report_lines = [
        f"Merge Report — {date.today()}",
        f"New APIs added: {len(results.new_apis)}",
        f"URL updates applied (broken): {len(results.url_updates_applied)}",
        f"URL diffs flagged: {len(results.url_updates)}",
        f"Cross-category flags: {len(results.cross_category)}",
        f"Domain match flags: {len(results.domain_matches)}",
        f"Duplicates skipped: {len(results.duplicates)}",
        f"Renamed skipped: {len(results.renamed)}",
    ]
    report_path = output_dir / "merge-report.txt"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"\n{BOLD}Files written:{RESET}")
    print(f"  {new_path}")
    if all_url_updates:
        print(f"  {output_dir / 'url-updates.json'}")
    if flagged:
        print(f"  {output_dir / 'flagged-review.json'}")
    print(f"  {report_path}")


# --- Main ---

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge new APIs from public-apis-2 into apis.json"
    )
    parser.add_argument("--apply", action="store_true",
                        help="Write merged data to apis.json (default is dry-run)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show per-entry classification")
    parser.add_argument("--source", type=Path, default=SOURCE_FILE,
                        help=f"Source file (default: {SOURCE_FILE})")
    args = parser.parse_args()

    # Validate input files
    if not TARGET_FILE.exists():
        print(f"{RED}Target not found: {TARGET_FILE}{RESET}")
        sys.exit(1)
    if not args.source.exists():
        print(f"{RED}Source not found: {args.source}{RESET}")
        sys.exit(1)

    # Load data
    with open(TARGET_FILE, encoding="utf-8") as f:
        target = json.load(f)
    with open(args.source, encoding="utf-8") as f:
        source_data = json.load(f)

    source = source_data["entries"]

    # Count tested entries before merge (for verification)
    tested_before = sum(1 for a in target if a["status"] != "pending")

    print(f"{BOLD}Merging public-apis-2 → public-apis{RESET}")
    print(f"Source: {len(source)} entries")
    print(f"Target: {len(target)} entries ({tested_before} tested)")
    if not args.apply:
        print(f"{YELLOW}(dry run — no changes will be written){RESET}")
    print()

    # Build lookup and classify
    lookup = build_lookup(target)
    results = classify_and_merge(source, target, lookup, verbose=args.verbose)

    # Identify new categories
    existing_cats = {a["category"] for a in target}
    new_cat_entries = [a for a in results.new_apis if a["category"] not in existing_cats]
    new_cats = sorted({a["category"] for a in new_cat_entries})

    # Print report
    print_report(results, len(target), len(source))

    if new_cats:
        print(f"\n{BOLD}NEW CATEGORIES{RESET}")
        for cat in new_cats:
            count = sum(1 for a in results.new_apis if a["category"] == cat)
            print(f"  {GREEN}{cat}{RESET}: {count} entries")

    if not results.new_apis and not results.url_updates_applied:
        print(f"\n{YELLOW}Nothing to merge.{RESET}")
        return

    # Apply or preview
    if args.apply:
        merged = insert_sorted(target, results.new_apis)

        # Verify no tested data lost (account for broken→pending URL updates)
        tested_after = sum(1 for a in merged if a["status"] != "pending")
        expected_tested = tested_before - len(results.url_updates_applied)
        if tested_after < expected_tested:
            print(f"\n{RED}ERROR: Tested count dropped from {tested_before} to {tested_after} "
                  f"(expected {expected_tested} after {len(results.url_updates_applied)} URL updates). "
                  f"Aborting.{RESET}")
            sys.exit(1)

        # Write merged apis.json
        with open(TARGET_FILE, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
            f.write("\n")

        print(f"\n{GREEN}Wrote {len(merged)} entries to {TARGET_FILE.name}{RESET}")
        print(f"  (was {len(target)}, added {len(results.new_apis)} new)")
        print(f"  Tested entries preserved: {tested_after}")

        # Write report files
        write_reports(results, REPORT_DIR)
    else:
        print(f"\n{YELLOW}Dry run complete. Use --apply to write changes.{RESET}")
        # Still write report files in dry-run for review
        write_reports(results, REPORT_DIR)


if __name__ == "__main__":
    main()
