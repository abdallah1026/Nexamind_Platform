import json
import redis.asyncio as aioredis
from typing import List, Dict, Optional

class ShortTermMemory:
    """In-session conversation memory stored in Redis"""
    
    def __init__(self, redis_url: str, max_messages: int = 20, ttl: int = 3600):
        self.redis = aioredis.from_url(redis_url)
        self.max_messages = max_messages
        self.ttl = ttl

    def _key(self, session_id: str) -> str:
        return f"stm:{session_id}"

    async def add(self, session_id: str, role: str, content: str):
        key = self._key(session_id)
        msg = json.dumps({"role": role, "content": content})
        await self.redis.rpush(key, msg)
        await self.redis.ltrim(key, -self.max_messages, -1)
        await self.redis.expire(key, self.ttl)

    async def get(self, session_id: str) -> List[Dict]:
        key = self._key(session_id)
        msgs = await self.redis.lrange(key, 0, -1)
        return [json.loads(m) for m in msgs]

    async def clear(self, session_id: str):
        await self.redis.delete(self._key(session_id))
