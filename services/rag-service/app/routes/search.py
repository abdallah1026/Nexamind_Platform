from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/api/v1", tags=["Search"])

class SearchRequest(BaseModel):
    query: str
    collection: str = "default"
    n_results: int = 5
    use_hybrid: bool = True
    filters: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    score: float
    id: str

@router.post("/search", response_model=List[SearchResult])
async def search(
    request: SearchRequest,
    x_tenant_id: Optional[str] = Header(None)
):
    from ..main import vector_store, settings
    from ..ingestion.embedder import get_embeddings
    from ..retrieval.hybrid_search import hybrid_rerank

    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-Id header required")

    embeddings = await get_embeddings([request.query], settings.LLM_GATEWAY_URL)
    query_embedding = embeddings[0]
    
    collection_name = f"{x_tenant_id}_{request.collection}"
    
    where = None
    if request.filters:
        where = {k: {"$eq": v} for k, v in request.filters.items()}
    
    results = await vector_store.query(
        collection_name, query_embedding,
        n_results=request.n_results * 2 if request.use_hybrid else request.n_results,
        where=where
    )
    
    if request.use_hybrid and results:
        results = hybrid_rerank(results, request.query)
        results = results[:request.n_results]
    
    return [SearchResult(**r) for r in results]

@router.post("/collections/{collection_name}/query")
async def query_collection(
    collection_name: str,
    request: SearchRequest,
    x_tenant_id: Optional[str] = Header(None)
):
    request.collection = collection_name
    return await search(request, x_tenant_id)
