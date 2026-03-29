"""Router /upload"""
from __future__ import annotations
import os, uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from services.file_processor import process_file, process_url, UPLOAD_DIR
from services.rag_service import rag_service

MAX_MB = int(os.getenv("MAX_FILE_SIZE_MB", 500))
ALLOWED = {".pdf",".docx",".doc",".pptx",".ppt",".txt",".md",
           ".csv",".xlsx",".xls",".png",".jpg",".jpeg",".webp",
           ".mp3",".wav",".m4a",".mp4",".mov",".avi"}
router = APIRouter()


@router.post("/file")
async def upload_file(file: UploadFile = File(...), session_id: str = Form(None)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"Extension no soportada: {ext}")
    data = await file.read()
    if len(data) / 1024 / 1024 > MAX_MB:
        raise HTTPException(413, f"Archivo muy grande. Max: {MAX_MB}MB")
    sid  = session_id or str(uuid.uuid4())
    dest = UPLOAD_DIR / sid; dest.mkdir(parents=True, exist_ok=True)
    fp   = dest / file.filename; fp.write_bytes(data)
    try:
        text = await process_file(fp)
    except Exception as e:
        raise HTTPException(422, f"Error procesando archivo: {e}")
    if not text.strip():
        raise HTTPException(422, "No se pudo extraer texto del archivo")
    idx = await rag_service.index_document(sid, text, file.filename)
    return JSONResponse({"session_id": sid, "filename": file.filename,
                         "size_mb": round(len(data)/1024/1024, 2),
                         "chars_extracted": len(text), **idx, "preview": text[:500], "status": "ready"})


@router.post("/url")
async def upload_url(url: str = Form(...), session_id: str = Form(None)):
    sid = session_id or str(uuid.uuid4())
    try:
        text = await process_url(url)
    except Exception as e:
        raise HTTPException(422, f"Error procesando URL: {e}")
    if not text.strip():
        raise HTTPException(422, "No se pudo extraer texto")
    idx = await rag_service.index_document(sid, text, url)
    return JSONResponse({"session_id": sid, "url": url, "chars_extracted": len(text), **idx, "status": "ready"})
