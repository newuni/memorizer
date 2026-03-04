# Contributing

Thanks for contributing to memorizer.

## Setup

```bash
git clone https://github.com/newuni/memorizer.git
cd memorizer
cp .env.example .env
```

## Local development

```bash
docker compose up --build
```

API docs: `http://localhost:8000/docs`

## Tests

```bash
pytest -q
```

For CI-like lightweight tests:

```bash
pip install -r requirements-test.txt
pytest -q
```

## Pull requests

- Keep PRs focused and small when possible.
- Add/update tests for behavior changes.
- Update docs (README/BLUEPRINT/ROADMAP) when relevant.
- Ensure CI is green before requesting review.

## Commit style

Conventional-ish prefixes are recommended:
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation only
- `test:` tests
- `ci:` pipeline changes
- `chore:` maintenance
