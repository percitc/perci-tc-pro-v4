import { FileText, Zap } from 'lucide-react'
import './Header.css'
export default function Header({sessionId,documents}){
  return(
    <header className="app-header">
      <div className="header-left">
        <h1 className="header-title"><span className="gradient-text">PERCI TC PRO AI</span></h1>
        <p className="header-sub">Cerebro Digital Educativo · Multi-Provider IA</p>
      </div>
      <div className="header-right">
        {sessionId&&<div className="header-stat"><FileText size={12}/><span>{documents.length} doc{documents.length!==1?'s':''}</span></div>}
        <div className="header-stat accent"><Zap size={12}/><span>Online</span></div>
      </div>
    </header>
  )
}