import { useState, useCallback } from 'react'
import { Toaster } from 'react-hot-toast'
import Sidebar from './components/Sidebar'
import Header  from './components/Header'
import UploadZone from './components/UploadZone'
import ChatPanel from './components/ChatPanel'
import GeneratorPanel from './components/GeneratorPanel'
import AIStatus from './components/AIStatus'
import './styles/app.css'

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [documents, setDocuments] = useState([])
  const [activeTab, setActiveTab] = useState('upload')
  const handleSessionReady = useCallback((sid, docs) => {
    setSessionId(sid)
    setDocuments(prev => { const ex=prev.map(d=>d.name); return [...prev,...docs.filter(d=>!ex.includes(d.name))] })
    setActiveTab('chat')
  }, [])
  return (
    <div className="app-shell">
      <Toaster position="top-right" toastOptions={{style:{background:'var(--bg-elevated)',color:'var(--text-primary)',border:'1px solid var(--border)',fontFamily:'var(--font-body)'}}}/>
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} documents={documents} sessionId={sessionId}/>
      <main className="app-main">
        <Header sessionId={sessionId} documents={documents}/>
        <div className="app-content fade-up">
          {activeTab==='upload'    && <UploadZone onSessionReady={handleSessionReady} sessionId={sessionId}/>}
          {activeTab==='chat'      && <ChatPanel sessionId={sessionId}/>}
          {activeTab==='generate'  && <GeneratorPanel sessionId={sessionId}/>}
          {activeTab==='ai-status' && <AIStatus/>}
        </div>
      </main>
    </div>
  )
}