from __future__ import annotations

import requests


class MemorizerClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    def _req(self, method: str, path: str, **kwargs):
        r = requests.request(method, f"{self.base_url}{path}", headers=self.headers, timeout=30, **kwargs)
        r.raise_for_status()
        return r.json() if r.text else {}

    def add_memory(self, content: str, namespace: str = "default", meta: dict | None = None):
        return self._req("POST", "/api/v1/memories", json={"namespace": namespace, "content": content, "meta": meta or {}})

    def context(self, prompt: str, namespace: str = "default", top_k: int = 5, include_citations: bool = True):
        payload = {"namespace": namespace, "prompt": prompt, "top_k": top_k, "search_mode": "hybrid", "include_citations": include_citations}
        return self._req("POST", "/api/v1/context", json=payload)

    def profile(self, namespace: str = "default", q: str | None = None):
        return self._req("GET", "/api/v1/profile", params={"namespace": namespace, "q": q} if q else {"namespace": namespace})

    def export_tenant(self, namespace: str = "default"):
        return self._req("GET", "/api/v1/tenants/export", params={"namespace": namespace})

    def forget(self, memory_id: str):
        return self._req("POST", f"/api/v1/memories/{memory_id}/forget")

    def sync_connector(self, connector_id: str):
        return self._req("POST", f"/api/v1/connectors/{connector_id}/sync")
