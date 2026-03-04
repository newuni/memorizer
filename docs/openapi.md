# OpenAPI

The interactive OpenAPI docs are available at:

- `/docs` (Swagger UI)

Raw schema endpoint (FastAPI default):

- `/openapi.json`

Example:

```bash
curl http://localhost:8000/openapi.json | jq '.info,.paths|keys'
```
