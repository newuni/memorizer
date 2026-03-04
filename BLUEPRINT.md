# Memorizer Blueprint (v0)

## 1. Objective
Build a memory API for agents with multi-tenant isolation, semantic retrieval, and prompt-ready context assembly.

## 2. Architecture
- **API layer**: FastAPI
- **Storage layer**:
  - PostgreSQL tables for metadata and governance
  - pgvector for embeddings (single-table strategy in MVP)
- **Embedding provider abstraction**:
  - `LocalCPUEmbedder` (SentenceTransformers on CPU)
  - `GeminiEmbedder` configurable via `.env`
  - provider switch with `EMBEDDING_PROVIDER=local|gemini`

## 3. Domain model (MVP)
- `memories`
  - `id` (UUID)
  - `tenant_id` (TEXT)
  - `namespace` (TEXT)
  - `content` (TEXT)
  - `metadata` (JSONB)
  - `embedding` (VECTOR(384))
  - `created_at` / `updated_at`

## 4. Retrieval strategy
- Cosine similarity search (`embedding <=> query_embedding`)
- Filter by tenant + namespace
- Order by similarity and recency tie-break

## 5. API contract (v0.2)
- `POST /api/v1/memories`
- `POST /api/v1/memories/batch`
- `GET /api/v1/memories/search`
- `POST /api/v1/context`
- `DELETE /api/v1/memories/{memory_id}`
- `GET /health`

## 6. Security
- Tenant isolation enforced at query layer (v0.2)
- API key auth via `X-API-Key` (v0.2)
- Bootstrap dev key from env for local onboarding
- Audit logging planned in v0.3

## 7. Roadmap
- v0.1: core CRUD + semantic search + context endpoint
- v0.2: API keys + batch ingest + pluggable embeddings (local/gemini)
- v0.3: rerank, async workers, connectors, memory compaction
