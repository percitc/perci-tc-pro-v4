"""Router /query CON INTELIGENCIA DE CHAT"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.rag_service import rag_service
from services.chat_intelligence import extract_generation_params
from services import generators
import logging

router = APIRouter()
log = logging.getLogger("perci.query")


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
        # Detectar si es una petición de generación
        query_lower = req.query.lower()
        generate_keywords = [
            "genera", "crea", "dame", "hazme", "quiero",
            "generar", "crear", "hacer", "necesito"
        ]
        
        is_generate_request = any(kw in query_lower for kw in generate_keywords)
        
        # Si es petición de generación, extraer parámetros y generar
        if is_generate_request:
            log.info(f"Detectada petición de generación: {req.query}")
            
            # Obtener contexto de los documentos
            chunks = await rag_service.retrieve(req.session_id, req.query)
            if not chunks:
                return JSONResponse({
                    "response": "⚠️ No hay documentos cargados en esta sesión. Por favor, sube un documento primero.",
                    "type": "error"
                })
            
            context = "\n\n".join(c["text"] for c in chunks[:5])  # Primeros 5 chunks
            
            # Extraer parámetros de la instrucción
            params = await extract_generation_params(req.query, context[:1000])
            
            log.info(f"Parámetros detectados: {params}")
            
            # Generar contenido con parámetros
            try:
                result = await generators.generate(
                    output_type=params["tipo"],
                    context=context,
                    params=params
                )
                
                return JSONResponse({
                    "response": f"✅ {params['tipo'].title()} generado con tus especificaciones:",
                    "generation": result,
                    "params_detected": {
                        k: v for k, v in params.items()
                        if not k.startswith("_")  # Ocultar campos internos
                    },
                    "type": "generation"
                })
            except Exception as e:
                log.error(f"Error generando contenido: {e}")
                return JSONResponse({
                    "response": f"❌ Error al generar contenido: {str(e)}",
                    "type": "error"
                })
        
        # Chat normal (sin generación)
        result = await rag_service.chat(req.session_id, req.query, req.history, req.task)
        return JSONResponse(result)
        
    except Exception as e:
        log.error(f"Error en chat: {e}")
        raise HTTPException(500, str(e))


@router.post("/retrieve")
async def retrieve(req: ChatRequest):
    chunks = await rag_service.retrieve(req.session_id, req.query)
    return JSONResponse({"chunks": chunks, "count": len(chunks)})
