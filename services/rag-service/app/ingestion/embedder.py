# embedder.py
# generates embeddings for text chunks
#
# since groq doesnt support embeddings we use sentence-transformers locally
# model: all-MiniLM-L6-v2 - small, fast, good enough for semantic search
# downloads automatically on first run (~90MB)
#
# if you have openai key you can switch EMBEDDING_PROVIDER=openai in .env

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
    # doing import here so it only loads when needed
    from sentence_transformers import SentenceTransformer
    import asyncio
    
    # load model (cached after first time)
    # all-MiniLM-L6-v2 gives 384-dim embeddings - good balance of speed/quality
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # run in thread pool since sentence_transformers is synchronous
    loop = asyncio.get_event_loop()
    embeddings = await loop.run_in_executor(
        None, 
        lambda: model.encode(texts, convert_to_list=True)
    )
    
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
