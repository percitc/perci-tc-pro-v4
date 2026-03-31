"""PERCI TC PRO AI — Google Gemini Provider (1M token context, embeddings)"""
from __future__ import annotations
import os
import httpx
from .base_provider import BaseProvider, AIResponse, EmbeddingResponse

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider(BaseProvider):
    name                = "gemini"
    supports_embeddings = True

    def __init__(self):
        self.api_key     = os.getenv("GEMINI_API_KEY", "")
        self.model       = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        self.embed_model = os.getenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001")

    async def generate_response(self, prompt, context="", system="", history=None, options=None) -> AIResponse:
        o = options or {}
        sys_text = "\n\n".join(s for s in [system, f"CONTEXTO:\n{context}" if context else ""] if s)
        contents = []
        for m in (history or [])[-10:]:
            contents.append({"role": "user" if m["role"] == "user" else "model",
                              "parts": [{"text": m["content"]}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})
        body: dict = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": o.get("max_tokens", 2048),
                "temperature": o.get("temperature", 0.4)
            },
        }
        if sys_text:
            body["systemInstruction"] = {"parts": [{"text": sys_text}]}
        async with httpx.AsyncClient(timeout=90) as h:
            r = await h.post(
                f"{GEMINI_BASE}/models/{o.get('model', self.model)}:generateContent?key={self.api_key}",
                json=body, headers={"Content-Type": "application/json"}
            )
            r.raise_for_status()
            d = r.json()
        return AIResponse(
            content=d["candidates"][0]["content"]["parts"][0]["text"],
            provider=self.name, model=o.get("model", self.model),
            tokens_used=d.get("usageMetadata", {}).get("totalTokenCount", 0),
        )

    async def generate_embeddings(self, texts: list[str]) -> EmbeddingResponse:
        embs = []
        async with httpx.AsyncClient(timeout=60) as h:
            for i in range(0, len(texts), 100):
                body = {
                    "requests": [
                        {"model": self.embed_model, "content": {"parts": [{"text": t}]}}
                        for t in texts[i:i+100]
                    ]
                }
                r = await h.post(
                    f"{GEMINI_BASE}/{self.embed_model}:batchEmbedContents?key={self.api_key}",
                    json=body, headers={"Content-Type": "application/json"}
                )
                r.raise_for_status()
                embs.extend([x["values"] for x in r.json().get("embeddings", [])])
        return EmbeddingResponse(embeddings=embs, provider=self.name, model=self.embed_model)
