import httpx
from typing import Any, Dict, List, Optional

class RAGTool:
    name = "rag_tool"
    description = "Query the knowledge base for relevant documents"

    def __init__(self, rag_service_url: str, tenant_id: str):
        self.url = rag_service_url
        self.tenant_id = tenant_id

    async def execute(self, query: str, collection: str = "default", n_results: int = 5, filters: Optional[Dict] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(
                    f"{self.url}/api/v1/search",
                    json={"query": query, "collection": collection, "n_results": n_results, "use_hybrid": True, "filters": filters},
                    headers={"X-Tenant-Id": self.tenant_id}
                )
                resp.raise_for_status()
                results = resp.json()
                return {
                    "results": results,
                    "count": len(results),
                    "query": query
                }
            except Exception as e:
                return {"error": str(e), "results": []}

    def schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "query": {"type": "string"},
                "collection": {"type": "string", "default": "default"},
                "n_results": {"type": "integer", "default": 5}
            }
        }
