"""PERCI TC PRO AI — Groq Provider (ultra-rapido, Llama 3.1 + Whisper)"""
from __future__ import annotations
import os
import httpx
from .base_provider import BaseProvider, AIResponse, TranscriptionResponse

GROQ_BASE = "https://api.groq.com/openai/v1"


class GroqProvider(BaseProvider):
    name                   = "groq"
    supports_transcription = True

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model   = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

    def _h(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def generate_response(self, prompt, context="", system="", history=None, options=None) -> AIResponse:
        o = options or {}
        sys_text = "\n\n".join(s for s in [system, f"CONTEXTO:\n{context}" if context else ""] if s)
        msgs = []
        if sys_text: msgs.append({"role": "system", "content": sys_text})
        msgs.extend((history or [])[-10:])
        msgs.append({"role": "user", "content": prompt})
        async with httpx.AsyncClient(timeout=30) as h:
            r = await h.post(f"{GROQ_BASE}/chat/completions", headers=self._h(),
                             json={"model": o.get("model", self.model), "messages": msgs,
                                   "max_tokens": o.get("max_tokens", 2000), "temperature": o.get("temperature", 0.4)})
            r.raise_for_status()
            d = r.json()
        return AIResponse(content=d["choices"][0]["message"]["content"], provider=self.name,
                          model=d.get("model", self.model), tokens_used=d.get("usage", {}).get("total_tokens", 0))

    async def transcribe_audio(self, file_path: str, language: str = "es") -> TranscriptionResponse:
        with open(file_path, "rb") as f:
            async with httpx.AsyncClient(timeout=120) as h:
                r = await h.post(f"{GROQ_BASE}/audio/transcriptions",
                                 headers={"Authorization": f"Bearer {self.api_key}"},
                                 data={"model": "whisper-large-v3", "language": language},
                                 files={"file": f})
                r.raise_for_status()
        return TranscriptionResponse(text=r.json().get("text", ""), provider=self.name, language=language)
