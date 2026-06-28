

import os
from typing import List

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")

async def get_embeddings(texts: List[str], llm_gateway_url: str = "", model: str = "") -> List[List[float]]:
    """get embeddings - uses local sentence-transformers by default"""
    
    if EMBEDDING_PROVIDER == "openai" and llm_gateway_url:
        return await _openai_embeddings(texts, llm_gateway_url, model)
    else:
        return await _local_embeddings(texts)

async def _local_embeddings(texts: List[str]) -> List[List[float]]:
    """
    use sentence-transformers locally - no API key needed
    model is cached after first download
    """
    
    from sentence_transformers import SentenceTransformer
    import asyncio

    model = SentenceTransformer("all-MiniLM-L6-v2")

    loop = asyncio.get_event_loop()
    embeddings_np = await loop.run_in_executor(
        None, 
        lambda: model.encode(texts)
    )
    
    embeddings = [emb.tolist() for emb in embeddings_np]
    
    return embeddings

async def _openai_embeddings(texts: List[str], gateway_url: str, model: str) -> List[List[float]]:
    """fallback to openai via llm gateway if configured"""
    import httpx
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{gateway_url}/api/v1/embeddings",
            json={
                "model": model or "text-embedding-3-small", 
                "input": texts
            },
            headers={"X-Provider": "openai"}
        )
        resp.raise_for_status()
        return resp.json()["embeddings"]
