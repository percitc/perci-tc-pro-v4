import { useState } from 'react'
import { Sparkles, Loader, Download, Play, BookOpen, HelpCircle, Layout, Image, GraduationCap, Mic } from 'lucide-react'
import toast from 'react-hot-toast'
import ReactMarkdown from 'react-markdown'
import { genContent, genPodcast } from '../utils/api'
import './GeneratorPanel.css'
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
  const [active,setActive]=useState(null)
  const [loading,setLoading]=useState(false)
  const [result,setResult]=useState(null)
  const [audioUrl,setAudioUrl]=useState(null)
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
  const dl=(data,name,ext='json')=>{
    const blob=new Blob([typeof data==='string'?data:JSON.stringify(data,null,2)],{type:ext==='json'?'application/json':'text/plain'})
    const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`${name}.${ext}`;a.click()
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
          <div className="rp-header"><span>Podcast Educativo</span>
            <a href={audioUrl} download="podcast.mp3" className="btn btn-ghost" style={{fontSize:11,padding:'5px 12px'}}><Download size={12}/> MP3</a>
          </div>
          <audio controls src={audioUrl} style={{width:'100%',marginTop:10}}/>
        </div>
      )}
      {result&&<div className="result-panel fade-up"><ResultView r={result} dl={dl}/></div>}
    </div>
  )
}
function ResultView({r,dl}){
  const {type,data}=r; const c=data.content
  const Actions=()=>(
    <div className="rp-actions">
      {typeof c==='string'
        ?<button className="btn btn-ghost" style={{fontSize:11,padding:'5px 11px'}} onClick={()=>dl(c,type,'txt')}><Download size={12}/> TXT</button>
        :<button className="btn btn-ghost" style={{fontSize:11,padding:'5px 11px'}} onClick={()=>dl(c,type,'json')}><Download size={12}/> JSON</button>}
    </div>
  )
  if(type==='summary')return(<div><div className="rp-header"><span>Resumen Ejecutivo</span><Actions/></div><div className="prose rp-text">{c}</div></div>)
  if(type==='audio_script')return(<div><div className="rp-header"><span>Guion de Podcast</span><Actions/></div><pre className="script-view">{c}</pre></div>)
  if(type==='flashcards')return(<div><div className="rp-header"><span>Tarjetas ({c.tarjetas?.length})</span><Actions/></div>
    <div className="cards-grid">{c.tarjetas?.map((t,i)=>(
      <div key={i} className={`card diff-${t.dificultad}`}><p className="card-q">{t.pregunta}</p><p className="card-a">{t.respuesta}</p>
        <div className="card-meta"><span className="badge">{t.categoria}</span><span className="badge">{t.dificultad}</span></div>
      </div>))}</div></div>)
  if(type==='quiz')return(<div><div className="rp-header"><span>Cuestionario ({c.cuestionario?.length})</span><Actions/></div>
    <div className="quiz-list">{c.cuestionario?.map((q,i)=>(
      <div key={i} className="quiz-item"><p className="quiz-q"><b>{i+1}.</b> {q.pregunta}</p>
        <ul className="quiz-opts">{q.opciones?.map((o,j)=><li key={j} className={o.startsWith(q.respuesta_correcta)?'correct':''}>{o}</li>)}</ul>
        <p className="quiz-exp">💡 {q.explicacion}</p>
      </div>))}</div></div>)
  if(type==='slides')return(<div><div className="rp-header"><span>{c.titulo_presentacion}</span><Actions/></div>
    <div className="slides-grid">{c.slides?.map((s,i)=>(
      <div key={i} className={`slide type-${s.tipo}`}><div className="slide-num">{s.emoji} #{s.numero}</div>
        <h4 className="slide-title">{s.titulo}</h4>{s.subtitulo&&<p className="slide-sub">{s.subtitulo}</p>}
        <ul className="slide-pts">{s.puntos?.map((p,j)=><li key={j}>{p}</li>)}</ul>
      </div>))}</div></div>)
  if(type==='infographic')return(<div><div className="rp-header"><span>Infografia: {c.titulo}</span><Actions/></div>
    <div className="info-view">
      <div className="info-hdr" style={{background:c.color_principal||'var(--accent-1)'}}><h3>{c.titulo}</h3><p>{c.subtitulo}</p></div>
      {c.datos_clave&&<div className="info-stats">{c.datos_clave.map((d,i)=><div key={i} className="info-stat"><span className="stat-n">{d.numero}</span><span className="stat-d">{d.descripcion}</span></div>)}</div>}
      <div className="info-secs">{c.secciones?.map((s,i)=><div key={i} className="info-sec"><div className="info-sh"><span>{s.icono}</span><h4>{s.titulo}</h4></div><p>{s.descripcion}</p>{s.datos&&<ul>{s.datos.map((d,j)=><li key={j}>{d}</li>)}</ul>}</div>)}</div>
      {c.conclusion&&<div className="info-con">💡 {c.conclusion}</div>}
    </div></div>)
  if(type==='course')return(<div><div className="rp-header"><span>{c.titulo_curso}</span><Actions/></div>
    <div className="course-view">
      <div className="course-meta"><span>⏱ {c.duracion_estimada}</span><span>📊 {c.nivel}</span></div>
      <p className="course-desc">{c.descripcion}</p>
      <div className="modules">{c.modulos?.map((m,i)=>(
        <div key={i} className="module"><div className="mod-h"><span className="mod-num">{m.numero}</span><div><h4>{m.titulo}</h4><p>{m.descripcion}</p></div></div>
          <ul className="mod-temas">{m.temas?.map((t,j)=><li key={j}><b>{t.titulo}</b>: {t.contenido}</li>)}</ul>
        </div>))}</div>
    </div></div>)
  return(<div><div className="rp-header"><span>Resultado</span><Actions/></div><pre className="raw">{JSON.stringify(c,null,2)}</pre></div>)
}