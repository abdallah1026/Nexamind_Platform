from typing import Any, Dict
from ..base_agent import BaseAgent

class RevenueForecasterAgent(BaseAgent):
    name = "revenue_forecaster_agent"
    module = "sales"
    description = "Revenue predictions and pipeline analysis"
    tools = ["sql_tool", "calculation_tool", "api_tool", "rag_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Revenue Forecaster Agent for NexaMind Sales Platform.
Your role is to provide accurate revenue forecasts and pipeline insights.

Forecasting methodology:
- Weighted pipeline (probability-adjusted)
- Stage-based conversion rate analysis
- Rep-level performance modeling
- Seasonality and historical pattern matching
- Deal slippage prediction
- Commit vs best case vs worst case scenarios

Key metrics:
- Pipeline coverage ratio (target: 3-4x quota)
- Win rate by stage, rep, product
- Average deal size and sales cycle length
- Forecast accuracy (track against actuals)

Always segment forecasts: by rep, region, product line, and segment."""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        
        pipeline = await sql.execute(
            """SELECT stage, COUNT(*) as deals, SUM(amount) as total_value,
                AVG(probability) as avg_probability,
                SUM(amount * probability / 100) as weighted_value
            FROM deals
            WHERE tenant_id = :tenant_id AND status = 'open'
            GROUP BY stage ORDER BY weighted_value DESC""",
            {"tenant_id": self.tenant_id}
        )
        
        messages = [{"role": "user", "content": f"""
Request: {user_input}

Sales Pipeline Summary:
{pipeline}

Provide revenue forecast and pipeline analysis."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.2)
        return {"response": response, "pipeline_stages": pipeline.get("count", 0)}
