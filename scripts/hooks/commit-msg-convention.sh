#!/bin/bash
# Commit message hook: Enforce conventional commit format
# Installed to .git/hooks/commit-msg by scripts/install-hooks.sh

COMMIT_MSG_FILE="$1"
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Allow merge commits
if echo "$COMMIT_MSG" | grep -qE "^Merge "; then
    exit 0
fi

# Allow revert commits
if echo "$COMMIT_MSG" | grep -qE "^Revert "; then
    exit 0
fi

# Enforce: type(scope): description  OR  type: description
# Types: feat, fix, docs, chore, test, refactor, style
PATTERN="^(feat|fix|docs|chore|test|refactor|style)(\([a-z0-9-]+\))?: .+"

if ! echo "$COMMIT_MSG" | head -1 | grep -qE "$PATTERN"; then
    echo ""
    echo "⚠️  Commit message does not follow conventional format."
    echo ""
    echo "Suggested: type(scope): description"
    echo "Types: feat, fix, docs, chore, test, refactor, style"
    echo "Scope: optional, kebab-case (e.g., animals, ui, infra)"
    echo ""
    echo "Examples:"
    echo "  test(animals): complete no-auth API testing"
    echo "  feat(ui): add category progress bar"
    echo "  docs: update session notes"
    echo ""
    echo "Your message: $COMMIT_MSG"
    echo ""
    # Warning only — does not block the commit
fi

# Warn if first line is too long (72 char convention)
FIRST_LINE=$(echo "$COMMIT_MSG" | head -1)
if [ ${#FIRST_LINE} -gt 72 ]; then
    echo "⚠️  Commit subject is ${#FIRST_LINE} chars (convention: ≤72)"
fi
