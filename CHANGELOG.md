# Changelog

All notable changes to this project will be documented in this file.

## [0.2.2] - 2026-03-04
### Added
- Comprehensive `docs/` structure (quickstart, architecture, API reference, operations, security, troubleshooting).
- Concepts and cookbook pages.
- AI-friendly documentation files (`docs/llms.txt`, `docs/llms-full.txt`).

## [0.2.1] - 2026-03-04
### Added
- Hardening pass for search filters (`string_contains`, `numeric`, `array_contains`, `negate`).
- Weighted hybrid ranking controls (`memory_weight`, `chunk_weight`) in search/context.
- Extra test coverage for advanced filter operators and weighted ranking behavior.

## [0.2.0] - 2026-03-04
### Added
- Advanced search API capabilities: `search_mode`, `threshold`, metadata filters, rerank toggle.
- Hybrid retrieval from both `memories` and `document_chunks`.
- Documents ingestion pipeline (`documents`, `document_chunks`) with async processing tasks.
- User profile endpoint (`/api/v1/profile`) exposing static + dynamic summaries (+ optional query results).
- Connectors foundation (`github`, `web_crawler`) and sync task orchestration.
- Lightweight SDK stubs for Python and JavaScript under `sdk/`.
- Extended automated tests for advanced routes and memory filtering behavior.

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
