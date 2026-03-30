"""PERCI TC PRO AI v4 — Backend Principal"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging, uvicorn

from routers import upload, process, query, generate, ai_config
from services.rag_service import rag_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

os.makedirs("/tmp/perci_uploads", exist_ok=True)
os.makedirs("/tmp/perci_vectorstore", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rag_service.initialize()
    yield
    await rag_service.cleanup()


app = FastAPI(
    title="PERCI TC PRO AI",
    description="Plataforma SaaS educativa — Multi-Provider IA (OpenAI | Gemini | Groq | Claude | Ollama)",
    version="4.0.0",
    lifespan=lifespan,
)

# ── CORS primero — SIEMPRE antes que GZip ─────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(upload.router,    prefix="/upload",   tags=["Upload"])
app.include_router(process.router,   prefix="/process",  tags=["Process"])
app.include_router(query.router,     prefix="/query",    tags=["Query / Chat"])
app.include_router(generate.router,  prefix="/generate", tags=["Generate"])
app.include_router(ai_config.router, prefix="/ai",       tags=["AI Config"])


@app.get("/")
async def root():
    from services.ai import ai_router
    return {
        "name": "PERCI TC PRO AI",
        "version": "4.0.0",
        "providers_active": ai_router.available_providers(),
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=False)
