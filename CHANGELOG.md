# Changelog

All notable changes to this project will be documented in this file.

## [0.1.2] - 2026-03-04
### Added
- Public project files: `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`.
- Issue templates and PR template under `.github/`.
- CI/release/license badges and public quickstart improvements in README.

### Changed
- Enabled branch protection on `main` (required checks, 1 approval, conversation resolution, linear history).

## [0.1.1] - 2026-03-04
### Added
- GitHub Actions CI workflow (`tests`, `package-cli`).
- Lightweight `requirements-test.txt` for CI.

### Changed
- Lazy embedder loading to avoid heavy model imports during test/runtime init.

## [0.1.0] - 2026-03-04
### Added
- Initial public milestone: API + async ingestion + reranking + CLI + pipx packaging.
