"""Router /query"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.rag_service import rag_service

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str
    query: str
    history: list[dict] | None = None
    task: str = "auto"

@router.post("/chat")
async def chat(req: ChatRequest):
    if not req.session_id or not req.query:
        raise HTTPException(400, "session_id y query son requeridos")
    try:
        result = await rag_service.chat(req.session_id, req.query, req.history, req.task)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/retrieve")
async def retrieve(req: ChatRequest):
    chunks = await rag_service.retrieve(req.session_id, req.query)
    return JSONResponse({"chunks": chunks, "count": len(chunks)})
