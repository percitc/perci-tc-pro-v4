import { useState, useRef, useCallback } from 'react'
import { Upload, Link, FileText, Loader, CheckCircle, AlertCircle, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { uploadFile, uploadUrl } from '../utils/api'
import './UploadZone.css'
const ACCEPTED='.pdf,.docx,.pptx,.txt,.csv,.xlsx,.png,.jpg,.jpeg,.mp3,.wav,.mp4,.mov'
export default function UploadZone({onSessionReady,sessionId}){
  const [dragOver,setDragOver]=useState(false)
  const [files,setFiles]=useState([])
  const [urlInput,setUrlInput]=useState('')
  const [urlLoading,setUrlLoading]=useState(false)
  const inputRef=useRef()
  const processFiles=useCallback(async(fileList)=>{
    let sid=sessionId
    for(const file of fileList){
      const id=Date.now()+Math.random()
      setFiles(prev=>[...prev,{id,name:file.name,status:'uploading',progress:0}])
      try{
        const r=await uploadFile(file,sid,pct=>setFiles(prev=>prev.map(f=>f.id===id?{...f,progress:pct}:f)))
        setFiles(prev=>prev.map(f=>f.id===id?{...f,status:'done',result:r}:f))
        sid=r.session_id
        onSessionReady(sid,[{name:file.name}])
        toast.success(`${file.name} procesado (${r.embed_provider||'embeddings OK'})`)
      }catch(e){
        setFiles(prev=>prev.map(f=>f.id===id?{...f,status:'error',error:e.response?.data?.detail||'Error'}:f))
        toast.error(`Error con ${file.name}`)
      }
    }
  },[sessionId])
  const handleDrop=useCallback(async e=>{e.preventDefault();setDragOver(false);await processFiles(Array.from(e.dataTransfer.files))},[processFiles])
  const handleUrl=async()=>{
    if(!urlInput.trim())return
    setUrlLoading(true)
    try{
      const r=await uploadUrl(urlInput.trim(),sessionId)
      onSessionReady(r.session_id,[{name:urlInput.trim()}])
      toast.success('URL procesada')
      setUrlInput('')
    }catch(e){toast.error(e.response?.data?.detail||'Error al procesar URL')}
    finally{setUrlLoading(false)}
  }
  return(
    <div className="upload-wrapper">
      <div className="upload-hero"><h2>Carga tu conocimiento</h2><p>Sube cualquier archivo y transformalo en contenido educativo con IA</p></div>
      <div className={`drop-zone ${dragOver?'drag-over':''}`}
        onDragOver={e=>{e.preventDefault();setDragOver(true)}} onDragLeave={()=>setDragOver(false)}
        onDrop={handleDrop} onClick={()=>inputRef.current?.click()}>
        <input ref={inputRef} type="file" multiple accept={ACCEPTED} onChange={e=>processFiles(Array.from(e.target.files))} hidden/>
        <div className="drop-icon"><Upload size={28}/></div>
        <p className="drop-title">Arrastra archivos o haz clic para seleccionar</p>
        <p className="drop-sub">PDF · DOCX · PPTX · TXT · CSV · Excel · Imagen · Audio · Video</p>
        <p className="drop-limit">Hasta 500 MB por archivo</p>
      </div>
      <div className="url-wrap">
        <Link size={15} className="url-icon"/>
        <input type="url" placeholder="Pega una URL o enlace de YouTube..." value={urlInput}
          onChange={e=>setUrlInput(e.target.value)} onKeyDown={e=>e.key==='Enter'&&handleUrl()}/>
        <button className="btn btn-primary url-btn" onClick={handleUrl} disabled={urlLoading||!urlInput.trim()}>
          {urlLoading?<Loader size={13} className="spin"/>:'Procesar'}
        </button>
      </div>
      {files.length>0&&(
        <div className="file-list">
          {files.map(f=>(
            <div key={f.id} className={`file-item status-${f.status}`}>
              <FileText size={15} className="file-icon"/>
              <div className="file-info">
                <span className="file-name">{f.name}</span>
                {f.status==='uploading'&&<div className="prog-bar"><div className="prog-fill" style={{width:`${f.progress}%`}}/></div>}
                {f.status==='done'&&<span className="file-meta">{f.result?.chunks_indexed} chunks · {f.result?.embed_provider||'OK'}</span>}
                {f.status==='error'&&<span className="file-error">{f.error}</span>}
              </div>
              {f.status==='uploading'&&<Loader size={13} className="spin" style={{color:'var(--accent-1)'}}/>}
              {f.status==='done'&&<CheckCircle size={13} style={{color:'var(--green)'}}/>}
              {f.status==='error'&&<AlertCircle size={13} style={{color:'var(--rose)'}}/>}
              <button className="file-rm" onClick={()=>setFiles(p=>p.filter(x=>x.id!==f.id))}><X size={11}/></button>
            </div>
          ))}
        </div>
      )}
      <div className="types-grid">
        {[['📄','PDF','200+ pags'],['📝','DOCX/PPTX','Office'],['🖼️','Imagenes','OCR auto'],
          ['🎙️','Audio','Transcripcion'],['🎬','Video','MP4,MOV'],['🌐','URL/YouTube','Extraccion web']
        ].map(([icon,label,desc])=>(
          <div key={label} className="type-card">
            <span className="tc-icon">{icon}</span><span className="tc-label">{label}</span><span className="tc-desc">{desc}</span>
          </div>
        ))}
      </div>
    </div>
  )
}