"""Router /generate — con parámetros dinámicos desde el chat"""
from __future__ import annotations
import io, json, logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from services.rag_service import rag_service
from services.generators import generate, podcast_audio, tts

router = APIRouter()
log = logging.getLogger("perci.generate")


class GenerateRequest(BaseModel):
    session_id: str
    output_type: str
    query: str | None = None
    title: str | None = None
    num_items: int | None = None
    # NUEVOS PARÁMETROS DINÁMICOS
    params: dict | None = None  # Para recibir parámetros del chat


class TTSRequest(BaseModel):
    text: str
    voice: str = "onyx"


class ExportRequest(BaseModel):
    content: dict
    output_type: str
    format: str  # "pdf" o "docx"


# ── Generar contenido CON PARÁMETROS DINÁMICOS ────────────────────────────────

@router.post("/content")
async def gen_content(req: GenerateRequest):
    query  = req.query or "resume y explica el contenido completo"
    chunks = await rag_service.retrieve(req.session_id, query)
    if not chunks:
        raise HTTPException(404, "Sin documentos en esta sesion")
    context = "\n\n---\n\n".join(c["text"] for c in chunks)
    
    # Construir parámetros (combina params del chat + valores legacy)
    params = req.params or {}
    
    # Agregar valores legacy si no vienen en params
    if req.title and "title" not in params:
        params["title"] = req.title
    if req.num_items:
        if "cantidad" not in params:
            params["cantidad"] = req.num_items
    
    # Log para debugging
    log.info(f"Generando {req.output_type} con params: {params}")
    
    try:
        result = await generate(req.output_type, context, params=params)
        return JSONResponse(result)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        log.error(f"Error generando contenido: {e}")
        raise HTTPException(500, str(e))


# ── Exportar PDF (sin cambios) ────────────────────────────────────────────────

def _build_pdf(content: dict, output_type: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    # Estilos personalizados
    title_style = ParagraphStyle('Title2', parent=styles['Title'],
                                 fontSize=18, textColor=colors.HexColor('#1e40af'), spaceAfter=12)
    h2_style    = ParagraphStyle('H2', parent=styles['Heading2'],
                                 fontSize=13, textColor=colors.HexColor('#1e40af'), spaceAfter=8)
    body_style  = ParagraphStyle('Body2', parent=styles['Normal'],
                                 fontSize=10, leading=14, spaceAfter=6)
    label_style = ParagraphStyle('Label', parent=styles['Normal'],
                                 fontSize=9, textColor=colors.HexColor('#6b7280'))

    story = []

    # ... (mantén todo el código de _build_pdf igual)
    # Por brevedad no lo repito, pero NO lo cambies

    if output_type == "summary":
        story.append(Paragraph("Resumen Ejecutivo", title_style))
        story.append(Spacer(1, 0.3*cm))
        text = content if isinstance(content, str) else str(content)
        for line in text.split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip(), body_style))
    # ... resto del código igual

    doc.build(story)
    return buf.getvalue()


# ── Exportar DOCX (sin cambios) ───────────────────────────────────────────────

def _build_docx(content: dict, output_type: str) -> bytes:
    # ... (mantén todo igual, no lo cambies)
    pass  # Tu código actual aquí


# ── Endpoints de exportación (sin cambios) ────────────────────────────────────

@router.post("/export")
async def export_content(req: ExportRequest):
    """Exporta contenido generado a PDF o DOCX."""
    content = req.content.get("content", req.content)
    fmt     = req.format.lower()

    try:
        if fmt == "pdf":
            data     = _build_pdf(content, req.output_type)
            filename = f"{req.output_type}.pdf"
            media    = "application/pdf"
        elif fmt == "docx":
            data     = _build_docx(content, req.output_type)
            filename = f"{req.output_type}.docx"
            media    = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            raise HTTPException(400, "Formato no soportado. Usa 'pdf' o 'docx'")

        return StreamingResponse(
            iter([data]),
            media_type=media,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error al exportar: {e}")


# ── Audio CON PARÁMETROS DINÁMICOS ────────────────────────────────────────────

@router.post("/audio/tts")
async def gen_tts(req: TTSRequest):
    try:
        audio = await tts(req.text, req.voice)
        return StreamingResponse(iter([audio]), media_type="audio/mpeg",
                                 headers={"Content-Disposition": 'attachment; filename="audio.mp3"'})
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/audio/podcast")
async def gen_podcast(req: GenerateRequest):
    """Genera podcast con parámetros dinámicos de duración"""
    from services.generators import generate as gen
    
    chunks  = await rag_service.retrieve(req.session_id, req.query or "explica el contenido")
    if not chunks:
        raise HTTPException(404, "Sin documentos")
    
    context = "\n\n".join(c["text"] for c in chunks)
    
    # Usar parámetros dinámicos
    params = req.params or {}
    log.info(f"Generando audio con params: {params}")
    
    # Generar script con parámetros
    script_result = await gen("audio_script", context, params=params)
    script = script_result["content"]
    
    # Generar audio
    audio = await podcast_audio(script)
    
    return StreamingResponse(
        iter([audio]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": 'attachment; filename="podcast.mp3"'}
    )
