# Release Notes Draft

GitHub release automation is currently blocked because `gh auth status` reports an invalid token for `github.com`.

## Re-authenticate

```bash
gh auth login -h github.com
```

## Release commands

```bash
# Ensure working tree is clean and tests were run in your CI environment
git fetch --tags
git checkout main
git pull --ff-only

# Create annotated tag for this release
git tag -a v0.5.0 -m "v0.5.0"
git push origin v0.5.0

# Create GitHub release
gh release create v0.5.0 \
  --title "v0.5.0" \
  --notes-file CHANGELOG.md
```
