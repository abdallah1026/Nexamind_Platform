import httpx
from typing import Any, Dict, Optional

class APITool:
    name = "api_tool"
    description = "Make HTTP requests to external APIs"

    def __init__(self, **kwargs):
        pass

    async def execute(
        self,
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        body: Optional[Dict] = None,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers or {},
                    params=params,
                    json=body
                )
                return {
                    "status_code": response.status_code,
                    "data": response.json() if "application/json" in response.headers.get("content-type", "") else response.text,
                    "headers": dict(response.headers)
                }
            except Exception as e:
                return {"error": str(e), "status_code": 0}

    def schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                "url": {"type": "string"},
                "headers": {"type": "object"},
                "params": {"type": "object"},
                "body": {"type": "object"}
            }
        }
