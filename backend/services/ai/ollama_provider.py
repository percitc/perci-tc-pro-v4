"""PERCI TC PRO AI — Ollama Provider (modelos locales / offline)"""
from __future__ import annotations
import os
import httpx
from .base_provider import BaseProvider, AIResponse, EmbeddingResponse


class OllamaProvider(BaseProvider):
    name                = "ollama"
    supports_embeddings = True

    def __init__(self):
        self.base_url    = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model       = os.getenv("OLLAMA_MODEL", "llama3.1")
        self.embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

    async def generate_response(self, prompt, context="", system="", history=None, options=None) -> AIResponse:
        o = options or {}
        sys_text = "\n\n".join(s for s in [system, f"CONTEXTO:\n{context}" if context else ""] if s)
        msgs = []
        if sys_text: msgs.append({"role": "system", "content": sys_text})
        msgs.extend((history or [])[-10:])
        msgs.append({"role": "user", "content": prompt})
        async with httpx.AsyncClient(timeout=180) as h:
            r = await h.post(f"{self.base_url}/api/chat",
                             json={"model": o.get("model", self.model), "messages": msgs, "stream": False,
                                   "options": {"num_predict": o.get("max_tokens", 2000), "temperature": o.get("temperature", 0.4)}})
            r.raise_for_status()
            d = r.json()
        return AIResponse(content=d["message"]["content"], provider=self.name,
                          model=d.get("model", self.model), tokens_used=d.get("eval_count", 0))

    async def generate_embeddings(self, texts: list[str]) -> EmbeddingResponse:
        embs = []
        async with httpx.AsyncClient(timeout=60) as h:
            for t in texts:
                r = await h.post(f"{self.base_url}/api/embeddings",
                                 json={"model": self.embed_model, "prompt": t})
                r.raise_for_status()
                embs.append(r.json()["embedding"])
        return EmbeddingResponse(embeddings=embs, provider=self.name, model=self.embed_model)

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as h:
                return (await h.get(f"{self.base_url}/api/tags")).status_code == 200
        except Exception:
            return False
