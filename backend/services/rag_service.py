"""PERCI TC PRO AI — RAG Service (Multi-Provider, robusto)"""
from __future__ import annotations
import os, json
from pathlib import Path
from dotenv import load_dotenv
import numpy as np
from services.ai import ai_router, TaskType

load_dotenv()

VECTOR_STORE_PATH = Path(os.getenv("VECTOR_STORE_PATH", "./data/vectorstore"))
CHUNK_SIZE_MACRO  = int(os.getenv("CHUNK_SIZE_MACRO", 2000))
CHUNK_SIZE_MICRO  = int(os.getenv("CHUNK_SIZE_MICRO", 700))
CHUNK_OVERLAP     = int(os.getenv("CHUNK_OVERLAP", 150))
TOP_K_INITIAL     = int(os.getenv("TOP_K_INITIAL", 20))
TOP_K_FINAL       = int(os.getenv("TOP_K_FINAL", 6))

SYSTEM_PERCI = (
    "Eres PERCI, un asistente educativo de IA experto y amigable. "
    "Respondes SIEMPRE en espanol claro y profesional. "
    "Explicas como un profesor experto pero accesible. "
    "Basas tus respuestas UNICAMENTE en el contexto proporcionado. "
    "Si el contexto no contiene la informacion, lo dices honestamente."
)


def _chunk(text: str, size: int, overlap: int) -> list[str]:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, cur, cur_len = [], [], 0
    for p in paras:
        w = p.split()
        if cur_len + len(w) > size:
            if cur: chunks.append(" ".join(cur))
            cur = (cur[-overlap:] if len(cur) > overlap else cur) + w
            cur_len = len(cur)
        else:
            cur.extend(w); cur_len += len(w)
    if cur: chunks.append(" ".join(cur))
    return chunks


def hierarchical_chunks(text: str) -> list[dict]:
    out = []
    for i, macro in enumerate(_chunk(text, CHUNK_SIZE_MACRO, CHUNK_OVERLAP)):
        out.append({"type": "macro", "index": i, "text": macro})
        for j, micro in enumerate(_chunk(macro, CHUNK_SIZE_MICRO, CHUNK_OVERLAP // 2)):
            out.append({"type": "micro", "index": f"{i}.{j}", "text": micro})
    return out


class FAISSStore:
    def __init__(self, path: Path):
        self.path = path; self.path.mkdir(parents=True, exist_ok=True)
        self.index = None; self.meta: list[dict] = []; self.dim = None

    def _idx_path(self, sid): return self.path / f"{sid}.index"
    def _meta_path(self, sid): return self.path / f"{sid}.json"

    def load(self, sid: str):
        import faiss
        ip, mp = self._idx_path(sid), self._meta_path(sid)
        if ip.exists():
            self.index = faiss.read_index(str(ip))
            self.meta  = json.loads(mp.read_text())
            self.dim   = self.index.d
        else:
            self.index = None; self.meta = []; self.dim = None

    def save(self, sid: str):
        import faiss
        faiss.write_index(self.index, str(self._idx_path(sid)))
        self._meta_path(sid).write_text(json.dumps(self.meta, ensure_ascii=False))

    def add(self, embeddings: list[list[float]], metadata: list[dict]):
        import faiss
        dim = len(embeddings[0])
        if self.index is None or self.dim != dim:
            self.index = faiss.IndexFlatIP(dim); self.dim = dim
        vecs = np.array(embeddings, dtype="float32")
        vecs /= (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-10)
        self.index.add(vecs); self.meta.extend(metadata)

    def search(self, qvec: list[float], k: int) -> list[dict]:
        q = np.array([qvec], dtype="float32")
        q /= (np.linalg.norm(q) + 1e-10)
        scores, idxs = self.index.search(q, min(k, self.index.ntotal))
        return [{**self.meta[i], "score": float(s)} for s, i in zip(scores[0], idxs[0]) if i >= 0]


async def _rerank(query: str, candidates: list[dict], top_k: int) -> list[dict]:
    if len(candidates) <= top_k: return candidates
    snips = "\n\n".join(f"[{i}] {c['text'][:300]}" for i, c in enumerate(candidates))
    try:
        r = await ai_router.generate_response(
            prompt=f"Selecciona los {top_k} indices mas relevantes para: '{query}'\n\n{snips}\n\nResponde SOLO indices separados por coma: 0,2,5",
            task=TaskType.CHAT_RAPIDO, options={"max_tokens": 30, "temperature": 0},
        )
        idxs = [int(x.strip()) for x in r.content.split(",") if x.strip().isdigit()]
        result = [candidates[i] for i in idxs if 0 <= i < len(candidates)]
        return result if result else candidates[:top_k]
    except Exception:
        return candidates[:top_k]


class RAGService:
    def __init__(self):
        self.store = FAISSStore(VECTOR_STORE_PATH)

    async def initialize(self):
        VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)

    async def cleanup(self): pass

    async def index_document(self, session_id: str, text: str, doc_name: str) -> dict:
        chunks   = hierarchical_chunks(text)
        emb_resp = await ai_router.generate_embeddings([c["text"] for c in chunks])
        metadata = [{"text": c["text"], "type": c["type"], "chunk_index": c["index"],
                     "doc_name": doc_name, "session_id": session_id} for c in chunks]
        self.store.load(session_id)
        self.store.add(emb_resp.embeddings, metadata)
        self.store.save(session_id)
        return {"chunks_indexed": len(chunks), "doc_name": doc_name,
                "embed_provider": emb_resp.provider, "embed_model": emb_resp.model}

    async def retrieve(self, session_id: str, query: str) -> list[dict]:
        self.store.load(session_id)
        if not self.store.index or self.store.index.ntotal == 0: return []
        eq = await ai_router.generate_embeddings([query])
        return await _rerank(query, self.store.search(eq.embeddings[0], TOP_K_INITIAL), TOP_K_FINAL)

    async def chat(self, session_id: str, query: str,
                   history: list[dict] | None = None, task: str = "auto") -> dict:
        chunks  = await self.retrieve(session_id, query)
        context = "\n\n---\n\n".join(c["text"] for c in chunks)
        if task == "auto":
            resolved = TaskType.DOC_LARGO if len(context) > 4000 else TaskType.CHAT_RAPIDO
        else:
            resolved = TaskType(task) if task in TaskType._value2member_map_ else TaskType.ALTA_CALIDAD
        resp = await ai_router.generate_response(
            prompt=query, context=context, system=SYSTEM_PERCI,
            history=history, task=resolved, options={"max_tokens": 2000, "temperature": 0.4},
        )
        return {"answer": resp.content, "provider": resp.provider, "model": resp.model,
                "sources": [c["doc_name"] for c in chunks[:3]]}


rag_service = RAGService()
