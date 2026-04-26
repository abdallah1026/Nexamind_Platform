# simple rate limiter using redis
# limits requests per minute per tenant
# 
# using sliding window approach with redis keys that expire after 1 min

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
        # key based on tenant and current minute
        current_minute = int(time.time() // 60)
        key = f"ratelimit:{tenant_id}:{current_minute}"
        
        # increment counter
        count = await self.redis.incr(key)
        
        # set expiry if this is first request in this minute
        if count == 1:
            await self.redis.expire(key, 70)  # 70 sec to be safe
        
        remaining = max(0, self.rpm - count)
        allowed = count <= self.rpm
        
        return allowed, remaining
