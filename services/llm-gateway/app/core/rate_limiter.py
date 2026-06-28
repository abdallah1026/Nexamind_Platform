import redis.asyncio as aioredis
import time


class RateLimiter:
    
    def __init__(self, redis_url: str, requests_per_minute: int = 60):
        self.redis = aioredis.from_url(redis_url)
        self.rpm = requests_per_minute

    async def check(self, tenant_id: str):
        """
        check if tenant has exceeded rate limit
        returns (is_allowed, remaining_requests)
        """

        current_minute = int(time.time() // 60)
        key = f"ratelimit:{tenant_id}:{current_minute}"
        
        count = await self.redis.incr(key)
        
        if count == 1:
            await self.redis.expire(key, 70)  
        
        remaining = max(0, self.rpm - count)
        allowed = count <= self.rpm
        
        return allowed, remaining
