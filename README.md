# API Explorer

Browse and track 1,426 public APIs from the [public-apis](https://github.com/public-apis/public-apis) list. Filter by category, auth type, and status. Click any row to expand details and try live API calls directly in the browser.

**No frameworks. No build tools. Just HTML, CSS, and JS.**

## Quick Start

```bash
git clone https://github.com/securesigner/api-explorer.git
cd api-explorer
python3 -m http.server 8000
open http://localhost:8000
```

Or use any local server — open `index.html` with VS Code's [Live Server](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer) extension for auto-reload.

## Features

- **Search & filter** — by name, category, auth type, status
- **Sortable columns** — click any header
- **Expandable rows** — click a row to see notes and try-it controls
- **Live API calls** — hit "Try It" to fetch real responses inline (JSON, images, text)
- **Status tracking** — mark APIs as working, broken, needs-key, paid-only, or skipped

## Status Values

| Status      | Meaning                                    |
| ----------- | ------------------------------------------ |
| `pending`   | Not yet tested                             |
| `working`   | Confirmed functional, no auth or free tier |
| `broken`    | API dead, docs gone, or returns errors     |
| `paid-only` | Requires paid plan, no usable free tier    |
| `needs-key` | Works but requires API key signup          |
| `skipped`   | Not interesting or not applicable          |

## Data Schema

Each entry in `data/apis.json`:

```json
{
  "name": "Dogs",
  "url": "https://dog.ceo/dog-api/",
  "description": "Based on the Stanford Dogs Dataset",
  "auth": "none",
  "https": true,
  "cors": "yes",
  "category": "animals",
  "status": "working",
  "notes": "GET /api/breeds/image/random returns {message: url, status: success}",
  "date-checked": "2026-02-05",
  "try-it": {
    "url": "https://dog.ceo/api/breeds/image/random",
    "response-type": "json"
  }
}
```

### try-it Field

- `null` for untested/broken APIs, populated for working APIs
- `url` — endpoint URL, may contain `{param}` placeholders
- `response-type` — `"json"`, `"image"`, or `"text"`
- `params` — optional `{placeholder: default_value}` pairs for parameterized URLs

## Auth Types

| Auth            | Count | Notes                       |
| --------------- | ----- | --------------------------- |
| `none`          | 668   | No auth needed — start here |
| `api-key`       | 602   | Many have free tiers        |
| `oauth`         | 149   | OAuth flow required         |
| `x-mashape-key` | 6     | RapidAPI key                |
| `user-agent`    | 1     | Requires User-Agent header  |

## Scripts

| Script                         | Purpose                                            |
| ------------------------------ | -------------------------------------------------- |
| `scripts/parse-apis.py`        | Parse `public-apis.md` → `data/apis.json`          |
| `scripts/update-api-status.py` | Update an API's status, notes, and try-it URL      |
| `scripts/api-progress.py`      | Per-category progress dashboard                    |
| `scripts/api-healthcheck.py`   | Bulk health check working APIs                     |
| `scripts/install-hooks.sh`     | Install pre-commit, commit-msg, and pre-push hooks |

### Examples

```bash
# Update an API entry
python3 scripts/update-api-status.py "Dogs" --status working \
  --notes "GET /api/breeds/image/random" \
  --try-url "https://dog.ceo/api/breeds/image/random" --try-type json

# View progress (filter by auth type or category)
python3 scripts/api-progress.py --auth none
python3 scripts/api-progress.py --category animals

# Health check working APIs
python3 scripts/api-healthcheck.py --category animals
python3 scripts/api-healthcheck.py --fix    # auto-mark failures as broken
```

## Git Hooks

Optional hooks for data integrity. Install with:

```bash
bash scripts/install-hooks.sh
```

| Hook           | What it does                                                  |
| -------------- | ------------------------------------------------------------- |
| **pre-commit** | Validates `apis.json` schema, checks enums, auto-formats JSON |
| **commit-msg** | Warns on non-conventional commit format (doesn't block)       |
| **pre-push**   | Opt-in API health checks (`PUBLIC_APIS_HEALTHCHECK=1`)        |

Skip when needed: `git commit --no-verify` or `git push --no-verify`

## Progress

- **108** working
- **19** broken
- **4** needs-key
- **28** of 51 categories tested
- **1,295** still pending

See [CONTRIBUTING.md](CONTRIBUTING.md) to help test more APIs.

## License

[MIT](LICENSE)
