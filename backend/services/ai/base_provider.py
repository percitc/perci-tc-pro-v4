"""
PERCI TC PRO AI — Base Provider
Interfaz abstracta unificada. Todos los providers la implementan.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIResponse:
    content: str
    provider: str
    model: str
    tokens_used: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class EmbeddingResponse:
    embeddings: list[list[float]]
    provider: str
    model: str
    tokens_used: int = 0


@dataclass
class TranscriptionResponse:
    text: str
    provider: str
    language: str = "es"


class BaseProvider(ABC):
    name: str = "base"
    supports_embeddings: bool     = False
    supports_transcription: bool  = False

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        context: str = "",
        system: str = "",
        history: list[dict] | None = None,
        options: dict | None = None,
    ) -> AIResponse: ...

    async def generate_embeddings(self, texts: list[str]) -> EmbeddingResponse:
        raise NotImplementedError(f"{self.name}: embeddings no soportado")

    async def transcribe_audio(self, file_path: str, language: str = "es") -> TranscriptionResponse:
        raise NotImplementedError(f"{self.name}: transcripcion no soportada")

    async def health_check(self) -> bool:
        try:
            r = await self.generate_response("OK", options={"max_tokens": 5})
            return bool(r.content)
        except Exception:
            return False
