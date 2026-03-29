"""PERCI TC PRO AI — Anthropic Claude Provider (razonamiento profundo)"""
from __future__ import annotations
import os
import httpx
from .base_provider import BaseProvider, AIResponse

ANTHROPIC_BASE = "https://api.anthropic.com/v1"


class ClaudeProvider(BaseProvider):
    name = "claude"

    def __init__(self):
        self.api_key = os.getenv("CLAUDE_API_KEY", "")
        self.model   = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

    def _h(self):
        return {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}

    async def generate_response(self, prompt, context="", system="", history=None, options=None) -> AIResponse:
        o = options or {}
        sys_text = "\n\n".join(s for s in [system, f"CONTEXTO:\n{context}" if context else ""] if s)
        if not sys_text:
            sys_text = "Eres un asistente educativo experto. Respondes en espanol."
        msgs = []
        for m in (history or [])[-10:]:
            msgs.append({"role": m["role"], "content": m["content"]})
        msgs.append({"role": "user", "content": prompt})
        body = {"model": o.get("model", self.model), "max_tokens": o.get("max_tokens", 2000),
                "temperature": o.get("temperature", 0.4), "system": sys_text, "messages": msgs}
        async with httpx.AsyncClient(timeout=90) as h:
            r = await h.post(f"{ANTHROPIC_BASE}/messages", json=body, headers=self._h())
            r.raise_for_status()
            d = r.json()
        content = d["content"][0]["text"] if d.get("content") else ""
        usage   = d.get("usage", {})
        return AIResponse(content=content, provider=self.name, model=d.get("model", self.model),
                          tokens_used=usage.get("input_tokens", 0) + usage.get("output_tokens", 0))
