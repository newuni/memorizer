# Architecture

memorizer is a memory layer for AI agents.

## Components

- **FastAPI API**: request handling, auth, orchestration.
- **PostgreSQL + pgvector**:
  - `memories` store semantic memory vectors.
  - `documents` and `document_chunks` store source docs + chunk vectors.
  - `api_keys`, `ingestion_jobs`, `connectors` store control-plane data.
- **Redis + Celery**: async pipelines (batch ingestion, document processing, connector sync).

## Data flow

1. Client sends memory/document ingestion request.
2. API authenticates via `X-API-Key` and resolves tenant.
3. Embeddings are generated (local model or Gemini provider).
4. Rows are persisted in pgvector tables.
5. Search performs vector retrieval + optional rerank.
6. `/context` and `/profile` compose retrieval outputs for agent prompts.

## Search pipeline

- Candidate retrieval from memory vectors and (optionally) chunk vectors.
- Source weighting (`memory_weight`, `chunk_weight`) in hybrid mode.
- Threshold filtering.
- Metadata filters (`AND`/`OR`, string/numeric/array ops).
- Optional rerank.

## Multi-tenant model

Every query and write is constrained by `tenant_id` from the API key.
