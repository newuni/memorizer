# Getting Started in 10 Minutes

## 0) Prerequisites
- Docker + Docker Compose
- curl

## 1) Start memorizer (2 min)

```bash
git clone https://github.com/newuni/memorizer.git
cd memorizer
cp .env.example .env
docker compose up -d --build
```

## 2) Verify health (30s)

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status":"ok"}
```

## 3) Add your first memory (1 min)

```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "X-API-Key: dev-secret-change-me" \
  -H "Content-Type: application/json" \
  -d '{"namespace":"default","content":"User likes concise answers","meta":{"type":"preference"}}'
```

## 4) Retrieve context (1 min)

```bash
curl -X POST http://localhost:8000/api/v1/context \
  -H "X-API-Key: dev-secret-change-me" \
  -H "Content-Type: application/json" \
  -d '{"namespace":"default","prompt":"How should I reply?","top_k":5,"search_mode":"hybrid"}'
```

## 5) Ingest a document (2 min)

```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -H "X-API-Key: dev-secret-change-me" \
  -H "Content-Type: application/json" \
  -d '{"namespace":"default","content_type":"text","title":"FAQ","text_content":"Refunds are allowed within 14 days..."}'
```

## 6) Use in your agent (3 min)

- Before answering: call `/api/v1/context`.
- Inject `context` into system prompt.
- After important turns: call `/api/v1/memories` to persist durable facts.

Done 🎉
