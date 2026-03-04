export class MemorizerClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.headers = {
      "X-API-Key": apiKey,
      "Content-Type": "application/json",
    };
  }

  async addMemory(content, namespace = "default", meta = {}) {
    const r = await fetch(`${this.baseUrl}/api/v1/memories`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify({ namespace, content, meta }),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }

  async context(prompt, namespace = "default", topK = 5) {
    const r = await fetch(`${this.baseUrl}/api/v1/context`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify({ namespace, prompt, top_k: topK, search_mode: "hybrid" }),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }

  async profile(namespace = "default", q = null) {
    const u = new URL(`${this.baseUrl}/api/v1/profile`);
    u.searchParams.set("namespace", namespace);
    if (q) u.searchParams.set("q", q);
    const r = await fetch(u, { headers: this.headers });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }
}
