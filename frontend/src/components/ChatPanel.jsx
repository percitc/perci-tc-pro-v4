import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { Send, Loader, Bot, User, AlertTriangle, ChevronDown } from 'lucide-react'
import { sendChat } from '../utils/api'
import './ChatPanel.css'
const SUGS=['Cuales son los puntos principales?','Explica el concepto mas importante','Resume en 5 puntos clave','Que conclusiones podemos extraer?','Cuales son las aplicaciones practicas?']
const TASKS=[{v:'auto',l:'Auto'},{v:'chat_rapido',l:'Rapido'},{v:'doc_largo',l:'Doc largo'},{v:'razonamiento',l:'Razonamiento'},{v:'alta_calidad',l:'Alta calidad'}]
export default function ChatPanel({sessionId}){
  const [msgs,setMsgs]=useState([])
  const [input,setInput]=useState('')
  const [loading,setLoading]=useState(false)
  const [task,setTask]=useState('auto')
  const bottomRef=useRef(); const inputRef=useRef()
  useEffect(()=>{bottomRef.current?.scrollIntoView({behavior:'smooth'})},[msgs])
  useEffect(()=>{
    if(!sessionId&&msgs.length===0) setMsgs([{role:'assistant',content:'Hola! Soy **PERCI**. Sube un documento en **Archivos** y preguntame lo que quieras sobre el.'}])
  },[])
  const send=async(text)=>{
    const q=(text||input).trim(); if(!q||loading||!sessionId)return
    const hist=msgs.map(m=>({role:m.role,content:m.content}))
    setMsgs(p=>[...p,{role:'user',content:q},{role:'assistant',content:null,loading:true}])
    setInput(''); setLoading(true)
    try{
      const r=await sendChat(sessionId,q,hist,task)
      setMsgs(p=>[...p.slice(0,-1),{role:'assistant',content:r.answer,provider:r.provider,model:r.model}])
    }catch(e){
      setMsgs(p=>[...p.slice(0,-1),{role:'assistant',content:'Error al conectar con el servidor.',error:true}])
    }finally{setLoading(false);inputRef.current?.focus()}
  }
  return(
    <div className="chat-wrapper">
      <div className="chat-messages">
        {!sessionId&&msgs.length===0&&<div className="chat-empty"><Bot size={44}/><p>Sube un documento para comenzar</p></div>}
        {msgs.map((m,i)=>(
          <div key={i} className={`msg ${m.role}`}>
            <div className="msg-avatar">{m.role==='user'?<User size={13}/>:<Bot size={13}/>}</div>
            <div className={`msg-bubble ${m.error?'error':''}`}>
              {m.loading?<div className="thinking"><span/><span/><span/></div>
                :<div className="prose"><ReactMarkdown>{m.content}</ReactMarkdown></div>}
              {m.provider&&<div className="msg-meta">{m.provider} · {m.model}</div>}
            </div>
          </div>
        ))}
        <div ref={bottomRef}/>
      </div>
      {sessionId&&msgs.length<3&&(
        <div className="suggestions">{SUGS.map(s=><button key={s} className="sug-chip" onClick={()=>send(s)}>{s}</button>)}</div>
      )}
      <div className="chat-input-area">
        {!sessionId&&<div className="no-session"><AlertTriangle size={13}/><span>Sube un documento primero</span></div>}
        <div className="task-selector">
          {TASKS.map(t=><button key={t.v} className={`task-btn ${task===t.v?'active':''}`} onClick={()=>setTask(t.v)}>{t.l}</button>)}
        </div>
        <div className={`chat-input-wrap ${!sessionId?'disabled':''}`}>
          <textarea ref={inputRef} className="chat-ta" rows={1}
            placeholder={sessionId?'Pregunta sobre tu documento...':'Sube un documento primero...'}
            value={input} onChange={e=>setInput(e.target.value)} disabled={!sessionId||loading}
            onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}}/>
          <button className="send-btn" onClick={()=>send()} disabled={!sessionId||loading||!input.trim()}>
            {loading?<Loader size={15} className="spin"/>:<Send size={15}/>}
          </button>
        </div>
        <p className="chat-hint">Enter enviar · Shift+Enter nueva linea</p>
      </div>
    </div>
  )
}