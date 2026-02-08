#!/bin/bash
# Pre-commit hook: Validate and auto-format data/apis.json
# Installed to .git/hooks/pre-commit by scripts/install-hooks.sh

set -e

# Only run if apis.json is staged
if ! git diff --cached --name-only | grep -q "^data/apis.json$"; then
    exit 0
fi

echo "🔍 Pre-commit: Validating data/apis.json..."

JSON_FILE="data/apis.json"

# 1. Check JSON parses correctly
if ! python3 -c "import json; json.load(open('$JSON_FILE'))" 2>/dev/null; then
    echo "❌ FAILED: $JSON_FILE is not valid JSON"
    exit 1
fi

# 2. Run validation checks
VALIDATION=$(python3 -c "
import json, sys

with open('$JSON_FILE') as f:
    apis = json.load(f)

errors = []

VALID_STATUSES = {'pending', 'working', 'broken', 'paid-only', 'needs-key', 'skipped'}
VALID_AUTH = {'none', 'api-key', 'oauth', 'x-mashape-key', 'user-agent'}
VALID_CORS = {'yes', 'no', 'unknown'}
VALID_RESPONSE_TYPES = {'json', 'image', 'text'}
REQUIRED_FIELDS = ['name', 'url', 'description', 'auth', 'https', 'cors', 'category', 'status', 'notes', 'date-checked', 'try-it']

if not isinstance(apis, list):
    errors.append('Root must be an array')
    print('\n'.join(errors))
    sys.exit(0)

seen_pairs = set()
for i, api in enumerate(apis):
    prefix = f'Entry {i} ({api.get(\"name\", \"unknown\")})'

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in api:
            errors.append(f'{prefix}: missing field \"{field}\"')

    # Type checks
    if 'name' in api and not isinstance(api['name'], str):
        errors.append(f'{prefix}: name must be a string')
    if 'https' in api and not isinstance(api['https'], bool):
        errors.append(f'{prefix}: https must be a boolean')
    if 'notes' in api and not isinstance(api['notes'], str):
        errors.append(f'{prefix}: notes must be a string')

    # Enum checks
    if api.get('status') not in VALID_STATUSES:
        errors.append(f'{prefix}: invalid status \"{api.get(\"status\")}\"')
    if api.get('auth') not in VALID_AUTH:
        errors.append(f'{prefix}: invalid auth \"{api.get(\"auth\")}\"')
    if api.get('cors') not in VALID_CORS:
        errors.append(f'{prefix}: invalid cors \"{api.get(\"cors\")}\"')

    # Date format
    dc = api.get('date-checked')
    if dc is not None:
        import re
        if not isinstance(dc, str) or not re.match(r'^\d{4}-\d{2}-\d{2}$', dc):
            errors.append(f'{prefix}: date-checked must be null or YYYY-MM-DD')

    # try-it validation
    tryit = api.get('try-it')
    if tryit is not None:
        if not isinstance(tryit, dict):
            errors.append(f'{prefix}: try-it must be null or object')
        else:
            if 'url' not in tryit:
                errors.append(f'{prefix}: try-it missing url')
            if tryit.get('response-type') not in VALID_RESPONSE_TYPES:
                errors.append(f'{prefix}: try-it invalid response-type \"{tryit.get(\"response-type\")}\"')

    # Duplicate check (name + url pair)
    pair = (api.get('name', ''), api.get('url', ''))
    if pair in seen_pairs:
        errors.append(f'{prefix}: duplicate name+url pair')
    seen_pairs.add(pair)

if errors:
    print('\n'.join(errors[:20]))  # Limit output
    if len(errors) > 20:
        print(f'... and {len(errors) - 20} more errors')
" 2>&1)

if [ -n "$VALIDATION" ]; then
    echo "❌ FAILED: Validation errors in $JSON_FILE:"
    echo "$VALIDATION"
    exit 1
fi

# 3. Auto-format JSON (consistent 2-space indent)
python3 -c "
import json

with open('$JSON_FILE') as f:
    data = json.load(f)

with open('$JSON_FILE', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')
"

# Re-stage if formatting changed the file
git add "$JSON_FILE"

echo "✅ Pre-commit: $JSON_FILE validated and formatted"
