"""
PERCI TC PRO AI — Embeddings locales sin dependencias externas
Usa numpy (ya instalado) para crear vectores consistentes.
No requiere API key ni librerías pesadas.
"""
from __future__ import annotations
import hashlib
import numpy as np
from .base_provider import EmbeddingResponse

EMBED_DIM = 384  # dimension fija y consistente


def _text_to_vector(text: str) -> list[float]:
    """
    Convierte texto a vector usando hashing consistente.
    Mismo texto = mismo vector siempre.
    """
    # Dividir texto en palabras
    words = text.lower().split()
    vector = np.zeros(EMBED_DIM, dtype="float32")

    for i, word in enumerate(words):
        # Hash de cada palabra → posicion en el vector
        h = int(hashlib.md5(word.encode()).hexdigest(), 16)
        pos = h % EMBED_DIM
        # Peso por posicion en el texto (palabras al inicio pesan mas)
        weight = 1.0 / (1.0 + i * 0.1)
        vector[pos] += weight

    # Normalizar
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm

    return vector.tolist()


async def local_embed(texts: list[str]) -> EmbeddingResponse:
    """Genera embeddings locales sin API ni librerias pesadas."""
    embeddings = [_text_to_vector(text) for text in texts]
    return EmbeddingResponse(
        embeddings=embeddings,
        provider="local",
        model="hash-embedding-384",
    )
