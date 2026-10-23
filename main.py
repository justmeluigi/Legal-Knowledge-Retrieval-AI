import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from core.permissions import DEMO_USERS, UserRole, get_accessible_clearances
from core.schemas import QueryRequest, QueryResponse, IndexedDocumentSummary
from core.vector_store import LegalVectorStoreManager
from core.rag_engine import LegalRAGEngine
from core.llm_provider import is_ollama_running

load_dotenv()

app = FastAPI(
    title="Legal Knowledge Retrieval AI",
    description="Enterprise legal RAG engine with semantic search, grounded abstention, and RBAC clearance filtering.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
CORPUS_DIR = os.path.join(BASE_DIR, "legal_corpus")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize Vector Store and RAG Engine on startup
vector_manager = LegalVectorStoreManager.get_instance()
rag_engine = LegalRAGEngine(vector_manager=vector_manager)

# Ensure corpus is indexed
if os.path.exists(CORPUS_DIR):
    vector_manager.index_corpus(corpus_dir=CORPUS_DIR, force_reindex=False)


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Legal Knowledge Retrieval AI API is running.</h1>")


@app.get("/api/health")
async def health_check():
    ollama_online = is_ollama_running()
    chunk_count = vector_manager.vectorstore._collection.count()
    return {
        "status": "healthy",
        "system": "Legal Knowledge Retrieval AI",
        "default_active_provider": "qwen" if ollama_online else "mock",
        "ollama_active": ollama_online,
        "local_model": "qwen3.5:2b (Ollama)" if ollama_online else "Heuristic",
        "indexed_chunks": chunk_count,
        "rbac_tiers_enabled": ["PUBLIC", "INTERNAL", "LEGAL_COUNSEL", "EXECUTIVE_BOARD"]
    }


@app.get("/api/users")
async def get_demo_users():
    return {
        "users": [
            {
                "user_id": u.user_id,
                "name": u.name,
                "role": u.role.value,
                "title": u.title,
                "description": u.description,
                "permitted_clearances": get_accessible_clearances(u.role)
            }
            for u in DEMO_USERS.values()
        ]
    }


@app.get("/api/documents", response_model=List[IndexedDocumentSummary])
async def list_documents():
    return vector_manager.get_indexed_documents_summary(corpus_dir=CORPUS_DIR)


@app.get("/api/documents/{doc_id}/download")
async def download_document(doc_id: str):
    fpath = os.path.join(CORPUS_DIR, f"{doc_id}.pdf")
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail=f"Legal document '{doc_id}' not found")
    return FileResponse(fpath, filename=f"{doc_id}.pdf", media_type="application/pdf")


@app.post("/api/query", response_model=QueryResponse)
async def query_knowledge_base(req: QueryRequest):
    try:
        response = rag_engine.answer_query(req)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution error: {str(e)}")


@app.post("/api/reindex")
async def reindex_corpus():
    count = vector_manager.index_corpus(corpus_dir=CORPUS_DIR, force_reindex=True)
    return {"status": "success", "indexed_chunks": count}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8001))
    print(f"Starting Legal Knowledge Retrieval AI at http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=False)
