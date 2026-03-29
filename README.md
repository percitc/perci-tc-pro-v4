# PERCI TC PRO AI v4

Plataforma SaaS educativa con IA multi-proveedor.
Funciona con OpenAI, Gemini, Groq, Claude, Ollama — o cualquier combinacion.
Nunca se rompe por falta de un proveedor.

## Variables de entorno (Backend)
Agrega al menos una:
```
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
GROQ_API_KEY=gsk_...
CLAUDE_API_KEY=sk-ant-...
OLLAMA_URL=http://localhost:11434
```

## Variable de entorno (Frontend)
```
VITE_API_URL=https://URL-DE-TU-BACKEND
```

## Deploy Render
1. Subir a GitHub
2. Render -> New -> Blueprint -> conectar repo
3. Configurar variables de entorno
4. Deploy automatico

## Local
```bash
cd backend && pip install -r requirements.txt && cp .env.example .env && python main.py
cd frontend && npm install && cp .env.example .env && npm run dev
```
