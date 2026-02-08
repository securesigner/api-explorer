# Contributing

Help test the 1,295+ pending APIs! Every tested API makes this resource more useful.

## Testing Workflow

1. **Find untested APIs:**

   ```bash
   python3 scripts/api-progress.py --auth none    # no-auth APIs (easiest)
   python3 scripts/api-progress.py --category animals
   ```

2. **Test the endpoint** — use curl, a `.http` file with the [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) extension, or your browser:

   ```bash
   curl -s https://dog.ceo/api/breeds/image/random | python3 -m json.tool
   ```

3. **Update the entry** via CLI:

   ```bash
   python3 scripts/update-api-status.py "Dogs" --status working \
     --notes "GET /api/breeds/image/random" \
     --try-url "https://dog.ceo/api/breeds/image/random" --try-type json
   ```

4. **Commit with conventional format:**

   ```
   test(animals): mark Dogs as working
   ```

## Status Decision Tree

- **Endpoint returns data?** → `working`
- **Endpoint dead, 404, or docs gone?** → `broken`
- **Returns 401/403 requiring paid plan?** → `paid-only`
- **Works but requires API key signup?** → `needs-key`
- **Not interesting or not applicable?** → `skipped`

## Commit Format

```
type(scope): description
```

- **Types:** feat, fix, docs, chore, test, refactor, style
- **Scopes:** category names (`animals`, `books`) or areas (`ui`, `data`, `scripts`)

## Guidelines

- Use `scripts/update-api-status.py` instead of hand-editing `apis.json`
- One API per commit is fine, or batch a category
- Include a `try-url` for working APIs so others can verify
- Run `python3 scripts/api-healthcheck.py` before pushing to catch regressions
