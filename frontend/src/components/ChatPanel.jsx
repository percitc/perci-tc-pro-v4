import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { Send, Loader, Bot, User, AlertTriangle, Download, FileText, File } from 'lucide-react'
import { sendChat } from '../utils/api'
import axios from 'axios'
import toast from 'react-hot-toast'
import './ChatPanel.css'

const API_URL = 'https://perci-tc-pro-backend.onrender.com'

const SUGS = [
  'Cuales son los puntos principales?',
  'Explica el concepto mas importante',
  'Resume en 5 puntos clave',
  'Dame un resumen corto',
  'Crea 20 flashcards',
  'Genera un audio de 5 minutos',
]

const TASKS = [
  {v:'auto',l:'Auto'},
  {v:'chat_rapido',l:'Rapido'},
  {v:'doc_largo',l:'Doc largo'},
  {v:'razonamiento',l:'Razonamiento'},
  {v:'alta_calidad',l:'Alta calidad'}
]

export default function ChatPanel({sessionId}) {
  const [msgs, setMsgs] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [task, setTask] = useState('auto')
  const bottomRef = useRef()
  const inputRef = useRef()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({behavior:'smooth'})
  }, [msgs])

  useEffect(() => {
    if (!sessionId && msgs.length === 0) {
      setMsgs([{
        role: 'assistant',
        content: `# 🎉 ¡Hola! Soy **PERCI TC PRO AI**

Tu asistente educativo con **Inteligencia Artificial Avanzada**.

## 🚀 ¿Qué puedo hacer por ti?

### 📚 **Generar Contenido Educativo:**
- 📝 **Resúmenes** ejecutivos personalizados
- 🃏 **Flashcards** para memorización efectiva
- ❓ **Cuestionarios** con respuestas y explicaciones
- 📊 **Presentaciones** profesionales listas para usar
- 🎨 **Infografías** visuales y atractivas
- 🎓 **Cursos** completos modulares
- 🎙️ **Audios/Podcasts** educativos en español

### 💬 **Chat Inteligente:**
- Respondo preguntas sobre tus documentos
- Explico conceptos complejos de forma simple
- Te ayudo a estudiar y preparar exámenes

---

## ✨ **Ejemplos de lo que puedes pedirme:**

### 📋 Generación Básica:
- *"Dame un resumen corto"*
- *"Crea 30 flashcards avanzadas"*
- *"Genera un cuestionario de 15 preguntas"*

### 🎯 Generación Personalizada:
- *"Audio de 10 minutos bien detallado"*
- *"Resumen básico en 3 párrafos"*
- *"50 flashcards difíciles para examen"*
- *"Presentación de 20 slides"*

### 💡 Chat y Consultas:
- *"¿Cuáles son los puntos principales?"*
- *"Explícame el concepto de fotosíntesis"*
- *"Dame 5 conclusiones clave"*

---

## 🎬 **Para empezar:**

1. 📤 Sube un documento en **"Archivos"** (PDF, Word, PowerPoint, etc.)
2. 💬 Escríbeme lo que necesitas en el chat
3. ⚡ Recibe tu contenido en segundos

---

💡 **Tip:** Mientras más específico seas, mejores resultados obtendré.

**¡Sube tu primer documento y comencemos! 🚀**`
      }])
    }
  }, [])

  const send = async (text) => {
    const q = (text || input).trim()
    if (!q || loading || !sessionId) return

    const hist = msgs.map(m => ({role: m.role, content: m.content}))
    setMsgs(p => [...p, {role:'user', content:q}, {role:'assistant', content:null, loading:true}])
    setInput('')
    setLoading(true)

    try {
      const r = await sendChat(sessionId, q, hist, task)

      // Detectar si es generación
      if (r.type === 'generation') {
        setMsgs(p => [...p.slice(0, -1), {
          role: 'assistant',
          content: r.response,
          generation: r.generation,
          params: r.params_detected,
          provider: r.provider,
          model: r.model
        }])
      } else if (r.type === 'error') {
        setMsgs(p => [...p.slice(0, -1), {
          role: 'assistant',
          content: r.response,
          error: true
        }])
      } else {
        // Chat normal
        setMsgs(p => [...p.slice(0, -1), {
          role: 'assistant',
          content: r.answer,
          provider: r.provider,
          model: r.model
        }])
      }
    } catch(e) {
      setMsgs(p => [...p.slice(0, -1), {
        role: 'assistant',
        content: 'Error al conectar con el servidor.',
        error: true
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const exportGeneration = async (msg, format) => {
    if (!msg.generation) return

    toast.loading(`Exportando como ${format.toUpperCase()}...`)

    try {
      const resp = await axios.post(
        `${API_URL}/generate/export`,
        {
          content: msg.generation.content,
          output_type: msg.generation.type,
          format
        },
        { responseType: 'blob' }
      )

      const ext = format === 'pdf' ? 'pdf' : 'docx'
      const mime = format === 'pdf'
        ? 'application/pdf'
        : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      
      const url = URL.createObjectURL(new Blob([resp.data], {type: mime}))
      const a = document.createElement('a')
      a.href = url
      a.download = `${msg.generation.type}.${ext}`
      a.click()

      toast.success(`Descargado como ${ext.toUpperCase()}`)
    } catch(e) {
      toast.error('Error al exportar')
    }
  }

  const downloadJSON = (msg) => {
    if (!msg.generation) return
    const blob = new Blob([JSON.stringify(msg.generation.content, null, 2)], {type: 'application/json'})
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `${msg.generation.type}.json`
    a.click()
    toast.success('JSON descargado')
  }

  return (
    <div className="chat-wrapper">
      <div className="chat-messages">
        {!sessionId && msgs.length === 0 && (
          <div className="chat-empty">
            <Bot size={44}/>
            <p>Sube un documento para comenzar</p>
          </div>
        )}

        {msgs.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <div className="msg-avatar">
              {m.role === 'user' ? <User size={13}/> : <Bot size={13}/>}
            </div>

            <div className={`msg-bubble ${m.error ? 'error' : ''}`}>
              {m.loading ? (
                <div className="thinking"><span/><span/><span/></div>
              ) : (
                <>
                  <div className="prose">
                    <ReactMarkdown>{m.content}</ReactMarkdown>
                  </div>

                  {/* Mostrar parámetros detectados */}
                  {m.params && (
                    <div className="detected-params">
                      <strong>📊 Parámetros detectados:</strong>
                      <ul>
                        {Object.entries(m.params).map(([key, val]) => (
                          <li key={key}><code>{key}</code>: {String(val)}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Mostrar resultado generado */}
                  {m.generation && (
                    <div className="generation-result">
                      <GenerationPreview generation={m.generation} />
                      
                      {/* Botones de exportación */}
                      <div className="export-actions">
                        <button 
                          className="btn-export pdf"
                          onClick={() => exportGeneration(m, 'pdf')}
                        >
                          <FileText size={13}/> PDF
                        </button>
                        <button 
                          className="btn-export docx"
                          onClick={() => exportGeneration(m, 'docx')}
                        >
                          <File size={13}/> Word
                        </button>
                        <button 
                          className="btn-export json"
                          onClick={() => downloadJSON(m)}
                        >
                          <Download size={13}/> JSON
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}

              {m.provider && <div className="msg-meta">{m.provider} · {m.model}</div>}
            </div>
          </div>
        ))}

        <div ref={bottomRef}/>
      </div>

      {sessionId && msgs.length < 3 && (
        <div className="suggestions">
          {SUGS.map(s => (
            <button key={s} className="sug-chip" onClick={() => send(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="chat-input-area">
        {!sessionId && (
          <div className="no-session">
            <AlertTriangle size={13}/>
            <span>Sube un documento primero</span>
          </div>
        )}

        <div className="task-selector">
          {TASKS.map(t => (
            <button 
              key={t.v} 
              className={`task-btn ${task === t.v ? 'active' : ''}`}
              onClick={() => setTask(t.v)}
            >
              {t.l}
            </button>
          ))}
        </div>

        <div className={`chat-input-wrap ${!sessionId ? 'disabled' : ''}`}>
          <textarea 
            ref={inputRef} 
            className="chat-ta" 
            rows={1}
            placeholder={sessionId ? 'Pregunta o genera contenido...' : 'Sube un documento primero...'}
            value={input} 
            onChange={e => setInput(e.target.value)} 
            disabled={!sessionId || loading}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                send()
              }
            }}
          />
          <button 
            className="send-btn" 
            onClick={() => send()} 
            disabled={!sessionId || loading || !input.trim()}
          >
            {loading ? <Loader size={15} className="spin"/> : <Send size={15}/>}
          </button>
        </div>

        <p className="chat-hint">
          💡 Tip: Pide "crea 30 flashcards" o "audio de 10 min" · Enter enviar · Shift+Enter nueva línea
        </p>
      </div>
    </div>
  )
}

// Componente para preview del contenido generado
function GenerationPreview({generation}) {
  const {type, content} = generation

  // Resumen
  if (type === 'summary') {
    return (
      <div className="preview-summary">
        <h4>📋 Resumen</h4>
        <div className="prose-sm">{content}</div>
      </div>
    )
  }

  // Flashcards
  if (type === 'flashcards') {
    const tarjetas = content?.tarjetas || []
    return (
      <div className="preview-flashcards">
        <h4>🃏 {tarjetas.length} Flashcards</h4>
        <div className="mini-cards">
          {tarjetas.slice(0, 3).map((t, i) => (
            <div key={i} className="mini-card">
              <p><strong>P:</strong> {t.pregunta}</p>
              <p><strong>R:</strong> {t.respuesta.substring(0, 60)}...</p>
            </div>
          ))}
          {tarjetas.length > 3 && (
            <p className="more">+ {tarjetas.length - 3} más</p>
          )}
        </div>
      </div>
    )
  }

  // Quiz
  if (type === 'quiz') {
    const preguntas = content?.cuestionario || []
    return (
      <div className="preview-quiz">
        <h4>❓ {preguntas.length} Preguntas</h4>
        <ol className="mini-quiz">
          {preguntas.slice(0, 3).map((q, i) => (
            <li key={i}>{q.pregunta}</li>
          ))}
          {preguntas.length > 3 && <li>+ {preguntas.length - 3} más...</li>}
        </ol>
      </div>
    )
  }

  // Audio Script
  if (type === 'audio_script' || type === 'audio') {
    const wordCount = content.split(' ').length
    const estimatedMin = Math.round(wordCount / 150)
    return (
      <div className="preview-audio">
        <h4>🎙️ Guión de Podcast</h4>
        <p>📊 {wordCount} palabras (~{estimatedMin} min)</p>
        <pre className="script-preview">{content.substring(0, 300)}...</pre>
      </div>
    )
  }

  // Slides
  if (type === 'slides') {
    const slides = content?.slides || []
    return (
      <div className="preview-slides">
        <h4>📊 {slides.length} Diapositivas</h4>
        <p>{content.titulo_presentacion}</p>
      </div>
    )
  }

  // Default
  return (
    <div className="preview-default">
      <h4>✅ {type.toUpperCase()} generado</h4>
      <p>Descarga para ver el contenido completo</p>
    </div>
  )
}
