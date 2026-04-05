"""PERCI TC PRO AI — Generadores Educativos (Multi-Provider + ElevenLabs TTS)"""
from __future__ import annotations
import os, json, re
from services.ai import ai_router, TaskType
from dotenv import load_dotenv

load_dotenv()

TTS_VOICE_PROFESOR   = os.getenv("TTS_VOICE_PROFESOR",   "onyx")
TTS_VOICE_ASISTENTE  = os.getenv("TTS_VOICE_ASISTENTE",  "nova")
TTS_VOICE_ESTUDIANTE = os.getenv("TTS_VOICE_ESTUDIANTE", "shimmer")

ELEVENLABS_API_KEY   = os.getenv("ELEVENLABS_API_KEY", "")

# Voces de ElevenLabs en español (IDs predefinidos)
ELEVENLABS_VOICES = {
    "profesor":   os.getenv("ELEVENLABS_VOICE_PROFESOR",   "pNInz6obpgDQGcFmaJgB"),  # Adam
    "asistente":  os.getenv("ELEVENLABS_VOICE_ASISTENTE",  "EXAVITQu4vr4xnSDxMaL"),  # Bella
    "estudiante": os.getenv("ELEVENLABS_VOICE_ESTUDIANTE", "21m00Tcm4TlvDq8ikWAM"),  # Rachel
}

SYS = ("Eres PERCI, experto en educacion y diseno instruccional. "
       "Respondes SIEMPRE en espanol claro, didactico y profesional. "
       "Generas contenido estructurado, profundo y de alta calidad educativa. "
       "Cuando se pide JSON, respondes UNICAMENTE con JSON valido, sin texto adicional, "
       "sin bloques de codigo, sin explicaciones.")


# ── Helpers JSON ───────────────────────────────────────────────────────────────

def _extract_json(text: str) -> str:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    start = min(
        (text.find('{') if text.find('{') != -1 else len(text)),
        (text.find('[') if text.find('[') != -1 else len(text))
    )
    if start == len(text):
        return text
    open_char  = text[start]
    close_char = '}' if open_char == '{' else ']'
    end = text.rfind(close_char)
    if end == -1:
        return text
    return text[start:end+1]


def _safe_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        try:
            return json.loads(_extract_json(text))
        except Exception:
            return {"error": "No se pudo parsear la respuesta", "raw": text[:500]}


async def _llm(system: str, user: str, max_tokens: int = 4000) -> str:
    o = {"max_tokens": max_tokens, "temperature": 0.3}
    r = await ai_router.generate_response(
        prompt=user, system=system,
        task=TaskType.GENERACION, options=o
    )
    return r.content


# ── Generadores ────────────────────────────────────────────────────────────────

async def generate_summary(context: str, title: str = "") -> dict:
    t = await _llm(SYS,
        f"Genera un resumen ejecutivo completo{f' de: {title}' if title else ''}.\n"
        f"Estructura: introduccion, ideas principales (5-10), conceptos clave, conclusiones, aplicaciones practicas.\n\n"
        f"CONTENIDO:\n{context}")
    return {"type": "summary", "content": t}


async def generate_flashcards(context: str, num: int = 20) -> dict:
    r = await _llm(SYS,
        f'Crea {num} flashcards. JSON valido sin texto extra:\n'
        f'{{"tarjetas":[{{"id":1,"pregunta":"...","respuesta":"...","categoria":"tema","dificultad":"basico"}}]}}\n\n'
        f'CONTENIDO:\n{context[:6000]}')
    return {"type": "flashcards", "content": _safe_json(r)}


async def generate_quiz(context: str, num: int = 10) -> dict:
    r = await _llm(SYS,
        f'Crea {num} preguntas opcion multiple. JSON valido sin texto extra:\n'
        f'{{"cuestionario":[{{"id":1,"pregunta":"...","opciones":["A) ...","B) ...","C) ...","D) ..."],"respuesta_correcta":"A","explicacion":"...","dificultad":"basico"}}]}}\n\n'
        f'CONTENIDO:\n{context[:6000]}')
    return {"type": "quiz", "content": _safe_json(r)}


async def generate_slides(context: str, num_slides: int = 10) -> dict:
    r = await _llm(SYS,
        f'Crea {num_slides} diapositivas. JSON valido sin texto extra:\n'
        f'{{"titulo_presentacion":"titulo","slides":[{{"numero":1,"tipo":"portada","titulo":"...","subtitulo":"...","puntos":["..."],"nota_orador":"...","emoji":"🎯"}}]}}\n\n'
        f'CONTENIDO:\n{context[:6000]}')
    return {"type": "slides", "content": _safe_json(r)}


async def generate_infographic(context: str) -> dict:
    r = await _llm(SYS,
        f'Crea infografia educativa. JSON valido sin texto extra:\n'
        f'{{"titulo":"...","subtitulo":"...","color_principal":"#3B82F6","secciones":[{{"icono":"📚","titulo":"...","descripcion":"...","datos":["..."]}}],"datos_clave":[{{"numero":"90%","descripcion":"..."}}],"conclusion":"..."}}\n\n'
        f'CONTENIDO:\n{context[:5000]}')
    return {"type": "infographic", "content": _safe_json(r)}


async def generate_course(context: str, title: str = "") -> dict:
    r = await _llm(SYS,
        f'Crea curso educativo completo. JSON valido sin texto extra:\n'
        f'{{"titulo_curso":"...","descripcion":"...","duracion_estimada":"4 horas","nivel":"intermedio","objetivos":["..."],"modulos":[{{"numero":1,"titulo":"...","descripcion":"...","temas":[{{"titulo":"...","contenido":"...","actividad":"..."}}],"evaluacion":"..."}}],"evaluacion_final":"..."}}\n\n'
        f'CONTENIDO:\n{context[:8000]}', max_tokens=5000)
    return {"type": "course", "content": _safe_json(r)}


async def generate_audio_script(context: str) -> dict:
    t = await _llm(SYS,
        f"Guion podcast educativo 5-8 min con 2 voces. Formato EXACTO:\n"
        f"[PROFESOR]: texto\n[ASISTENTE]: texto\n\n"
        f"Natural, dinamico, espanol. Minimo 10 intercambios.\n\nCONTENIDO:\n{context[:6000]}",
        max_tokens=3000)
    return {"type": "audio_script", "content": t}


# ── TTS — ElevenLabs (principal) + OpenAI (fallback) ──────────────────────────

async def _tts_elevenlabs(text: str, voice_id: str) -> bytes:
    """Genera audio con ElevenLabs."""
    import httpx
    url  = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    body = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    async with httpx.AsyncClient(timeout=60) as h:
        r = await h.post(url, json=body, headers=headers)
        r.raise_for_status()
        return r.content


async def tts(text: str, voice: str = TTS_VOICE_PROFESOR) -> bytes:
    """
    TTS con prioridad:
    1. ElevenLabs (voces naturales en español)
    2. OpenAI TTS (fallback si no hay ElevenLabs)
    """
    # Mapear nombre de voz a ID de ElevenLabs
    voice_map = {
        TTS_VOICE_PROFESOR:   ELEVENLABS_VOICES["profesor"],
        TTS_VOICE_ASISTENTE:  ELEVENLABS_VOICES["asistente"],
        TTS_VOICE_ESTUDIANTE: ELEVENLABS_VOICES["estudiante"],
        "onyx":    ELEVENLABS_VOICES["profesor"],
        "nova":    ELEVENLABS_VOICES["asistente"],
        "shimmer": ELEVENLABS_VOICES["estudiante"],
    }

    # Intentar ElevenLabs primero
    if ELEVENLABS_API_KEY:
        try:
            voice_id = voice_map.get(voice, ELEVENLABS_VOICES["profesor"])
            return await _tts_elevenlabs(text, voice_id)
        except Exception as e:
            import logging
            logging.getLogger("perci.tts").warning(f"ElevenLabs fallo: {e}. Usando OpenAI...")

    # Fallback: OpenAI TTS
    return await ai_router.tts(text, voice)


async def podcast_audio(script: str) -> bytes:
    """Genera audio de podcast con multiples voces."""
    parts = []
    for line in script.split("\n"):
        line = line.strip()
        if   line.startswith("[PROFESOR]:"):
            parts.append(await tts(line[11:].strip(), TTS_VOICE_PROFESOR))
        elif line.startswith("[ASISTENTE]:"):
            parts.append(await tts(line[12:].strip(), TTS_VOICE_ASISTENTE))
        elif line.startswith("[ESTUDIANTE]:"):
            parts.append(await tts(line[13:].strip(), TTS_VOICE_ESTUDIANTE))
    return b"".join(parts)


# ── Dispatcher ─────────────────────────────────────────────────────────────────

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
