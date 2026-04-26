# cost tracking per tenant per month
# stored in redis as a running total
#
# groq prices are much cheaper than openai/anthropic
# updated: check https://groq.com/pricing for latest

import redis.asyncio as aioredis
from datetime import datetime


# approximate cost per 1k tokens (USD)
# groq is way cheaper, some models are basically free
COST_PER_1K = {
    # groq models
    "llama3-70b-8192":          {"input": 0.00059, "output": 0.00079},
    "llama3-8b-8192":           {"input": 0.00005, "output": 0.00008},
    "mixtral-8x7b-32768":       {"input": 0.00024, "output": 0.00024},
    "gemma2-9b-it":             {"input": 0.00020, "output": 0.00020},
    "llama-3.1-70b-versatile":  {"input": 0.00059, "output": 0.00079},
    "llama-3.1-8b-instant":     {"input": 0.00005, "output": 0.00008},
    
    # anthropic models (if used)
    "claude-sonnet-4-20250514": {"input": 0.003,   "output": 0.015},
    "claude-haiku-4-5-20251001":{"input": 0.00025, "output": 0.00125},
    
    # openai models (if used)
    "gpt-4o":                   {"input": 0.005,   "output": 0.015},
    "gpt-4o-mini":              {"input": 0.00015, "output": 0.0006},
}

DEFAULT_COST = {"input": 0.001, "output": 0.001}  # fallback if model not in list


class CostTracker:
    
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)

    async def track(self, tenant_id: str, model: str, input_tokens: int, output_tokens: int):
        costs = COST_PER_1K.get(model, DEFAULT_COST)
        cost = (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1000
        
        # store monthly total
        month_key = f"cost:{tenant_id}:{datetime.now().strftime('%Y-%m')}"
        await self.redis.incrbyfloat(month_key, cost)
        await self.redis.expire(month_key, 86400 * 35)  # keep for 35 days

    async def get_monthly_cost(self, tenant_id: str) -> float:
        key = f"cost:{tenant_id}:{datetime.now().strftime('%Y-%m')}"
        val = await self.redis.get(key)
        return round(float(val), 6) if val else 0.0
