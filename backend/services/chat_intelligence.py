"""Sistema inteligente de chat que extrae parámetros de las instrucciones del usuario"""
from __future__ import annotations
import re
from typing import Dict, Any
from services.ai import ai_router, TaskType

SYS_PARAMS_EXTRACTOR = """Eres un asistente que extrae parámetros de instrucciones del usuario.

El usuario pedirá generar contenido educativo. Tu trabajo es extraer:
- tipo: summary|flashcards|quiz|slides|infographic|course|audio
- cantidad: número de items (para flashcards, quiz, slides)
- duracion_minutos: duración en minutos (para audio)
- nivel_detalle: basico|intermedio|avanzado
- estilo: casual|formal|didactico
- enfoque: conceptos_clave|explicacion_completa|practica

Responde SOLO con JSON válido, sin texto adicional:
{
  "tipo": "audio",
  "cantidad": 10,
  "duracion_minutos": 5,
  "nivel_detalle": "intermedio",
  "estilo": "didactico",
  "enfoque": "explicacion_completa"
}"""


async def extract_generation_params(user_message: str, context: str = "") -> Dict[str, Any]:
    """
    Extrae parámetros de generación desde el mensaje del usuario.
    
    Ejemplos:
    - "dame un resumen corto" → {tipo: summary, nivel_detalle: basico}
    - "crea 50 flashcards avanzadas" → {tipo: flashcards, cantidad: 50, nivel_detalle: avanzado}
    - "audio de 3 minutos explicando esto" → {tipo: audio, duracion_minutos: 3}
    """
    import json
    import logging
    
    log = logging.getLogger("perci.chat_intelligence")
    
    # Primero intentar detección simple (más rápido)
    simple_params = _extract_params_simple(user_message)
    
    # Si es una petición clara y simple, usar detección directa
    if simple_params.get("_confidence") == "high":
        log.info(f"Parámetros detectados (simple): {simple_params}")
        return simple_params
    
    # Para casos complejos, usar IA
    try:
        prompt = f"""Instrucción del usuario: "{user_message}"

Contexto del documento: {context[:500] if context else "No disponible"}

Extrae los parámetros de generación."""

        response = await ai_router.generate_response(
            prompt=prompt,
            system=SYS_PARAMS_EXTRACTOR,
            task=TaskType.GENERACION,
            options={"max_tokens": 500, "temperature": 0.1}
        )
        
        # Limpiar y parsear JSON
        content = response.content.strip()
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        
        params = json.loads(content)
        
        # Valores por defecto si faltan
        defaults = {
            "tipo": "summary",
            "cantidad": 10,
            "duracion_minutos": 5,
            "nivel_detalle": "intermedio",
            "estilo": "didactico",
            "enfoque": "explicacion_completa"
        }
        
        final_params = {**defaults, **params}
        log.info(f"Parámetros detectados (IA): {final_params}")
        return final_params
        
    except Exception as e:
        log.warning(f"Error extrayendo parámetros con IA: {e}, usando detección simple")
        return simple_params


def _extract_params_simple(message: str) -> Dict[str, Any]:
    """Extracción de parámetros por keywords (fallback rápido)"""
    msg_lower = message.lower()
    
    params = {
        "tipo": "summary",
        "cantidad": 10,
        "duracion_minutos": 5,
        "nivel_detalle": "intermedio",
        "estilo": "didactico",
        "enfoque": "explicacion_completa",
        "_confidence": "low"  # Indica confianza en la detección
    }
    
    # Detectar tipo
    if any(word in msg_lower for word in ["flashcard", "tarjeta", "carta"]):
        params["tipo"] = "flashcards"
        params["_confidence"] = "high"
    elif any(word in msg_lower for word in ["quiz", "cuestionario", "pregunta", "examen", "test"]):
        params["tipo"] = "quiz"
        params["_confidence"] = "high"
    elif any(word in msg_lower for word in ["audio", "podcast", "escuchar", "grabacion"]):
        params["tipo"] = "audio"
        params["_confidence"] = "high"
    elif any(word in msg_lower for word in ["slide", "diapositiva", "presentacion", "ppt"]):
        params["tipo"] = "slides"
        params["_confidence"] = "high"
    elif any(word in msg_lower for word in ["infografia", "infographic"]):
        params["tipo"] = "infographic"
        params["_confidence"] = "high"
    elif any(word in msg_lower for word in ["curso", "course", "programa"]):
        params["tipo"] = "course"
        params["_confidence"] = "high"
    elif any(word in msg_lower for word in ["resumen", "summary", "resume"]):
        params["tipo"] = "summary"
        params["_confidence"] = "high"
    
    # Detectar cantidad (números en el mensaje)
    numbers = re.findall(r'\b(\d+)\b', message)
    if numbers:
        first_num = int(numbers[0])
        if params["tipo"] == "audio":
            params["duracion_minutos"] = first_num
        else:
            params["cantidad"] = first_num
        params["_confidence"] = "high"
    
    # Detectar nivel
    if any(word in msg_lower for word in ["basico", "simple", "facil", "corto", "breve", "resumido"]):
        params["nivel_detalle"] = "basico"
        params["_confidence"] = "high"
    elif any(word in msg_lower for word in ["avanzado", "complejo", "detallado", "largo", "profundo", "completo", "extenso"]):
        params["nivel_detalle"] = "avanzado"
        params["_confidence"] = "high"
    
    # Detectar duración específica para audio
    duracion_match = re.search(r'(\d+)\s*min', msg_lower)
    if duracion_match:
        params["duracion_minutos"] = int(duracion_match.group(1))
        params["_confidence"] = "high"
    
    # Detectar enfoque
    if any(word in msg_lower for word in ["conceptos clave", "puntos principales", "lo importante"]):
        params["enfoque"] = "conceptos_clave"
    elif any(word in msg_lower for word in ["ejemplo", "practica", "aplicacion", "caso real"]):
        params["enfoque"] = "practica"
    
    return params
