

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from ..providers.base import EmbeddingRequest, EmbeddingResponse

router = APIRouter(prefix="/api/v1", tags=["Embeddings"])

@router.post("/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(
    request: EmbeddingRequest,
    x_tenant_id: Optional[str] = Header(None),
    x_provider: Optional[str] = Header(None)
):
    from ..main import get_provider, settings, cost_tracker

    provider_name = x_provider or settings.DEFAULT_PROVIDER
    if provider_name == "groq":
        raise HTTPException(
            status_code=400,
            detail="Groq does not support embeddings. The RAG service handles embeddings locally. "
                   "Set X-Provider: openai header if you have an OpenAI key."
        )
    
    provider = get_provider(provider_name)
    response = await provider.embed(request)
    
    if x_tenant_id:
        await cost_tracker.track(x_tenant_id, response.model, response.tokens_used, 0)
    
    return response
