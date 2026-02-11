# Public APIs Tracker

Personal tool to explore 1,774 public APIs. Track which ones work, which are broken, and take notes.

API data sourced from [public-apis](https://github.com/public-apis/public-apis) and [marcelscruz/public-apis](https://github.com/marcelscruz/public-apis).

## Setup

```bash
python3 scripts/parse-apis.py    # parse markdown to JSON (first time only)
python3 -m http.server 8000      # serve locally
open http://localhost:8000
bash scripts/install-hooks.sh    # install git hooks (one-time)
```

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/parse-apis.py` | Parse `public-apis.md` into `data/apis.json` |
| `scripts/update-api-status.py` | Update API status/notes/try-it without hand-editing JSON |
| `scripts/api-progress.py` | Per-category progress dashboard |
| `scripts/api-healthcheck.py` | Bulk health check working APIs |
| `scripts/batch-update.py` | Apply batch updates from a JSON session file |
| `scripts/merge-apis-2.py` | Merge new APIs from a second source list |
| `scripts/install-hooks.sh` | Install pre-commit, commit-msg, and pre-push hooks |

### Quick Examples

```bash
# Update an API entry
python3 scripts/update-api-status.py "Dogs" --status working \
  --notes "GET /api/breeds/image/random" \
  --try-url "https://dog.ceo/api/breeds/image/random" --try-type json

# View progress
python3 scripts/api-progress.py --auth none

# Health check a category
python3 scripts/api-healthcheck.py --category animals
```

## Status Values

| Status | Meaning |
|--------|---------|
| `pending` | Not yet tested |
| `working` | Confirmed functional |
| `broken` | API dead or returns errors |
| `paid-only` | Requires paid plan |
| `needs-key` | Works but requires API key |
| `skipped` | Not interesting or N/A |

## AI-Assisted Development

This project includes AI infrastructure in `.claude/` with skills, references, and git hooks.
See [CLAUDE.md](CLAUDE.md) for full details on the AI workflow, testing process, and project conventions.
