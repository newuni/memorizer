# API Examples (end-to-end)

All examples use:

```bash
export MEMORIZER_URL=http://localhost:8000
export MEMORIZER_API_KEY=dev-secret-change-me
```

## 1) Add memory

```bash
curl -X POST "$MEMORIZER_URL/api/v1/memories" \
  -H "X-API-Key: $MEMORIZER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "namespace":"default",
    "content":"User prefers concise Spanish responses",
    "meta":{"type":"preference","team":"support"}
  }'
```

## 2) Hybrid search with filters

```bash
curl "$MEMORIZER_URL/api/v1/memories/search?namespace=default&q=spanish&top_k=5&search_mode=hybrid&threshold=0.4&memory_weight=1.2&chunk_weight=0.8&filters=%7B%22key%22%3A%22type%22%2C%22value%22%3A%22preference%22%7D" \
  -H "X-API-Key: $MEMORIZER_API_KEY"
```

## 3) Build context for LLM prompt

```bash
curl -X POST "$MEMORIZER_URL/api/v1/context" \
  -H "X-API-Key: $MEMORIZER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "namespace":"default",
    "prompt":"How should I answer this user?",
    "top_k":5,
    "search_mode":"hybrid",
    "threshold":0.5,
    "rerank":true,
    "memory_weight":1.1,
    "chunk_weight":0.9
  }'
```

## 4) User profile (+ query)

```bash
curl "$MEMORIZER_URL/api/v1/profile?namespace=default&q=deployment&top_k=5" \
  -H "X-API-Key: $MEMORIZER_API_KEY"
```

## 5) Ingest document (text)

```bash
curl -X POST "$MEMORIZER_URL/api/v1/documents" \
  -H "X-API-Key: $MEMORIZER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "namespace":"default",
    "content_type":"text",
    "title":"Runbook",
    "text_content":"Use Docker Compose for deployment...",
    "meta":{"source":"runbook"}
  }'
```

## 6) Connector + sync

```bash
curl -X POST "$MEMORIZER_URL/api/v1/connectors" \
  -H "X-API-Key: $MEMORIZER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "namespace":"default",
    "provider":"github",
    "config":{"repo_url":"https://github.com/newuni/memorizer"}
  }'
```
