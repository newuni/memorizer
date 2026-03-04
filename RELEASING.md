# Releasing

We create a GitHub Release for each relevant change set.

## Versioning
Use SemVer:
- `MAJOR`: breaking API/contract changes
- `MINOR`: new features, backward compatible
- `PATCH`: fixes/docs/tests/internal improvements

## Steps
1. Ensure `main` is green and pushed.
2. Bump `version` in `pyproject.toml`.
3. Create release:

```bash
gh release create vX.Y.Z \
  --repo newuni/memorizer \
  --title "vX.Y.Z" \
  --generate-notes
```

Optional custom notes:
```bash
gh release create vX.Y.Z \
  --repo newuni/memorizer \
  --title "vX.Y.Z" \
  --notes "Highlights..."
```

## Current baseline
- `v0.1.0` published.
