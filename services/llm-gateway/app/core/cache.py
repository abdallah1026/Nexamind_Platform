# LLM response cache using Redis
# caching saves API costs - important for graduation project budget lol
# 
# only cache when temperature=0 (deterministic responses)
# dont cache creative responses since they should vary

import json
import hashlib
import redis.asyncio as aioredis
from typing import Optional


class LLMCache:
    
    def __init__(self, redis_url: str, ttl: int = 3600):
        self.redis = aioredis.from_url(redis_url)
        self.ttl = ttl  # cache for 1 hour by default

    def _make_key(self, model: str, messages: list, temperature: float) -> str:
        # create unique key from request params
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
        # only cache if temperature is 0 (same input = same output)
        if temperature == 0:
            key = self._make_key(model, messages, temperature)
            await self.redis.setex(key, self.ttl, json.dumps(response))

    async def close(self):
        await self.redis.aclose()
