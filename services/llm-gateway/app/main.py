

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379/1"

    GROQ_API_KEY: str = ""

    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    DEFAULT_PROVIDER: str = "groq"
    
    RATE_LIMIT_RPM: int = 60

    class Config:
        env_file = ".env"

settings = Settings()

from .core.cache import LLMCache
from .core.rate_limiter import RateLimiter
from .core.cost_tracker import CostTracker
from .providers.base import BaseLLMProvider

cache = LLMCache(settings.REDIS_URL)
rate_limiter = RateLimiter(settings.REDIS_URL, settings.RATE_LIMIT_RPM)
cost_tracker = CostTracker(settings.REDIS_URL)

def get_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """return the right provider based on config"""
    
    name = provider_name or settings.DEFAULT_PROVIDER
    
    if name == "groq":
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in .env file")
        from .providers.groq_provider import GroqProvider
        return GroqProvider(settings.GROQ_API_KEY)
    
    elif name == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in .env file")
        from .providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(settings.ANTHROPIC_API_KEY)
    
    elif name == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in .env file")
        from .providers.openai_provider import OpenAIProvider
        return OpenAIProvider(settings.OPENAI_API_KEY)
    
    else:
        raise ValueError(f"unknown provider: {name}. use groq, anthropic, or openai")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"LLM Gateway starting - default provider: {settings.DEFAULT_PROVIDER}")
    yield
    await cache.close()
    print("LLM Gateway shutdown")

app = FastAPI(
    title="NexaMind LLM Gateway",
    description="Unified gateway for Groq, Anthropic, OpenAI",
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

from .routes.completions import router as completions_router
from .routes.embeddings import router as embeddings_router

app.include_router(completions_router)
app.include_router(embeddings_router)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "llm-gateway",
        "default_provider": settings.DEFAULT_PROVIDER
    }
