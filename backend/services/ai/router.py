"""
PERCI TC PRO AI — AI Router v4
Embeddings: OpenAI > Gemini > Ollama > LOCAL (numpy, sin API)
"""
from __future__ import annotations
import os
import asyncio
import logging
from enum import Enum

from .base_provider import BaseProvider, AIResponse, EmbeddingResponse, TranscriptionResponse

logger = logging.getLogger("perci.router")


class TaskType(str, Enum):
    CHAT_RAPIDO   = "chat_rapido"
    DOC_LARGO     = "doc_largo"
    RAZONAMIENTO  = "razonamiento"
    ALTA_CALIDAD  = "alta_calidad"
    GENERACION    = "generacion"
    OFFLINE       = "offline"
    EMBEDDINGS    = "embeddings"
    TRANSCRIPCION = "transcripcion"


TASK_ROUTING: dict[TaskType, list[str]] = {
    TaskType.CHAT_RAPIDO:   ["groq",   "openai", "claude", "gemini", "ollama"],
    TaskType.DOC_LARGO:     ["gemini", "claude", "openai", "groq",   "ollama"],
    TaskType.RAZONAMIENTO:  ["claude", "openai", "gemini", "groq",   "ollama"],
    TaskType.ALTA_CALIDAD:  ["openai", "claude", "gemini", "groq",   "ollama"],
    TaskType.GENERACION:    ["openai", "claude", "gemini", "groq",   "ollama"],
    TaskType.OFFLINE:       ["ollama", "groq",   "openai", "claude", "gemini"],
    TaskType.EMBEDDINGS:    ["openai", "gemini", "ollama"],
    TaskType.TRANSCRIPCION: ["openai", "groq"],
}

TIMEOUTS = {"groq": 30, "openai": 90, "gemini": 90, "claude": 90, "ollama": 180}


class AIRouter:
    def __init__(self):
        self._providers:   dict[str, BaseProvider] = {}
        self._manual:      str | None              = os.getenv("AI_PROVIDER")
        self._initialized: bool                    = False

    def _detect_and_init(self):
        from .openai_provider import OpenAIProvider
        from .gemini_provider import GeminiProvider
        from .groq_provider   import GroqProvider
        from .claude_provider import ClaudeProvider
        from .ollama_provider import OllamaProvider

        candidates = {
            "openai": (os.getenv("OPENAI_API_KEY"), OpenAIProvider),
            "gemini": (os.getenv("GEMINI_API_KEY"), GeminiProvider),
            "groq":   (os.getenv("GROQ_API_KEY"),   GroqProvider),
            "claude": (os.getenv("CLAUDE_API_KEY"),  ClaudeProvider),
            "ollama": (os.getenv("OLLAMA_URL"),      OllamaProvider),
        }

        for name, (key, cls) in candidates.items():
            if not key:
                logger.debug(f"[Router] {name}: sin configurar, omitido")
                continue
            try:
                self._providers[name] = cls()
                logger.info(f"[Router] {name}: ACTIVO")
            except Exception as e:
                logger.warning(f"[Router] {name}: error al inicializar — {e}")

        if not self._providers:
            logger.error("[Router] SIN PROVEEDORES")
        else:
            logger.info(f"[Router] Proveedores activos: {list(self._providers.keys())}")

        self._initialized = True

    def _ensure(self):
        if not self._initialized:
            self._detect_and_init()

    def _ordered(self, task: TaskType) -> list[BaseProvider]:
        preference = TASK_ROUTING.get(task, list(self._providers.keys()))
        if self._manual and self._manual in self._providers:
            rest = [p for p in preference if p != self._manual]
            preference = [self._manual] + rest
        return [self._providers[p] for p in preference if p in self._providers]

    async def _try_providers(self, providers, coro_factory, task_name):
        if not providers:
            raise RuntimeError("No hay proveedores de IA disponibles.")
        last_err = None
        for provider in providers:
            timeout = TIMEOUTS.get(provider.name, 60)
            try:
                logger.info(f"[Router] {task_name} -> {provider.name}")
                result = await asyncio.wait_for(coro_factory(provider), timeout=timeout)
                return result
            except asyncio.TimeoutError:
                logger.warning(f"[Router] {provider.name}: timeout, siguiente...")
                last_err = TimeoutError(f"{provider.name} timeout")
            except Exception as e:
                logger.warning(f"[Router] {provider.name}: {type(e).__name__}: {e}, siguiente...")
                last_err = e
        raise RuntimeError(f"Todos los proveedores fallaron en '{task_name}'. Error: {last_err}")

    async def generate_response(
        self,
        prompt: str,
        context: str = "",
        system: str = "",
        history: list[dict] | None = None,
        options: dict | None = None,
        task: TaskType = TaskType.ALTA_CALIDAD,
    ) -> AIResponse:
        self._ensure()
        providers = self._ordered(task)
        return await self._try_providers(
            providers,
            lambda p: p.generate_response(prompt, context, system, history, options),
            f"generate_response/{task}",
        )

    async def generate_embeddings(self, texts: list[str]) -> EmbeddingResponse:
        """
        Embeddings con fallback completo:
        OpenAI -> Gemini -> Ollama -> LOCAL (numpy, sin API, siempre funciona)
        """
        self._ensure()
        emb_providers = [
            self._providers[p]
            for p in TASK_ROUTING[TaskType.EMBEDDINGS]
            if p in self._providers and self._providers[p].supports_embeddings
        ]

        if emb_providers:
            try:
                return await self._try_providers(
                    emb_providers,
                    lambda p: p.generate_embeddings(texts),
                    "generate_embeddings",
                )
            except Exception as e:
                logger.warning(f"[Router] APIs de embeddings fallaron: {e}. Usando embeddings locales...")

        # Fallback local — numpy, sin API, siempre disponible
        logger.info("[Router] Usando embeddings locales (numpy hash-based)")
        from .local_embeddings import local_embed
        return await local_embed(texts)

    async def transcribe_audio(self, file_path: str, language: str = "es") -> TranscriptionResponse:
        self._ensure()
        providers = [
            self._providers[p]
            for p in TASK_ROUTING[TaskType.TRANSCRIPCION]
            if p in self._providers and self._providers[p].supports_transcription
        ]
        return await self._try_providers(
            providers,
            lambda p: p.transcribe_audio(file_path, language),
            "transcribe_audio",
        )

    async def generate_summary(self, text: str) -> AIResponse:
        return await self.generate_response(
            prompt=f"Genera un resumen ejecutivo completo en espanol:\n\n{text[:8000]}",
            system="Eres un experto en sintesis educativa. Responde en espanol claro.",
            task=TaskType.GENERACION,
        )

    def available_providers(self) -> list[str]:
        self._ensure()
        return list(self._providers.keys())

    def status(self) -> dict:
        self._ensure()
        return {
            "providers": list(self._providers.keys()),
            "mode": self._manual or "automatico",
            "total": len(self._providers),
        }

    def set_provider(self, name: str | None):
        self._ensure()
        if name and name not in self._providers:
            raise ValueError(f"Proveedor '{name}' no disponible. Activos: {list(self._providers.keys())}")
        self._manual = name

    async def health_check_all(self) -> dict[str, bool]:
        self._ensure()
        results = {}
        for name, provider in self._providers.items():
            try:
                results[name] = await asyncio.wait_for(provider.health_check(), timeout=10)
            except Exception:
                results[name] = False
        return results

    async def tts(self, text: str, voice: str = "onyx") -> bytes:
        self._ensure()
        if "openai" not in self._providers:
            raise RuntimeError("TTS requiere OPENAI_API_KEY configurada")
        return await self._providers["openai"].tts(text, voice)


ai_router = AIRouter()
