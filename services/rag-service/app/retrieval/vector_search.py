

import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional

class VectorStore:
    
    def __init__(self, host: str, port: int, auth_token: str):
        self.client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=ChromaSettings(
                chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
                chroma_client_auth_credentials=auth_token,
            )
        )

    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )

    async def upsert(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ):
        collection = self.get_or_create_collection(collection_name)

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    async def query(
        self,
        collection_name: str,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:

        try:
            collection = self.client.get_collection(collection_name)
        except Exception:
            return []
        
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"]
        }
        if where:
            kwargs["where"] = where
        
        results = collection.query(**kwargs)

        output = []
        for i, doc in enumerate(results["documents"][0]):
            output.append({
                "content": doc,
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i],  
                "id": results["ids"][0][i]
            })
        
        return output

    async def delete(self, collection_name: str, doc_id: str):
        try:
            collection = self.client.get_collection(collection_name)
            
            collection.delete(where={"doc_id": {"$eq": doc_id}})
        except Exception as e:
            print(f"delete failed: {e}")
