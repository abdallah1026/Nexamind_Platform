from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Depends
from typing import Optional
import uuid
import os
import aiofiles

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])
UPLOAD_DIR = "/app/uploads"

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection: str = "default",
    x_tenant_id: Optional[str] = Header(None),
):
    from ..main import vector_store, settings
    from ..ingestion.loader import load_document
    from ..ingestion.chunker import chunk_text
    from ..ingestion.embedder import get_embeddings

    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-Id header required")

    doc_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{file.filename}")
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)
    
    try:
        text = await load_document(file_path, file.content_type or "text/plain")
        chunks = chunk_text(text)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No content extracted from document")
        
        embeddings = await get_embeddings(chunks, settings.LLM_GATEWAY_URL)
        
        collection_name = f"{x_tenant_id}_{collection}"
        chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {"doc_id": doc_id, "tenant_id": x_tenant_id, "filename": file.filename,
             "chunk_index": i, "total_chunks": len(chunks)}
            for i in range(len(chunks))
        ]
        
        await vector_store.upsert(collection_name, chunk_ids, embeddings, chunks, metadatas)
        
        return {
            "doc_id": doc_id,
            "filename": file.filename,
            "chunks": len(chunks),
            "collection": collection_name,
            "status": "indexed"
        }
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    collection: str = "default",
    x_tenant_id: Optional[str] = Header(None)
):
    from ..main import vector_store
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-Id header required")
    
    collection_name = f"{x_tenant_id}_{collection}"
    await vector_store.delete(collection_name, doc_id)
    return {"doc_id": doc_id, "status": "deleted"}
