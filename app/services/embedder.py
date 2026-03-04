import hashlib
from app.core.config import settings


class DummyEmbedder:
    """Deterministic local embedder for MVP/dev.

    Replace with real embedding provider in v0.2.
    """

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vals = []
        for i in range(settings.embedding_dim):
            b = digest[i % len(digest)]
            vals.append((b / 255.0) * 2 - 1)
        return vals


embedder = DummyEmbedder()
