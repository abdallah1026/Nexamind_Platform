# rag service - handles document upload and semantic search
# embeddings are done locally using sentence-transformers (no api key needed)
# vector storage is chromadb

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://nexamind:nexamind_secret@localhost:5432/nexamind"
    REDIS_URL: str = "redis://localhost:6379/2"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_AUTH_TOKEN: str = "nexamind-chroma-token"
    LLM_GATEWAY_URL: str = "http://localhost:8002"
    
    # local = use sentence-transformers (default, no api key needed)
    # openai = use openai via llm gateway (requires openai key)
    EMBEDDING_PROVIDER: str = "local"

    class Config:
        env_file = ".env"


settings = Settings()

# set env var so embedder.py picks it up
import os
os.environ["EMBEDDING_PROVIDER"] = settings.EMBEDDING_PROVIDER

from .retrieval.vector_search import VectorStore

vector_store = VectorStore(
    settings.CHROMA_HOST, 
    settings.CHROMA_PORT, 
    settings.CHROMA_AUTH_TOKEN
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"RAG service starting - embedding provider: {settings.EMBEDDING_PROVIDER}")
    
    # pre-load the embedding model so first request isnt slow
    if settings.EMBEDDING_PROVIDER == "local":
        print("loading sentence-transformers model (first time may take a minute to download)...")
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            print("embedding model loaded OK")
        except Exception as e:
            print(f"warning: could not pre-load embedding model: {e}")
    
    yield
    print("RAG service shutdown")


app = FastAPI(
    title="NexaMind RAG Service",
    description="Document ingestion and semantic search with local embeddings",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routes.documents import router as docs_router
from .routes.search import router as search_router

app.include_router(docs_router)
app.include_router(search_router)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "rag-service",
        "embedding_provider": settings.EMBEDDING_PROVIDER
    }
