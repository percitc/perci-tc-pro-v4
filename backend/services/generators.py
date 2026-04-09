"""PERCI TC PRO AI — Generadores Educativos con gTTS"""
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
    """
    Genera guion de podcast optimizado para ~10 minutos de audio.
    La IA resume y explica el contenido de forma concisa.
    """
    # Calcular límite: ~150 palabras = 1 minuto → 10 min = ~1500 palabras
    prompt = (
        f"Crea un guion de podcast educativo de MAXIMO 10 MINUTOS (~1500 palabras).\n"
        f"IMPORTANTE: Resume y explica SOLO lo mas importante del contenido.\n"
        f"Formato EXACTO:\n"
        f"[PROFESOR]: Bienvenidos a PERCI TC PRO. Hoy hablaremos sobre...\n"
        f"[ASISTENTE]: Excelente tema. ¿Podrias explicar...?\n"
        f"[PROFESOR]: Claro, lo principal es...\n\n"
        f"Reglas:\n"
        f"- Natural, conversacional, dinamico\n"
        f"- Minimo 10 intercambios, maximo 20\n"
        f"- Enfocate en conceptos clave, no en todos los detalles\n"
        f"- Cada dialogo: 2-4 oraciones MAX\n"
        f"- IMPORTANTE: NO exceder 1500 palabras totales\n\n"
        f"CONTENIDO A RESUMIR:\n{context[:8000]}"
    )
    
    t = await _llm(SYS, prompt, max_tokens=3000)
    return {"type": "audio_script", "content": t}


# ── TTS con gTTS (Google Text-to-Speech - GRATIS) ─────────────────────────────

async def tts(text: str, voice: str = "es") -> bytes:
    """
    Genera audio con gTTS (Google TTS - 100% GRATIS).
    Funciona bien en español, sin límites de uso.
    """
    from gtts import gTTS
    import io
    import logging
    
    log = logging.getLogger("perci.tts")
    
    try:
        log.info(f"Generando audio con gTTS (idioma: {voice}, {len(text)} caracteres)")
        
        # Generar audio
        tts_obj = gTTS(text=text, lang=voice, slow=False)
        
        # Guardar en memoria
        audio_buffer = io.BytesIO()
        tts_obj.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        audio_bytes = audio_buffer.read()
        log.info(f"✓ Audio generado: {len(audio_bytes)} bytes")
        
        return audio_bytes
        
    except Exception as e:
        log.error(f"Error generando audio con gTTS: {e}")
        raise RuntimeError(f"⚠️ Error al generar audio: {str(e)}")


async def podcast_audio(script: str) -> bytes:
    """
    Genera audio de podcast con gTTS.
    Combina todas las líneas en un solo audio continuo.
    """
    import logging
    log = logging.getLogger("perci.podcast")
    
    # Limpiar script y combinar todo el texto
    clean_lines = []
    for line in script.split("\n"):
        line = line.strip()
        if line.startswith("[PROFESOR]:"):
            clean_lines.append(line[11:].strip())
        elif line.startswith("[ASISTENTE]:"):
            clean_lines.append(line[12:].strip())
        elif line.startswith("[ESTUDIANTE]:"):
            clean_lines.append(line[13:].strip())
        elif line and not line.startswith("["):
            clean_lines.append(line)
    
    # Unir todo el texto con pausas
    full_text = ". ".join(clean_lines)
    
    log.info(f"Generando podcast: {len(full_text)} caracteres, ~{len(full_text.split())} palabras")
    
    # Generar audio completo
    return await tts(full_text, "es")


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
