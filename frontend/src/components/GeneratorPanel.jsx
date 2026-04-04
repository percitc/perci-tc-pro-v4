import { useState } from 'react'
import { Sparkles, Loader, Download, Play, BookOpen, HelpCircle, Layout, Image, GraduationCap, Mic, FileText, File } from 'lucide-react'
import toast from 'react-hot-toast'
import ReactMarkdown from 'react-markdown'
import { genContent, genPodcast } from '../utils/api'
import axios from 'axios'
import './GeneratorPanel.css'

const API_URL = 'https://perci-tc-pro-backend.onrender.com'

const GENS=[
  {id:'summary',     icon:BookOpen,      label:'Resumen',      desc:'Resumen ejecutivo',         color:'#00e5ff'},
  {id:'flashcards',  icon:Layout,        label:'Tarjetas',     desc:'Flashcards para memorizar', color:'#a78bfa'},
  {id:'quiz',        icon:HelpCircle,    label:'Cuestionario', desc:'Opcion multiple',           color:'#f59e0b'},
  {id:'slides',      icon:Layout,        label:'Slides',       desc:'Presentacion estructurada', color:'#10d9a0'},
  {id:'infographic', icon:Image,         label:'Infografia',   desc:'Datos visuales',            color:'#f43f5e'},
  {id:'course',      icon:GraduationCap, label:'Curso',        desc:'Modulos completos',         color:'#0057ff'},
  {id:'audio_script',icon:Mic,           label:'Guion',        desc:'Script de podcast',         color:'#ec4899'},
  {id:'podcast',     icon:Play,          label:'Podcast MP3',  desc:'Audio con IA',              color:'#14b8a6'},
]

export default function GeneratorPanel({sessionId}){
  const [active,setActive]   = useState(null)
  const [loading,setLoading] = useState(false)
  const [result,setResult]   = useState(null)
  const [audioUrl,setAudioUrl] = useState(null)
  const [exporting,setExporting] = useState(null)

  const run=async(gen)=>{
    if(!sessionId)return toast.error('Sube un documento primero')
    setActive(gen.id);setLoading(true);setResult(null);setAudioUrl(null)
    try{
      if(gen.id==='podcast'){
        const url=await genPodcast(sessionId);setAudioUrl(url);toast.success('Podcast generado')
      }else{
        const d=await genContent(sessionId,gen.id);setResult({type:gen.id,data:d});toast.success(`${gen.label} generado`)
      }
    }catch(e){toast.error(e.response?.data?.detail||'Error al generar')}
    finally{setLoading(false)}
  }

  const exportFile=async(format)=>{
    if(!result)return
    setExporting(format)
    try{
      const resp = await axios.post(
        `${API_URL}/generate/export`,
        { content: result.data, output_type: result.type, format },
        { responseType: 'blob' }
      )
      const ext  = format === 'pdf' ? 'pdf' : 'docx'
      const mime = format === 'pdf'
        ? 'application/pdf'
        : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      const url  = URL.createObjectURL(new Blob([resp.data],{type:mime}))
      const a    = document.createElement('a')
      a.href     = url
      a.download = `${result.type}.${ext}`
      a.click()
      toast.success(`Descargado como ${ext.toUpperCase()}`)
    }catch(e){
      toast.error('Error al exportar')
    }finally{
      setExporting(null)
    }
  }

  const dlJSON=(data,name)=>{
    const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'})
    const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`${name}.json`;a.click()
  }

  return(
    <div className="gen-wrapper">
      <div className="gen-hero"><h2>Generar Contenido Educativo</h2><p>Transforma documentos en materiales de aprendizaje</p></div>
      <div className="gen-grid">
        {GENS.map(g=>(
          <button key={g.id} className={`gen-card ${active===g.id?'active':''}`} style={{'--cc':g.color}} onClick={()=>run(g)} disabled={loading}>
            <div className="gc-icon">{loading&&active===g.id?<Loader size={19} className="spin"/>:<g.icon size={19}/>}</div>
            <div className="gc-text"><span className="gc-label">{g.label}</span><span className="gc-desc">{g.desc}</span></div>
          </button>
        ))}
      </div>

      {audioUrl&&(
        <div className="result-panel">
          <div className="rp-header"><span>🎙️ Podcast Educativo</span>
            <a href={audioUrl} download="podcast.mp3" className="btn btn-ghost" style={{fontSize:11,padding:'5px 12px'}}><Download size={12}/> MP3</a>
          </div>
          <audio controls src={audioUrl} style={{width:'100%',marginTop:10}}/>
        </div>
      )}

      {result&&(
        <div className="result-panel fade-up">
          {/* Botones de exportacion */}
          <div className="export-bar">
            <span className="export-label">Descargar como:</span>
            <button className="btn btn-export pdf" onClick={()=>exportFile('pdf')} disabled={!!exporting}>
              {exporting==='pdf'?<Loader size={13} className="spin"/>:<FileText size={13}/>}
              PDF
            </button>
            <button className="btn btn-export docx" onClick={()=>exportFile('docx')} disabled={!!exporting}>
              {exporting==='docx'?<Loader size={13} className="spin"/>:<File size={13}/>}
              Word
            </button>
            <button className="btn btn-export json" onClick={()=>dlJSON(result.data.content, result.type)}>
              <Download size={13}/> JSON
            </button>
          </div>
          <ResultView r={result}/>
        </div>
      )}
    </div>
  )
}

function ResultView({r}){
  const {type,data}=r; const c=data.content

  if(type==='summary')return(
    <div><div className="rp-header"><span>📋 Resumen Ejecutivo</span></div>
      <div className="prose rp-text">{c}</div></div>
  )

  if(type==='audio_script')return(
    <div><div className="rp-header"><span>🎙️ Guion de Podcast</span></div>
      <pre className="script-view">{c}</pre></div>
  )

  if(type==='flashcards'){
    const tarjetas = c?.tarjetas || (Array.isArray(c)?c:[])
    return(<div><div className="rp-header"><span>🃏 Tarjetas ({tarjetas.length})</span></div>
      <div className="cards-grid">{tarjetas.map((t,i)=>(
        <div key={i} className={`card diff-${t.dificultad}`}>
          <p className="card-q">{t.pregunta}</p><p className="card-a">{t.respuesta}</p>
          <div className="card-meta"><span className="badge">{t.categoria}</span><span className="badge">{t.dificultad}</span></div>
        </div>))}</div></div>)
  }

  if(type==='quiz'){
    const preguntas = c?.cuestionario || (Array.isArray(c)?c:[])
    return(<div><div className="rp-header"><span>❓ Cuestionario ({preguntas.length} preguntas)</span></div>
      <div className="quiz-list">{preguntas.map((q,i)=>(
        <div key={i} className="quiz-item">
          <p className="quiz-q"><b>{i+1}.</b> {q.pregunta}</p>
          <ul className="quiz-opts">{q.opciones?.map((o,j)=><li key={j} className={o.startsWith(q.respuesta_correcta)?'correct':''}>{o}</li>)}</ul>
          <p className="quiz-exp">💡 {q.explicacion}</p>
        </div>))}</div></div>)
  }

  if(type==='slides'){
    const slides = c?.slides || []
    const titulo = c?.titulo_presentacion || 'Presentación'
    return(<div><div className="rp-header"><span>📊 {titulo}</span></div>
      <div className="slides-grid">{slides.map((s,i)=>(
        <div key={i} className={`slide type-${s.tipo}`}>
          <div className="slide-num">{s.emoji} #{s.numero}</div>
          <h4 className="slide-title">{s.titulo}</h4>
          {s.subtitulo&&<p className="slide-sub">{s.subtitulo}</p>}
          <ul className="slide-pts">{s.puntos?.map((p,j)=><li key={j}>{p}</li>)}</ul>
        </div>))}</div></div>)
  }

  if(type==='infographic'){
    const info = c || {}
    return(<div><div className="rp-header"><span>🎨 Infografia: {info.titulo}</span></div>
      <div className="info-view">
        <div className="info-hdr" style={{background:info.color_principal||'#3B82F6'}}><h3>{info.titulo}</h3><p>{info.subtitulo}</p></div>
        {info.datos_clave&&<div className="info-stats">{info.datos_clave.map((d,i)=>(
          <div key={i} className="info-stat"><span className="stat-n">{d.numero}</span><span className="stat-d">{d.descripcion}</span></div>))}</div>}
        <div className="info-secs">{info.secciones?.map((s,i)=>(
          <div key={i} className="info-sec"><div className="info-sh"><span>{s.icono}</span><h4>{s.titulo}</h4></div>
            <p>{s.descripcion}</p>{s.datos&&<ul>{s.datos.map((d,j)=><li key={j}>{d}</li>)}</ul>}</div>))}</div>
        {info.conclusion&&<div className="info-con">💡 {info.conclusion}</div>}
      </div></div>)
  }

  if(type==='course'){
    const course = c || {}
    return(<div><div className="rp-header"><span>🎓 {course.titulo_curso}</span></div>
      <div className="course-view">
        <div className="course-meta"><span>⏱ {course.duracion_estimada}</span><span>📊 {course.nivel}</span></div>
        <p className="course-desc">{course.descripcion}</p>
        <div className="modules">{course.modulos?.map((m,i)=>(
          <div key={i} className="module">
            <div className="mod-h"><span className="mod-num">{m.numero}</span><div><h4>{m.titulo}</h4><p>{m.descripcion}</p></div></div>
            <ul className="mod-temas">{m.temas?.map((t,j)=><li key={j}><b>{t.titulo}</b>: {t.contenido}</li>)}</ul>
          </div>))}</div>
      </div></div>)
  }

  return(<div><div className="rp-header"><span>Resultado</span></div>
    <pre className="raw">{JSON.stringify(c,null,2)}</pre></div>)
}
