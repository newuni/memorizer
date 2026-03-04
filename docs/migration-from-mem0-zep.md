# Migration Guide (Mem0 / Zep style)

This guide helps move to memorizer incrementally.

## 1) Map core concepts

- **User/session scope** -> `tenant_id` + `namespace`
- **Memory entries** -> `memories`
- **Knowledge docs** -> `documents` + `document_chunks`
- **Context retrieval** -> `/context` and `/profile`

## 2) Export old memories

Export as JSON lines with fields:
- `content`
- `metadata`
- optional `created_at`

## 3) Transform payloads

Convert each row to:

```json
{
  "namespace": "default",
  "content": "...",
  "meta": {"source": "migration", "legacy_id": "..."}
}
```

## 4) Import in batches

Use:
- `POST /api/v1/memories/batch` for small/medium loads
- `POST /api/v1/memories/batch/async` for large loads

## 5) Validate retrieval parity

- Compare top-k relevance on a benchmark query set.
- Tune `threshold`, `memory_weight`, `chunk_weight`, and rerank.

## 6) Cutover strategy

- Dual-write for 1-2 weeks (legacy + memorizer).
- Read from memorizer in shadow mode first.
- Switch read path once quality is stable.

## 7) Rollback plan

- Keep legacy read path togglable.
- Keep migration scripts idempotent.
- Snapshot DB before final cutover.
