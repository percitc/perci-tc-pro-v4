import axios from 'axios'
const API = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000', timeout: 120000 })
export const uploadFile = (file, sessionId, onProgress) => {
  const f = new FormData(); f.append('file', file); if (sessionId) f.append('session_id', sessionId)
  return API.post('/upload/file', f, { headers:{'Content-Type':'multipart/form-data'}, onUploadProgress: e => onProgress && onProgress(Math.round(e.loaded*100/e.total)) }).then(r => r.data)
}
export const uploadUrl = (url, sessionId) => {
  const f = new FormData(); f.append('url', url); if (sessionId) f.append('session_id', sessionId)
  return API.post('/upload/url', f).then(r => r.data)
}
export const sendChat    = (sid, query, history=[], task='auto') => API.post('/query/chat', {session_id:sid, query, history, task}).then(r=>r.data)
export const genContent  = (sid, type, opts={}) => API.post('/generate/content', {session_id:sid, output_type:type, ...opts}).then(r=>r.data)
export const genTTS      = (text, voice='onyx') => API.post('/generate/audio/tts', {text, voice}, {responseType:'blob'}).then(r=>URL.createObjectURL(new Blob([r.data],{type:'audio/mpeg'})))
export const genPodcast  = sid => API.post('/generate/audio/podcast', {session_id:sid, output_type:'audio_script'}, {responseType:'blob'}).then(r=>URL.createObjectURL(new Blob([r.data],{type:'audio/mpeg'})))
export const aiStatus    = () => API.get('/ai/status').then(r=>r.data)
export const setProvider = p  => API.post('/ai/provider', {provider:p}).then(r=>r.data)
export const aiHealth    = () => API.get('/ai/health').then(r=>r.data)
export const getSession  = sid=> API.get(`/process/session/${sid}`).then(r=>r.data)