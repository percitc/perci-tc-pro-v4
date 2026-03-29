"""PERCI TC PRO AI — Generadores Educativos (Multi-Provider)"""
from __future__ import annotations
import os, json
from services.ai import ai_router, TaskType
from dotenv import load_dotenv

load_dotenv()

TTS_VOICE_PROFESOR   = os.getenv("TTS_VOICE_PROFESOR",   "onyx")
TTS_VOICE_ASISTENTE  = os.getenv("TTS_VOICE_ASISTENTE",  "nova")
TTS_VOICE_ESTUDIANTE = os.getenv("TTS_VOICE_ESTUDIANTE", "shimmer")

SYS = ("Eres PERCI, experto en educacion y diseno instruccional. "
       "Respondes SIEMPRE en espanol claro, didactico y profesional. "
       "Generas contenido estructurado, profundo y de alta calidad educativa.")


async def _llm(system: str, user: str, json_mode=False, max_tokens=4000) -> str:
    o = {"max_tokens": max_tokens, "temperature": 0.5}
    if json_mode: o["response_format"] = {"type": "json_object"}
    r = await ai_router.generate_response(prompt=user, system=system, task=TaskType.GENERACION, options=o)
    return r.content


async def generate_summary(context: str, title: str = "") -> dict:
    t = await _llm(SYS, f"Resumen ejecutivo completo{f' de: {title}' if title else ''}.\n"
                        f"Estructura: introduccion, ideas principales, conceptos clave, conclusiones, aplicaciones.\n\nCONTENIDO:\n{context}")
    return {"type": "summary", "content": t}


async def generate_flashcards(context: str, num: int = 20) -> dict:
    r = await _llm(SYS, f'Crea {num} flashcards. JSON exacto:\n'
                        f'{{"tarjetas":[{{"id":1,"pregunta":"...","respuesta":"...","categoria":"...","dificultad":"basico|intermedio|avanzado"}}]}}\n\nCONTENIDO:\n{context[:8000]}',
                   json_mode=True)
    return {"type": "flashcards", "content": json.loads(r)}


async def generate_quiz(context: str, num: int = 15) -> dict:
    r = await _llm(SYS, f'Crea {num} preguntas opcion multiple. JSON exacto:\n'
                        f'{{"cuestionario":[{{"id":1,"pregunta":"...","opciones":["A)...","B)...","C)...","D)..."],"respuesta_correcta":"A","explicacion":"...","dificultad":"basico|intermedio|avanzado"}}]}}\n\nCONTENIDO:\n{context[:8000]}',
                   json_mode=True)
    return {"type": "quiz", "content": json.loads(r)}


async def generate_slides(context: str, num_slides: int = 12) -> dict:
    r = await _llm(SYS, f'Crea {num_slides} diapositivas. JSON exacto:\n'
                        f'{{"titulo_presentacion":"...","slides":[{{"numero":1,"tipo":"portada|contenido|seccion|conclusion","titulo":"...","subtitulo":"...","puntos":["..."],"nota_orador":"...","emoji":"🎯"}}]}}\n\nCONTENIDO:\n{context[:8000]}',
                   json_mode=True)
    return {"type": "slides", "content": json.loads(r)}


async def generate_infographic(context: str) -> dict:
    r = await _llm(SYS, f'Infografia educativa. JSON exacto:\n'
                        f'{{"titulo":"...","subtitulo":"...","color_principal":"#hex","secciones":[{{"icono":"emoji","titulo":"...","descripcion":"...","datos":["..."]}}],"datos_clave":[{{"numero":"42%","descripcion":"..."}}],"conclusion":"..."}}\n\nCONTENIDO:\n{context[:6000]}',
                   json_mode=True)
    return {"type": "infographic", "content": json.loads(r)}


async def generate_course(context: str, title: str = "") -> dict:
    r = await _llm(SYS, f'Curso educativo completo. JSON exacto:\n'
                        f'{{"titulo_curso":"...","descripcion":"...","duracion_estimada":"X horas","nivel":"principiante|intermedio|avanzado","objetivos":["..."],"modulos":[{{"numero":1,"titulo":"...","descripcion":"...","temas":[{{"titulo":"...","contenido":"...","actividad":"..."}}],"evaluacion":"..."}}],"evaluacion_final":"..."}}\n\nCONTENIDO:\n{context[:10000]}',
                   json_mode=True, max_tokens=6000)
    return {"type": "course", "content": json.loads(r)}


async def generate_audio_script(context: str) -> dict:
    t = await _llm(SYS, f"Guion podcast educativo 5-8 min con 2 voces:\n"
                        f"[PROFESOR]: (explica)\n[ASISTENTE]: (pregunta/resume)\n\nNatural, dinamico, en espanol.\n\nCONTENIDO:\n{context[:8000]}",
                   max_tokens=3000)
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
    "summary": generate_summary, "flashcards": generate_flashcards,
    "quiz": generate_quiz, "slides": generate_slides,
    "infographic": generate_infographic, "course": generate_course,
    "audio_script": generate_audio_script,
}

async def generate(output_type: str, context: str, **kwargs) -> dict:
    fn = GENERATORS.get(output_type)
    if not fn: raise ValueError(f"Tipo no soportado: {output_type}")
    return await fn(context, **kwargs)
