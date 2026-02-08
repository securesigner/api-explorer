#!/bin/bash
# Install git hooks from scripts/hooks/ into .git/hooks/
# Run once after cloning: bash scripts/install-hooks.sh

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS_SRC="$REPO_ROOT/scripts/hooks"
HOOKS_DST="$REPO_ROOT/.git/hooks"

echo "Installing git hooks..."

# Pre-commit
cp "$HOOKS_SRC/pre-commit-validate.sh" "$HOOKS_DST/pre-commit"
chmod +x "$HOOKS_DST/pre-commit"
echo "  ✅ pre-commit  → JSON validation & formatting"

# Commit-msg
cp "$HOOKS_SRC/commit-msg-convention.sh" "$HOOKS_DST/commit-msg"
chmod +x "$HOOKS_DST/commit-msg"
echo "  ✅ commit-msg   → Conventional commit enforcement"

# Pre-push
cp "$HOOKS_SRC/pre-push-healthcheck.sh" "$HOOKS_DST/pre-push"
chmod +x "$HOOKS_DST/pre-push"
echo "  ✅ pre-push     → API health checks (informational)"

echo ""
echo "Done! Hooks installed to .git/hooks/"
echo "To skip hooks on a commit: git commit --no-verify"
echo "To skip hooks on a push:   git push --no-verify"
