# main.py - entry point for the agent orchestrator service
# this is the main service that handles all agent routing
# runs on port 8000

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://nexamind:nexamind_secret@localhost:5432/nexamind"
    REDIS_URL: str = "redis://localhost:6379/3"
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    LLM_GATEWAY_URL: str = "http://localhost:8002"
    RAG_SERVICE_URL: str = "http://localhost:8003"
    SECRET_KEY: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    # email settings (optional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    class Config:
        env_file = ".env"


settings = Settings()

# setup db and redis connections
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

# global redis client
redis_client = None


async def get_coordinator(tenant_id: str) -> AgentCoordinator:
    """creates an AgentCoordinator for a given tenant"""
    # note: db session is created here and passed to coordinator
    # not ideal but works for now
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
    # startup
    global redis_client
    redis_client = aioredis.from_url(settings.REDIS_URL)
    print("connected to redis")
    
    yield
    
    # shutdown - cleanup connections
    await redis_client.aclose()
    await engine.dispose()
    print("cleanup done")


app = FastAPI(
    title="NexaMind Agent Orchestrator",
    description="Multi-agent AI platform - Graduation Project 2024",
    version="1.0.0",
    lifespan=lifespan
)

# allow all origins for development
# TODO: restrict this in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# register routes
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


@app.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "service": "agent-orchestrator",
        "total_agents": 20
    }
