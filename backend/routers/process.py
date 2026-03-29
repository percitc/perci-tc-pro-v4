"""Router /process"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from services.rag_service import VECTOR_STORE_PATH
import json, shutil
from pathlib import Path

router = APIRouter()

@router.get("/session/{session_id}")
async def get_session(session_id: str):
    mp = VECTOR_STORE_PATH / f"{session_id}.json"
    if not mp.exists(): raise HTTPException(404, "Sesion no encontrada")
    meta = json.loads(mp.read_text())
    docs = list({m["doc_name"] for m in meta})
    return JSONResponse({"session_id": session_id, "documents": docs,
                         "total_chunks": len(meta), "status": "ready"})

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    for ext in [".index", ".json"]:
        p = VECTOR_STORE_PATH / f"{session_id}{ext}"
        if p.exists(): p.unlink()
    up = Path(f"./data/uploads/{session_id}")
    if up.exists(): shutil.rmtree(up)
    return JSONResponse({"status": "deleted", "session_id": session_id})
