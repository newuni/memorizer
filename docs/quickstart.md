# Quickstart

## 1) Run locally

```bash
git clone https://github.com/newuni/memorizer.git
cd memorizer
cp .env.example .env
docker compose up --build
```

API: `http://localhost:8000`  
Docs UI: `http://localhost:8000/docs`

## 2) Bootstrap key

By default:

- Tenant: `default`
- API key: `dev-secret-change-me`

Send in header:

```http
X-API-Key: dev-secret-change-me
```

## 3) Add memory

```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "X-API-Key: dev-secret-change-me" \
  -H "Content-Type: application/json" \
  -d '{"namespace":"default","content":"User prefers concise responses","meta":{"type":"preference"}}'
```

## 4) Search memory

```bash
curl "http://localhost:8000/api/v1/memories/search?namespace=default&q=concise&top_k=5" \
  -H "X-API-Key: dev-secret-change-me"
```

## 5) Build context

```bash
curl -X POST http://localhost:8000/api/v1/context \
  -H "X-API-Key: dev-secret-change-me" \
  -H "Content-Type: application/json" \
  -d '{"namespace":"default","prompt":"How should I answer this user?","top_k":5,"search_mode":"hybrid"}'
```
