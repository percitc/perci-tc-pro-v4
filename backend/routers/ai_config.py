"""Router /ai — Control del AI Router en tiempo real"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.ai import ai_router, TaskType

router = APIRouter()


class ProviderSet(BaseModel):
    provider: str | None = None   # None = automatico


@router.get("/status")
async def status():
    s = ai_router.status()
    return JSONResponse({**s, "task_routing": {t.value: p for t, p in {
        TaskType.CHAT_RAPIDO:  ["groq","openai","claude","gemini","ollama"],
        TaskType.DOC_LARGO:    ["gemini","claude","openai","groq","ollama"],
        TaskType.RAZONAMIENTO: ["claude","openai","gemini","groq","ollama"],
        TaskType.ALTA_CALIDAD: ["openai","claude","gemini","groq","ollama"],
        TaskType.GENERACION:   ["openai","claude","gemini","groq","ollama"],
        TaskType.OFFLINE:      ["ollama","groq","openai","claude","gemini"],
    }.items()}})


@router.post("/provider")
async def set_provider(req: ProviderSet):
    try:
        ai_router.set_provider(req.provider)
        return JSONResponse({"mode": "manual" if req.provider else "automatico",
                             "provider": req.provider})
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/health")
async def health():
    results = await ai_router.health_check_all()
    return JSONResponse({"providers": results,
                         "healthy":   [k for k,v in results.items() if v],
                         "unhealthy": [k for k,v in results.items() if not v]})


@router.post("/test")
async def test(req: ProviderSet):
    avail = ai_router.available_providers()
    if req.provider and req.provider not in avail:
        raise HTTPException(400, f"No disponible. Activos: {avail}")
    current = ai_router._manual
    try:
        ai_router.set_provider(req.provider)
        r = await ai_router.generate_response(
            "Hola, confirma que funcionas correctamente. Responde en una frase en espanol.",
            task=TaskType.CHAT_RAPIDO, options={"max_tokens": 60}
        )
        return JSONResponse({"provider": r.provider, "model": r.model,
                             "response": r.content, "tokens": r.tokens_used})
    finally:
        ai_router._manual = current
