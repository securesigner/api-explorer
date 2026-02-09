#!/usr/bin/env python3
"""Health check working APIs by hitting their try-it endpoints.

Usage:
    python3 scripts/api-healthcheck.py                     # Check all working APIs
    python3 scripts/api-healthcheck.py --category animals   # Check one category
    python3 scripts/api-healthcheck.py --fix                # Auto-mark failures as broken
    python3 scripts/api-healthcheck.py --timeout 5          # Custom timeout per request
    python3 scripts/api-healthcheck.py --verbose            # Show response details
"""

# SECURITY NOTE — SSRF risk accepted for local dev tool
#
# This script makes HTTP requests to URLs stored in data/apis.json:
#   - SSL verification is disabled (some APIs have expired/invalid certs)
#   - Redirects are followed by default (urllib behavior)
#   - No URL scheme or destination validation in this script
#
# This is acceptable because:
#   - This script runs locally on the developer's machine only
#   - It is never deployed to any server or CI/CD pipeline
#   - URLs in apis.json are validated at commit time by the pre-commit hook
#     (.claude/hooks/pre-commit-api-validate.sh) which rejects private IPs,
#     localhost, and dangerous URL schemes (file://, javascript://, etc.)
#   - The pre-commit hook is the security boundary; this script trusts the data
#
# If this script is ever used in a shared or automated context, add:
#   1. URL allowlist validation before each request
#   2. SSL verification (remove ctx.check_hostname/ctx.verify_mode overrides)
#   3. Redirect chain validation

import argparse
import json
import sys
import urllib.request
import urllib.error
import ssl
import re
from datetime import date
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


def resolve_url(url, params=None):
    """Replace {placeholder} tokens in URL with param defaults."""
    if not params:
        return url
    for key, val in params.items():
        url = url.replace(f"{{{key}}}", str(val))
    return url


def check_api(api, timeout=10, verbose=False):
    """Check a single API's try-it endpoint. Returns (passed, detail)."""
    tryit = api.get("try-it")
    if not tryit or not tryit.get("url"):
        return None, "no try-it URL"

    url = resolve_url(tryit["url"], tryit.get("params"))
    expected_type = tryit.get("response-type", "json")

    try:
        # Create SSL context that doesn't verify (some APIs have cert issues)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, headers={
            "User-Agent": "PublicAPIs-HealthCheck/1.0",
            "Accept": "application/json, text/plain, image/*, */*",
        })

        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            status = resp.status
            content_type = resp.headers.get("Content-Type", "")
            body = resp.read(4096)  # Read up to 4KB for validation

            if status < 200 or status >= 400:
                return False, f"HTTP {status}"

            # Validate response type
            if expected_type == "json":
                try:
                    json.loads(body)
                    detail = f"HTTP {status}, valid JSON ({len(body)} bytes)"
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Some APIs return valid data but not UTF-8 parseable in first 4KB
                    if "json" in content_type.lower() or "javascript" in content_type.lower():
                        detail = f"HTTP {status}, JSON content-type ({len(body)} bytes)"
                    else:
                        return False, f"HTTP {status}, expected JSON but got {content_type}"
            elif expected_type == "image":
                if "image" in content_type.lower() or len(body) > 100:
                    detail = f"HTTP {status}, {content_type} ({len(body)} bytes)"
                else:
                    return False, f"HTTP {status}, expected image but got {content_type}"
            else:
                detail = f"HTTP {status}, {len(body)} bytes"

            if verbose:
                detail += f"\n    Content-Type: {content_type}"
                if expected_type in ("json", "text"):
                    preview = body[:200].decode("utf-8", errors="replace")
                    detail += f"\n    Preview: {preview}"

            return True, detail

    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        reason = str(e.reason) if hasattr(e, "reason") else str(e)
        return False, f"URL error: {reason}"
    except TimeoutError:
        return False, "Connection timeout"
    except OSError as e:
        return False, f"Connection error: {e}"
    except Exception as e:
        return False, f"Error: {type(e).__name__}: {e}"


def main():
    parser = argparse.ArgumentParser(description="Health check working APIs")
    parser.add_argument("--category", "-c", help="Check only APIs in this category")
    parser.add_argument("--timeout", "-t", type=int, default=10,
                        help="Timeout per request in seconds (default: 10)")
    parser.add_argument("--fix", action="store_true",
                        help="Auto-mark failed APIs as broken")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show response details")
    args = parser.parse_args()

    # Load data
    with open(DATA_FILE) as f:
        apis = json.load(f)

    # Filter to working APIs
    candidates = [a for a in apis if a["status"] == "working"]

    if args.category:
        candidates = [a for a in candidates if a["category"] == args.category]

    if not candidates:
        cat_msg = f" in category '{args.category}'" if args.category else ""
        print(f"{YELLOW}No working APIs found{cat_msg}{RESET}")
        sys.exit(0)

    # Separate those with try-it URLs from those without
    testable = [a for a in candidates if a.get("try-it") and a["try-it"].get("url")]
    skipped = [a for a in candidates if not a.get("try-it") or not a["try-it"].get("url")]

    cat_label = f" ({args.category})" if args.category else ""
    print(f"{BOLD}Health Check{cat_label}{RESET}")
    print(f"{len(testable)} testable, {len(skipped)} skipped (no try-it URL)\n")

    passed = 0
    failed = 0
    failed_apis = []

    for i, api in enumerate(testable, 1):
        url = resolve_url(api["try-it"]["url"], api["try-it"].get("params"))
        # Truncate URL for display
        display_url = url[:60] + "..." if len(url) > 63 else url

        sys.stdout.write(f"  [{i}/{len(testable)}] {api['name']:<30} ")
        sys.stdout.flush()

        ok, detail = check_api(api, timeout=args.timeout, verbose=args.verbose)

        if ok:
            print(f"{GREEN}PASS{RESET}  {DIM}{detail}{RESET}")
            passed += 1
        else:
            print(f"{RED}FAIL{RESET}  {detail}")
            failed += 1
            failed_apis.append(api)

    # Summary
    print(f"\n{'─' * 60}")
    print(f"{BOLD}Results:{RESET} {GREEN}{passed} passed{RESET}, {RED}{failed} failed{RESET}, {DIM}{len(skipped)} skipped{RESET}")

    if failed_apis:
        print(f"\n{RED}Failed APIs:{RESET}")
        for api in failed_apis:
            print(f"  - {api['name']} ({api['category']})")

    # Auto-fix mode
    if args.fix and failed_apis:
        print(f"\n{YELLOW}Auto-fixing {len(failed_apis)} failed APIs...{RESET}")
        today = str(date.today())
        for api in failed_apis:
            # Find in original array and update
            for orig in apis:
                if orig is api or (orig["name"] == api["name"] and orig["url"] == api["url"]):
                    orig["status"] = "broken"
                    orig["notes"] = f"Health check failed on {today}. Previous: {orig.get('notes', '')}"
                    orig["date-checked"] = today
                    orig["try-it"] = None
                    break

        with open(DATA_FILE, "w") as f:
            json.dump(apis, f, indent=2, ensure_ascii=False)
            f.write("\n")

        print(f"{GREEN}Updated {len(failed_apis)} entries in {DATA_FILE.name}{RESET}")

    # Exit code for CI/hooks
    if failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
