"""
PERCI TC PRO AI — Embeddings Locales (fallback sin OpenAI)
Usa sentence-transformers si no hay API de embeddings disponible.
Dimension: 384 (all-MiniLM-L6-v2) — consistente dentro de una sesion.
"""
from __future__ import annotations
import os
from .base_provider import EmbeddingResponse

_model = None
_dim   = 384


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


async def local_embed(texts: list[str]) -> EmbeddingResponse:
    """Genera embeddings locales usando sentence-transformers."""
    model  = _get_model()
    vecs   = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return EmbeddingResponse(
        embeddings=vecs.tolist(),
        provider="local",
        model="all-MiniLM-L6-v2",
    )
