"""PERCI TC PRO AI — Generadores Educativos (Multi-Provider)"""
from __future__ import annotations
import os, json, re
from services.ai import ai_router, TaskType
from dotenv import load_dotenv

load_dotenv()

TTS_VOICE_PROFESOR   = os.getenv("TTS_VOICE_PROFESOR",   "onyx")
TTS_VOICE_ASISTENTE  = os.getenv("TTS_VOICE_ASISTENTE",  "nova")
TTS_VOICE_ESTUDIANTE = os.getenv("TTS_VOICE_ESTUDIANTE", "shimmer")

SYS = ("Eres PERCI, experto en educacion y diseno instruccional. "
       "Respondes SIEMPRE en espanol claro, didactico y profesional. "
       "Generas contenido estructurado, profundo y de alta calidad educativa. "
       "Cuando se pide JSON, respondes UNICAMENTE con JSON valido, sin texto adicional, "
       "sin bloques de codigo, sin explicaciones.")


def _extract_json(text: str) -> str:
    """Extrae JSON limpio de una respuesta que puede tener markdown."""
    # Quitar bloques ```json ... ```
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    # Buscar el primer { o [ y el ultimo } o ]
    start = min(
        (text.find('{') if text.find('{') != -1 else len(text)),
        (text.find('[') if text.find('[') != -1 else len(text))
    )
    if start == len(text):
        return text
    # Encontrar el cierre correspondiente
    open_char  = text[start]
    close_char = '}' if open_char == '{' else ']'
    end = text.rfind(close_char)
    if end == -1:
        return text
    return text[start:end+1]


def _safe_json(text: str) -> dict:
    """Parsea JSON de forma segura con fallback."""
    try:
        return json.loads(text)
    except Exception:
        try:
            clean = _extract_json(text)
            return json.loads(clean)
        except Exception:
            return {"error": "No se pudo parsear la respuesta", "raw": text[:500]}


async def _llm(system: str, user: str, max_tokens: int = 4000) -> str:
    """Llama al LLM sin json_mode (compatible con Groq y OpenAI)."""
    o = {"max_tokens": max_tokens, "temperature": 0.3}
    r = await ai_router.generate_response(
        prompt=user, system=system,
        task=TaskType.GENERACION, options=o
    )
    return r.content


async def generate_summary(context: str, title: str = "") -> dict:
    t = await _llm(
        SYS,
        f"Genera un resumen ejecutivo completo{f' de: {title}' if title else ''}.\n"
        f"Estructura: introduccion, ideas principales (5-10), conceptos clave, conclusiones, aplicaciones practicas.\n\n"
        f"CONTENIDO:\n{context}"
    )
    return {"type": "summary", "content": t}


async def generate_flashcards(context: str, num: int = 20) -> dict:
    r = await _llm(
        SYS,
        f'Crea {num} flashcards sobre el contenido. '
        f'Responde UNICAMENTE con este JSON valido, sin texto adicional:\n'
        f'{{"tarjetas":[{{"id":1,"pregunta":"pregunta aqui","respuesta":"respuesta aqui","categoria":"tema","dificultad":"basico"}}]}}\n\n'
        f'CONTENIDO:\n{context[:6000]}'
    )
    return {"type": "flashcards", "content": _safe_json(r)}


async def generate_quiz(context: str, num: int = 10) -> dict:
    r = await _llm(
        SYS,
        f'Crea {num} preguntas de opcion multiple. '
        f'Responde UNICAMENTE con este JSON valido, sin texto adicional:\n'
        f'{{"cuestionario":[{{"id":1,"pregunta":"pregunta","opciones":["A) opcion1","B) opcion2","C) opcion3","D) opcion4"],"respuesta_correcta":"A","explicacion":"explicacion","dificultad":"basico"}}]}}\n\n'
        f'CONTENIDO:\n{context[:6000]}'
    )
    return {"type": "quiz", "content": _safe_json(r)}


async def generate_slides(context: str, num_slides: int = 10) -> dict:
    r = await _llm(
        SYS,
        f'Crea {num_slides} diapositivas para presentacion. '
        f'Responde UNICAMENTE con este JSON valido, sin texto adicional:\n'
        f'{{"titulo_presentacion":"titulo","slides":[{{"numero":1,"tipo":"portada","titulo":"titulo","subtitulo":"subtitulo","puntos":["punto1","punto2"],"nota_orador":"nota","emoji":"🎯"}}]}}\n\n'
        f'CONTENIDO:\n{context[:6000]}'
    )
    return {"type": "slides", "content": _safe_json(r)}


async def generate_infographic(context: str) -> dict:
    r = await _llm(
        SYS,
        f'Crea una infografia educativa. '
        f'Responde UNICAMENTE con este JSON valido, sin texto adicional:\n'
        f'{{"titulo":"titulo","subtitulo":"subtitulo","color_principal":"#3B82F6","secciones":[{{"icono":"📚","titulo":"seccion","descripcion":"descripcion","datos":["dato1","dato2"]}}],"datos_clave":[{{"numero":"90%","descripcion":"descripcion"}}],"conclusion":"conclusion"}}\n\n'
        f'CONTENIDO:\n{context[:5000]}'
    )
    return {"type": "infographic", "content": _safe_json(r)}


async def generate_course(context: str, title: str = "") -> dict:
    r = await _llm(
        SYS,
        f'Crea un curso educativo completo. '
        f'Responde UNICAMENTE con este JSON valido, sin texto adicional:\n'
        f'{{"titulo_curso":"titulo","descripcion":"descripcion","duracion_estimada":"4 horas","nivel":"intermedio","objetivos":["objetivo1","objetivo2"],"modulos":[{{"numero":1,"titulo":"modulo","descripcion":"descripcion","temas":[{{"titulo":"tema","contenido":"contenido","actividad":"actividad"}}],"evaluacion":"evaluacion"}}],"evaluacion_final":"evaluacion"}}\n\n'
        f'CONTENIDO:\n{context[:8000]}',
        max_tokens=5000
    )
    return {"type": "course", "content": _safe_json(r)}


async def generate_audio_script(context: str) -> dict:
    t = await _llm(
        SYS,
        f"Escribe un guion de podcast educativo de 5-8 minutos con 2 voces.\n"
        f"Formato EXACTO (una linea por turno):\n"
        f"[PROFESOR]: texto del profesor aqui\n"
        f"[ASISTENTE]: texto del asistente aqui\n\n"
        f"Natural, dinamico, en espanol. Minimo 10 intercambios.\n\n"
        f"CONTENIDO:\n{context[:6000]}",
        max_tokens=3000
    )
    return {"type": "audio_script", "content": t}


async def tts(text: str, voice: str = TTS_VOICE_PROFESOR) -> bytes:
    return await ai_router.tts(text, voice)


async def podcast_audio(script: str) -> bytes:
    parts = []
    for line in script.split("\n"):
        line = line.strip()
        if   line.startswith("[PROFESOR]:"):   parts.append(await tts(line[11:].strip(), TTS_VOICE_PROFESOR))
        elif line.startswith("[ASISTENTE]:"):  parts.append(await tts(line[12:].strip(), TTS_VOICE_ASISTENTE))
        elif line.startswith("[ESTUDIANTE]:"): parts.append(await tts(line[13:].strip(), TTS_VOICE_ESTUDIANTE))
    return b"".join(parts)


GENERATORS = {
    "summary":      generate_summary,
    "flashcards":   generate_flashcards,
    "quiz":         generate_quiz,
    "slides":       generate_slides,
    "infographic":  generate_infographic,
    "course":       generate_course,
    "audio_script": generate_audio_script,
}


async def generate(output_type: str, context: str, **kwargs) -> dict:
    fn = GENERATORS.get(output_type)
    if not fn: raise ValueError(f"Tipo no soportado: {output_type}")
    return await fn(context, **kwargs)
