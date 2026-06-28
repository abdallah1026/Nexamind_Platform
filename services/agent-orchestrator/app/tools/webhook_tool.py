import httpx
import hmac
import hashlib
import json
import asyncio
from typing import Any, Dict, Optional

class WebhookTool:
    name = "webhook_tool"
    description = "Send webhook notifications to configured endpoints"

    def __init__(self, **kwargs):
        pass

    async def execute(
        self,
        url: str,
        payload: Dict[str, Any],
        secret: Optional[str] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        body = json.dumps(payload)
        
        if secret:
            sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
            headers["X-Signature-256"] = f"sha256={sig}"
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(url, content=body, headers=headers)
                    if resp.status_code < 300:
                        return {"status": "delivered", "status_code": resp.status_code, "attempt": attempt + 1}
                    if resp.status_code < 500:
                        return {"status": "failed", "status_code": resp.status_code, "error": resp.text}
            except Exception as e:
                if attempt == max_retries - 1:
                    return {"status": "failed", "error": str(e), "attempts": max_retries}
            await asyncio.sleep(2 ** attempt)  
        
        return {"status": "failed", "error": "Max retries exceeded"}

    def schema(self) -> Dict:
        return {"name": self.name, "description": self.description,
                "parameters": {"url": {"type": "string"}, "payload": {"type": "object"}}}
