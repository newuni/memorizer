from __future__ import annotations

from typing import Protocol

from app.core.config import settings


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class LocalCPUEmbedder:
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name, device="cpu")

    def embed(self, text: str) -> list[float]:
        vec = self.model.encode(text, normalize_embeddings=True)
        out = vec.tolist() if hasattr(vec, "tolist") else list(vec)
        if len(out) != settings.embedding_dim:
            raise ValueError(
                f"Local embedding dim mismatch: model returned {len(out)} but EMBEDDING_DIM={settings.embedding_dim}."
            )
        return out


class GeminiEmbedder:
    def __init__(self, api_key: str, model_name: str):
        import google.generativeai as genai

        if not api_key:
            raise ValueError("GEMINI_API_KEY is required when EMBEDDING_PROVIDER=gemini")
        genai.configure(api_key=api_key)
        self.genai = genai
        self.model_name = model_name

    def embed(self, text: str) -> list[float]:
        result = self.genai.embed_content(
            model=self.model_name,
            content=text,
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=settings.embedding_dim,
        )
        emb = result["embedding"]
        if len(emb) != settings.embedding_dim:
            raise ValueError(
                f"Gemini embedding dim mismatch: got {len(emb)} expected {settings.embedding_dim}."
            )
        return emb


class _LazyEmbedder:
    def __init__(self):
        self._impl: Embedder | None = None

    def _build(self) -> Embedder:
        provider = settings.embedding_provider.lower().strip()
        if provider == "local":
            return LocalCPUEmbedder(settings.local_embed_model)
        if provider == "gemini":
            return GeminiEmbedder(settings.gemini_api_key, settings.gemini_embed_model)
        raise ValueError("Invalid EMBEDDING_PROVIDER. Use 'local' or 'gemini'.")

    def embed(self, text: str) -> list[float]:
        if self._impl is None:
            self._impl = self._build()
        return self._impl.embed(text)


embedder: Embedder = _LazyEmbedder()
