

import json
import hashlib
import redis.asyncio as aioredis
from typing import Optional


class LLMCache:
    
    def __init__(self, redis_url: str, ttl: int = 3600):
        self.redis = aioredis.from_url(redis_url)
        self.ttl = ttl  

    def _make_key(self, model: str, messages: list, temperature: float) -> str:
        data = json.dumps({
            "model": model, 
            "messages": messages, 
            "temperature": temperature
        }, sort_keys=True)
        return "llm_cache:" + hashlib.md5(data.encode()).hexdigest()

    async def get(self, model: str, messages: list, temperature: float) -> Optional[dict]:
        key = self._make_key(model, messages, temperature)
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set(self, model: str, messages: list, temperature: float, response: dict):
        if temperature == 0:
            key = self._make_key(model, messages, temperature)
            await self.redis.setex(key, self.ttl, json.dumps(response))

    async def close(self):
        await self.redis.aclose()
