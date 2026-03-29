"""Router /generate"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from services.rag_service import rag_service
from services.generators import generate, podcast_audio, tts

router = APIRouter()


class GenerateRequest(BaseModel):
    session_id: str
    output_type: str
    query: str | None = None
    title: str | None = None
    num_items: int | None = None


class TTSRequest(BaseModel):
    text: str
    voice: str = "onyx"


@router.post("/content")
async def gen_content(req: GenerateRequest):
    query  = req.query or "resume y explica el contenido completo"
    chunks = await rag_service.retrieve(req.session_id, query)
    if not chunks:
        raise HTTPException(404, "Sin documentos en esta sesion")
    context = "\n\n---\n\n".join(c["text"] for c in chunks)
    kwargs: dict = {}
    if req.title: kwargs["title"] = req.title
    if req.num_items:
        if req.output_type in ("flashcards","quiz"): kwargs["num"] = req.num_items
        elif req.output_type == "slides": kwargs["num_slides"] = req.num_items
    try:
        return JSONResponse(await generate(req.output_type, context, **kwargs))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/audio/tts")
async def gen_tts(req: TTSRequest):
    try:
        audio = await tts(req.text, req.voice)
        return StreamingResponse(iter([audio]), media_type="audio/mpeg",
                                 headers={"Content-Disposition": 'attachment; filename="audio.mp3"'})
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/audio/podcast")
async def gen_podcast(req: GenerateRequest):
    from services.generators import generate as gen
    chunks  = await rag_service.retrieve(req.session_id, req.query or "explica el contenido")
    if not chunks: raise HTTPException(404, "Sin documentos")
    context = "\n\n".join(c["text"] for c in chunks)
    script  = (await gen("audio_script", context))["content"]
    audio   = await podcast_audio(script)
    return StreamingResponse(iter([audio]), media_type="audio/mpeg",
                             headers={"Content-Disposition": 'attachment; filename="podcast.mp3"'})
