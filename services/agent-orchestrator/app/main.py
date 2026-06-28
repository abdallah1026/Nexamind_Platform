

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://nexamind:nexamind_secret@localhost:5432/nexamind"
    REDIS_URL: str = "redis://redis:6379/3"
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    LLM_GATEWAY_URL: str = "http://localhost:8002"
    RAG_SERVICE_URL: str = "http://localhost:8003"
    SECRET_KEY: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import redis.asyncio as aioredis
from .orchestrator.coordinator import AgentCoordinator

engine = create_async_engine(
    settings.DATABASE_URL, 
    pool_size=10, 
    max_overflow=20, 
    pool_pre_ping=True
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

redis_client = None

async def get_coordinator(tenant_id: str) -> AgentCoordinator:
    """creates an AgentCoordinator for a given tenant"""

    async with AsyncSessionLocal() as session:
        return AgentCoordinator(
            tenant_id=tenant_id,
            llm_url=settings.LLM_GATEWAY_URL,
            rag_url=settings.RAG_SERVICE_URL,
            db_session=session,
            redis=redis_client,
            config={
                "smtp_host": settings.SMTP_HOST,
                "smtp_port": settings.SMTP_PORT,
                "smtp_user": settings.SMTP_USER,
                "smtp_password": settings.SMTP_PASSWORD,
            }
        )

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    global redis_client
    redis_client = aioredis.from_url(settings.REDIS_URL)
    print("connected to redis")
    
    yield

    await redis_client.aclose()
    await engine.dispose()
    print("cleanup done")

app = FastAPI(
    title="NexaMind Agent Orchestrator",
    description="Multi-agent AI platform - Graduation Project 2024",
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

from .routes.chat import router as chat_router
from .routes.finance import router as finance_router
from .routes.hr import router as hr_router
from .routes.operations import router as ops_router
from .routes.sales import router as sales_router
from .routes.support import router as support_router

app.include_router(chat_router)
app.include_router(finance_router)
app.include_router(hr_router)
app.include_router(ops_router)
app.include_router(sales_router)
app.include_router(support_router)

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "service": "agent-orchestrator",
        "total_agents": 20
    }

import httpx
from fastapi import Request, Response
from fastapi.routing import APIRoute

AUTH_SERVICE_BASE = settings.AUTH_SERVICE_URL

@app.api_route("/api/v1/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def auth_proxy(path: str, request: Request):
    target_url = f"{AUTH_SERVICE_BASE}/api/v1/auth/{path}"

    params = dict(request.query_params)

    body = await request.body()

    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        proxy_response = await client.request(
            method=request.method,
            url=target_url,
            params=params,
            content=body,
            headers=headers,
        )
    
    return Response(
        content=proxy_response.content,
        status_code=proxy_response.status_code,
        headers=dict(proxy_response.headers),
        media_type=proxy_response.headers.get("content-type"),
    )
