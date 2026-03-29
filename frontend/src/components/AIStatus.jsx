import { useState, useEffect } from 'react'
import { Activity, RefreshCw, CheckCircle, XCircle, Loader, Zap } from 'lucide-react'
import { aiStatus, aiHealth, setProvider } from '../utils/api'
import toast from 'react-hot-toast'
import './AIStatus.css'
const COLORS={'openai':'#00e5ff','gemini':'#4285f4','groq':'#f59e0b','claude':'#a78bfa','ollama':'#10d9a0','local':'#6b7280'}
const LABELS={'openai':'OpenAI','gemini':'Google Gemini','groq':'Groq','claude':'Anthropic Claude','ollama':'Ollama Local','local':'Local (sentence-transformers)'}
export default function AIStatus(){
  const [status,setStatus]=useState(null)
  const [health,setHealth]=useState(null)
  const [loading,setLoading]=useState(false)
  const [settingProv,setSettingProv]=useState(null)
  const load=async()=>{
    setLoading(true)
    try{
      const [s,h]=await Promise.all([aiStatus(),aiHealth()])
      setStatus(s);setHealth(h)
    }catch(e){toast.error('Error al obtener estado de IA')}
    finally{setLoading(false)}
  }
  useEffect(()=>{load()},[])
  const handleSetProvider=async(p)=>{
    setSettingProv(p)
    try{
      await setProvider(p)
      toast.success(p?`Proveedor forzado: ${p}`:'Modo automatico activado')
      load()
    }catch(e){toast.error(e.response?.data?.detail||'Error')}
    finally{setSettingProv(null)}
  }
  return(
    <div className="ai-wrapper">
      <div className="ai-hero">
        <Activity size={28} style={{color:'var(--accent-1)'}}/>
        <div><h2>Proveedores de IA</h2><p>Estado en tiempo real · Seleccion inteligente con fallback automatico</p></div>
        <button className="btn btn-ghost refresh-btn" onClick={load} disabled={loading}>
          <RefreshCw size={14} className={loading?'spin':''}/>Actualizar
        </button>
      </div>
      {loading&&!status&&<div className="ai-loading"><Loader size={22} className="spin"/><p>Detectando proveedores...</p></div>}
      {status&&(
        <>
          <div className="mode-bar">
            <div className="mode-info">
              <Zap size={14} style={{color:'var(--accent-1)'}}/>
              <span>Modo actual: <strong>{status.mode==='automatico'?'Automatico (recomendado)':'Manual — '+status.mode}</strong></span>
            </div>
            {status.mode!=='automatico'&&(
              <button className="btn btn-ghost" style={{fontSize:11,padding:'5px 12px'}} onClick={()=>handleSetProvider(null)}>
                Volver a automatico
              </button>
            )}
          </div>
          <div className="providers-grid">
            {['openai','gemini','groq','claude','ollama'].map(p=>{
              const active=status.providers?.includes(p)
              const healthy=health?.providers?.[p]
              const isCurrent=status.mode===p
              return(
                <div key={p} className={`provider-card ${active?'active':''} ${isCurrent?'current':''}`} style={{'--pc':COLORS[p]||'#666'}}>
                  <div className="pc-top">
                    <div className="pc-dot" style={{background:active?(healthy?COLORS[p]:'var(--amber)'):'var(--text-muted)'}}/>
                    <span className="pc-name">{LABELS[p]||p}</span>
                    {active&&health&&(healthy?<CheckCircle size={13} style={{color:'var(--green)'}}/>:<XCircle size={13} style={{color:'var(--rose)'}}/>)}
                  </div>
                  <div className="pc-status">
                    {!active&&<span className="pc-tag off">Sin configurar</span>}
                    {active&&healthy&&<span className="pc-tag ok">Activo</span>}
                    {active&&health&&!healthy&&<span className="pc-tag warn">Con errores</span>}
                  </div>
                  {active&&(
                    <button className={`btn ${isCurrent?'btn-primary':'btn-ghost'} pc-btn`}
                      onClick={()=>handleSetProvider(isCurrent?null:p)} disabled={settingProv===p}>
                      {settingProv===p?<Loader size={11} className="spin"/>:isCurrent?'Activo':'Usar'}
                    </button>
                  )}
                </div>
              )
            })}
          </div>
          {status.task_routing&&(
            <div className="routing-table">
              <h3>Tabla de Routing por Tarea</h3>
              <div className="rt-grid">
                {Object.entries(status.task_routing).map(([task,providers])=>(
                  <div key={task} className="rt-row">
                    <span className="rt-task">{task.replace('_',' ')}</span>
                    <div className="rt-providers">
                      {providers.filter(p=>status.providers?.includes(p)).map((p,i)=>(
                        <span key={p} className="rt-badge" style={{borderColor:COLORS[p],color:COLORS[p]}}>
                          {i===0&&'★ '}{p}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}