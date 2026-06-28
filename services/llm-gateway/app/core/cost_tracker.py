

import redis.asyncio as aioredis
from datetime import datetime

COST_PER_1K = {
    "llama3-70b-8192":          {"input": 0.00059, "output": 0.00079},
    "llama3-8b-8192":           {"input": 0.00005, "output": 0.00008},
    "mixtral-8x7b-32768":       {"input": 0.00024, "output": 0.00024},
    "gemma2-9b-it":             {"input": 0.00020, "output": 0.00020},
    "llama-3.1-70b-versatile":  {"input": 0.00059, "output": 0.00079},
    "llama-3.1-8b-instant":     {"input": 0.00005, "output": 0.00008},
}

DEFAULT_COST = {"input": 0.001, "output": 0.001}  

class CostTracker:
    
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)

    async def track(self, tenant_id: str, model: str, input_tokens: int, output_tokens: int):
        costs = COST_PER_1K.get(model, DEFAULT_COST)
        cost = (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1000

        month_key = f"cost:{tenant_id}:{datetime.now().strftime('%Y-%m')}"
        await self.redis.incrbyfloat(month_key, cost)
        await self.redis.expire(month_key, 86400 * 35)  

    async def get_monthly_cost(self, tenant_id: str) -> float:
        key = f"cost:{tenant_id}:{datetime.now().strftime('%Y-%m')}"
        val = await self.redis.get(key)
        return round(float(val), 6) if val else 0.0
