from typing import Dict, Any, Optional, List
import json

class ContextManager:
    """Manages context assembly for agent invocations"""
    
    def __init__(self, tenant_id: str, redis_client=None):
        self.tenant_id = tenant_id
        self.redis = redis_client

    async def build_context(
        self, 
        session_id: Optional[str],
        user_input: str,
        additional_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        context = {
            "tenant_id": self.tenant_id,
            "user_input": user_input,
            **(additional_context or {})
        }
        
        if session_id and self.redis:
            history = await self._get_session_history(session_id)
            if history:
                context["conversation_history"] = history
        
        return context

    async def _get_session_history(self, session_id: str) -> List[Dict]:
        if not self.redis:
            return []
        key = f"stm:{session_id}"
        msgs = await self.redis.lrange(key, -10, -1)
        return [json.loads(m) for m in msgs]

    async def save_interaction(
        self, 
        session_id: str, 
        user_input: str, 
        response: str
    ):
        if not self.redis or not session_id:
            return
        key = f"stm:{session_id}"
        await self.redis.rpush(key, json.dumps({"role": "user", "content": user_input}))
        await self.redis.rpush(key, json.dumps({"role": "assistant", "content": response}))
        await self.redis.ltrim(key, -20, -1)
        await self.redis.expire(key, 3600)
