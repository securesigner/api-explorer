#!/bin/bash
# Pre-push hook: Run health checks on working APIs with try-it URLs
# Installed to .git/hooks/pre-push by scripts/install-hooks.sh
#
# This hook is OPT-IN. Set the env var to enable:
#   export PUBLIC_APIS_HEALTHCHECK=1
# Or run manually: python3 scripts/api-healthcheck.py
#
# Skip entirely with: git push --no-verify

if [ "$PUBLIC_APIS_HEALTHCHECK" != "1" ]; then
    exit 0
fi

echo "🔍 Pre-push: Running API health checks..."

# Set a total timeout to avoid blocking pushes too long
TIMEOUT=60

# Run health check with a timeout wrapper
if command -v timeout &> /dev/null; then
    # GNU timeout (Linux)
    RESULT=$(timeout "$TIMEOUT" python3 scripts/api-healthcheck.py --timeout 5 2>&1) || true
elif command -v gtimeout &> /dev/null; then
    # GNU timeout via Homebrew (macOS)
    RESULT=$(gtimeout "$TIMEOUT" python3 scripts/api-healthcheck.py --timeout 5 2>&1) || true
else
    # No timeout command available — run with Python's own timeout
    RESULT=$(python3 scripts/api-healthcheck.py --timeout 5 2>&1) || true
fi

EXIT_CODE=$?

echo "$RESULT"

if echo "$RESULT" | grep -q "FAIL"; then
    echo ""
    echo "⚠️  Some API health checks failed. Review above."
    echo "   This is informational — push will proceed."
    echo "   Consider running: python3 scripts/api-healthcheck.py --fix"
    echo ""
fi

# Always allow push
exit 0
