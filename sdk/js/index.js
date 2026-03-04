export class MemorizerClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.headers = {
      "X-API-Key": apiKey,
      "Content-Type": "application/json",
    };
  }

  async _req(path, opts = {}) {
    const r = await fetch(`${this.baseUrl}${path}`, { headers: this.headers, ...opts });
    if (!r.ok) throw new Error(await r.text());
    const txt = await r.text();
    return txt ? JSON.parse(txt) : {};
  }

  addMemory(content, namespace = "default", meta = {}) {
    return this._req(`/api/v1/memories`, { method: "POST", body: JSON.stringify({ namespace, content, meta }) });
  }

  context(prompt, namespace = "default", topK = 5, includeCitations = true) {
    return this._req(`/api/v1/context`, {
      method: "POST",
      body: JSON.stringify({ namespace, prompt, top_k: topK, search_mode: "hybrid", include_citations: includeCitations }),
    });
  }

  async profile(namespace = "default", q = null) {
    const u = new URL(`${this.baseUrl}/api/v1/profile`);
    u.searchParams.set("namespace", namespace);
    if (q) u.searchParams.set("q", q);
    return this._req(u.pathname + u.search);
  }

  exportTenant(namespace = "default") {
    return this._req(`/api/v1/tenants/export?namespace=${encodeURIComponent(namespace)}`);
  }

  forget(memoryId) {
    return this._req(`/api/v1/memories/${memoryId}/forget`, { method: "POST" });
  }

  syncConnector(connectorId) {
    return this._req(`/api/v1/connectors/${connectorId}/sync`, { method: "POST" });
  }
}
