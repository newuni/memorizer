from __future__ import annotations

import requests


class MemorizerClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    def add_memory(self, content: str, namespace: str = "default", meta: dict | None = None):
        payload = {"namespace": namespace, "content": content, "meta": meta or {}}
        r = requests.post(f"{self.base_url}/api/v1/memories", json=payload, headers=self.headers, timeout=20)
        r.raise_for_status()
        return r.json()

    def context(self, prompt: str, namespace: str = "default", top_k: int = 5):
        payload = {"namespace": namespace, "prompt": prompt, "top_k": top_k, "search_mode": "hybrid"}
        r = requests.post(f"{self.base_url}/api/v1/context", json=payload, headers=self.headers, timeout=20)
        r.raise_for_status()
        return r.json()

    def profile(self, namespace: str = "default", q: str | None = None):
        params = {"namespace": namespace}
        if q:
            params["q"] = q
        r = requests.get(f"{self.base_url}/api/v1/profile", params=params, headers=self.headers, timeout=20)
        r.raise_for_status()
        return r.json()
