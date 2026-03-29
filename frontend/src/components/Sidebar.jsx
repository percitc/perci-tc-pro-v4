import { MessageSquare, Upload, Sparkles, FileText, Brain, Activity } from 'lucide-react'
import './Sidebar.css'
const NAV = [
  {id:'upload',   icon:Upload,        label:'Archivos',   desc:'Sube documentos'},
  {id:'chat',     icon:MessageSquare, label:'Chat IA',    desc:'Pregunta al cerebro'},
  {id:'generate', icon:Sparkles,      label:'Generar',    desc:'Crea contenido'},
  {id:'ai-status',icon:Activity,      label:'Proveedores',desc:'Estado de IA'},
]
export default function Sidebar({activeTab,setActiveTab,documents,sessionId}){
  return(
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon"><Brain size={18}/></div>
        <div><div className="logo-title">PERCI TC PRO</div><div className="logo-sub">AI Educativo v4</div></div>
      </div>
      <nav className="sidebar-nav">
        {NAV.map(item=>(
          <button key={item.id} className={`nav-item ${activeTab===item.id?'active':''}`} onClick={()=>setActiveTab(item.id)}>
            <item.icon size={17}/>
            <div className="nav-text"><span className="nav-label">{item.label}</span><span className="nav-desc">{item.desc}</span></div>
            {activeTab===item.id&&<div className="nav-indicator"/>}
          </button>
        ))}
      </nav>
      {documents.length>0&&(
        <div className="sidebar-docs">
          <div className="docs-header"><FileText size={11}/><span>Documentos ({documents.length})</span></div>
          <ul className="docs-list">{documents.map((d,i)=>(
            <li key={i} className="doc-item" title={d.name||d}>
              <span className="doc-dot"/><span className="doc-name">{(d.name||d).slice(0,22)}</span>
            </li>
          ))}</ul>
        </div>
      )}
      <div className="sidebar-footer">
        {sessionId&&<div className="session-badge"><span className="session-dot"/><span>Sesion activa</span></div>}
      </div>
    </aside>
  )
}