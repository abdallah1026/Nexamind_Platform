from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from ..providers.base import CompletionRequest, CompletionResponse

router = APIRouter(prefix="/api/v1", tags=["Completions"])

@router.post("/chat/completions", response_model=CompletionResponse)
async def chat_completion(
    request: CompletionRequest,
    x_tenant_id: Optional[str] = Header(None),
    x_provider: Optional[str] = Header(None)
):
    from ..main import get_provider, rate_limiter, cost_tracker, cache
    
    # Rate limiting
    if x_tenant_id:
        allowed, remaining = await rate_limiter.check(x_tenant_id)
        if not allowed:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Cache check
    msgs = [m.model_dump() for m in request.messages]
    cached = await cache.get(request.model, msgs, request.temperature)
    if cached:
        return CompletionResponse(**cached)
    
    provider = get_provider(x_provider)
    response = await provider.complete(request)
    
    # Track cost
    if x_tenant_id:
        await cost_tracker.track(x_tenant_id, response.model, response.input_tokens, response.output_tokens)
    
    # Cache response
    await cache.set(request.model, msgs, request.temperature, response.model_dump())
    
    return response

@router.get("/models")
async def list_models(x_provider: Optional[str] = Header(None)):
    from ..main import get_provider
    provider = get_provider(x_provider)
    models = await provider.list_models()
    return {"models": models}

@router.get("/health")
async def health():
    return {"status": "healthy", "service": "llm-gateway"}
