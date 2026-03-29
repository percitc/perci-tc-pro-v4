"""PERCI TC PRO AI — OpenAI Provider (GPT-4o + embeddings + Whisper + TTS)"""
from __future__ import annotations
import os
from openai import AsyncOpenAI
from .base_provider import BaseProvider, AIResponse, EmbeddingResponse, TranscriptionResponse


class OpenAIProvider(BaseProvider):
    name                   = "openai"
    supports_embeddings    = True
    supports_transcription = True

    def __init__(self):
        self.client      = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model       = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.embed_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
        self.tts_model   = os.getenv("TTS_MODEL", "tts-1-hd")

    def _build_messages(self, prompt, context, system, history):
        msgs = []
        parts = [s for s in [system, f"CONTEXTO:\n{context}" if context else ""] if s]
        if parts:
            msgs.append({"role": "system", "content": "\n\n".join(parts)})
        msgs.extend((history or [])[-10:])
        msgs.append({"role": "user", "content": prompt})
        return msgs

    async def generate_response(self, prompt, context="", system="", history=None, options=None) -> AIResponse:
        o = options or {}
        r = await self.client.chat.completions.create(
            model=o.get("model", self.model),
            messages=self._build_messages(prompt, context, system, history),
            max_tokens=o.get("max_tokens", 2000),
            temperature=o.get("temperature", 0.4),
        )
        return AIResponse(
            content=r.choices[0].message.content,
            provider=self.name, model=r.model,
            tokens_used=r.usage.total_tokens if r.usage else 0,
        )

    async def generate_embeddings(self, texts: list[str]) -> EmbeddingResponse:
        all_emb, tokens = [], 0
        for i in range(0, len(texts), 100):
            r = await self.client.embeddings.create(model=self.embed_model, input=texts[i:i+100])
            all_emb.extend([x.embedding for x in r.data])
            if r.usage: tokens += r.usage.total_tokens
        return EmbeddingResponse(embeddings=all_emb, provider=self.name, model=self.embed_model, tokens_used=tokens)

    async def transcribe_audio(self, file_path: str, language: str = "es") -> TranscriptionResponse:
        with open(file_path, "rb") as f:
            r = await self.client.audio.transcriptions.create(
                model="whisper-1", file=f, language=language, response_format="text"
            )
        return TranscriptionResponse(text=str(r), provider=self.name, language=language)

    async def tts(self, text: str, voice: str = "onyx") -> bytes:
        parts = []
        for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            r = await self.client.audio.speech.create(
                model=self.tts_model, voice=voice, input=chunk, response_format="mp3"
            )
            parts.append(r.content)
        return b"".join(parts)
