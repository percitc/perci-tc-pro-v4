"""PERCI TC PRO AI — Generadores Educativos DINÁMICOS"""
from __future__ import annotations
import os, json, re
from services.ai import ai_router, TaskType
from dotenv import load_dotenv

load_dotenv()

SYS = ("Eres PERCI, experto en educacion y diseno instruccional. "
       "Respondes SIEMPRE en espanol claro, didactico y profesional. "
       "Generas contenido estructurado, profundo y de alta calidad educativa. "
       "Cuando se pide JSON, respondes UNICAMENTE con JSON valido, sin texto adicional, "
       "sin bloques de codigo, sin explicaciones.")


# ── Helpers ────────────────────────────────────────────────────────────────────

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


# ── Generadores DINÁMICOS ──────────────────────────────────────────────────────

async def generate_summary(context: str, params: dict = None, **kwargs) -> dict:
    """Resumen con profundidad configurable"""
    params = params or {}
    nivel = params.get("nivel_detalle", "intermedio")
    
    niveles_texto = {
        "basico": "breve y sencillo (2-3 párrafos)",
        "intermedio": "completo con estructura clara (5-7 párrafos)",
        "avanzado": "exhaustivo y profundo (10+ párrafos con análisis detallado)"
    }
    
    t = await _llm(SYS,
        f"Genera un resumen {niveles_texto[nivel]}.\n"
        f"Estructura: introduccion, ideas principales, conceptos clave, conclusiones, aplicaciones practicas.\n\n"
        f"CONTENIDO:\n{context}")
    return {"type": "summary", "content": t, "params": params}


async def generate_flashcards(context: str, params: dict = None, **kwargs) -> dict:
    """Flashcards con cantidad y dificultad configurable"""
    params = params or {}
    num = params.get("cantidad", kwargs.get("num", 20))
    nivel = params.get("nivel_detalle", "intermedio")
    
    dificultad_instruccion = {
        "basico": "preguntas simples y directas",
        "intermedio": "preguntas que requieren comprensión",
        "avanzado": "preguntas que requieren análisis profundo y aplicación"
    }
    
    r = await _llm(SYS,
        f'Crea {num} flashcards con {dificultad_instruccion[nivel]}. JSON valido sin texto extra:\n'
        f'{{"tarjetas":[{{"id":1,"pregunta":"...","respuesta":"...","categoria":"tema","dificultad":"{nivel}"}}]}}\n\n'
        f'CONTENIDO:\n{context[:8000]}')
    return {"type": "flashcards", "content": _safe_json(r), "params": params}


async def generate_quiz(context: str, params: dict = None, **kwargs) -> dict:
    """Quiz con cantidad y dificultad configurable"""
    params = params or {}
    num = params.get("cantidad", kwargs.get("num", 10))
    nivel = params.get("nivel_detalle", "intermedio")
    
    r = await _llm(SYS,
        f'Crea {num} preguntas opcion multiple nivel {nivel}. JSON valido sin texto extra:\n'
        f'{{"cuestionario":[{{"id":1,"pregunta":"...","opciones":["A) ...","B) ...","C) ...","D) ..."],"respuesta_correcta":"A","explicacion":"...","dificultad":"{nivel}"}}]}}\n\n'
        f'CONTENIDO:\n{context[:8000]}')
    return {"type": "quiz", "content": _safe_json(r), "params": params}


async def generate_slides(context: str, params: dict = None, **kwargs) -> dict:
    """Slides con cantidad configurable"""
    params = params or {}
    num_slides = params.get("cantidad", kwargs.get("num_slides", 10))
    
    r = await _llm(SYS,
        f'Crea {num_slides} diapositivas. JSON valido sin texto extra:\n'
        f'{{"titulo_presentacion":"titulo","slides":[{{"numero":1,"tipo":"portada","titulo":"...","subtitulo":"...","puntos":["..."],"nota_orador":"...","emoji":"🎯"}}]}}\n\n'
        f'CONTENIDO:\n{context[:8000]}')
    return {"type": "slides", "content": _safe_json(r), "params": params}


async def generate_infographic(context: str, params: dict = None, **kwargs) -> dict:
    """Infografía con profundidad configurable"""
    params = params or {}
    
    r = await _llm(SYS,
        f'Crea infografia educativa. JSON valido sin texto extra:\n'
        f'{{"titulo":"...","subtitulo":"...","color_principal":"#3B82F6","secciones":[{{"icono":"📚","titulo":"...","descripcion":"...","datos":["..."]}}],"datos_clave":[{{"numero":"90%","descripcion":"..."}}],"conclusion":"..."}}\n\n'
        f'CONTENIDO:\n{context[:6000]}')
    return {"type": "infographic", "content": _safe_json(r), "params": params}


async def generate_course(context: str, params: dict = None, **kwargs) -> dict:
    """Curso con profundidad configurable"""
    params = params or {}
    nivel = params.get("nivel_detalle", "intermedio")
    
    r = await _llm(SYS,
        f'Crea curso educativo nivel {nivel}. JSON valido sin texto extra:\n'
        f'{{"titulo_curso":"...","descripcion":"...","duracion_estimada":"4 horas","nivel":"{nivel}","objetivos":["..."],"modulos":[{{"numero":1,"titulo":"...","descripcion":"...","temas":[{{"titulo":"...","contenido":"...","actividad":"..."}}],"evaluacion":"..."}}],"evaluacion_final":"..."}}\n\n'
        f'CONTENIDO:\n{context[:10000]}', max_tokens=6000)
    return {"type": "course", "content": _safe_json(r), "params": params}


async def generate_audio_script(context: str, params: dict = None, **kwargs) -> dict:
    """
    Script de audio con duración CONFIGURABLE.
    params['duracion_minutos'] controla la longitud.
    """
    params = params or {}
    duracion = params.get("duracion_minutos", 5)
    nivel = params.get("nivel_detalle", "intermedio")
    enfoque = params.get("enfoque", "explicacion_completa")
    
    # Calcular palabras: ~150 palabras = 1 minuto
    max_palabras = duracion * 150
    
    enfoques_texto = {
        "conceptos_clave": "enfócate SOLO en los conceptos más importantes",
        "explicacion_completa": "explica de forma completa y didáctica",
        "practica": "incluye ejemplos prácticos y aplicaciones reales"
    }
    
    prompt = (
        f"Crea un guion de podcast educativo de EXACTAMENTE {duracion} MINUTOS (~{max_palabras} palabras).\n"
        f"Nivel: {nivel}\n"
        f"Enfoque: {enfoques_texto.get(enfoque, enfoques_texto['explicacion_completa'])}\n\n"
        f"Formato EXACTO:\n"
        f"[PROFESOR]: texto\n"
        f"[ASISTENTE]: texto\n\n"
        f"Reglas:\n"
        f"- Natural, conversacional, dinamico\n"
        f"- Dialogo balanceado entre profesor y asistente\n"
        f"- Cada intervención: 2-4 oraciones\n"
        f"- CRÍTICO: Respetar límite de {max_palabras} palabras (~{duracion} min)\n\n"
        f"CONTENIDO:\n{context[:10000]}"
    )
    
    t = await _llm(SYS, prompt, max_tokens=int(max_palabras * 2))
    return {"type": "audio_script", "content": t, "params": params}


# ── TTS con gTTS ───────────────────────────────────────────────────────────────

async def tts(text: str, voice: str = "es") -> bytes:
    """Genera audio con gTTS"""
    from gtts import gTTS
    import io
    import logging
    
    log = logging.getLogger("perci.tts")
    
    try:
        log.info(f"Generando audio: {len(text)} caracteres")
        tts_obj = gTTS(text=text, lang=voice, slow=False)
        audio_buffer = io.BytesIO()
        tts_obj.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.read()
    except Exception as e:
        log.error(f"Error gTTS: {e}")
        raise RuntimeError(f"Error al generar audio: {str(e)}")


async def podcast_audio(script: str) -> bytes:
    """Genera podcast desde script"""
    clean_lines = []
    for line in script.split("\n"):
        line = line.strip()
        if line.startswith("[PROFESOR]:"):
            clean_lines.append(line[11:].strip())
        elif line.startswith("[ASISTENTE]:"):
            clean_lines.append(line[12:].strip())
        elif line and not line.startswith("["):
            clean_lines.append(line)
    
    full_text = ". ".join(clean_lines)
    return await tts(full_text, "es")


# ── Dispatcher ─────────────────────────────────────────────────────────────────

GENERATORS = {
    "summary":      generate_summary,
    "flashcards":   generate_flashcards,
    "quiz":         generate_quiz,
    "slides":       generate_slides,
    "infographic":  generate_infographic,
    "course":       generate_course,
    "audio":        generate_audio_script,
    "audio_script": generate_audio_script,
}


async def generate(output_type: str, context: str, params: dict = None, **kwargs) -> dict:
    """
    Generador dinámico que acepta parámetros.
    
    params puede incluir:
    - cantidad: int
    - duracion_minutos: int
    - nivel_detalle: basico|intermedio|avanzado
    - estilo: casual|formal|didactico
    - enfoque: conceptos_clave|explicacion_completa|practica
    """
    fn = GENERATORS.get(output_type)
    if not fn:
        raise ValueError(f"Tipo no soportado: {output_type}")
    
    # Merge params con kwargs
    all_params = {**(params or {}), **kwargs}
    
    return await fn(context, params=all_params, **kwargs)
